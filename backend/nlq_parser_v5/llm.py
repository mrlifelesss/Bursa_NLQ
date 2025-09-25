from __future__ import annotations

import json
import os
import re
from typing import Dict, List, Optional, Tuple
import datetime as dt
from pathlib import Path

# Prefer RapidFuzz; fallback to TheFuzz if unavailable
try:  # pragma: no cover
    from rapidfuzz import process as fuzz_process  # type: ignore
    from rapidfuzz import fuzz as fuzz_ratio  # type: ignore
except Exception:  # pragma: no cover
    from thefuzz import process as fuzz_process  # type: ignore
    from thefuzz import fuzz as fuzz_ratio  # type: ignore

try:
    from google import genai  # type: ignore
    from google.genai import types  # type: ignore
    from google.genai.errors import ClientError  # type: ignore
except Exception:  # pragma: no cover
    genai = None
    types = None
    ClientError = Exception  # type: ignore

from .models import QueryParseResult, TimeFrame
from .reports import _load_title_events
from .text_utils import _unique_preserve
from .timeframes import _extract_timeframe
from .text_utils import _get_today


# --- Fuzzy-canonicalization helpers (module-level, shared by LLM callers) ---
def get_field(obj: dict, keys: List[str]) -> Optional[str]:
    for k in keys:
        if k in obj and obj[k]:
            return obj[k]
    return None


def fuzzy_canonize(
    items: List[str],
    alias_map: Dict[str, List[str]],
    *,
    fallback_raw: bool = False,
    threshold: int = 75,
) -> List[str]:
    """Pick the single best canonical for each item using process.extractOne.
    If extractOne doesn't reach `threshold`, fallback to comparing with
    partial_ratio and use that if it meets the threshold. Optionally
    preserve raw items when no match is found and fallback_raw is True.
    """
    if not items or not alias_map:
        return list(dict.fromkeys(items)) if fallback_raw else []
    flat = {alias: canon for canon, arr in alias_map.items() for alias in (arr or [])}
    keys = list(flat.keys())
    out = set()
    for it in items:
        try:
            best = fuzz_process.extractOne(it, keys)
        except Exception:
            best = None
        used = False
        if best and best[1] >= threshold:
            out.add(flat[best[0]])
            used = True
        else:
            # fallback: try partial_ratio across keys
            best_partial = None
            best_score = 0
            for k in keys:
                try:
                    score = fuzz_ratio.partial_ratio(str(it), k)
                except Exception:
                    score = 0
                if score > best_score:
                    best_score = score
                    best_partial = k
            if best_partial and best_score >= threshold:
                print(f"fuzzy_canonize fallback: input='{it}', alias='{best_partial}', score={best_score} (partial_ratio)")
                out.add(flat[best_partial])
                used = True
        if (not used) and fallback_raw and it:
            out.add(it)
    return sorted(out)


def fuzzy_canonize_multi(
    items: List[str],
    alias_map: Dict[str, List[str]],
    *,
    threshold: int = 70,
    allow_partial_fallback: bool = True,
) -> List[str]:
    """Return canonical names whose aliases fuzz-match any item, ordered by max score desc.
    First try WRatio; if nothing is found and allow_partial_fallback is True,
    retry using partial_ratio to capture shorter/partial matches.
    """
    if not items or not alias_map:
        return []
    scores: Dict[str, int] = {}
    debug_matches: List[Tuple[str, str, int, str]] = []  # (input, alias, score, method)

    def _run_compare(method_name: str):
        for it in items:
            it_s = str(it or "").strip()
            if not it_s:
                continue
            for canon, aliases in alias_map.items():
                for alias in (aliases or []):
                    try:
                        if method_name == 'wratio':
                            score = fuzz_ratio.WRatio(it_s, alias)
                        else:
                            score = fuzz_ratio.partial_ratio(it_s, alias)
                    except Exception:
                        score = 0
                    if score >= threshold:
                        debug_matches.append((it_s, alias, score, method_name))
                        prev = scores.get(canon, 0)
                        if score > prev:
                            scores[canon] = score

    # First try with WRatio
    _run_compare('wratio')

    # If nothing found, try partial_ratio as a fallback and mark the method in debug
    if not scores and allow_partial_fallback:
        _run_compare('partial')

    ordered = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    return [c for c, _ in ordered]



