from __future__ import annotations

import json
import os
import re
import datetime as dt
from pathlib import Path
from typing import Dict, List

from .constants import _HEBREW_STOP_WORDS


def _get_today() -> dt.date:
    s = os.getenv("NLQ_TEST_TODAY")
    if s:
        try:
            return dt.date.fromisoformat(s.strip())
        except Exception:
            pass
    return dt.date.today()


def _normalize_text(s: str) -> str:
    # Light normalization without harming Hebrew text.
    # Normalize quotes and dashes (incl. Hebrew maqaf U+05BE), remove RTL/LTR and NBSP marks
    # Invisible directionality and non-breaking spaces commonly appear in Hebrew text
    for ch in (
        "\u200f",  # RLM
        "\u200e",  # LRM
        "\u202a", "\u202b", "\u202c", "\u202d", "\u202e",  # embeddings/overrides
        "\u2066", "\u2067", "\u2068", "\u2069",  # directional isolates
        "\u00a0",  # NBSP
    ):
        s = s.replace(ch, " ")
    s = s.replace("-", "-").replace("-", "-").replace("?", "-")
    s = s.replace("\"", '"').replace("\"", '"').replace(",", '"').replace("?", '"')
    s = s.replace("'", "'").replace("`", "'").replace("?", "'").replace("?", '"')
    # Collapse whitespace, pad punctuation to help token-ish boundaries
    s = re.sub(r"[\t\r\f\v]", " ", s)
    s = re.sub(r"([.,:;!?()\[\]{}\-\/\\\"'])", r" \1 ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _remove_stop_words(text: str) -> str:
    """Normalize and remove Hebrew stop words before downstream parsing.
    Keeps token boundaries simple by re-joining with single spaces.
    """
    norm = _normalize_text(text)
    tokens = norm.split()
    kept = [t for t in tokens if t not in _HEBREW_STOP_WORDS]
    return " ".join(kept)


def _unique_preserve(seq: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _load_aliases_from_json(path: Path) -> Dict[str, List[str]]:
    with path.open("r", encoding="utf-8") as f:
        obj = json.load(f)
    # Ensure canonical appears in its own alias list
    fixed: Dict[str, List[str]] = {}
    for canonical, aliases in obj.items():
        items = list(dict.fromkeys([canonical] + list(aliases or [])))
        fixed[canonical] = items

    # Special handling: if this is the announcement aliases file, merge titles from the full Hebrew grouping
    try:
        if path.name.startswith("announcement_aliases"):
            full_titles_path = path.parent / "announcement_aliases._full_heb1.json"
            if full_titles_path.exists():
                full = json.loads(full_titles_path.read_text(encoding="utf-8"))
                groups = full.get("groups", []) if isinstance(full, dict) else []
                for g in groups:
                    title = (g or {}).get("title")
                    events = (g or {}).get("events", []) or []
                    if not title:
                        continue
                    # Ensure each title exists as its own canonical (so we can detect and expand it later)
                    if title not in fixed:
                        fixed[title] = [title]
                    elif title not in fixed[title]:
                        fixed[title].append(title)
    except Exception:
        # Non-fatal; proceed with base aliases
        pass

    return fixed

