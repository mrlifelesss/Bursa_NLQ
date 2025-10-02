from __future__ import annotations

import os
import re
from typing import Dict, List, Optional, Tuple

from .models import QueryParseResult, TimeFrame
from .text_utils import _normalize_text, _remove_stop_words
from .aliases import (
    _expand_company_aliases,
    _expand_report_aliases,
    _find_aliases,
    _find_aliases_fuzzy,
)
from .reports import _postprocess_reports
from .timeframes import _extract_timeframe, _relative_to_absolute
from .quantity import _extract_quantity
from .scoring import _calculate_coverage_confidence
from . import constants as _C

try:
    from .llm import _parse_with_gemma
except Exception:  # pragma: no cover
    def _parse_with_gemma(*args, **kwargs):  # type: ignore
        return None


def _synthesize_query_from_result(r: QueryParseResult) -> str:
    """Build a plain text query from a QueryParseResult to re-run heuristics."""
    parts: List[str] = []
    if r.companies:
        parts.append(" ".join(map(str, r.companies)))
    if r.report_types:
        parts.append(" ".join(map(str, r.report_types)))
    tf_snippet = None
    try:
        if r.time_frame and getattr(r.time_frame, "raw", None):
            tf_snippet = r.time_frame.raw
        elif r.time_frame and r.time_frame.kind == "absolute" and r.time_frame.start_date and r.time_frame.end_date:
            tf_snippet = f"{r.time_frame.start_date.isoformat()} {r.time_frame.end_date.isoformat()}"
    except Exception:
        tf_snippet = None
    if tf_snippet:
        parts.append(tf_snippet)
    return " ".join(p for p in parts if p)


