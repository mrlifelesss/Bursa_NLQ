from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .models import QueryParseResult, TimeFrame
from .timeframes import _relative_to_absolute


@dataclass
class DynamoSchemaConfig:
    """
    Config describing how to map QueryParseResult into a DynamoDB query.

    - table_name: DynamoDB table name.
    - pk_attr: Partition key attribute for the primary access pattern (e.g., 'company').
    - sk_attr: Sort key attribute (typically a date/timestamp) or None if table has only PK.
    - date_format: How to format absolute dates for the sort key or date attribute.
      Supported: 'iso_date' (YYYY-MM-DD), 'iso_datetime' (YYYY-MM-DDTHH:MM:SSZ),
                 'epoch_seconds', 'epoch_millis'.
    - report_type_attr: Name of the attribute holding report type(s) to filter by. Optional.
    - report_type_is_list: If True, use contains(attr, :v) semantics; else equality/IN.
    - report_type_match: Override how report types are matched. One of {"auto", "scalar", "list", "map_keys"}.
      Use "map_keys" when report types are stored as keys in a map attribute (e.g., events).
    - scan_descending: If True, return newest-first (ScanIndexForward=False).

    Optional alternate access patterns (GSI):
    - gsi_name_by_report_type: If set and no companies provided, query this GSI by report type.
    - gsi_pk_attr: The GSI partition key attribute (e.g., 'report_type').
    - gsi_sk_attr: The GSI sort key attribute (e.g., same date attr as table or another field).
    - gsi_name_by_date: If set and no companies/report types provided, query by date using a
      fixed partition key value (see gsi_date_pk_attr and gsi_date_pk_value).
    - gsi_date_pk_attr: Attribute name for the date-sorting GSI partition key (e.g., 'dummy').
    - gsi_date_pk_value: Constant value that all items share in that attribute to allow global-by-date queries.
    """

    table_name: str
    pk_attr: str
    sk_attr: Optional[str] = None
    date_format: str = "iso_date"
    report_type_attr: Optional[str] = None
    report_type_is_list: bool = False
    report_type_match: str = "auto"
    scan_descending: bool = True
    # Optional GSI for queries by report type when companies are not provided
    gsi_name_by_report_type: Optional[str] = None
    gsi_pk_attr: Optional[str] = None
    gsi_sk_attr: Optional[str] = None
    # Optional GSI for queries by date with a constant PK
    gsi_name_by_date: Optional[str] = None
    gsi_date_pk_attr: Optional[str] = None
    gsi_date_pk_value: Optional[str] = None

# Pre-configured defaults for CompanyDisclosuresHebrew
DEFAULT_COMPANY_DISCLOSURES_CONFIG = DynamoSchemaConfig(
    table_name="CompanyDisclosuresHebrew",
    pk_attr="issuerName",
    sk_attr="publicationDate",
    date_format="iso_date",
    report_type_attr="form_type",
    report_type_is_list=False,
    scan_descending=True,
    gsi_name_by_report_type="form_type-publicationDate-index",
    gsi_pk_attr="form_type",
    gsi_sk_attr="publicationDate",
    gsi_name_by_date="Sort-By-Dates-Index",
    gsi_date_pk_attr="dummy",
    # IMPORTANT: set this to the constant value used in your items; '1' is a common choice
    gsi_date_pk_value="True",
)


@dataclass
class BuiltQuery:
    """Container for both DynamoDB Query API params and PartiQL statement."""

    # High-level (boto3 Table.query style) parameters
    api_params: Dict[str, Any]
    # PartiQL statement + positional parameters (in the order of '?')
    partiql_statement: str
    partiql_parameters: List[Any]


def _format_date(d: dt.date, fmt: str) -> Any:
    if fmt == "iso_date":
        return d.isoformat()
    if fmt == "iso_datetime":
        # represent start of day in UTC
        return dt.datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=dt.timezone.utc).isoformat().replace("+00:00", "Z")
    if fmt == "epoch_seconds":
        return int(dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc).timestamp())
    if fmt == "epoch_millis":
        return int(dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc).timestamp() * 1000)
    raise ValueError(f"Unsupported date_format: {fmt}")


def _get_absolute_window(tf: TimeFrame) -> Optional[Tuple[dt.date, dt.date]]:
    try:
        if tf and tf.kind == "absolute" and tf.start_date and tf.end_date:
            return tf.start_date, tf.end_date
    except Exception:
        pass
    return None


