"""
This file is using the PyDantic library for data validation and settings management. Pydantic validation works by checking incoming 
request data against the fields and types defined in your model (OpportunityCreate). If the data doesn't
 match—like missing required fields or wrong types—FastAPI automatically returns a 422 error with details.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Literal, Any
from datetime import datetime

class OpportunityCreate(BaseModel):

    company: str  # required
    contact: Optional[str] = None
    sku: Optional[str] = None
    qty: Optional[int] = None
    budget: Optional[float] = None
    notes: Optional[str] = None

class EmailReceived(BaseModel):
    id: int
    subject: str
    sender: str
    recipient: Optional[str] = None
    body: str
    is_read: bool
    received_at: datetime  # ISO format datetime
    processed: bool

    class Config:
        from_attributes = True

Intent = Literal["new_lead", "pricing", "renewal", "spam"]

class AgentResponse(BaseModel):
    email: EmailReceived
    intent: Intent
    metadata: OpportunityCreate | Dict[str, Any]  # OpportunityCreate for new_lead, dict for others