from __future__ import annotations

import datetime as dt
import re
from typing import List, Optional, Tuple

try:
    from dateparser.search import search_dates as _dp_search_dates  # type: ignore
except Exception:  # pragma: no cover
    _dp_search_dates = None

from .constants import _HEBREW_MONTHS, _HEB_MONTH_IDX, _REL_UNIT_MAP, _HEBREW_NUM_WORDS
from .models import TimeFrame
from .text_utils import _get_today, _normalize_text


# Optional Hebrew single-letter prefix before terms (ב/ל/כ/ו/ה/מ/ש)
_HEB_PREFIX = r"(?:[בלכוהמש]-?)?"

def _year_from_token(tok: str, today: dt.date) -> Optional[int]:
    tok = tok.strip()
    if re.fullmatch(r"(?:19|20)\d{2}", tok):
        return int(tok)
    # soft words: השנה / שנה שעברה / אשתקד
    from .constants import _HEBREW_YEAR_WORDS  # type: ignore
    key = tok
    if key in _HEBREW_YEAR_WORDS:
        label = _HEBREW_YEAR_WORDS[key]
        if label == "this_year":
            return today.year
        if label == "last_year":
            return today.year - 1
    return None

def _month_from_name(name: str) -> Optional[int]:
    name = name.strip()
    if name in _HEB_MONTH_IDX:
        return _HEB_MONTH_IDX[name]
    # alt spelling for March already in constants: "מרס" → 3
    return None

def _extract_half_or_start_end(norm: str, today: Optional[dt.date]) -> Optional[Tuple[TimeFrame, List[str], Tuple[int,int]]]:
    """
    Handles:
      - מחצית הראשונה/השנייה של <year|השנה|שנה שעברה>
      - מתחילת (החודש|הרבעון|השנה)  [→ start .. today]
      - מסוף/עד סוף (החודש|הרבעון|השנה) [→ today .. end]
    """
    notes: List[str] = []
    today = today or _get_today()

    # Half-year
    m_half = re.search(r"(מחצית|חצי)\s*(?:ה)?(ראשונה|שנייה)\s*(?:של)?\s*(?:שנת|שנה)?\s*(?P<y>[\w\s]+)?", norm)
    if m_half:
        which = m_half.group(2)
        ytok = (m_half.group("y") or "").strip()
        year = _year_from_token(ytok, today) or today.year
        if which.startswith("ראשונ"):
            start = dt.date(year, 1, 1); end = dt.date(year, 6, 30)
        else:
            start = dt.date(year, 7, 1); end = dt.date(year, 12, 31)
        tf = TimeFrame(kind="absolute", start_date=start, end_date=end, raw=m_half.group(0))
        notes.append("tf:half_year")
        return tf, notes, m_half.span()

    # "from start of ..." → for month/quarter: start .. today; for year: full year
    m_start = re.search(r"(מתחילת|מתחלה של|מתחלת)\s*(החודש|הרבעון|השנה)", norm)
    if m_start:
        unit = m_start.group(2)
        if "חודש" in unit:
            start = today.replace(day=1)
            end = today
        elif "רבעון" in unit:
            q = (today.month - 1) // 3 + 1
            start = dt.date(today.year, 3*(q-1)+1, 1)
            end = today
        else:
            # Interpret "מתחילת השנה" as the whole current year
            start = dt.date(today.year, 1, 1)
            end = dt.date(today.year, 12, 31)
        tf = TimeFrame(kind="absolute", start_date=start, end_date=end, raw=m_start.group(0))
        notes.append("tf:start_of_period_to_today")
        return tf, notes, m_start.span()

    # "until end of ..." → today .. end
    m_end = re.search(r"(עד(?:\s*ל)?\s*סוף|מסוף)\s*(החודש|הרבעון|השנה)", norm)
    if m_end:
        unit = m_end.group(2)
        if "חודש" in unit:
            # last day of month
            next_m = today.month + 1
            next_y = today.year + (1 if next_m == 13 else 0)
            next_m = 1 if next_m == 13 else next_m
            end = (dt.date(next_y, next_m, 1) - dt.timedelta(days=1))
        elif "רבעון" in unit:
            q = (today.month - 1) // 3 + 1
            q_start = dt.date(today.year, 3*(q-1)+1, 1)
            if q < 4:
                next_q_start = dt.date(today.year, 3*q+1, 1)
            else:
                next_q_start = dt.date(today.year+1, 1, 1)
            end = next_q_start - dt.timedelta(days=1)
        else:
            end = dt.date(today.year, 12, 31)
        start = today
        tf = TimeFrame(kind="absolute", start_date=start, end_date=end, raw=m_end.group(0))
        notes.append("tf:today_to_end_of_period")
        return tf, notes, m_end.span()

    return None


