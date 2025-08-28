import time, json
from typing import Dict, Any, Optional
from backend.app.db import SessionLocal, get_db
from sqlalchemy.orm import Session
from fastapi import Depends
from backend.app import models
from backend.app.metrics import Metrics
from backend.app.mcp_setup.mcp_contracts import LeadResult, SearchLeadsRequest, SearchLeadsResponse, UpsertArgs, UpsertResponse


class CRM_toolServer:
    def __init__(self):
        self.latencies = []

    def search_leads(self, req: SearchLeadsRequest, db:Session)-> SearchLeadsResponse:
        query = req.query.lower()

        rows = db.query(models.Opportunity) \
                .filter(models.Opportunity.company.ilike(f"%{query}%")) \
                .limit(10) \
                .all()

        results = [
            LeadResult(
                id = row.id,
                company = row.company,
                contact = row.contact
            )
            for row in rows
        ]

        return SearchLeadsResponse(
            results=results,
            total=len(results)
        )

    def upsert_opportunity(self, args: UpsertArgs, db: Session) -> UpsertResponse:
        t0 = time.perf_counter()
        metadata = args.fields

        exists = (
            db.query(models.Opportunity) \
            .filter(metadata.source_email_id == models.Opportunity.source_email_id) \
            .first()
        )

        fields_to_check = [
            "company",
            "contact",
            "sku",
            "qty",
            "budget",
            "notes"
        ]

        if exists:
            difference = {}
            for field in fields_to_check:
                if getattr(metadata,field) is not None and getattr(metadata, field) != getattr(exists, field):
                    difference[field] = {
                        "old": getattr(exists, field),
                        "new": getattr(metadata, field)
                    }
        else:
            new_dict = {k:getattr(metadata,k) for k in fields_to_check if getattr(metadata,k) is not None}
            difference = {k: {"from": None, "to": v} for k, v in new_dict.items()}

        dt = (time.perf_counter() - t0) * 1000
        self.latencies.append(dt)

        if args.dry_run:
            Metrics.tool_latencies = self.latencies
            return UpsertResponse(
                dry_run=True,
                status="validated",
                id = exists.id if exists else None,
                difference=difference
            )
        
        # Real write path: apply changes or create new record
        if exists:
            changed = False
            for attr in fields_to_check:
                new_val = getattr(metadata, attr, None)
                if new_val is not None and new_val != getattr(exists, attr):
                    setattr(exists, attr, new_val)
                    changed = True
            if changed:
                db.add(exists)
                result_status = "updated" if changed else "no_change"
                result_id = exists.id
            # created_flag = False
            # updated_flag = changed
        else:
            new_o = models.Opportunity(
                source_email_id = metadata.source_email_id,
                company = getattr(metadata, "company", None),
                contact = getattr(metadata, "contact", None),
                sku = getattr(metadata, "sku", None),
                qty = getattr(metadata, "qty", None),
                budget = getattr(metadata, "budget", None),
                notes = getattr(metadata, "notes", None),
            )
            db.add(new_o)
            db.flush()  # populate id
            result_status = "created"
            result_id = new_o.id
            # created_flag = True
            # updated_flag = False

        # updating the latency'
        Metrics.tool_latencies = self.latencies
        
        # adding to the logs and then persisting the records in the DB 
        db.add(models.AuditLog(
            action = "Upserted record",
            email_id = metadata.source_email_id,
            payload = {
                "result": {
                    "status": result_status,
                    "id": result_id,
                    "diff": difference
                }
            }
        ))

        db.commit()

        return UpsertResponse(
            dry_run=False,
            status=result_status,
            id=result_id,
            difference=difference
        )