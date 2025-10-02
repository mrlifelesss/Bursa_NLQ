from pathlib import Path
import os
import sys
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, Iterable, List, Literal, Optional, Tuple
from decimal import Decimal
from copy import deepcopy
from datetime import date, datetime
from functools import lru_cache
import re, unicodedata
import json
from mangum import Mangum
from botocore.exceptions import ClientError

try:
    import boto3  # noqa: F401
except ImportError:
    raise HTTPException(status_code=500, detail="boto3 is not installed. pip install boto3")

try:
    import requests  # noqa: F401
    from requests import RequestException
except ImportError:
    requests = None  # type: ignore[assignment]
    RequestException = Exception  # type: ignore[assignment]

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from nlq_parser_v5 import (
    parse_nlq,
    DynamoSchemaConfig,
    QueryParseResult,
    build_dynamodb_queries,
    build_single_query_string,
    BuiltQuery,
)
from nlq_parser_v5.text_utils import _load_aliases_from_json


def _build_alias_lookup(alias_map: Dict[str, List[str]]) -> List[Tuple[str, str]]:
    """Flatten {canonical: [aliases]} into [(alias, canonical)], dedup on normalized alias."""
    lookup: List[Tuple[str, str]] = []
    seen: set[str] = set()
    for canonical, aliases in alias_map.items():
        for alias in aliases:
            alias_value = (alias or "").strip()
            if not alias_value:
                continue
            norm_key = _norm(alias_value)
            if norm_key in seen:
                continue
            seen.add(norm_key)
            lookup.append((alias_value, canonical))  # keep original alias text for display
    return lookup

_HEB_NIKUD = re.compile(r"[\u0591-\u05C7]")
def _norm(s: str) -> str:
    """Normalize Hebrew strings for matching:
    - NFKC, remove niqqud
    - NBSP/narrow NBSP -> space
    - maqaf (־) -> hyphen
    - collapse whitespace
    - casefold
    """
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = _HEB_NIKUD.sub("", s)                       # remove vowel marks (optional)
    s = s.replace("\u00A0", " ").replace("\u202F", " ")  # NBSPs -> space
    s = s.replace("\u05BE", "-").replace("־", "-")       # maqaf -> hyphen
    s = re.sub(r"\s+", " ", s).strip()
    return s.casefold()

def _suggest_from_lookup(lookup: List[Tuple[str, str]], term: str, limit: int) -> List[Dict[str, str]]:
    if not term or not lookup:
        return []
    q = _norm(term)

    prefix: List[Dict[str, str]] = []
    word:   List[Dict[str, str]] = []
    contains: List[Dict[str, str]] = []

    seen_norms: set[str] = set()
    seen_canon: set[str] = set()

    for alias, canonical in lookup:
        an = _norm(alias)
        if not an:
            continue

        item = {"alias": alias, "canonical": canonical}
        canon_key = _norm(canonical) if isinstance(canonical, str) else an

        if an.startswith(q):
            if an in seen_norms or canon_key in seen_canon:
                continue
            seen_norms.add(an)
            seen_canon.add(canon_key)
            prefix.append(item)
            if len(prefix) >= limit:
                # fast exit if we already have enough strong hits
                return prefix[:limit]
            continue

        if f" {q}" in an:
            if an in seen_norms or canon_key in seen_canon:
                continue
            seen_norms.add(an)
            seen_canon.add(canon_key)
            word.append(item)
            continue

        if q in an:
            if an in seen_norms or canon_key in seen_canon:
                continue
            seen_norms.add(an)
            seen_canon.add(canon_key)
            contains.append(item)

    results = (prefix + word + contains)[:limit]
    return results



#Run as uvicorn scripts.server:app --reload --port 8000
#  
# Load aliases exactly like your Streamlit app
package_dir = SCRIPT_DIR / "nlq_parser_v5"
try:
    company_aliases = _load_aliases_from_json(package_dir / "company_aliases.json")
    report_aliases  = _load_aliases_from_json(package_dir / "announcement_aliases.json")
    _company_alias_lookup = _build_alias_lookup(company_aliases)
    _report_alias_lookup = _build_alias_lookup(report_aliases)
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Failed to load aliases: {e}")