def _extract_before_month_year(norm: str) -> Optional[Tuple[TimeFrame, List[str], Tuple[int, int]]]:
    """
    Handles phrases like: לפני <MonthName> <Year>
    Interpreted as: 1900-01-01 .. last-day-of-month-before(<Month, Year>)
    """
    notes: List[str] = []
    month_names = "|".join(map(re.escape, _HEBREW_MONTHS + ["מרס"]))
    m = re.search(rf"\bלפני\s+(?P<m>{month_names})\s+(?P<y>(?:19|20)\d{{2}})\b", norm)
    if not m:
        return None
    mon = _month_from_name(m.group("m"))
    y = int(m.group("y"))
    if not mon:
        return None
    if mon == 1:
        end = dt.date(y - 1, 12, 31)
    else:
        end = dt.date(y, mon, 1) - dt.timedelta(days=1)
    start = dt.date(1900, 1, 1)
    tf = TimeFrame(kind="absolute", start_date=start, end_date=end, raw=m.group(0))
    notes.append("tf:before_month_year")
    return tf, notes, m.span()


def _extract_since_start_of_month(norm: str, today: Optional[dt.date]) -> Optional[Tuple[TimeFrame, List[str], Tuple[int, int]]]:
    """
    Handles: מאז תחילת <MonthName> [<Year>|השנה]
    Defaults year to current if not specified.
    """
    notes: List[str] = []
    today = today or _get_today()
    month_names = "|".join(map(re.escape, _HEBREW_MONTHS + ["מרס"]))
    m = re.search(rf"\bמאז\s+תחילת\s+(?P<m>{month_names})(?:\s+(?P<y>(?:19|20)\d{{2}}|השנה))?\b", norm)
    if not m:
        return None
    mon = _month_from_name(m.group("m"))
    ytok = (m.group("y") or "").strip()
    if ytok == "השנה" or not ytok:
        y = today.year
    else:
        y = int(ytok)
    if not mon:
        return None
    start = dt.date(y, mon, 1)
    end = today
    tf = TimeFrame(kind="absolute", start_date=start, end_date=end, raw=m.group(0))
    notes.append("tf:since_start_of_month_to_today")
    return tf, notes, m.span()


def _extract_last_weekday(norm: str, today: Optional[dt.date]) -> Optional[Tuple[TimeFrame, List[str], Tuple[int, int]]]:
    """
    Handles: יום <weekday> שעבר → absolute date of last week's <weekday>
    """
    notes: List[str] = []
    today = today or _get_today()
    weekdays = {
        "ראשון": 6,  # Python Monday=0, Sunday=6
        "שני": 0,
        "שלישי": 1,
        "רביעי": 2,
        "חמישי": 3,
        "שישי": 4,
        "שבת": 5,
    }
    m = re.search(r"\bיום\s+(ראשון|שני|שלישי|רביעי|חמישי|שישי|שבת)\s+שעבר\b", norm)
    if not m:
        return None
    target = weekdays[m.group(1)]
    delta = ((today.weekday() - target) % 7) + 7
    d = today - dt.timedelta(days=delta)
    tf = TimeFrame(kind="absolute", start_date=d, end_date=d, raw=m.group(0))
    notes.append("tf:last_weekday")
    return tf, notes, m.span()
# --- timeframes.py (NEW function) ---
def _extract_between_months(norm: str, today: Optional[dt.date]) -> Optional[Tuple[TimeFrame, List[str], Tuple[int,int]]]:
    """
    Handles: בין <MonthName> ל<MonthName> (שנת|של)? <year|השנה|שנה שעברה>
    Defaults year if not given: prefer 'this_year' unless text says 'last year'.
    """
    notes: List[str] = []
    today = today or _get_today()
    month_names = "|".join(map(re.escape, _HEBREW_MONTHS + ["מרס"]))
    pat = rf"בין\s+(?P<m1>{month_names})\s+ל(?P<m2>{month_names})(?:\s+(?:שנת|של)?\s*(?P<y>[\w\s]+))?"
    m = re.search(pat, norm)
    if not m:
        return None
    ytok = (m.group("y") or "").strip()
    year = _year_from_token(ytok, today) or today.year
    m1 = _month_from_name(m.group("m1")); m2 = _month_from_name(m.group("m2"))
    if not m1 or not m2:
        return None
    start = dt.date(year, m1, 1)
    # end: last day of m2
    if m2 < 12:
        end = dt.date(year, m2+1, 1) - dt.timedelta(days=1)
    else:
        end = dt.date(year, 12, 31)
    tf = TimeFrame(kind="absolute", start_date=start, end_date=end, raw=m.group(0))
    notes.append("tf:between_months")
    return tf, notes, m.span()