def parse_nlq(
    text: str,
    company_aliases: Dict[str, List[str]],
    report_aliases: Dict[str, List[str]],
    auto_expand_aliases: bool = True,
    allow_llm_fallback: bool = True,
    force_absolute_timeframe: bool = True,
) -> QueryParseResult:
    res = QueryParseResult()
    res.notes.append("Begin heuristic parsing.")

    # Remove stop words before most steps and normalize
    filtered_text = _remove_stop_words(text)
    norm_text = _normalize_text(filtered_text)
    # Keep a normalized version of the raw input for timeframe parsing (to keep cues like 'מאז', 'מתחילת')
    raw_norm_text = _normalize_text(text)
    all_found_spans: List[Tuple[int, int]] = []

    # Expand alias dictionaries (if requested)
    comp_aliases = _expand_company_aliases(company_aliases) if auto_expand_aliases else company_aliases
    rep_aliases = _expand_report_aliases(report_aliases) if auto_expand_aliases else report_aliases

    # Build lookups {alias phrase -> canonical}
    comp_lookup = {phrase: canon for canon, arr in comp_aliases.items() for phrase in (arr or [])}
    comp_lookup = dict(sorted(comp_lookup.items(), key=lambda kv: len(kv[0]), reverse=True))
    rep_lookup = {phrase: canon for canon, arr in rep_aliases.items() for phrase in (arr or [])}
    rep_lookup = dict(sorted(rep_lookup.items(), key=lambda kv: len(kv[0]), reverse=True))

    # Companies: run on raw normalized text (avoid losing names made of stop-words like "אל על")
    companies, comp_map, comp_notes, comp_spans = _find_aliases(raw_norm_text, comp_lookup)
    if not companies:
        fuzzy_companies, fuzzy_comp_map, fuzzy_notes, fuzzy_spans = _find_aliases_fuzzy(raw_norm_text, comp_lookup)
        if fuzzy_companies:
            companies, comp_map = fuzzy_companies, fuzzy_comp_map
            comp_notes.extend(["companies:fallback_fuzzy"] + fuzzy_notes)
            comp_spans.extend(fuzzy_spans)
    res.companies = companies
    res.matched_company_aliases = comp_map
    res.notes.extend(comp_notes)
    all_found_spans.extend(comp_spans)

    # Reports: exact first, then fuzzy fallback if nothing found
    reports, rep_map, rep_notes, rep_spans = _find_aliases(norm_text, rep_lookup, allow_overlaps=True, prioritize_full_match=True)
    if not reports:
        fuzzy_reports, fuzzy_rep_map, fuzzy_notes, fuzzy_spans = _find_aliases_fuzzy(norm_text, rep_lookup, allow_overlaps=True)
        if fuzzy_reports:
            reports, rep_map = fuzzy_reports, fuzzy_rep_map
            rep_notes.extend(["reports:fallback_fuzzy"] + fuzzy_notes)
            rep_spans.extend(fuzzy_spans)
    reports = _postprocess_reports(reports, norm_text)
    res.report_types = reports
    res.matched_report_aliases = rep_map
    res.notes.extend(rep_notes)
    all_found_spans.extend(rep_spans)

    # Timeframe — parse on raw normalized text to preserve cues removed as stop-words
    tf, tf_notes, tf_span = _extract_timeframe(raw_norm_text)
    if force_absolute_timeframe and tf.kind == "relative":
        tf = _relative_to_absolute(tf)
        tf_notes.append("tf:forced_absolute")
    res.time_frame = tf
    res.notes.extend(tf_notes)
    if tf_span:
        all_found_spans.append(tf_span)

    # Quantity (prefer number tied to report phrase; ignore timeframe numbers)
    rep_union = "|".join([re.escape(p) for p in sorted(rep_lookup.keys(), key=len, reverse=True)])
    near_re = re.compile(rf"(?<!\d)(\d{{1,4}})(?!\d)\s+(?:{rep_union})", re.IGNORECASE) if rep_union else None
    # Block numbers inside the detected timeframe span as well as report spans
    extra_blocks = list(rep_spans)
    if tf_span:
        extra_blocks.append(tf_span)
    qty, qty_notes, qty_span = _extract_quantity(norm_text, near_re, extra_blocked_spans=extra_blocks)
    res.quantity = qty
    res.notes.extend(qty_notes)
    if qty_span:
        all_found_spans.append(qty_span)

    # Confidence
    res.confidence = _calculate_coverage_confidence(norm_text, all_found_spans)

    # Compose a sentence from tokens covered by heuristics
    def _overlaps(a, b):
        return max(a[0], b[0]) < min(a[1], b[1])

    tokens = list(re.finditer(r"\b\w+\b", norm_text))
    covered_tokens = [t.group(0) for t in tokens if any(_overlaps(t.span(), s) for s in all_found_spans)]
    heuristics_sentence = " ".join(covered_tokens)
    res.heuristics_understood_text = heuristics_sentence or None
    res.final_understood_text = heuristics_sentence or None

    # Fallback to LLM if needed
    is_empty = not res.companies and not res.report_types and res.quantity is None and res.time_frame.kind == "none"
    needs_llm = False  # can be toggled by keywords if desired

    # Early classification for invalid/irrelevant intents (stock price, advice, SQL), independent of Hebrew presence
    price_re = re.compile(r"\b(?:מחיר|שער)\s+מנ(?:יה|יית)\b")
    advice_re = re.compile(r"\bכדאי\s+להשקיע\b|\bלהשקיע\b.*\bכדאי\b|\bשוק\s+ההון\b|\bלקנות\s+עכשיו\b|\bלמכור\s+עכשיו\b")
    sql_re = re.compile(r"\b(SELECT|INSERT|UPDATE|DELETE)\b", flags=re.IGNORECASE)
    if price_re.search(text):
        res.error = "Unintelligible query: The query is about stock prices, not company announcements."
        res.notes.append(f"Error: {res.error}")
        res.confidence = 0.0
        return res
    if advice_re.search(text):
        res.error = "Unintelligible query: The query is a request for financial advice, not a search."
        res.notes.append(f"Error: {res.error}")
        res.confidence = 0.0
        return res
    if sql_re.search(text):
        res.error = "Unintelligible query: Input contains invalid characters or patterns."
        res.notes.append(f"Error: {res.error}")
        res.confidence = 0.0
        return res

    # Early handling for unintelligible queries to avoid LLM overriding the error
    has_hebrew = bool(re.search(r"[\u0590-\u05FF]", text))
    vague_re = re.compile(r"\b(תחפש|חפש|תמצא|מצא|תבדוק|בדוק|בבקשה)\b")
    is_vague_hebrew = is_empty and has_hebrew and bool(vague_re.search(text)) and (len(text.strip()) <= 25)
    if is_empty and (not has_hebrew or is_vague_hebrew):
        res.confidence = 0.0
        if not has_hebrew:
            error_msg = "Unintelligible query: No recognized keywords, company names, or numbers found."
        else:
            error_msg = "Unintelligible query: The input is too short or vague to be a valid query."
        res.error = error_msg
        res.notes.append(f"Error: {error_msg}")
        return res

    if allow_llm_fallback and (needs_llm or is_empty or res.confidence < 1):
        res.notes.append(
            f"Heuristics insufficient (Keywords: {needs_llm}, Empty: {is_empty}, Confidence: {res.confidence:.2f}). Escalating to LLM."
        )
        # Send the original text to LLM to avoid losing names via stop-word removal
        llm_result = _parse_with_gemma(text, company_aliases, report_aliases)
        if llm_result is not None:
            # Option B: replace LLM result entirely with heuristic re-parse of synthesized sentence
            final_sentence = _synthesize_query_from_result(llm_result)
            if final_sentence:
                # Re-run heuristics on the synthesized sentence, with LLM disabled
                heur_res = parse_nlq(
                    final_sentence,
                    company_aliases,
                    report_aliases,
                    auto_expand_aliases=auto_expand_aliases,
                    allow_llm_fallback=False,
                    force_absolute_timeframe=force_absolute_timeframe,
                )
                # Preserve diagnostics and raw LLM text
                pre_understood = heuristics_sentence or None
                post_understood = heur_res.heuristics_understood_text
                heur_res.heuristics_understood_text = pre_understood
                heur_res.final_understood_text = post_understood
                heur_res.llm_raw = getattr(llm_result, "llm_raw", None)
                # Prefer LLM absolute timeframe over any heuristic reparse result
                if getattr(llm_result, "time_frame", None) and llm_result.time_frame.kind == "absolute":
                    heur_res.time_frame = llm_result.time_frame
                    heur_res.notes.append("carry:timeframe_from_llm:absolute_preferred")
                # Otherwise, if we still have relative and forcing absolute is enabled, convert
                if force_absolute_timeframe and heur_res.time_frame.kind == "relative":
                    heur_res.time_frame = _relative_to_absolute(heur_res.time_frame)
                    heur_res.notes.append("tf:forced_absolute")
                # Carry-through: preserve LLM-derived timeframe/types if heuristics dropped them
                if heur_res.time_frame.kind == "none" and llm_result.time_frame.kind != "none":
                    heur_res.time_frame = llm_result.time_frame
                    heur_res.notes.append("carry:timeframe_from_llm")
                if (not heur_res.report_types) and getattr(llm_result, "report_types", None):
                    heur_res.report_types = list(llm_result.report_types)
                    heur_res.notes.append("carry:report_types_from_llm")
                heur_res.notes = (
                    res.notes
                    + llm_result.notes
                    + heur_res.notes
                    + [f"Reparsed synthesized sentence with heuristics: '{final_sentence}' (Option B)"]
                )
                return heur_res
            else:
                # Fallback: keep LLM result if we cannot build a synthesized sentence
                llm_result.notes = res.notes + llm_result.notes + ["LLM used; no synthesized sentence."]
                llm_result.heuristics_understood_text = heuristics_sentence or None
                llm_result.final_understood_text = None
                return llm_result

    # Error heuristic for unintelligible queries (kept for completeness)
    is_unintelligible = is_empty and not re.search(r"[\u0590-\u05FF]", text)
    if is_unintelligible:
        res.confidence = 0.0
        error_msg = "Unintelligible query: No recognized keywords, company names, or numbers found."
        if len(text.strip()) < 3:
            error_msg = "Unintelligible query: The input is too short to be a valid query."
        elif re.search(r"\b(SELECT|INSERT|UPDATE|DELETE)\b", text, flags=re.IGNORECASE):
            error_msg = "Unintelligible query: Input contains invalid characters or patterns."
        res.error = error_msg
        res.notes.append(f"Error: {error_msg}")

    return res


