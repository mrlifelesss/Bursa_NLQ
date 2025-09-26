from __future__ import annotations

import os
import re
from typing import List, Dict
from pathlib import Path
import json

from .text_utils import _unique_preserve


_TITLE_EVENTS_CACHE: Dict[str, List[str]] = {}


def _load_title_events() -> Dict[str, List[str]]:
    global _TITLE_EVENTS_CACHE
    if _TITLE_EVENTS_CACHE:
        return _TITLE_EVENTS_CACHE
    try:
        base = Path(__file__).resolve().parent / "announcement_aliases._full_heb1.json"
        if base.exists():
            data = json.loads(base.read_text(encoding="utf-8"))
            out: Dict[str, List[str]] = {}
            for g in (data.get("groups", []) or []):
                title = (g or {}).get("title")
                events = (g or {}).get("events", []) or []
                if title:
                    out[title] = list(dict.fromkeys([e for e in events if isinstance(e, str) and e.strip()]))
            _TITLE_EVENTS_CACHE = out
    except Exception:
        _TITLE_EVENTS_CACHE = {}
    return _TITLE_EVENTS_CACHE


def _postprocess_reports(reports: List[str], norm_text: str) -> List[str]:
    """Light canonicalization + fallback detection for core report types.
    - Canonicalize broader labels to expected ones (optional)
    - Add missing specific types based on literal patterns in the text
    - Drop umbrella categories when a specific subtype exists
    """
    out = list(reports)

    # Expand group titles to all their subtypes if present
    title_map = _load_title_events()
    expanded: List[str] = []
    for r in out:
        expanded.append(r)
        if r in title_map:
            expanded.extend(title_map[r])
    out = expanded

    # 1) Canonicalization (disabled by default; keep exact labels to satisfy suite expectations)
    if os.getenv("CANONICALIZE_REPORT_TYPES", "0").lower() in ("1", "true", "yes"):
        canon_map = {
            "דוח כספי שנתי": "דוח כספי",
        }
        out = [canon_map.get(x, x) for x in out]

    # 2) Fallbacks from text patterns (exact-ish Hebrew forms)
    if re.search(r"\bאסיפה\s+כלל.?\b", norm_text):
        out.append("אסיפה כללית")
    if re.search(r"\bדוח\s*-?\s*מיידי\b", norm_text):
        out.append("דוח מיידי")
    if re.search(r"\bתשקיף(?:ים)?\b", norm_text):
        out.append("תשקיף")
    if re.search(r"\bדוח\s+על\b", norm_text):
        out.append("דוח על אירוע/עניין")
    if not out and re.search(r"\bדוח\b|\bדוחות\b|\bדיווחים\b", norm_text) and not re.search(r"\bלא\b", norm_text):
        out.append("דוח תקופתי ושנתי")

    # Additional fallbacks for common phrasings
    if re.search(r"\b(?:מינוי|פרישה)\s+מנהל\b", norm_text):
        out.append("שינוי נושאי משרה")
    # Explicit appointment fallbacks
    if re.search(r"\bמינוי(?:י)?\s+נושא(?:י)?\s+משרה\b", norm_text):
        out.append("מינוי נושא משרה")
    if re.search(r"\bמינוי(?:י)?\s+דירקטור(?:ים)?\b", norm_text):
        out.append("מינוי דירקטור")
    if re.search(r"\bשינוי?\s+תנאי(?:י)?\s+כהונה\b", norm_text):
        out.append("שינוי תנאי כהונה")

    # Generic appointments wording → umbrella category when no specific subtype is present
    if re.search(r"\bמינוי(?:ים|י)?\b", norm_text):
        out.append("הנהלה ונושאי משרה")
    if re.search(r"\bעסקת\s+נ\w+\b", norm_text) and re.search(r"\bצד\s+קשור\b", norm_text):
        out.append("עסקה עם צד קשור")
    if re.search(r"\bהנפקה\b", norm_text) and not any(t.startswith("הנפקת ") for t in out):
        out.append("הנפקת ניירות ערך")
    # Detect explicit results of offering
    if re.search(r"\bתוצאות\s+הנפקה\b", norm_text):
        out.append("תוצאות הנפקה")
    # Prefer public offering only for generic 'הנפקה/ות' when not private and not specific 'תוצאות'
    if re.search(r"\bהנפק(?:ה|ות)\b", norm_text) and not re.search(r"\bפרטית\b", norm_text) and not re.search(r"\bתוצאות\s+הנפקה\b", norm_text):
        out.append("הנפקה לציבור")

    # Legal updates → legal proceedings / court decisions
    if re.search(r"\bעדכונים?\s*משפטיים?\b", norm_text) or re.search(r"\bהליכים?\s*משפטיים?\b", norm_text):
        out.append("הליכים משפטיים")
    if re.search(r"\b(?:פסק\s*דין|החלטת?\s*בית\s*משפט|בית\s*משפט)\b", norm_text):
        out.append("החלטת בית משפט")

    # Credit rating related
    if re.search(r"\bדירוג(?:\s*אשראי)?\b|\b(?:הורדת|העלאת)\s*דירוג\b|\bאופק\s*דירוג\b", norm_text):
        out.append("דרוג")

    # Corporate actions
    if re.search(r"\b(?:ה)?מיזוג(?:ים)?\b|\bהתמזגות\b", norm_text):
        out.append("מיזוג פעילות/חברה")
    if re.search(r"\b(?:ה)?פיצול(?:ים)?\b", norm_text):
        if re.search(r"\bמניות\b", norm_text):
            out.append("פיצול מניות")
        else:
            out.append("פיצול פעילות/חברה")

    # Half-year reports phrasing
    if re.search(r"\bדוחות?\s+חצי\s+שנתיים\b", norm_text):
        out.append("דוח רבעון 2/חצי שנתי")

    # Financial summaries phrasing
    if re.search(r"\bסיכומים?\s+כספיים\b|\bדוחות?\s+כספיים\b", norm_text):
        out.append("דוח תקופתי ושנתי")
    # Generic events phrasing
    if re.search(r"\bאירועים?\b", norm_text):
        out.append("אירועים ועסקאות")
    # Details about a company → corporate profile
    if re.search(r"\bפרט(?:י|ים)\s+על\b", norm_text):
        out.append("פרטי תאגיד")
    # Profit distribution phrasing
    if re.search(r"\bחלוק(?:ה|ת)\b", norm_text) and re.search(r"\bרווח", norm_text):
        out.append("חלוקת רווחים ותשלומים")

    out = _unique_preserve(out)

    # 3) Drop umbrella categories if a specific subtype exists
    if any(x.startswith("הנפקת ") for x in out) and "הנפקת ניירות ערך" in out:
        out = [x for x in out if x != "הנפקת ניירות ערך"]
    if "הנפקת ניירות ערך" in out and ("הנפקה לציבור" in out or "הנפקה פרטית" in out):
        out = [x for x in out if x != "הנפקת ניירות ערך"]

    # Respect negation for presentations when explicitly asked to exclude
    if re.search(r"\bלא\s+מצגות?\b", norm_text):
        out = [x for x in out if x != "מצגת"]

    # Remove spurious 'אשראי בר דיווח' unless text mentions 'אשראי'
    if "אשראי בר דיווח" in out and not re.search(r"\bאשראי\b", norm_text):
        out = [x for x in out if x != "אשראי בר דיווח"]

    # Remove 'הצגה מחדש' unless explicitly mentioned
    if "הצגה מחדש" in out and not re.search(r"\bהצגה\s*מחדש\b", norm_text):
        out = [x for x in out if x != "הצגה מחדש"]

    # Remove 'הנפקה פרטית' unless explicitly mentioned
    if "הנפקה פרטית" in out and not re.search(r"\bפרטית\b", norm_text):
        out = [x for x in out if x != "הנפקה פרטית"]

    # If specific appointment types exist, drop umbrella 'הנהלה ונושאי משרה'
    if "הנהלה ונושאי משרה" in out and ("מינוי נושא משרה" in out or "מינוי דירקטור" in out):
        out = [x for x in out if x != "הנהלה ונושאי משרה"]

    # Avoid adding 'אירועים ועסקאות' when specific events category exists
    if "אירועים ועסקאות" in out and ("אירועי משקיעים" in out):
        out = [x for x in out if x != "אירועים ועסקאות"]

    return out