def _extract_since(norm: str, today: Optional[dt.date]) -> Optional[Tuple[TimeFrame, List[str], Tuple[int, int]]]:
    """
    Handles phrases like:
      - מאז <MonthName> <Year>  → start at first day of month, end today
      - מאז <Year>              → start at Jan 1st of year, end today
    """
    notes: List[str] = []
    today = today or _get_today()
    month_names = "|".join(map(re.escape, _HEBREW_MONTHS + ["מרס"]))

    m1 = re.search(rf"\bמאז\s+(?:{_HEB_PREFIX})?(?P<m>{month_names})\s+(?P<y>(?:19|20)\d{{2}})\b", norm)
    if m1:
        mon = _month_from_name(m1.group("m"))
        y = int(m1.group("y"))
        if mon:
            start = dt.date(y, mon, 1)
            end = today
            tf = TimeFrame(kind="absolute", start_date=start, end_date=end, raw=m1.group(0))
            notes.append("tf:since_month_year_to_today")
            return tf, notes, m1.span()

    m2 = re.search(r"\bמאז\s+(?P<y>(?:19|20)\d{2})\b", norm)
    if m2:
        y = int(m2.group("y"))
        start = dt.date(y, 1, 1)
        end = today
        tf = TimeFrame(kind="absolute", start_date=start, end_date=end, raw=m2.group(0))
        notes.append("tf:since_year_to_today")
        return tf, notes, m2.span()

    return None

def _extract_season(norm: str) -> Optional[Tuple[TimeFrame, List[str], Tuple[int, int]]]:
    """
    Recognize Hebrew seasons + year and map to fixed month ranges:
      אביב → Mar–May; קיץ → Jun–Aug; סתיו → Sep–Nov; חורף → Dec–Feb(next year)
    """
    notes: List[str] = []
    # Allow optional single-letter Hebrew prefix (e.g., 'מאביב 2023')
    m = re.search(rf"\b(?:{_HEB_PREFIX})?(?P<s>אביב|קיץ|סתיו|חורף)\s+(?P<y>(?:19|20)\d{{2}})\b", norm)
    if not m:
        return None
    s = m.group("s"); y = int(m.group("y"))
    if s == "אביב":
        start = dt.date(y, 3, 1); end = dt.date(y, 5, 31)
    elif s == "קיץ":
        start = dt.date(y, 6, 1); end = dt.date(y, 8, 31)
    elif s == "סתיו":
        start = dt.date(y, 9, 1); end = dt.date(y, 11, 30)
    else:
        start = dt.date(y, 12, 1)
        y2 = y + 1
        try:
            feb_end = dt.date(y2, 2, 29)
        except ValueError:
            feb_end = dt.date(y2, 2, 28)
        end = feb_end
    tf = TimeFrame(kind="absolute", start_date=start, end_date=end, raw=m.group(0))
    notes.append("tf:season")
    return tf, notes, m.span()

def _absolute_date_spans(norm: str) -> List[Tuple[int, int]]:
    """Coarse spans for absolute date fragments using dateparser (if available)."""
    spans: List[Tuple[int, int]] = []
    if _dp_search_dates is None:
        return spans
    pairs = _dp_search_dates(
        norm,
        languages=["he", "en"],
        settings={
            "DATE_ORDER": "DMY",
            "PREFER_DAY_OF_MONTH": "first",
        },
    ) or []
    for frag, _ in pairs:
        found_any = False
        for m in re.finditer(re.escape(frag), norm):
            spans.append(m.span())
            found_any = True
        if not found_any:
            frag_pat = re.escape(frag)
            frag_pat = (
                frag_pat.replace(r"\.", r"\s*\.\s*")
                .replace(r"\/", r"\s*\/\s*")
                .replace(r"\-", r"\s*\-\s*")
            )
            for m in re.finditer(frag_pat, norm):
                spans.append(m.span())
    return spans


