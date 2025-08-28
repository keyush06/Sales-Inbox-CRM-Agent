# Sales-Inbox-CRM-Agent
An AI agent that triages sales emails, extracts structured deal info, and proposes/commits CRM updates through a tool boundary (MCP-shaped). Includes a tiny UI, metrics, evaluation harness, and optional Azure container deployment.

##### (Please note that this project is my side project and is still WIP)

### A Sneak Peek
- #### Triage & Extraction:
  Classifies email intent (new_lead, pricing, renewal, spam) and extracts {company, contact, sku, qty, budget, notes} via LLM (with a stub fallback).

- #### Propose → Approve (safe by default):

  - Propose: run the agent and get a validated dry-run CRM change (no writes).

  - Approve: commit the proposed change to the CRM table.

- #### MCP-shaped tools:

  - crm.search_leads(query)

  - crm.upsert_opportunity(fields, dry_run) (validates on dry-run; writes on commit)

- #### Audit & Metrics:
  Every action is logged; metrics include p50/p95 latency per step and cost/email.

- #### Tiny Frontend:
  Minimal inbox → detail → run agent → review diff → approve.

- #### Eval Harness:
  Batch evaluation over seed emails (intent micro-F1, simple field exact-match).

  ### 🧰 Tech stack
  - FastAPI
  - SQLAlchemy
  - Pydantic
  - Streamlit (tiny UI)
  - Docker · (optional)
  - OpenAI API (optional)
  - Azure App Service + ACR