def build_dynamodb_queries(
    res: QueryParseResult,
    cfg: DynamoSchemaConfig,
) -> List[BuiltQuery]:
    """
    Convert a QueryParseResult into one or more DynamoDB queries and PartiQL statements.

    Returns one BuiltQuery per targeted partition (e.g., per company), or per report_type
    when using a GSI and companies are not provided. If neither companies nor report_types
    are present but a global-by-date GSI is configured (with a constant PK), returns a
    BuiltQuery over that GSI keyed by the constant value.

    Notes:
    - If res.error is set, returns an empty list.
    - If no companies and no report_types (and no date-GSI configured), returns empty.
    - Quantity maps to 'Limit'.
    - Timeframe maps to the sort key BETWEEN if sk_attr is provided; otherwise no range.
    - Report types map to a FilterExpression (for API) or WHERE clause additions (for PartiQL).
    """

    if getattr(res, "error", None):
        return []

    # Normalize timeframe to absolute if possible
    tf = getattr(res, "time_frame", None)
    if tf and getattr(tf, "kind", None) == "relative":
        try:
            tf = _relative_to_absolute(tf)
        except Exception:
            pass
    abs_window = _get_absolute_window(tf) if tf else None

    limit = getattr(res, "quantity", None)
    companies = list(getattr(res, "companies", []) or [])
    report_types = list(getattr(res, "report_types", []) or [])

    built: List[BuiltQuery] = []

    # Helper to attach report type filter to API params and PartiQL
    def _apply_report_filter(
        api_names: Dict[str, str],
        api_values: Dict[str, Any],
        api_filters: List[str],
        partiql_where_snippets: List[str],
        partiql_params: List[Any],
    ) -> None:
        if not report_types or not cfg.report_type_attr:
            return


        attr_name = cfg.report_type_attr
        api_names.setdefault("#rt", attr_name)

        mode = (getattr(cfg, "report_type_match", "auto") or "auto").lower()
        if mode not in {"auto", "scalar", "list", "map_keys"}:
            mode = "auto"
        if mode == "auto":
            mode = "list" if getattr(cfg, "report_type_is_list", False) else "scalar"

        normalized_rts = []
        for rt in report_types:
            if rt is None:
                continue
            if not isinstance(rt, str):
                rt = str(rt)
            rt = rt.strip()
            if not rt or rt in normalized_rts:
                continue
            normalized_rts.append(rt)

        if not normalized_rts:
            return

        attr_for_partiql = attr_name.replace('"', '\"')

        if mode == "list":
            api_conds = []
            partiql_conds = []
            for idx_rt, rt in enumerate(normalized_rts):
                val_key = f":rt{idx_rt}"
                api_values[val_key] = rt
                api_conds.append(f"contains(#rt, {val_key})")
                partiql_conds.append(f'contains("{attr_for_partiql}", ?)')
                partiql_params.append(rt)
            if api_conds:
                api_filters.append("(" + " OR ".join(api_conds) + ")")
                partiql_where_snippets.append("(" + " OR ".join(partiql_conds) + ")")
        elif mode == "map_keys":
            api_conds = []
            partiql_conds = []
            for idx_rt, rt in enumerate(normalized_rts):
                name_token = f"#rk{idx_rt}"
                api_names[name_token] = rt
                api_conds.append(f"attribute_exists(#rt.{name_token})")
                escaped = rt.replace("'", "''")
                partiql_conds.append(f'attribute_exists("{attr_for_partiql}"[''{escaped}''])')
            if api_conds:
                api_filters.append("(" + " OR ".join(api_conds) + ")")
                partiql_where_snippets.append("(" + " OR ".join(partiql_conds) + ")")
        else:
            value_keys = []
            for idx_rt, rt in enumerate(normalized_rts):
                val_key = f":rt{idx_rt}"
                api_values[val_key] = rt
                value_keys.append(val_key)
                partiql_params.append(rt)
            if value_keys:
                api_filters.append("#rt IN (" + ", ".join(value_keys) + ")")
                placeholders = ", ".join(["?"] * len(value_keys))
                partiql_where_snippets.append(f'"{attr_for_partiql}" IN ({placeholders})')

    # Case A: we have companies → primary query pattern per company
    if companies:
        for comp in companies:
            names: Dict[str, str] = {"#pk": cfg.pk_attr}
            values: Dict[str, Any] = {":pk": comp}
            filters: List[str] = []
            where_parts: List[str] = [f"\"{cfg.pk_attr}\" = ?"]
            partiql_params: List[Any] = [comp]

            key_cond = "#pk = :pk"
            if cfg.sk_attr and abs_window:
                start, end = abs_window
                names["#sk"] = cfg.sk_attr
                values[":start"] = _format_date(start, cfg.date_format)
                values[":end"] = _format_date(end, cfg.date_format)
                key_cond += " AND #sk BETWEEN :start AND :end"
                where_parts.append(f"\"{cfg.sk_attr}\" BETWEEN ? AND ?")
                partiql_params.extend([values[":start"], values[":end"]])

            # Attach report type filter if requested
            _apply_report_filter(names, values, filters, where_parts, partiql_params)

            api_params: Dict[str, Any] = {
                "TableName": cfg.table_name,
                "KeyConditionExpression": key_cond,
                "ExpressionAttributeNames": names,
                "ExpressionAttributeValues": values,
            }
            if filters:
                api_params["FilterExpression"] = " AND ".join(filters)
            if limit is not None:
                api_params["Limit"] = int(limit)
            if cfg.sk_attr is not None:
                api_params["ScanIndexForward"] = not cfg.scan_descending

            partiql_stmt = f"SELECT * FROM \"{cfg.table_name}\" WHERE " + " AND ".join(where_parts)
            if limit is not None:
                partiql_stmt += f" LIMIT {int(limit)}"

            built.append(BuiltQuery(api_params=api_params, partiql_statement=partiql_stmt, partiql_parameters=partiql_params))

        return built

    # Case B: no companies, but we may have a GSI by report type
    if (not companies) and cfg.gsi_name_by_report_type and report_types and cfg.gsi_pk_attr:
        for rt in report_types:
            names: Dict[str, str] = {"#pk": cfg.gsi_pk_attr}
            values: Dict[str, Any] = {":pk": rt}
            where_parts: List[str] = [f"\"{cfg.gsi_pk_attr}\" = ?"]
            partiql_params: List[Any] = [rt]

            key_cond = "#pk = :pk"
            if cfg.gsi_sk_attr and abs_window:
                start, end = abs_window
                names["#sk"] = cfg.gsi_sk_attr
                values[":start"] = _format_date(start, cfg.date_format)
                values[":end"] = _format_date(end, cfg.date_format)
                key_cond += " AND #sk BETWEEN :start AND :end"
                where_parts.append(f"\"{cfg.gsi_sk_attr}\" BETWEEN ? AND ?")
                partiql_params.extend([values[":start"], values[":end"]])

            api_params = {
                "TableName": cfg.table_name,
                "IndexName": cfg.gsi_name_by_report_type,
                "KeyConditionExpression": key_cond,
                "ExpressionAttributeNames": names,
                "ExpressionAttributeValues": values,
            }
            if limit is not None:
                api_params["Limit"] = int(limit)
            if cfg.gsi_sk_attr is not None:
                api_params["ScanIndexForward"] = not cfg.scan_descending

            partiql_stmt = f"SELECT * FROM \"{cfg.table_name}\".\"{cfg.gsi_name_by_report_type}\" WHERE " + " AND ".join(where_parts)
            if limit is not None:
                partiql_stmt += f" LIMIT {int(limit)}"

            built.append(BuiltQuery(api_params=api_params, partiql_statement=partiql_stmt, partiql_parameters=partiql_params))

        return built

    # Case C: no companies and no report types, but a global-by-date GSI exists
    if (
        (not companies)
        and (not report_types)
        and cfg.gsi_name_by_date
        and cfg.gsi_date_pk_attr
        and cfg.gsi_date_pk_value is not None
    ):
        names: Dict[str, str] = {"#pk": cfg.gsi_date_pk_attr}
        values: Dict[str, Any] = {":pk": cfg.gsi_date_pk_value}
        where_parts: List[str] = [f"\"{cfg.gsi_date_pk_attr}\" = ?"]
        partiql_params: List[Any] = [cfg.gsi_date_pk_value]

        key_cond = "#pk = :pk"
        if cfg.gsi_sk_attr and abs_window:
            start, end = abs_window
            names["#sk"] = cfg.gsi_sk_attr
            values[":start"] = _format_date(start, cfg.date_format)
            values[":end"] = _format_date(end, cfg.date_format)
            key_cond += " AND #sk BETWEEN :start AND :end"
            where_parts.append(f"\"{cfg.gsi_sk_attr}\" BETWEEN ? AND ?")
            partiql_params.extend([values[":start"], values[":end"]])

        api_params = {
            "TableName": cfg.table_name,
            "IndexName": cfg.gsi_name_by_date,
            "KeyConditionExpression": key_cond,
            "ExpressionAttributeNames": names,
            "ExpressionAttributeValues": values,
        }
        if limit is not None:
            api_params["Limit"] = int(limit)
        if cfg.gsi_sk_attr is not None:
            api_params["ScanIndexForward"] = not cfg.scan_descending

        partiql_stmt = f"SELECT * FROM \"{cfg.table_name}\".\"{cfg.gsi_name_by_date}\" WHERE " + " AND ".join(where_parts)
        if limit is not None:
            partiql_stmt += f" LIMIT {int(limit)}"

        built.append(BuiltQuery(api_params=api_params, partiql_statement=partiql_stmt, partiql_parameters=partiql_params))
        return built

    # Nothing to build
    return built


def build_single_query_string(
    res: QueryParseResult,
    cfg: DynamoSchemaConfig,
) -> Optional[str]:
    """
    Convenience: return a human-readable PartiQL-like description for logging
    or copy/paste, combining multiple statements with '; '. Returns None if empty.
    """
    qs = build_dynamodb_queries(res, cfg)
    if not qs:
        return None
    parts = []
    for q in qs:
        # Render with literal params for readability (only safe for logging)
        stmt = q.partiql_statement
        rendered = stmt
        for p in q.partiql_parameters:
            if isinstance(p, str):
                lit = f"'{p.replace("'", "''")}'"
            else:
                lit = str(p)
            rendered = rendered.replace("?", lit, 1)
        parts.append(rendered)
    return "; ".join(parts)