def _absolute_number_token_spans(norm: str) -> List[Tuple[int, int]]:
    """Fine-grained spans for numeric tokens inside absolute date patterns.
    Covers dd/mm/(yy)yy, dd.mm.(yy)yy, dd-mm-(yy)yy and month/year forms.
    """
    spans: List[Tuple[int, int]] = []
    p_dmy = re.compile(r"(?<!\d)(?P<d>\d{1,2})\s*[./-]\s*(?P<m>\d{1,2})\s*[./-]\s*(?P<y>\d{2,4})(?!\d)")
    for m in p_dmy.finditer(norm):
        spans.append(m.span("d"))
        spans.append(m.span("m"))
        spans.append(m.span("y"))
    p_my1 = re.compile(r"(?<!\d)(?P<m>\d{1,2})\s*[./-]\s*(?P<y>\d{2,4})(?!\s*[./-]\s*\d)")
    p_my2 = re.compile(r"(?<!\d)(?P<y>\d{2,4})\s*[./-]\s*(?P<m>\d{1,2})(?!\d)")
    for m in list(p_my1.finditer(norm)) + list(p_my2.finditer(norm)):
        spans.append(m.span("m"))
        spans.append(m.span("y"))
    return spans


def _extract_absolute_clean(norm: str) -> Optional[Tuple[TimeFrame, Tuple[int, int]]]:
    """
    Robust absolute date extractor recognizing:
      - Hebrew MonthName + Year (e.g., מרץ 2025, מרץ 2025 בלבד)
      - Numeric dates (DMY): dd/mm/yyyy, dd.mm.yyyy, dd-mm-yy
      - Month/Year: mm/yyyy or yyyy-mm
      - Year only: 2025 or שנת 2025

    Returns (TimeFrame, span) where span is the character range of the matched
    fragment(s). If multiple absolute fragments are present, returns the min–max range.
    """
    try:
        text = norm

        month_names = list(_HEBREW_MONTHS)
        if "מרץ" not in month_names:
            month_names.append("מרץ")
        month_idx = dict(_HEB_MONTH_IDX)
        month_idx["מרץ"] = 3
        month_name_pattern = "|".join(map(re.escape, month_names))

        month_ranges: List[Tuple[dt.date, dt.date, Tuple[int, int]]] = []
        day_points: List[Tuple[dt.date, Tuple[int, int]]] = []
        year_ranges: List[Tuple[int, Tuple[int, int]]] = []
        blocked_spans: List[Tuple[int, int]] = []

        def overlaps(a: Tuple[int, int], b: Tuple[int, int]) -> bool:
            return not (a[1] <= b[0] or b[1] <= a[0])

        # Hebrew MonthName + Year (both orders; allow attached one-letter prefix)
        p1 = re.compile(
            rf"(?:חודש|בחודש|ב)?\s*(?:{_HEB_PREFIX})?(?P<month>{month_name_pattern})\s+(?:שנת\s*)?(?P<year>(?:19|20)\d{{2}})"
        )
        p2 = re.compile(
            rf"(?:שנת\s*)?(?P<year>(?:19|20)\d{{2}})\s+(?:{_HEB_PREFIX})?(?P<month>{month_name_pattern})"
        )
        for m in list(p1.finditer(text)) + list(p2.finditer(text)):
            y = int(m.group("year"))
            mon_name = m.group("month")
            mon = month_idx.get(mon_name)
            if not mon:
                continue
            start = dt.date(y, mon, 1)
            end = (dt.date(y, mon + 1, 1) - dt.timedelta(days=1)) if mon < 12 else dt.date(y, 12, 31)
            sp = m.span()
            month_ranges.append((start, end, sp))
            blocked_spans.append(sp)

        # Full numeric dates DMY: dd/mm/yyyy etc.
        p_dmy = re.compile(r"(?<!\d)(?P<d>\d{1,2})\s*[./-]\s*(?P<m>\d{1,2})\s*[./-]\s*(?P<y>\d{2,4})(?!\d)")
        for m in p_dmy.finditer(text):
            sp = m.span()
            if any(overlaps(sp, b) for b in blocked_spans):
                continue
            d = int(m.group("d")); mon = int(m.group("m")); y = int(m.group("y"))
            if y < 100:
                y += 2000
            try:
                dt_val = dt.date(y, mon, d)
            except ValueError:
                continue
            day_points.append((dt_val, sp))
            blocked_spans.append(sp)

        # Month/Year numeric: mm/yyyy or yyyy/mm
        p_my1 = re.compile(r"(?<!\d)(?P<m>\d{1,2})\s*[./-]\s*(?P<y>\d{2,4})(?!\s*[./-]\s*\d)")
        p_my2 = re.compile(r"(?<!\d)(?P<y>\d{2,4})\s*[./-]\s*(?P<m>\d{1,2})(?!\d)")
        for m in list(p_my1.finditer(text)) + list(p_my2.finditer(text)):
            sp = m.span()
            if any(overlaps(sp, b) for b in blocked_spans):
                continue
            mon = int(m.group("m")); y = int(m.group("y"))
            if y < 100:
                y += 2000
            if not (1 <= mon <= 12):
                continue
            start = dt.date(y, mon, 1)
            end = (dt.date(y, mon + 1, 1) - dt.timedelta(days=1)) if mon < 12 else dt.date(y, 12, 31)
            month_ranges.append((start, end, sp))
            blocked_spans.append(sp)

        # Standalone year: 4-digit 19xx or 20xx
        p_year = re.compile(r"(?<!\d)(?P<y>(?:19|20)\d{2})(?!\d)")
        for m in p_year.finditer(text):
            sp = m.span("y")
            if any(overlaps(sp, b) for b in blocked_spans):
                continue
            y = int(m.group("y"))
            year_ranges.append((y, sp))

        # Prefer explicit month ranges if present
        if month_ranges:
            start = min(r[0] for r in month_ranges)
            end = max(r[1] for r in month_ranges)
            smin = min(sp[0] for _, _, sp in month_ranges)
            smax = max(sp[1] for _, _, sp in month_ranges)
            tf = TimeFrame(kind="absolute", start_date=start, end_date=end, raw=text[smin:smax])
            return tf, (smin, smax)

        # Multiple explicit days → covering range
        if len(day_points) >= 2:
            dates_sorted = sorted(d for d, _ in day_points)
            start, end = dates_sorted[0], dates_sorted[-1]
            smin = min(sp[0] for _, sp in day_points)
            smax = max(sp[1] for _, sp in day_points)
            tf = TimeFrame(kind="absolute", start_date=start, end_date=end, raw=text[smin:smax])
            return tf, (smin, smax)

        # Single day → day range
        if len(day_points) == 1:
            d0, sp = day_points[0]
            tf = TimeFrame(kind="absolute", start_date=d0, end_date=d0, raw=text[sp[0]:sp[1]])
            return tf, sp

        # Only years → full year or coverage across listed years
        if year_ranges:
            years = sorted(y for y, _ in year_ranges)
            y0, y1 = years[0], years[-1]
            start = dt.date(y0, 1, 1)
            end = dt.date(y1, 12, 31)
            smin = min(sp[0] for _, sp in year_ranges)
            smax = max(sp[1] for _, sp in year_ranges)
            tf = TimeFrame(kind="absolute", start_date=start, end_date=end, raw=text[smin:smax])
            return tf, (smin, smax)

        return None
    except Exception:
        return None


