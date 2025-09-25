from __future__ import annotations

import re
from typing import List, Optional, Tuple

from .text_utils import _normalize_text
from .timeframes import _absolute_date_spans, _absolute_number_token_spans
from .constants import _HEBREW_NUM_WORDS


def _extract_quantity(
    text: str,
    report_phrase_pattern: Optional[re.Pattern] = None,
    *,
    extra_blocked_spans: Optional[List[Tuple[int, int]]] = None,
) -> Tuple[Optional[int], List[str], Optional[Tuple[int, int]]]:
    """Extract a quantity, avoiding numbers that belong to timeframe/date phrases.
    Returns (quantity, notes, span) where span is the character span of the matched number.
    """
    notes: List[str] = []
    norm = _normalize_text(text)

    # 1) Number adjacent to a report phrase
    if report_phrase_pattern is not None:
        for m in report_phrase_pattern.finditer(norm):
            try:
                q = int(m.group(1))
            except ValueError:
                continue
            if 1900 <= q <= 2099:
                notes.append("qty:skip_year_like")
                continue
            notes.append("qty:adjacent_to_report")
            return q, notes, m.span(1)

    # 2) Block numbers part of timeframe/date fragments
    tf_num_spans: List[Tuple[int, int]] = []
    tf_re = re.compile(r"(?:\bמ-?)?(?P<num>\d{1,3})\s*(?:־)?(?P<unit>שעה|שעות|יום|ימים|שבוע|שבועות|חודש|חודשים|שנה|שנים)\s*(?:האחרון|האחרונה|האחרונים)?")
    for m in tf_re.finditer(norm):
        tf_num_spans.append(m.span("num"))

    abs_spans = _absolute_date_spans(norm)
    abs_token_spans = _absolute_number_token_spans(norm)
    blocked_spans: List[Tuple[int, int]] = []
    blocked_spans.extend(tf_num_spans)
    blocked_spans.extend(abs_spans)
    blocked_spans.extend(abs_token_spans)
    if extra_blocked_spans:
        blocked_spans.extend(extra_blocked_spans)

    def overlaps(i, j, a, b):
        return not (j <= a or b <= i)

    for m in re.finditer(r"(?<!\d)(\d{1,4})(?!\d)", norm):
        i, j = m.span(1)
        if any(overlaps(i, j, a, b) for (a, b) in blocked_spans):
            continue
        try:
            val = int(m.group(1))
        except ValueError:
            continue
        if 1900 <= val <= 2099:
            notes.append("qty:skip_year_like")
            continue
        return val, notes, m.span(1)

    # 3) Hebrew numerals (two-word, like "עשרים וחמש") – simplified composition
    for m in re.finditer(r"\b(\S+)\s+ו(\S+)\b", norm):
        w1, w2 = m.group(1), m.group(2)
        if w1 in _HEBREW_NUM_WORDS and w2 in _HEBREW_NUM_WORDS:
            val1 = _HEBREW_NUM_WORDS[w1]
            val2 = _HEBREW_NUM_WORDS[w2]
            if val1 > 10 and val2 < 10:
                return val1 + val2, notes, m.span()

    # 4) Single Hebrew numeral token
    for m in re.finditer(r"\S+", norm):
        tok = m.group(0)
        val = _HEBREW_NUM_WORDS.get(tok)
        if val is not None and tok not in ("שבועיים", "חודשיים", "שנתיים"):
            return val, notes, m.span()

    notes.append("No quantity extracted.")
    return None, notes, None