app = FastAPI()

ALLOWED_ORIGINS = ["https://main.dfwhu4l3em50s.amplifyapp.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["content-type"],
    allow_credentials=False,
)

@app.options("/{path:path}")
def cors_preflight(path: str):
    return Response(
        status_code=204,
        headers={
            "Access-Control-Allow-Origin": ALLOWED_ORIGINS[0],
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "content-type",
            "Access-Control-Max-Age": "600",
        },
    )
@app.get("/health")
def health():
    return {"ok": True}

handler = Mangum(app)  # THis is what lambda is looking for

DEFAULT_API_URL_PARAMETER = "/myapp/api/url"
DEFAULT_API_KEY_PARAMETER = "/myapp/api/key"

_api_url_param_env = os.getenv("EXTERNAL_API_URL_PARAMETER")
if _api_url_param_env:
    API_URL_PARAMETER_NAME = _api_url_param_env.strip() or DEFAULT_API_URL_PARAMETER
else:
    API_URL_PARAMETER_NAME = DEFAULT_API_URL_PARAMETER

_api_key_param_env = os.getenv("EXTERNAL_API_KEY_PARAMETER")
if _api_key_param_env is None:
    API_KEY_PARAMETER_NAME = DEFAULT_API_KEY_PARAMETER
else:
    API_KEY_PARAMETER_NAME = _api_key_param_env.strip()

try:
    API_TIMEOUT_SECONDS = float(os.getenv("EXTERNAL_API_TIMEOUT_SECONDS", "10"))
    if API_TIMEOUT_SECONDS <= 0:
        API_TIMEOUT_SECONDS = 10.0
except ValueError:
    API_TIMEOUT_SECONDS = 10.0

@lru_cache(maxsize=32)
def _api_config_from_parameter_store(
    url_parameter_name: str,
    key_parameter_name: Optional[str],
    profile_name: Optional[str],
    region_name: Optional[str],
) -> Tuple[str, Optional[str]]:
    session = boto3.session.Session(profile_name=profile_name or None, region_name=region_name or None)
    ssm = session.client("ssm")
    try:
        url_resp = ssm.get_parameter(Name=url_parameter_name)
    except ClientError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load API url from Parameter Store: {_err_msg(exc)}") from exc

    parameter_details = url_resp.get("Parameter") or {}
    url_value = (parameter_details.get("Value") or "").strip()
    if not url_value:
        raise HTTPException(status_code=500, detail=f"Parameter {url_parameter_name} did not return a value.")

    api_key_value: Optional[str] = None
    resolved_key_name = (key_parameter_name or "").strip()
    if resolved_key_name:
        try:
            key_resp = ssm.get_parameter(Name=resolved_key_name, WithDecryption=True)
        except ClientError as exc:
            raise HTTPException(status_code=500, detail=f"Failed to load API key from Parameter Store: {_err_msg(exc)}") from exc
        key_details = key_resp.get("Parameter") or {}
        api_key_value = key_details.get("Value")
        if api_key_value is None:
            raise HTTPException(status_code=500, detail=f"Parameter {resolved_key_name} did not return a value.")

    return url_value, api_key_value