def _quarter_to_dates(q: int, year: int) -> Tuple[dt.date, dt.date]:
    start_month = 3 * (q - 1) + 1
    start = dt.date(year, start_month, 1)
    next_start = dt.date(year, start_month + 3, 1) if start_month in (1, 4, 7) else dt.date(year + 1, 1, 1)
    end = next_start - dt.timedelta(days=1)
    return start, end


def _extract_timeframe_absolute(norm: str, today: Optional[dt.date] = None) -> Tuple[Optional[TimeFrame], List[str], Optional[Tuple[int, int]]]:
    """Absolute timeframe detection only (month/year, specific years, quarters)."""
    notes: List[str] = []
    abs_tf_result = _extract_absolute_clean(norm)
    if abs_tf_result is not None:
        abs_tf, abs_tf_span = abs_tf_result
        notes.append("dateparser:absolute")
        return abs_tf, notes, abs_tf_span

    # Year keyword (e.g., שנת 2025)
    year_match = re.search(r"\b(?:שנת|שנה)\s+(19\d{2}|20\d{2})\b", norm)
    if year_match:
        year = int(year_match.group(1))
        notes.append("tf:keyword_year")
        start = dt.date(year, 1, 1)
        end = dt.date(year, 12, 31)
        return TimeFrame(kind="absolute", start_date=start, end_date=end, raw=year_match.group(0)), notes, year_match.span()

    # Quarter expressions (רבעון/Q)
    ord_map = {"ראשון": 1, "שני": 2, "שלישי": 3, "רביעי": 4}
    qword = re.search(r"רבעון\s*(ראשון|שני|שלישי|רביעי)(?:\s*(?P<y>19\d{2}|20\d{2}))?", norm)
    if qword:
        q = ord_map[qword.group(1)]
        y = int(qword.group("y") or (today or _get_today()).year)
        start, end = _quarter_to_dates(q, y)
        notes.append("tf:absolute_quarter_word")
        return TimeFrame(kind="absolute", start_date=start, end_date=end, raw=qword.group(0)), notes, qword.span()
    qmatch = re.search(r"(?:רבעון|Q)\s*(?P<q>[1-4])(?:\s*(?P<y>19\d{2}|20\d{2}))?", norm, flags=re.IGNORECASE)
    if qmatch:
        today = today or _get_today()
        q = int(qmatch.group("q"))
        y = int(qmatch.group("y") or today.year)
        start, end = _quarter_to_dates(q, y)
        notes.append("tf:absolute_quarter")
        return TimeFrame(kind="absolute", start_date=start, end_date=end, raw=qmatch.group(0)), notes, qmatch.span()

    return None, notes, None


