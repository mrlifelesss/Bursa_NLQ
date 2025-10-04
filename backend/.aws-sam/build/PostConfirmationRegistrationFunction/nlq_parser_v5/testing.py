from __future__ import annotations

import datetime as dt
import json
from typing import Any, Dict, Tuple

import os


def _get_today() -> dt.date:
    s = os.getenv("NLQ_TEST_TODAY")
    if s:
        try:
            return dt.date.fromisoformat(s.strip())
        except Exception:
            pass
    return dt.date.today()


def _normalize_expected(exp: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize expected test-case schema across legacy and current keys.
    Accepts singular (company_name/report_type) and plural lists (company_names/report_types).
    time_frame expected format (when relative): {"unit": "day|week|month|year", "value": int}
    """
    if "company_names" in exp and exp["company_names"] is not None:
        companies = list(exp["company_names"]) or None
    elif "company_name" in exp and exp["company_name"] is not None:
        companies = [exp["company_name"]]
    else:
        companies = None

    if "report_types" in exp and exp["report_types"] is not None:
        rtypes = list(exp["report_types"]) or None
    elif "report_type" in exp and exp["report_type"] is not None:
        rtypes = [exp["report_type"]]
    else:
        rtypes = None

    qty = exp.get("quantity")

    tf = exp.get("time_frame")
    if isinstance(tf, dict) and {"unit", "value"}.issubset(tf.keys()):
        tf_norm = {"unit": str(tf["unit"]).lower(), "value": int(tf["value"]) }
    else:
        tf_norm = None if tf in (None, "", []) else tf

    err = exp.get("error")

    return {
        "company_names": companies,
        "report_types": rtypes,
        "quantity": qty,
        "time_frame": tf_norm,
        "error": err,
    }

_UNIT_SINGULAR = {
    "days": "day",
    "weeks": "week",
    "months": "month",
    "years": "year",
}


def _project_result_for_compare(res: Any) -> Dict[str, Any]:
    companies = res.companies or None
    rtypes = res.report_types or None
    qty = res.quantity
    tf = None

    if res.time_frame.kind == "relative" and res.time_frame.relative_value is not None and res.time_frame.relative_unit:
        if res.time_frame.relative_unit == "days" and int(res.time_frame.relative_value) in (0, 1):
            _d = _get_today() - dt.timedelta(days=int(res.time_frame.relative_value))
            tf = {
                "start_date": _d.isoformat(),
                "end_date": _d.isoformat(),
            }
        if res.time_frame.relative_unit == "months" and res.time_frame.relative_value % 3 == 0:
            if res.time_frame.raw and ("רבעון" in res.time_frame.raw or "quarter" in res.time_frame.raw.lower()):
                 tf = {"unit": "quarter", "value": res.time_frame.relative_value // 3}
        if tf is None:
            tf = {
                "unit": _UNIT_SINGULAR.get(res.time_frame.relative_unit, res.time_frame.relative_unit),
                "value": int(res.time_frame.relative_value),
            }

    elif res.time_frame.kind == "absolute" and res.time_frame.start_date and res.time_frame.end_date:
        tf = {
            "start_date": res.time_frame.start_date.isoformat(),
            "end_date": res.time_frame.end_date.isoformat(),
        }

    return {
        "company_names": companies,
        "report_types": rtypes,
        "quantity": qty,
        "time_frame": tf,
        "error": res.error,
    }


_DEF_EMPTY = object()


def _eq_or_empty(expected, got) -> Tuple[bool, str]:
    """Strict if expected is not None; if expected is None, require got to be None/empty."""
    if expected is None:
        if got in (None, [], ""):
            return True, "ok: expected none"
        return False, f"expected none, got {got!r}"
    if isinstance(expected, list):
        got_list = got or []
        return (expected == got_list, f"expected {expected}, got {got_list}")
    return (expected == got, f"expected {expected}, got {got}")


def _compare_cases(expected: Dict[str, Any], got: Dict[str, Any]) -> Tuple[bool, str]:
    if isinstance(expected.get("company_names"), list):
        expected["company_names"].sort()
    if isinstance(got.get("company_names"), list):
        got["company_names"].sort()
    if isinstance(expected.get("report_types"), list):
        expected["report_types"].sort()
    if isinstance(got.get("report_types"), list):
        got["report_types"].sort()

    checks = []
    ok, why = _eq_or_empty(expected.get("company_names"), got.get("company_names"))
    checks.append((ok, "company_names", why))
    ok2, why2 = _eq_or_empty(expected.get("report_types"), got.get("report_types"))
    checks.append((ok2, "report_types", why2))
    ok3, why3 = _eq_or_empty(expected.get("quantity"), got.get("quantity"))
    checks.append((ok3, "quantity", why3))

    exp_tf = expected.get("time_frame")
    got_tf = got.get("time_frame")
    if exp_tf is None:
        ok4 = got_tf in (None, {})
        why4 = "ok: expected none" if ok4 else f"expected none, got {got_tf}"
    else:
        ok4 = (exp_tf == got_tf)
        why4 = f"expected {exp_tf}, got {got_tf}"
    checks.append((ok4, "time_frame", why4))

    ok5, why5 = _eq_or_empty(expected.get("error"), got.get("error"))
    checks.append((ok5, "error", why5))

    all_ok = all(c[0] for c in checks)
    detail = "; ".join([f"{name}: {'OK' if ok else 'FAIL'} ({why})" for ok, name, why in checks])
    return all_ok, detail