def call_parameter_store_api(
    payload: Dict[str, Any],
    *,
    url_parameter_name: Optional[str] = None,
    key_parameter_name: Optional[str] = None,
    aws_profile: Optional[str] = None,
    aws_region: Optional[str] = None,
    timeout_seconds: Optional[float] = None,
    extra_headers: Optional[Dict[str, str]] = None,
) -> Any:
    if requests is None:
        raise HTTPException(status_code=500, detail="requests is not installed. pip install requests")

    resolved_url_name = (url_parameter_name or API_URL_PARAMETER_NAME).strip()
    if not resolved_url_name:
        raise HTTPException(status_code=500, detail="API URL parameter name is not configured.")

    resolved_key_name = key_parameter_name
    if resolved_key_name is None:
        resolved_key_name = API_KEY_PARAMETER_NAME

    resolved_key_name = (resolved_key_name or "").strip() or None

    url_value, api_key_value = _api_config_from_parameter_store(
        resolved_url_name,
        resolved_key_name,
        aws_profile,
        aws_region,
    )

    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if extra_headers:
        headers.update(extra_headers)

    if api_key_value:
        existing = {key.lower() for key in headers}
        if "x-api-key" not in existing:
            headers["x-api-key"] = api_key_value

    effective_timeout = API_TIMEOUT_SECONDS if not timeout_seconds or timeout_seconds <= 0 else timeout_seconds

    try:
        response = requests.post(url_value, json=payload, headers=headers, timeout=effective_timeout)
        response.raise_for_status()
    except RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Failed to call downstream API: {exc}") from exc

    try:
        return response.json()
    except ValueError:
        return {"raw": response.text}

def _company_name_suggestions(term: str, limit: int) -> List[Dict[str, str]]:
    return _suggest_from_lookup(_company_alias_lookup, term, limit)

def _report_type_suggestions(term: str, limit: int) -> List[Dict[str, str]]:
    return _suggest_from_lookup(_report_alias_lookup, term, limit)

def _smart_suggestions(term: str, limit: int) -> List[Dict[str, str]]:
    results: List[Dict[str, str]] = []
    if not term:
        return results
    company = _company_name_suggestions(term, limit)
    report = _report_type_suggestions(term, limit)
    sources = [(company, "company"), (report, "report")]
    indices = [0, 0]
    seen_aliases: set[str] = set()
    while len(results) < limit and any(idx < len(items) for (items, _), idx in zip(sources, indices)):
        for source_idx, (items, source_type) in enumerate(sources):
            index = indices[source_idx]
            while index < len(items) and len(results) < limit:
                item = items[index]
                index += 1
                indices[source_idx] = index
                alias = (item.get("alias") or "").strip() if isinstance(item, dict) else ""
                if not alias:
                    continue
                alias_key = alias.casefold()
                if alias_key in seen_aliases:
                    continue
                seen_aliases.add(alias_key)
                canonical = item.get("canonical") if isinstance(item, dict) else None
                results.append({
                    "alias": alias,
                    "canonical": canonical,
                    "type": source_type,
                })
                break
    return results

def _err_msg(e: Exception) -> str:
    # boto3/ClientError has a rich response; fall back to str(e)
    if isinstance(e, ClientError):
        err = e.response.get("Error", {})
        code = err.get("Code")
        msg = err.get("Message")
        return f"{code}: {msg}" if code and msg else (msg or str(e))
    # Some boto3 errors are plain exceptions with .response dict
    resp = getattr(e, "response", None) or {}
    if isinstance(resp, dict):
        err = resp.get("Error", {})
        if isinstance(err, dict) and ("Code" in err or "Message" in err):
            code = err.get("Code")
            msg = err.get("Message")
            return f"{code}: {msg}" if code and msg else (msg or str(e))
    return str(e)


@app.get("/company-suggestions")
def company_suggestions(q: str = Query(""), limit: int = Query(8, ge=1, le=50)):
    term = (q or "").strip()
    if not term:
        return {"suggestions": []}
    matches = _company_name_suggestions(term, limit)
    return {"suggestions": matches}

@app.get("/report-suggestions")
def report_suggestions(q: str = Query(""), limit: int = Query(8, ge=1, le=50)):
    term = (q or "").strip()
    if not term:
        return {"suggestions": []}
    matches = _report_type_suggestions(term, limit)
    return {"suggestions": matches}

@app.get("/smart-suggestions")
def smart_suggestions(q: str = Query(""), limit: int = Query(8, ge=1, le=50)):
    term = (q or "").strip()
    if not term:
        return {"suggestions": []}
    matches = _smart_suggestions(term, limit)
    return {"suggestions": matches}

# Configure CORS origins (override via CORS_ALLOW_ORIGINS env)
DEFAULT_CORS_ALLOW_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://10.100.102.28:5173",
    "https://main.dfwhu4l3em50s.amplifyapp.com",
)

