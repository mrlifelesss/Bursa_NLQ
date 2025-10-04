from __future__ import annotations

import re
from typing import List, Tuple

from .constants import _HEBREW_STOP_WORDS


def _calculate_coverage_confidence(
    norm_text: str,
    all_spans: List[Tuple[int, int]],
) -> float:
    """Calculate confidence by coverage of non-stop-word tokens within matched spans."""
    all_tokens = list(re.finditer(r"\b\w+\b", norm_text))
    meaningful = [t for t in all_tokens if t.group(0) not in _HEBREW_STOP_WORDS]
    n = len(meaningful)
    if n == 0:
        return 0.0
    covered = set()
    for e_start, e_end in all_spans:
        for i, tok in enumerate(meaningful):
            t_start, t_end = tok.span()
            if max(e_start, t_start) < min(e_end, t_end):
                covered.add(i)
    return len(covered) / n