def _extract_timeframe_relative(norm: str, today: Optional[dt.date] = None) -> Tuple[Optional[TimeFrame], List[str], Optional[Tuple[int, int]]]:
    """Relative timeframe detection only (e.g., 7 ימים, שבוע שעבר, אתמול)."""
    notes: List[str] = []
    today = today or _get_today()

    # Accept optional prefixes (ב/ל/מ), the determiner ה-, and "שעבר" variant.
    q_adj = r"(?:הפיסקלי|הכספי|הפיננסי)?"
    # Half-year relative should win over generic 'שנה האחרונה'
    m_half_year = re.search(r"\b(?:ב|ל|מ)?חצי\s+(?:ה)?שנה(?:\s*האחרונה)?\b", norm)
    if m_half_year:
        notes.append("tf:half_year_relative")
        return TimeFrame(kind="relative", relative_value=6, relative_unit="months", raw=m_half_year.group(0)), notes, m_half_year.span()
    implied_one_patterns = {
        rf"\b(?:ב|ל|מ)?(?:ה)?שבוע(?:\s*(?:{q_adj})?\s*(?:האחרון|הזה|שעבר))?\b": ("weeks", 1),
        rf"\b(?:ב|ל|מ)?(?:ה)?חודש(?:\s*(?:האחרון|הזה|שעבר))?\b": ("months", 1),
        rf"\b(?:ב|ל|מ)?(?:ה)?רבעון(?:\s*{q_adj})?(?:\s*(?:האחרון|הזה|שעבר))?\b": ("months", 3),
        # For years, require an explicit modifier to avoid matching plain 'השנה' (e.g., after stop-word removal)
        rf"\b(?:ב|ל|מ)?(?:ה)?שנה(?:\s*(?:האחרונה|הזו|שעברה))\b": ("years", 1),
    }
    for pattern, (unit, value) in implied_one_patterns.items():
        m = re.search(pattern, norm)
        if m:
            notes.append(f"tf:implied_one:{unit}")
            return TimeFrame(kind="relative", relative_value=value, relative_unit=unit, raw=m.group(0)), notes, m.span()

    m_today = re.search(r"\bמ?היום\b", norm)
    if m_today:
        notes.append("tf:keyword_today")
        return TimeFrame(kind="relative", relative_value=0, relative_unit="days", raw="היום"), notes, m_today.span()

    m_yesterday = re.search(r"\bמ?אתמול\b", norm)
    if m_yesterday:
        notes.append("tf:keyword_yesterday")
        return TimeFrame(kind="relative", relative_value=1, relative_unit="days", raw="אתמול"), notes, m_yesterday.span()
    # (handled above) half-year relative

    m_shilshom = re.search(r"\bשלשום\b", norm)
    if m_shilshom:
        notes.append("tf:keyword_shilshom")
        return TimeFrame(kind="relative", relative_value=2, relative_unit="days", raw="שלשום"), notes, m_shilshom.span()
    
    # Hours → ceil to days. Accept optional prefix 'מ-' and article 'ה' in 'השעות'
    m_hours = re.search(r"(?:\bמ-?)?(?P<num>\d{1,3})\s*(?:ה)?שעות?\s*(?:האחרונות|האחרונה|האחרונים)?", norm)
    if m_hours:
        num_h = int(m_hours.group("num"))
        # ceil to days
        days = (num_h + 23) // 24
        notes.append("tf:hours_as_days")
        return TimeFrame(kind="relative", relative_value=days, relative_unit="days", raw=m_hours.group(0)), notes, m_hours.span()
    m_last_hours = re.search(r"\bהשעות\s*(האחרונות|האחרונה)\b", norm)
    if m_last_hours:
        notes.append("tf:last_hours_default_24h")
        return TimeFrame(kind="relative", relative_value=1, relative_unit="days", raw=m_last_hours.group(0)), notes, m_last_hours.span()

    # Quick forms for "last hours/day"
    m_last_hours = re.search(r"\b(?:ב)?ה?שעות\s*(האחרונות|האחרונה)\b", norm)
    if m_last_hours:
        notes.append("tf:last_hours_default_24h")
        return TimeFrame(kind="relative", relative_value=1, relative_unit="days", raw=m_last_hours.group(0)), notes, m_last_hours.span()

    # "ביממה האחרונה" → 1 day
    m_yom = re.search(r"\bב?יממה\s*(האחרונה)\b", norm)
    if m_yom:
        notes.append("tf:last_24h_yemama")
        return TimeFrame(kind="relative", relative_value=1, relative_unit="days", raw=m_yom.group(0)), notes, m_yom.span()

    # “הימים/השבועות/החודשים/השנים האחרונים|האחרונה|האלה” → implied range=1
    m_last = re.search(r"(הימים|השבועות|החודשים|השנים)\s*(האחרונ(?:ים|ה)|האלה|שעבר)", norm)
    if m_last:
        unit_word = m_last.group(1)
        unit = _REL_UNIT_MAP.get(unit_word, None)
        if unit:
            notes.append("tf:last_period_implied_one")
            return TimeFrame(kind="relative", relative_value=1, relative_unit=unit, raw=m_last.group(0)), notes, m_last.span()
        
    rel = re.search(
        r"(?:\bמ-?)?(?P<num>\d{1,3})\s*(?:־)?(?P<unit>יום|ימים|שבוע|שבועות|חודש|חודשים|שנה|שנים)\s*(?:האחרונ(?:ה|ים)?|האחרון)?",
        norm,
    )
    if rel:
        num = int(rel.group("num"))
        unit = _REL_UNIT_MAP.get(rel.group("unit"), None)
        if unit:
            return TimeFrame(kind="relative", relative_value=num, relative_unit=unit, raw=rel.group(0)), notes, rel.span()

    dual = re.search(rf"\b(?:{_HEB_PREFIX})?(שבועיים|חודשיים|שנתיים)\b", norm)
    if dual:
        unit_map = {"שבועיים": (2, "weeks"), "חודשיים": (2, "months"), "שנתיים": (2, "years")}
        val, unit = unit_map[dual.group(1)]
        return TimeFrame(kind="relative", relative_value=val, relative_unit=unit, raw=dual.group(0)), notes, dual.span()

    # Half-year relative: "חצי שנה" / "חצי השנה האחרונה"
    m_halfyear_rel = re.search(r"\bחצי\s+(?:ה)?שנה(?:\s*האחרונה)?\b", norm)
    if m_halfyear_rel:
        notes.append("tf:half_year_relative")
        return TimeFrame(kind="relative", relative_value=6, relative_unit="months", raw=m_halfyear_rel.group(0)), notes, m_halfyear_rel.span()

    # Generic "recent" phrasings
    m_lak = re.search(r"\bלאחרונה\b", norm)
    if m_lak:
        notes.append("tf:recent_default_2w")
        return TimeFrame(kind="relative", relative_value=2, relative_unit="weeks", raw=m_lak.group(0)), notes, m_lak.span()

    m_tkufa = re.search(r"\b(?:ב)?תקופה\s*(האחרונה)\b", norm)
    if m_tkufa:
        notes.append("tf:recent_period_default_3m")
        return TimeFrame(kind="relative", relative_value=3, relative_unit="months", raw=m_tkufa.group(0)), notes, m_tkufa.span()

    m_updates = re.search(r"\bעדכונים?\s*(האחרונ(?:ים|ה))\b", norm)
    if m_updates:
        notes.append("tf:recent_updates_default_1w")
        return TimeFrame(kind="relative", relative_value=1, relative_unit="weeks", raw=m_updates.group(0)), notes, m_updates.span()

    # "מה חדש" → default recent window (3 months)
    m_whats_new = re.search(r"\bמה\s+חדש\b", norm)
    if m_whats_new:
        notes.append("tf:whats_new_default_3m")
        return TimeFrame(kind="relative", relative_value=3, relative_unit="months", raw=m_whats_new.group(0)), notes, m_whats_new.span()

    # "לפני <num> (יום|ימים|שבוע|שבועות)"
    m_before_rel = re.search(r"\bלפני\s+(?P<n>\d{1,3}|\S+)\s+(?P<u>יום|ימים|שבוע|שבועות)\b", norm)
    if m_before_rel:
        n_raw = m_before_rel.group("n")
        try:
            n = int(n_raw)
        except ValueError:
            n = _HEBREW_NUM_WORDS.get(n_raw, None) or 0
        unit_word = m_before_rel.group("u")
        unit = _REL_UNIT_MAP.get(unit_word, None)
        if n > 0 and unit:
            notes.append("tf:before_relative")
            return TimeFrame(kind="relative", relative_value=n, relative_unit=unit, raw=m_before_rel.group(0)), notes, m_before_rel.span()

    # "הכי עדכני" → default recent window 7 days
    m_latest = re.search(r"\bהכי\s+עדכנ\S*\b|\bהעדכנ\S*\b", norm)
    if m_latest:
        notes.append("tf:latest_default_7d")
        return TimeFrame(kind="relative", relative_value=7, relative_unit="days", raw=m_latest.group(0)), notes, m_latest.span()

    return None, notes, None