def _configured_cors_origins() -> List[str]:
    raw = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
    if not raw:
        return list(DEFAULT_CORS_ALLOW_ORIGINS)
    if raw == "*":
        return ["*"]
    origins = [origin.strip() for origin in raw.split(",")]
    filtered = [origin for origin in origins if origin]
    return filtered or list(DEFAULT_CORS_ALLOW_ORIGINS)

CORS_ALLOW_ORIGINS = _configured_cors_origins()


def _json_safe(value: Any) -> Any:
    """Convert Decimal and nested types to JSON-friendly values."""
    if isinstance(value, Decimal):
        if value == value.to_integral_value():
            return int(value)
        return float(value)
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    return value


def _coerce_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    if isinstance(value, (Decimal, int, float)):
        return str(value)
    return str(value)


def _to_iso_date(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (int, float, Decimal)):
        try:
            return datetime.utcfromtimestamp(float(value)).date().isoformat()
        except Exception:
            return None
    if isinstance(value, str):
        txt = value.strip()
        if not txt:
            return None
        normalised = txt.replace('Z', '+00:00')
        try:
            return datetime.fromisoformat(normalised).date().isoformat()
        except Exception:
            match = re.search(r"(\d{4}-\d{2}-\d{2})", txt)
            if match:
                return match.group(1)
    return None


def _filters_from_parse_result(parsed: QueryParseResult) -> Dict[str, Any]:
    filters: Dict[str, Any] = {}
    if parsed.companies:
        filters['companyNames'] = parsed.companies
    if parsed.report_types:
        filters['announcementTypes'] = parsed.report_types
    if parsed.quantity:
        filters['limit'] = parsed.quantity
    if parsed.time_frame:
        filters['timeFrameKind'] = parsed.time_frame.kind
        if parsed.time_frame.start_date:
            filters['startDate'] = parsed.time_frame.start_date.isoformat()
        if parsed.time_frame.end_date:
            filters['endDate'] = parsed.time_frame.end_date.isoformat()
    return filters


def _diagnostics_from_parse_result(parsed: QueryParseResult) -> Dict[str, Any]:
    return {
        'confidence': parsed.confidence,
        'notes': parsed.notes,
        'error': parsed.error,
        'matchedCompanyAliases': parsed.matched_company_aliases,
        'matchedReportAliases': parsed.matched_report_aliases,
        'heuristicsText': parsed.heuristics_understood_text,
        'finalText': parsed.final_understood_text,
    }


def _extract_doc_link(item: Dict[str, Any]) -> Optional[str]:
    direct = _coerce_str(item.get('url') or item.get('doc_link') or item.get('docUrl'))
    if direct:
        return direct
    attached = item.get('attachedFiles') or item.get('files')
    if isinstance(attached, str):
        raw = attached.strip()
        if not raw:
            return None
        if raw.startswith('{') or raw.startswith('['):
            try:
                parsed = json.loads(raw)
            except Exception:
                return raw
            attached = parsed
        else:
            return raw
    if isinstance(attached, dict):
        return _coerce_str(attached.get('url') or attached.get('href'))
    if isinstance(attached, Iterable) and not isinstance(attached, (str, bytes)):
        for entry in attached:
            if isinstance(entry, dict):
                link = _coerce_str(entry.get('url') or entry.get('href'))
                if link:
                    return link
            else:
                link = _coerce_str(entry)
                if link:
                    return link
    return None


def _build_company_info_link(item: Dict[str, Any]) -> Optional[str]:
    link = _coerce_str(item.get('companyInfoLink') or item.get('company_info_link'))
    if link:
        return link
    registration = _coerce_str(item.get('registration_number') or item.get('companyId') or item.get('issuer_id'))
    if registration:
        return f"https://maya.tase.co.il/he/companies/{registration}"
    return None


