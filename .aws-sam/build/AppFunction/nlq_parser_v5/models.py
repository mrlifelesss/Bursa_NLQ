from __future__ import annotations

import datetime as dt
from typing import List, Dict, Optional

from pydantic import BaseModel, Field


class TimeFrame(BaseModel):
    kind: str = Field(description="'relative', 'absolute', or 'none'")
    # Relative
    relative_value: Optional[int] = None
    relative_unit: Optional[str] = None  # 'days'|'weeks'|'months'|'years'
    # Absolute
    start_date: Optional[dt.date] = None
    end_date: Optional[dt.date] = None
    # Diagnostics
    raw: Optional[str] = None


class QueryParseResult(BaseModel):
    companies: List[str] = Field(default_factory=list)
    matched_company_aliases: Dict[str, str] = Field(default_factory=dict)
    report_types: List[str] = Field(default_factory=list)
    matched_report_aliases: Dict[str, str] = Field(default_factory=dict)
    quantity: Optional[int] = None
    time_frame: TimeFrame = Field(default_factory=lambda: TimeFrame(kind="none"))
    confidence: float = 0.0
    notes: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    # If LLM fallback was used, store its raw textual response for auditing
    llm_raw: Optional[str] = None
    # Diagnostic: words covered by heuristics (pre-LLM)
    heuristics_understood_text: Optional[str] = None
    # Diagnostic: words covered by final parse (post-LLM if used, else same as heuristics)
    final_understood_text: Optional[str] = None
