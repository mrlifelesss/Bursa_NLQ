from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

# Prefer RapidFuzz for speed and licensing; fallback to TheFuzz if unavailable
try:  # pragma: no cover
    from rapidfuzz import fuzz, process as fuzz_process  # type: ignore
except Exception:  # pragma: no cover
    from thefuzz import fuzz, process as fuzz_process  # type: ignore

from .constants import (
    _DEF_PLURAL_FLIPS,
    _DEF_REPORT_EXTRAS,
    _DEF_HYPHENS,
    _HEBREW_STOP_WORDS,
)
from .text_utils import _normalize_text


# Allow a Hebrew one-letter prefix (ב/ל/כ/ו/ה/מ/ש) optionally with hyphen before alias
_HEB_PREFIX = r"(?:[בלכוהמש]-?)?"  # optional


def _expand_company_aliases(dic: Dict[str, List[str]]) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for canon, arr in dic.items():
        aliases = set(arr or [])
        aliases.add(canon)
        expanded = set()
        for a in aliases:
            if not a:
                continue
            n = a.strip()
            n = re.sub(f"[{_DEF_HYPHENS}]", "-", n)
            n = re.sub(r"\s+", " ", n).strip(" -.,")
            expanded.add(n)
            # strip legal suffix
            _LEGAL_SUFFIX_RE = re.compile(r"\s*(?:\(?\s*ח[\"\"?'\"]?ל\s*\)?\.?|\bLTD\b\.?|\bLtd\b\.?|\bLimited\b\.?)\s*$", re.IGNORECASE)
            n2 = _LEGAL_SUFFIX_RE.sub("", n).strip(" -.,")
            if n2:
                expanded.add(n2)
            # remove quotes variants
            n3 = n2.replace('"', '').replace("״", '').replace("'", '').strip()
            if n3:
                expanded.add(n3)
        out[canon] = list(dict.fromkeys(sorted(expanded, key=lambda s: (len(s), s))))
    return out


def _expand_report_aliases(dic: Dict[str, List[str]]) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for canon, arr in dic.items():
        aliases = set(arr or [])
        aliases.add(canon)
        expanded = set()
        for a in aliases:
            if not a:
                continue
            n = re.sub(r"\s+", " ", a).strip(" -.,")
            expanded.add(n)
            for a_, b_ in _DEF_PLURAL_FLIPS:
                if a_ in n:
                    expanded.add(n.replace(a_, b_))
            if n in _DEF_REPORT_EXTRAS:
                for extra in _DEF_REPORT_EXTRAS[n]:
                    expanded.add(extra)
        out[canon] = list(dict.fromkeys(sorted(expanded, key=lambda s: (len(s), s))))
    return out


def _find_aliases(
    text: str,
    phrase_lookup: Dict[str, str],
    *,
    keep_top_k: Optional[int] = None,
    prefer_longest: bool = True,
    allow_overlaps: bool = False,
    prioritize_full_match: bool = False,
) -> Tuple[List[str], Dict[str, str], List[str], List[Tuple[int, int]]]:
    """
    Span-aware alias selection:
    - Prefer longer, more-specific aliases
    - Suppress overlapping matches across different canonicals
    - Returns: canonicals, matched_aliases, notes, and a list of character spans.
    """
    notes: List[str] = []
    norm = _normalize_text(text)

    # normalize phrases to align with normalized text
    phrase_lookup_norm: Dict[str, str] = {}
    for phrase, canonical in phrase_lookup.items():
        pnorm = _normalize_text(phrase)
        phrase_lookup_norm[pnorm] = canonical

    candidates: List[Tuple[int, int, str, str, int]] = []
    for phrase, canonical in phrase_lookup_norm.items():
        if not phrase:
            continue
        p = re.escape(phrase)
        pattern = rf"(?<!\S){_HEB_PREFIX}{p}(?!\S)"
        for m in re.finditer(pattern, norm, flags=re.IGNORECASE):
            tok_count = len(phrase.split())
            candidates.append((m.start(), m.end(), phrase, canonical, tok_count))

    if not candidates:
        if phrase_lookup:
            notes.append("No alias matches found.")
        return [], {}, notes, []

    if prioritize_full_match:
        full = [(s, e, ph, ca, tc) for (s, e, ph, ca, tc) in candidates if s == 0 and e == len(norm)]
        if full:
            candidates = full

    # sort: more tokens -> longer span -> earlier position
    if prefer_longest:
        candidates.sort(key=lambda t: (-t[4], -(t[1] - t[0]), t[0]))
    else:
        candidates.sort(key=lambda t: (t[0], -t[4], -(t[1] - t[0])))

    selected: List[Tuple[int, int, str, str, int]] = []
    used_spans: List[Tuple[int, int]] = []
    seen_canonicals: set = set()

    def overlaps(a: Tuple[int, int], b: Tuple[int, int]) -> bool:
        return not (a[1] <= b[0] or b[1] <= a[0])

    for start, end, phrase, canonical, tok_count in candidates:
        if canonical in seen_canonicals:
            continue
        span = (start, end)
        is_sub_match = any(s[0] <= span[0] and s[1] >= span[1] and s != span for s in used_spans)
        if is_sub_match and not allow_overlaps:
            continue
        if (not allow_overlaps) and any(overlaps(span, s) for s in used_spans):
            continue
        selected.append((start, end, phrase, canonical, tok_count))
        used_spans.append(span)
        seen_canonicals.add(canonical)
        if keep_top_k is not None and len(seen_canonicals) >= keep_top_k:
            break

    found: Dict[str, List[str]] = {}
    for _, _, phrase, canon, _ in selected:
        if canon not in found:
            found[canon] = []
        if phrase not in found[canon]:
            found[canon].append(phrase)

    canonicals = sorted(list(found.keys()))
    final_map = {c: v[0] for c, v in found.items()}
    return canonicals, final_map, notes, used_spans