def _build_stock_graph_link(item: Dict[str, Any]) -> Optional[str]:
    link = _coerce_str(item.get('stockGraphLink') or item.get('stock_graph_link'))
    if link:
        return link
    security_id = _coerce_str(item.get('security_id') or item.get('securityId') or item.get('securityNumber'))
    if security_id:
        return f"https://market.tase.co.il/he/market_data/security/{security_id}/graph"
    return None


def _map_item_to_data_item(item: Dict[str, Any], idx: int) -> Dict[str, Any]:
    company = (
        _coerce_str(item.get('issuerName'))
        or _coerce_str(item.get('company_name_he'))
        or _coerce_str(item.get('company_name_en'))
        or 'Unknown'
    )
    #raw_type = item.get('form_type') or item.get('formType') or item.get('events') or item.get('report_type')
    raw_type = item.get('events') or item.get('report_type')
    if isinstance(raw_type, dict):
        raw_type = ', '.join(key for key, value in raw_type.items() if value)
    elif isinstance(raw_type, Iterable) and not isinstance(raw_type, (str, bytes)):
        raw_type = ', '.join(str(v) for v in raw_type if v)
    announcement_type = _coerce_str(raw_type) or 'Unknown'

    announcement_date = (
        _to_iso_date(item.get('publicationDate'))
        or _to_iso_date(item.get('submission_date'))
        or _to_iso_date(item.get('publication_date'))
        or ''
    )

    summary = (
        _coerce_str(item.get('subject'))
        or _coerce_str(item.get('title'))
        or _coerce_str(item.get('headline'))
        or ''
    )

    doc_link = _extract_doc_link(item) or '#'
    company_info_link = _build_company_info_link(item) or '#'
    stock_graph_link = _build_stock_graph_link(item) or '#'
    pro_summary_link = _coerce_str(item.get('pro_url') or item.get('proUrl') or item.get('analysis_url')) or doc_link

    return {
        'id': idx,
        'companyName': company,
        'announcementType': announcement_type,
        'announcementDate': announcement_date,
        'summary': summary,
        'docLink': doc_link,
        'webLink': doc_link,
        'companyInfoLink': company_info_link,
        'stockGraphLink': stock_graph_link,
        'proSummaryLink': pro_summary_link or '#',
    }

class ParseReq(BaseModel):
    query: str
    auto_expand_aliases: bool = True
    force_absolute_timeframe: bool = True
    test_today: str | None = None  # "YYYY-MM-DD" to mimic NLQ_TEST_TODAY

class QueryReq(BaseModel):
    query: str
    auto_expand_aliases: bool = True
    force_absolute_timeframe: bool = True
    test_today: Optional[str] = None

    table_name: str = "CompanyDisclosuresHebrew"
    pk_attr: str = "issuerName"
    sk_attr: Optional[str] = "publicationDate"
    date_format: Literal["iso_date","iso_datetime","epoch_seconds","epoch_millis"] = "iso_date"
    report_type_attr: Optional[str] = "events"
    report_type_is_list: bool = False
    report_type_match: Literal["auto","scalar","list","map_keys"] = "map_keys"
    scan_descending: bool = True

    # optional GSIs
    gsi_name_by_report_type: str | None = "form_type-publicationDate-index"
    gsi_pk_attr: str | None = "form_type"
    gsi_sk_attr: str | None = "publicationDate"

    gsi_name_by_date: str | None = "Sort-By-Dates-Index"
    gsi_date_pk_attr: str | None = "dummy"
    gsi_date_pk_value: str | None = "1"


class RunReq(QueryReq):
    # extend QueryReq with run settings
    mode: Literal["api","partiql"] = "api"
    aws_region: str = "us-east-1"
    aws_profile: Optional[str] = None
    endpoint_url: Optional[str] = None
    max_items: int = 50
    
class AnnouncementsReq(RunReq):
    include_raw: bool = False

class ParseBuildRunReq(RunReq):
    """Same fields as RunReq (inherits), so we can reuse validation & defaults."""
    pass