def _extract_timeframe(text: str, today: Optional[dt.date] = None) -> Tuple[TimeFrame, List[str], Optional[Tuple[int, int]]]:
    notes: List[str] = []
    norm = _normalize_text(text)
    today = today or _get_today()

    # 1) NEW: half-year / start-end / between-months / before-month-year / since-start-of-month / since / seasons (prefer specific constructs)
    adv = _extract_half_or_start_end(norm, today)
    if adv:
        tf, adv_notes, adv_span = adv
        return tf, adv_notes, adv_span

    adv_between = _extract_between_months(norm, today)
    if adv_between:
        tf, adv_notes, adv_span = adv_between
        return tf, adv_notes, adv_span

    adv_before = _extract_before_month_year(norm)
    if adv_before:
        tf, adv_notes, adv_span = adv_before
        return tf, adv_notes, adv_span

    adv_since_start = _extract_since_start_of_month(norm, today)
    if adv_since_start:
        tf, adv_notes, adv_span = adv_since_start
        return tf, adv_notes, adv_span

    adv_since = _extract_since(norm, today)
    if adv_since:
        tf, adv_notes, adv_span = adv_since
        return tf, adv_notes, adv_span

    adv_season = _extract_season(norm)
    if adv_season:
        tf, adv_notes, adv_span = adv_season
        return tf, adv_notes, adv_span

    adv_last_wd = _extract_last_weekday(norm, today)
    if adv_last_wd:
        tf, adv_notes, adv_span = adv_last_wd
        return tf, adv_notes, adv_span

    # 2) Relative (existing + hours/phrasing tweaks)
    rel_tf, rel_notes, rel_span = _extract_timeframe_relative(norm, today)
    if rel_tf is not None:
        return rel_tf, rel_notes, rel_span

    # 3) Absolute (generic month/year/day recognition)
    abs_tf_result = _extract_absolute_clean(norm)
    if abs_tf_result is not None:
        abs_tf2, abs_span2 = abs_tf_result
        notes.append("dateparser:absolute")
        return abs_tf2, notes, abs_span2

    notes.append("No timeframe extracted.")
    return TimeFrame(kind="none"), notes, None