def _read_prompt_template(filename: str, **fmt: str) -> Optional[str]:
    """Load and format a prompt template from prompts/<filename>.
    Cleans up templates copied from code strings (quoted lines, escaped \n).
    Returns None on failure.
    """
    try:
        base = Path(__file__).resolve().parent / "prompts" / filename
        raw = base.read_text(encoding="utf-8")
        lines = raw.splitlines()
        cleaned: List[str] = []
        for ln in lines:
            t = ln.strip()
            if (t.startswith('f"') and t.endswith('"')):
                t = t[2:-1]
            elif (t.startswith('"') and t.endswith('"')):
                t = t[1:-1]
            cleaned.append(t)
        s = "\n".join(cleaned)
        s = s.replace("\\n", "\n").replace("\\t", "\t").replace("\\\"", '"')
        return s.format(**fmt)
    except Exception:
        return None


def _parse_with_gemma(
    text: str,
    company_aliases: Dict[str, List[str]],
    report_aliases: Dict[str, List[str]],
    model_name: str = "models/gemma-3-27b-it" #models/gemma-3-27b-it", models/gemini-2.5-pro
) -> Optional[QueryParseResult]:
    """Parse via Google GenAI (Gemma/Gemini) as a fallback. Returns None if unavailable."""
    if genai is None:
        return None

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None

    today = _get_today().isoformat()
    prompt = _read_prompt_template("NLQParseSingle_v1.txt", today=today, text=text)
    if not prompt:
        prompt = f"Today is {today}. Convert this Hebrew query to JSON: {text}"
    try:
        client = genai.Client(api_key=api_key)  # type: ignore
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.1) if types else None,  # type: ignore
        )
        response_text = getattr(response, "text", None) or ""
        m = re.search(r"\{.*\}", response_text, re.DOTALL)
        if not m:
            return None
        data = json.loads(m.group(0))

        res = QueryParseResult()
        # Keep the raw textual output for auditing/testing downloads
        res.llm_raw = response_text

        # Canonicalize via fuzzy against alias maps (use shared helpers)
        res.companies = fuzzy_canonize(data.get("companies", []) or [], company_aliases, fallback_raw=True)
        # For report types, include all plausible matches (not just best one), ordered by confidence
        res.report_types = fuzzy_canonize_multi(data.get("report_types", []) or [], report_aliases)
        # Expand titles (if any) to their subtypes; also expand custom combined label
        try:
            title_map = _load_title_events()
        except Exception:
            title_map = {}
        expanded = list(res.report_types)
        for rt in list(res.report_types):
            if rt in title_map:
                expanded.extend(title_map.get(rt, []))
            if rt == "מיזוגים ופיצולים":
                expanded.extend(["מיזוג פעילות/חברה", "פיצול פעילות/חברה"])
        res.report_types = _unique_preserve(expanded)

        q = data.get("quantity")
        res.quantity = int(q) if isinstance(q, int) else None

        # Timeframe: prefer absolute START/END in LLM output; fallback to time_frame_text
        start_s = get_field(data, ["START Date", "Start Date", "start_date", "START_DATE"]) or None
        end_s = get_field(data, ["END Date", "End Date", "end_date", "END_DATE"]) or None
        if start_s and end_s:
            try:
                sd = dt.date.fromisoformat(str(start_s).strip())
                ed = dt.date.fromisoformat(str(end_s).strip())
                res.time_frame = TimeFrame(kind="absolute", start_date=sd, end_date=ed, raw=f"{sd.isoformat()}..{ed.isoformat()}")
                res.notes.append("tf:from_llm_absolute")
            except Exception:
                pass
        if res.time_frame.kind == "none":
            tf_text = get_field(data, ["time_frame_text", "timeframe_text", "time_frame"]) or None
            if tf_text:
                tf, tf_notes, _ = _extract_timeframe(tf_text)
                res.time_frame = tf
                res.notes.extend(tf_notes)

        res.notes.append(f"Parsed with LLM ({model_name}).")
        return res

    except ClientError:  # type: ignore
        return None
    except Exception:
        return None


