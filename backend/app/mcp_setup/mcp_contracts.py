from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

"""
These are basically the new schemas for the tool input/output
"""

class LeadResult(BaseModel):
    id: int
    company: Optional[str] = None
    contact: Optional[str] = None

class SearchLeadsRequest(BaseModel):
    query: str = Field(..., min_length=1)

class SearchLeadsResponse(BaseModel):
    results: List[LeadResult]
    total: int

class UpsertFields(BaseModel):
    source_email_id: int
    company: Optional[str] = None
    contact: Optional[str] = None
    sku: Optional[str] = None
    qty: Optional[int] = None
    budget: Optional[float] = None
    notes: Optional[str] = None

class UpsertArgs(BaseModel):
    fields: UpsertFields
    dry_run: bool = Field(True, description="If true, do not commit to DB")

class UpsertResponse(BaseModel):
    dry_run: bool
    status: Literal["validated","created","updated", "no_change"]
    id: Optional[int] = None
    # created: bool = False
    # updated: bool = False
    difference: Dict[str, Any] = {}