def parse_nlq_batch(
    texts: List[str],
    company_aliases: Dict[str, List[str]],
    report_aliases: Dict[str, List[str]],
    auto_expand_aliases: bool = True,
    allow_llm_fallback: bool = True,
    force_absolute_timeframe: bool = True,
) -> List[QueryParseResult]:
    """Batch version: runs heuristics for all inputs, then sends only the ones
    that need escalation to the LLM in a single batch call, and applies Option B
    (re-parse synthesized sentence with heuristics)."""
    results: List[QueryParseResult] = []
    heuristics_only: List[QueryParseResult] = []
    # First pass: heuristics only, no LLM
    for t in texts:
        hres = parse_nlq(
            t,
            company_aliases,
            report_aliases,
            auto_expand_aliases=auto_expand_aliases,
            allow_llm_fallback=False,
            force_absolute_timeframe=force_absolute_timeframe,
        )
        heuristics_only.append(hres)

    # Decide which need LLM
    need_idx: List[int] = []
    for i, r in enumerate(heuristics_only):
        is_empty = not r.companies and not r.report_types and r.quantity is None and r.time_frame.kind == "none"
        # Do not escalate if heuristics already concluded it's unintelligible (preserve error)
        if allow_llm_fallback and (r.error is None) and (is_empty or (r.confidence < 1)):
            need_idx.append(i)

    if allow_llm_fallback and need_idx:
        # Batch LLM call only for needed indices
        from .llm import _parse_with_gemma_batch  # local import to avoid hard dep when unused
        # Send original texts to the LLM (do not remove stop words so names like "אל על" remain)
        texts_needed = [texts[i] for i in need_idx]
        llm_results = _parse_with_gemma_batch(texts_needed, company_aliases, report_aliases)
        # Apply Option B per needed item
        for j, i in enumerate(need_idx):
            lr = llm_results[j]
            if lr is None:
                # Keep heuristics-only result
                continue
            final_sentence = _synthesize_query_from_result(lr)
            if final_sentence:
                heur_res = parse_nlq(
                    final_sentence,
                    company_aliases,
                    report_aliases,
                    auto_expand_aliases=auto_expand_aliases,
                    allow_llm_fallback=False,
                    force_absolute_timeframe=force_absolute_timeframe,
                )
                pre_understood = heuristics_only[i].heuristics_understood_text
                post_understood = heur_res.heuristics_understood_text
                heur_res.heuristics_understood_text = pre_understood
                heur_res.final_understood_text = post_understood
                heur_res.llm_raw = getattr(lr, "llm_raw", None)
                # Prefer LLM absolute timeframe over any heuristic reparse result
                if getattr(lr, "time_frame", None) and lr.time_frame.kind == "absolute":
                    heur_res.time_frame = lr.time_frame
                    heur_res.notes.append("carry:timeframe_from_llm:absolute_preferred")
                # Otherwise, if we still have relative and forcing absolute is enabled, convert
                if force_absolute_timeframe and heur_res.time_frame.kind == "relative":
                    heur_res.time_frame = _relative_to_absolute(heur_res.time_frame)
                    heur_res.notes.append("tf:forced_absolute")
                # Carry-through: preserve LLM-derived timeframe/types if heuristics dropped them
                if heur_res.time_frame.kind == "none" and lr.time_frame.kind != "none":
                    heur_res.time_frame = lr.time_frame
                    heur_res.notes.append("carry:timeframe_from_llm")
                if (not heur_res.report_types) and getattr(lr, "report_types", None):
                    heur_res.report_types = list(lr.report_types)
                    heur_res.notes.append("carry:report_types_from_llm")
                heur_res.notes = (
                    heuristics_only[i].notes + lr.notes + heur_res.notes + [
                        f"Reparsed synthesized sentence with heuristics: '{final_sentence}' (Option B, batch)"
                    ]
                )
                heuristics_only[i] = heur_res
            else:
                lr.heuristics_understood_text = heuristics_only[i].heuristics_understood_text
                lr.final_understood_text = None
                # Preserve heuristics error if LLM didn't set one
                if getattr(lr, "error", None) is None and getattr(heuristics_only[i], "error", None):
                    lr.error = heuristics_only[i].error
                lr.notes = heuristics_only[i].notes + lr.notes + ["LLM used; no synthesized sentence (batch)."]
                heuristics_only[i] = lr

    results = heuristics_only
    return results