def _relative_to_absolute(tf: TimeFrame, today: Optional[dt.date] = None) -> TimeFrame:
    """Convert a relative TimeFrame to an absolute [start_date, end_date] using 'today'.
    Days/weeks: end = today, start = today - N days/weeks
    Months/years: end = today, start = same-day in past months/years (clamped to month end)
    If tf is not relative, returned unchanged.
    """
    if tf is None or tf.kind != "relative" or tf.relative_value is None or tf.relative_unit is None:
        return tf
    today = today or _get_today()

    def clamp_day(y: int, m: int, d: int) -> dt.date:
        # last day of month
        if m == 12:
            last = dt.date(y, 12, 31)
        else:
            last = dt.date(y, m + 1, 1) - dt.timedelta(days=1)
        day = min(d, last.day)
        return dt.date(y, m, day)

    val = int(tf.relative_value)
    unit = tf.relative_unit
    end = today
    if unit == "days":
        start = today - dt.timedelta(days=val)
    elif unit == "weeks":
        start = today - dt.timedelta(days=val * 7)
    elif unit == "months":
        y = today.year
        m = today.month - val
        while m <= 0:
            y -= 1
            m += 12
        start = clamp_day(y, m, today.day)
    elif unit == "years":
        start_year = today.year - val
        start = clamp_day(start_year, today.month, today.day)
    else:
        return tf
    return TimeFrame(kind="absolute", start_date=start, end_date=end, raw=tf.raw)
