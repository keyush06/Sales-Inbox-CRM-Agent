import json
from unittest import result
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from backend.app.db import Base, engine, get_db
from backend.app.mcp_setup.mcp_contracts import UpsertFields, UpsertArgs
from backend.app.mcp_setup.mcp_server import CRM_toolServer as CRMToolServer
from backend.app import models
from backend.app.schemas import AgentResponse, EmailReceived, OpportunityCreate
from backend.app.agent import _classify_extract
from datetime import datetime
import json

## Now that we have made llm.py, we can change the calls directed to the LLMs
from backend.app.llm import _classify_intent_llm, _extract_metadata_llm
from backend.app.metrics import Metrics

# creating the fastapi object
app = FastAPI(title = "Sales Inbox CRM agent")

## creating tables on startup
"""
When you define a class like Opportunity(Base), you're telling SQLAlchemy:

This class maps to a table called opportunities in your database.
Each attribute (like company, qty, etc.) becomes a column in that table.

SQLAlchemy looks at all your model classes (Opportunity, User, AuditLog, etc.) 
and automatically creates the corresponding 
tables in your database (SQLite in your case), if they don't already exist.
"""
Base.metadata.create_all(bind=engine)

## health endpoint
@app.get("/health")
def health_check():
    return {"status": "ok"}

## emails endpoint
@app.get("/emails", response_model=List[EmailReceived])
def get_all_emails(db: Session = Depends(get_db)):
    emails = db.query(models.Email).order_by(models.Email.id).all()
    return emails

## get any specific email
@app.get("/emails/{email_id}", response_model=EmailReceived)
def get_email(email_id: int, db: Session = Depends(get_db)):
    email = db.query(models.Email).get(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return email

## get list of emails
@app.get("/emails/batch", response_model=List[EmailReceived])
def _get_emails(email_ids: List[int] = Query(...), db: Session = Depends(get_db)):
    emails = db.query(models.Email).filter(models.Email.id.in_(email_ids)).all()
    return emails

@app.post("/run_agent/{email_id}", response_model=AgentResponse)
def run_agent(email_id: int, db: Session = Depends(get_db)):
    email = db.query(models.Email).get(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    # Call the agent function
    # response = _classify_extract(email) ## prototype when the llm wasn't configured
    response_intent, stats_classify = _classify_intent_llm(email)
    response_metadata, stats_extract = _extract_metadata_llm(email)

    response_metadata = response_metadata.model_dump()  # this wil just change it to dict
    # print("**++ response data", response_metadata)
    print(type(response_metadata))

    ## processing the metrics
    Metrics.classify_latencies.append(float(stats_classify.get("latency_milliseconds", 0)))
    Metrics.extract_latencies.append(float(stats_extract.get("latency_milliseconds", 0)))
    Metrics.total_cost+= float(stats_classify.get("cost", 0.0)) + float(stats_extract.get("cost", 0.0))
    Metrics.total_tokens+= int(stats_classify.get("total_tokens", 0)) + int(stats_extract.get("total_tokens", 0))

    fields = UpsertFields(
        source_email_id=email_id,
        company=response_metadata.get("company"),
        contact=response_metadata.get("contact"),
        sku=response_metadata.get("sku"),
        qty=response_metadata.get("qty"),
        budget=response_metadata.get("budget"),
        notes=response_metadata.get("notes")
    )

    args_passed = UpsertArgs(fields=fields, dry_run=True)
    result = CRMToolServer().upsert_opportunity(args_passed, db)

    response = AgentResponse(
        email=email,
        intent=response_intent,
        metadata = response_metadata
    )


    ## Make an audit trail by adding this to the audit table
    log = models.AuditLog(
        email_id = email_id,
        action = "run_agent",
        payload = {
            "agent_result":response.model_dump(mode = "json"),
            "upsert_result": result.model_dump()  # added after we have the tool functionality v3
        },
        created_at = datetime.utcnow()
    )

    db.add(log)
    db.commit()

    return response

@app.post("/approve/{email_id}")
def commit_email(email_id: int, db:Session = Depends(get_db)):
    """We will use the agent run logs to commit the last run agent"""

    log = db.query(
        models.AuditLog
    ).filter(models.AuditLog.email_id==email_id,models.AuditLog.action == "run_agent") \
    .order_by(models.AuditLog.created_at.desc()).first()

    if not log:
        raise HTTPException(status_code=404, detail="No agent run log found for this email")
    
    print("this is what log payload is", log.payload, type(log))
    payload = log.payload or {}
    # print("payload here: ", payload)
    print(type(payload))

    if isinstance(payload, str):
        payload = json.loads(payload)

    metadata_opp = payload.get("metadata", {})
    print("Payload has been changed to dict here: ",type(payload))

    """The steps below were done previously without the MCP wherein the decisions
        were made by the agent.
    """
    # opportunity = models.Opportunity(
    #     source_email_id = email_id,
    #     company = metadata_opp.get("company"),
    #     contact = metadata_opp.get("contact"),
    #     sku = metadata_opp.get("sku"),
    #     qty = metadata_opp.get("qty"),
    #     budget = metadata_opp.get("budget"),
    #     notes = metadata_opp.get("notes")
    # )

    ## here we add the record to our base table
    #db.add(opportunity) # first way

    """Now we will use the mcp server to upsert the record"""
    upsert_fields = UpsertFields(
        source_email_id = email_id,
        company = metadata_opp.get("company"),
        contact = metadata_opp.get("contact"),
        sku = metadata_opp.get("sku"),
        qty = metadata_opp.get("qty"),
        budget = metadata_opp.get("budget"),
        notes = metadata_opp.get("notes")
    )

    upsert_args = UpsertArgs(
        fields=upsert_fields,
        dry_run=False
    )

    result = CRMToolServer().upsert_opportunity(upsert_args, db)

    ## changing the status
    email = db.query(models.Email).get(email_id)
    if email:
        email.processed = True

    # Now we add it to our audit table
    ## manually converting to the dictionary
    """
    Remember opportunity here is a SQLAlchemy instance and we cannot use model_dump()
    here. We have to create a dict ourselves and then add it to the logs table.
    Though the step is not necessary as the responses are taken care of by the MCP
    """
#     db.add(models.AuditLog(
#     action = "Approve",
#     email_id = email_id,
#     payload = {
#         "source_email_id": opportunity.source_email_id,
#         "company": opportunity.company,
#         "contact": opportunity.contact,
#         "sku": opportunity.sku,
#         "qty": opportunity.qty,
#         "budget": opportunity.budget,
#         "notes": opportunity.notes
#     },
#     created_at = datetime.now()
# ))

    db.commit()
    return {"status": "success", "result_tool": result} if email.processed else {"status": "failed"}

## adding a get metrics endpoint
@app.get("/metrics")
def get_metrics(db:Session = Depends(get_db)):
    processed = db.query(models.Email).filter(models.Email.processed==True).count()
    results = Metrics._get_metrics()
    # print(f"the result of the metrics is rightly {type(results)=={dict}}")
    results["processed_emails"] = processed
    return results