def _parse_with_gemma_batch(
    texts: List[str],
    company_aliases: Dict[str, List[str]],
    report_aliases: Dict[str, List[str]],
    model_name: str = "models/gemma-3-27b-it" #models/gemma-3-27b-it", models/gemini-2.5-pro
) -> List[Optional[QueryParseResult]]:
    """Batch LLM parsing: sends multiple queries in one prompt if possible.
    Returns a list aligned with inputs; None entries indicate failure for that item.
    Falls back to per-item calls if batch parsing fails.
    """
    if genai is None:
        return [None] * len(texts)

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return [None] * len(texts)

    try:
        client = genai.Client(api_key=api_key)  # type: ignore

        # Instruct model to return a JSON array of objects in index order
        numbered = "\n".join([f"{i}: {t}" for i, t in enumerate(texts)])
        today = _get_today().isoformat()
        prompt = _read_prompt_template("NLQParseBatch-v1.txt", today=today, numbered=numbered)
        if not prompt:
            prompt = f"Today is {today}. Return a JSON array of parsed objects for these queries with 'index':\n{numbered}"

        response = client.models.generate_content(  # type: ignore
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.1) if types else None,  # type: ignore
        )
        response_text = getattr(response, "text", None) or ""
        m = re.search(r"\[.*\]", response_text, re.DOTALL)
        if not m:
            raise ValueError("Batch LLM did not return a JSON array")
        arr = json.loads(m.group(0))
        if not isinstance(arr, list):
            raise ValueError("Batch LLM returned non-list JSON")

        # Canonicalization helper
        def _canonize(items: List[str], alias_map: Dict[str, List[str]], *, fallback_raw: bool = False, threshold: int = 75) -> List[str]:
            try:
                from rapidfuzz import process as _proc  # type: ignore
            except Exception:
                from thefuzz import process as _proc  # type: ignore
            if not items or not alias_map:
                return list(dict.fromkeys(items)) if fallback_raw else []
            flat = {alias: canon for canon, arr in alias_map.items() for alias in (arr or [])}
            keys = list(flat.keys())
            out = set()
            for it in items:
                try:
                    best = _proc.extractOne(it, keys)
                except Exception:
                    best = None
                used = False
                if best and best[1] >= threshold:
                    out.add(flat[best[0]])
                    used = True
                else:
                    # fallback to partial_ratio across keys
                    best_partial = None
                    best_score = 0
                    try:
                        from rapidfuzz import fuzz as _f  # type: ignore
                    except Exception:
                        from thefuzz import fuzz as _f  # type: ignore
                    for k in keys:
                        try:
                            score = _f.partial_ratio(str(it), k)
                        except Exception:
                            score = 0
                        if score > best_score:
                            best_score = score
                            best_partial = k
                    if best_partial and best_score >= threshold:
                        print(f"_canonize (batch) fallback: input='{it}', alias='{best_partial}', score={best_score} (partial_ratio)")
                        out.add(flat[best_partial])
                        used = True
                if (not used) and fallback_raw and it:
                    out.add(it)
            return sorted(out)

        def _canonize_multi(items: List[str], alias_map: Dict[str, List[str]], *, threshold: int = 70) -> List[str]:
            try:
                from rapidfuzz import fuzz as _f  # type: ignore
            except Exception:
                from thefuzz import fuzz as _f  # type: ignore
            if not items or not alias_map:
                return []
            scores: Dict[str, int] = {}

            def _run_compare_batch(method: str):
                for it in items:
                    it_s = str(it or "").strip()
                    if not it_s:
                        continue
                    for canon, aliases in alias_map.items():
                        for alias in (aliases or []):
                            try:
                                if method == 'wratio':
                                    score = _f.WRatio(it_s, alias)
                                else:
                                    score = _f.partial_ratio(it_s, alias)
                            except Exception:
                                score = 0
                            if score >= threshold:
                                prev = scores.get(canon, 0)
                                if score > prev:
                                    scores[canon] = score

            # Try WRatio first
            _run_compare_batch('wratio')
            # Fallback to partial_ratio if nothing found
            if not scores:
                _run_compare_batch('partial')

            ordered = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
            return [c for c, _ in ordered]

        results: List[Optional[QueryParseResult]] = [None] * len(texts)
        for obj in arr:
            if not isinstance(obj, dict):
                continue
            idx = obj.get("index")
            if not isinstance(idx, int) or not (0 <= idx < len(texts)):
                continue
            res = QueryParseResult()
            # Keep only the relevant per-item JSON object as llm_raw, not the whole batch array
            try:
                res.llm_raw = json.dumps(obj, ensure_ascii=False)
            except Exception:
                res.llm_raw = str(obj)
            res.companies = fuzzy_canonize(obj.get("companies", []) or [], company_aliases, fallback_raw=True)
            # For report types, include all plausible matches (not just best one), ordered by confidence
            res.report_types = fuzzy_canonize_multi(obj.get("report_types", []) or [], report_aliases)
            # Expand titles (if any) to their subtypes; also expand custom combined label
            try:
                title_map = _load_title_events()
            except Exception:
                title_map = {}
            expanded = list(res.report_types)
            for rt in list(res.report_types):
                if rt in title_map:
                    expanded.extend(title_map.get(rt, []))
                if rt == "מיזוגים ופיצולים":
                    expanded.extend(["מיזוג פעילות/חברה", "פיצול פעילות/חברה"])
            res.report_types = _unique_preserve(expanded)
            q = obj.get("quantity")
            res.quantity = int(q) if isinstance(q, int) else None
            # Timeframe: prefer absolute START/END directly
            start_s = get_field(obj, ["START Date", "Start Date", "start_date", "START_DATE"]) or None
            end_s = get_field(obj, ["END Date", "End Date", "end_date", "END_DATE"]) or None
            if start_s and end_s:
                try:
                    sd = dt.date.fromisoformat(str(start_s).strip())
                    ed = dt.date.fromisoformat(str(end_s).strip())
                    res.time_frame = TimeFrame(kind="absolute", start_date=sd, end_date=ed, raw=f"{sd.isoformat()}..{ed.isoformat()}")
                    res.notes.append("tf:from_llm_absolute")
                except Exception:
                    pass
            if res.time_frame.kind == "none":
                tf_text = get_field(obj, ["time_frame_text", "timeframe_text", "time_frame"]) or None
                if tf_text:
                    tf, tf_notes, _ = _extract_timeframe(tf_text)
                    res.time_frame = tf
                    res.notes.extend(tf_notes)
            res.notes.append(f"Parsed with LLM batch ({model_name}).")
            results[idx] = res

        # Any gaps? try per-item fallback for just those
        for i in range(len(texts)):
            if results[i] is None:
                results[i] = _parse_with_gemma(texts[i], company_aliases, report_aliases, model_name)
        return results
    except ClientError:  # type: ignore
        return [_parse_with_gemma(t, company_aliases, report_aliases, model_name) for t in texts]
    except Exception:
        return [_parse_with_gemma(t, company_aliases, report_aliases, model_name) for t in texts]