def _find_aliases_fuzzy(
    text: str,
    phrase_lookup: Dict[str, str],
    *,
    score_threshold: int = 90,
    allow_overlaps: bool = False,
) -> Tuple[List[str], Dict[str, str], List[str], List[Tuple[int, int]]]:
    """
    Finds aliases using fuzzy matching with extra guards against false positives.
    - Uses WRatio for robust, length-aware matching.
    - Suppresses overlapping matches.
    - Ignores trivial matches on very short words.
    - Strips punctuation from candidates before matching.
    """
    notes: List[str] = []
    norm = _normalize_text(text)
    all_aliases = sorted(phrase_lookup.keys(), key=len, reverse=True)
    candidates = []
    text_tokens = norm.split()

    for n in range(1, len(text_tokens) + 1):
        for i in range(len(text_tokens) - n + 1):
            sub_sequence = " ".join(text_tokens[i : i + n])
            clean_sub_sequence = sub_sequence.strip('.,?!;:"\'')
            sub_tokens = clean_sub_sequence.split()
            if all(token in _HEBREW_STOP_WORDS for token in sub_tokens):
                continue
            if len(clean_sub_sequence) <= 2 and clean_sub_sequence not in phrase_lookup:
                continue
            for alias in all_aliases:
                max_len_ratio = 2.5 if len(alias) < 10 else 1.5
                if len(clean_sub_sequence) > len(alias) * max_len_ratio:
                    continue
                # Use WRatio (RapidFuzz or TheFuzz depending on availability)
                score = fuzz.WRatio(clean_sub_sequence, alias)
                if score >= score_threshold:
                    # Coverage guard: avoid matching a tiny fragment of a long alias
                    alias_norm = _normalize_text(alias)
                    alias_clean = alias_norm.strip('.,?!;:"\'')
                    alias_len = max(1, len(alias_clean.replace(' ', '')))
                    match_len = len(clean_sub_sequence.replace(' ', ''))
                    coverage_char = match_len / alias_len
                    # Require either decent character coverage or at least 2 tokens matched
                    if coverage_char < 0.6 and len(sub_tokens) < 2:
                        continue
                    start_pos = norm.find(clean_sub_sequence)
                    if start_pos == -1:
                        continue
                    end_pos = start_pos + len(clean_sub_sequence)
                    canonical = phrase_lookup[alias]
                    candidates.append((start_pos, end_pos, canonical, clean_sub_sequence, score))

    if not candidates:
        notes.append("No fuzzy alias matches found.")
        return [], {}, notes, []

    candidates.sort(key=lambda t: (-t[4], -(t[1] - t[0])))

    selected: Dict[str, str] = {}
    used_spans: List[Tuple[int, int]] = []

    def overlaps(a: Tuple[int, int], b: Tuple[int, int]) -> bool:
        return not (a[1] <= b[0] or b[1] <= a[0])

    for start, end, canonical, matched_text, score in candidates:
        if canonical in selected:
            continue
        span = (start, end)
        if (not allow_overlaps) and any(overlaps(span, s) for s in used_spans):
            continue
        selected[canonical] = matched_text
        used_spans.append(span)
        notes.append(f"Fuzzy match for '{canonical}': found '{matched_text}' with score {score}")

    canonicals = sorted(list(selected.keys()))
    final_spans = list(used_spans)
    return canonicals, selected, notes, final_spans