@app.post("/parse")
def parse(req: ParseReq):
    # mimic Streamlit env override
    if req.test_today:
        os.environ["NLQ_TEST_TODAY"] = req.test_today
    result = parse_nlq(
        req.query,
        company_aliases,
        report_aliases,
        auto_expand_aliases=req.auto_expand_aliases,
        force_absolute_timeframe=req.force_absolute_timeframe,
    )
    return result.model_dump(mode="json")

@app.post("/filters")
def extract_filters(req: ParseReq):
    if req.test_today:
        os.environ["NLQ_TEST_TODAY"] = req.test_today
    parsed = parse_nlq(
        req.query,
        company_aliases,
        report_aliases,
        auto_expand_aliases=req.auto_expand_aliases,
        force_absolute_timeframe=req.force_absolute_timeframe,
    )
    return {
        "filters": _filters_from_parse_result(parsed),
        "diagnostics": _diagnostics_from_parse_result(parsed),
        "raw": parsed.model_dump(mode="json"),
    }


@app.post("/queries")
def build_queries(req: QueryReq):
    if req.test_today:
        os.environ["NLQ_TEST_TODAY"] = req.test_today

    # 1) parse
    parsed = parse_nlq(
        req.query,
        company_aliases,
        report_aliases,
        auto_expand_aliases=req.auto_expand_aliases,
        force_absolute_timeframe=req.force_absolute_timeframe,
    )

    # 2) build dynamo queries
    cfg = DynamoSchemaConfig(
        table_name=req.table_name,
        pk_attr=req.pk_attr,
        sk_attr=req.sk_attr,
        date_format=req.date_format,
        report_type_attr=req.report_type_attr,
        report_type_is_list=req.report_type_is_list,
        report_type_match=req.report_type_match,
        scan_descending=req.scan_descending,
        gsi_name_by_report_type=req.gsi_name_by_report_type,
        gsi_pk_attr=req.gsi_pk_attr,
        gsi_sk_attr=req.gsi_sk_attr,
        gsi_name_by_date=req.gsi_name_by_date,
        gsi_date_pk_attr=req.gsi_date_pk_attr,
        gsi_date_pk_value=req.gsi_date_pk_value,
    )
    built = build_dynamodb_queries(parsed, cfg) or []
    rendered = build_single_query_string(parsed, cfg)

    # 3) serialize for JSON
    out = []
    for q in built:
        out.append({
            "api_params": q.api_params,
            "partiql_statement": q.partiql_statement,
            "partiql_parameters": q.partiql_parameters,
        })
    return {"built": out, "rendered_partiql": rendered}

@app.post("/run")
def run_queries(req: RunReq):
    # 0) optional test-today override
    if req.test_today:
        os.environ["NLQ_TEST_TODAY"] = req.test_today

    # 1) parse
    parsed = parse_nlq(
        req.query,
        company_aliases,
        report_aliases,
        auto_expand_aliases=req.auto_expand_aliases,
        force_absolute_timeframe=req.force_absolute_timeframe,
    )

    # 2) build queries
    cfg = DynamoSchemaConfig(
        table_name=req.table_name,
        pk_attr=req.pk_attr,
        sk_attr=req.sk_attr,
        date_format=req.date_format,
        report_type_attr=req.report_type_attr,
        report_type_is_list=req.report_type_is_list,
        report_type_match=req.report_type_match,
        scan_descending=req.scan_descending,
        gsi_name_by_report_type=req.gsi_name_by_report_type,
        gsi_pk_attr=req.gsi_pk_attr,
        gsi_sk_attr=req.gsi_sk_attr,
        gsi_name_by_date=req.gsi_name_by_date,
        gsi_date_pk_attr=req.gsi_date_pk_attr,
        gsi_date_pk_value=req.gsi_date_pk_value,
    )
    built = build_dynamodb_queries(parsed, cfg) or []
    if not built:
        return {"items": [], "fetched": 0, "note": "No queries built (missing entities or error)."}

    # 3) run them

    sess_kwargs: Dict[str, Any] = {}
    if req.aws_profile:
        sess_kwargs["profile_name"] = req.aws_profile
    if req.aws_region:
        sess_kwargs["region_name"] = req.aws_region
    session = boto3.session.Session(**sess_kwargs)

    all_items: List[Dict[str, Any]] = []
    max_items = max(1, min(5000, req.max_items))

    if req.mode.lower() == "api":
        dynamodb = session.resource("dynamodb", endpoint_url=(req.endpoint_url or None))
        table = dynamodb.Table(cfg.table_name)
        for q in built:
            if len(all_items) >= max_items:
                break
            params = deepcopy(q.api_params)
            params.pop("TableName", None)  # Table.query doesn't accept TableName
            resp = table.query(**params)
            items = resp.get("Items", []) or []
            remaining = max_items - len(all_items)
            all_items.extend(items[:remaining])
            while ("LastEvaluatedKey" in resp) and (len(all_items) < max_items):
                params["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
                resp = table.query(**params)
                items = resp.get("Items", []) or []
                remaining = max_items - len(all_items)
                if remaining <= 0:
                    break
                all_items.extend(items[:remaining])
            if len(all_items) >= max_items:
                break
    else:
        client = session.client("dynamodb", endpoint_url=(req.endpoint_url or None))
        from boto3.dynamodb.types import TypeSerializer, TypeDeserializer
        ser = TypeSerializer(); deser = TypeDeserializer()

        def _deser_item(av_item):
            return {k: deser.deserialize(v) for k, v in (av_item or {}).items()}

        for q in built:
            if len(all_items) >= max_items:
                break
            params = [ser.serialize(p) for p in (q.partiql_parameters or [])]
            resp = client.execute_statement(Statement=q.partiql_statement, Parameters=params)
            items = [_deser_item(it) for it in resp.get("Items", [])]
            remaining = max_items - len(all_items)
            all_items.extend(items[:remaining])
            while ("NextToken" in resp) and (len(all_items) < max_items):
                resp = client.execute_statement(Statement=q.partiql_statement, Parameters=params, NextToken=resp["NextToken"])
                items = [_deser_item(it) for it in resp.get("Items", [])]
                remaining = max_items - len(all_items)
                if remaining <= 0:
                    break
                all_items.extend(items[:remaining])
            if len(all_items) >= max_items:
                break

    safe = _json_safe(all_items)
    return {"items": safe, "fetched": len(safe)}

@app.post("/announcements")
def announcements(req: AnnouncementsReq):
    # ---- wrap the DynamoDB work so we see the true cause on 500
    try:
        run_result = run_queries(req)     # <- likely where DynamoDB is called
    except Exception as e:
        msg = _err_msg(e)
        log.exception("announcements: run_queries failed: %s", msg)
        # Surface the exact reason to help debug from the browser/CloudWatch
        raise HTTPException(status_code=500, detail=msg)

    parsed_payload = run_result.get("parsed") or {}
    try:
        parsed = QueryParseResult.model_validate(parsed_payload)
    except Exception:
        parsed = QueryParseResult()

    items = run_result.get("items") or []
    mapped_items = [
        _map_item_to_data_item(item, idx)
        for idx, item in enumerate(items, start=1)
    ]
    response = {
        "items": mapped_items,
        "fetched": run_result.get("fetched", len(mapped_items)),
        "filters": _filters_from_parse_result(parsed),
        "diagnostics": _diagnostics_from_parse_result(parsed),
        "renderedPartiql": run_result.get("rendered_partiql"),
    }
    if req.include_raw:
        response["rawItems"] = items
        response["builtQueries"] = run_result.get("built")
        response["parsed"] = parsed_payload
    return response


@app.post("/parse-build-run")
def parse_build_run(req: ParseBuildRunReq):
    # 1) Parse (use your env override if you want to support test_today)
    parsed = parse_nlq(
        req.query,
        company_aliases,
        report_aliases,
        auto_expand_aliases=req.auto_expand_aliases,
        force_absolute_timeframe=req.force_absolute_timeframe,
    )

    # 2) Build
    cfg = DynamoSchemaConfig(
        table_name=req.table_name,
        pk_attr=req.pk_attr,
        sk_attr=req.sk_attr,
        date_format=req.date_format,
        report_type_attr=req.report_type_attr,
        report_type_is_list=req.report_type_is_list,
        report_type_match=req.report_type_match,
        scan_descending=req.scan_descending,
        gsi_name_by_report_type=req.gsi_name_by_report_type,
        gsi_pk_attr=req.gsi_pk_attr,
        gsi_sk_attr=req.gsi_sk_attr,
        gsi_name_by_date=req.gsi_name_by_date,
        gsi_date_pk_attr=req.gsi_date_pk_attr,
        gsi_date_pk_value=req.gsi_date_pk_value,
    )
    built = build_dynamodb_queries(parsed, cfg) or []
    rendered = build_single_query_string(parsed, cfg)

    if not built:
        return {
            "parsed": parsed.model_dump(mode="json"),
            "built": [],
            "rendered_partiql": rendered,
            "items": [],
            "fetched": 0,
            "note": "No queries built (missing entities or filters).",
        }

    # 3) Run
    try:
        import boto3
    except ImportError:
        raise HTTPException(status_code=500, detail="boto3 is not installed. pip install boto3")

    session = boto3.session.Session(
        profile_name=(req.aws_profile or None),
        region_name=(req.aws_region or None),
    )

    all_items: List[Dict[str, Any]] = []
    max_items = max(1, min(5000, req.max_items))

    if req.mode.lower() == "api":
        dynamodb = session.resource("dynamodb", endpoint_url=(req.endpoint_url or None))
        table = dynamodb.Table(cfg.table_name)
        for q in built:
            if len(all_items) >= max_items:
                break
            params = deepcopy(q.api_params)
            params.pop("TableName", None)
            resp = table.query(**params)
            items = resp.get("Items", []) or []
            remaining = max_items - len(all_items)
            all_items.extend(items[:remaining])
            while ("LastEvaluatedKey" in resp) and (len(all_items) < max_items):
                params["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
                resp = table.query(**params)
                items = resp.get("Items", []) or []
                remaining = max_items - len(all_items)
                if remaining <= 0:
                    break
                all_items.extend(items[:remaining])
            if len(all_items) >= max_items:
                break
    else:
        client = session.client("dynamodb", endpoint_url=(req.endpoint_url or None))
        from boto3.dynamodb.types import TypeSerializer, TypeDeserializer
        ser = TypeSerializer(); deser = TypeDeserializer()

        def _deser_item(av_item):
            return {k: deser.deserialize(v) for k, v in (av_item or {}).items()}

        for q in built:
            if len(all_items) >= max_items:
                break
            params = [ser.serialize(p) for p in (q.partiql_parameters or [])]
            resp = client.execute_statement(Statement=q.partiql_statement, Parameters=params)
            items = [_deser_item(it) for it in resp.get("Items", [])]
            remaining = max_items - len(all_items)
            all_items.extend(items[:remaining])
            while ("NextToken" in resp) and (len(all_items) < max_items):
                resp = client.execute_statement(Statement=q.partiql_statement, Parameters=params, NextToken=resp["NextToken"])
                items = [_deser_item(it) for it in resp.get("Items", [])]
                remaining = max_items - len(all_items)
                if remaining <= 0:
                    break
                all_items.extend(items[:remaining])
            if len(all_items) >= max_items:
                break

    # If you already have _json_safe in /run, reuse it here.
    def _json_safe(value: Any) -> Any:
        from decimal import Decimal
        if isinstance(value, Decimal):
            return int(value) if value == value.to_integral_value() else float(value)
        if isinstance(value, dict):
            return {k: _json_safe(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [_json_safe(v) for v in value]
        return value

    return {
        "parsed": parsed.model_dump(mode="json"),
        "built": [
            {
                "api_params": q.api_params,
                "partiql_statement": q.partiql_statement,
                "partiql_parameters": q.partiql_parameters,
            } for q in built
        ],
        "rendered_partiql": rendered,
        "items": _json_safe(all_items),
        "fetched": len(all_items),
    }
