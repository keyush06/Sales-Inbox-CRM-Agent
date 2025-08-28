import time, json, requests, statistics
from typing import Tuple, List
from backend.app.agent import _classify_extract
from backend.app.db import SessionLocal
from backend.app import models

api = "http://127.0.0.1:8000"

def corrects(y_pred, y_true):
    correct = [1 for (a,b) in zip(y_pred, y_true) if a==b]
    return sum(correct)/len(y_true) if len(y_true)>0 else 0.0

## debug
def email_to_dict(e: models.Email) -> dict:
    return {
        "id": e.id,
        "subject": e.subject,
        "sender": e.sender,
        "recipient": e.recipient,
        "body": e.body,
        "is_read": bool(e.is_read),
        "received_at": e.received_at.isoformat() if getattr(e, "received_at", None) else None,
        "processed": bool(e.processed),
    }

def eval_loop():
    db = SessionLocal()
    emails = db.query(models.Email).order_by(models.Email.id.asc()).all()

    intents_true, intents_llm = [], []
    latencies = []
    total = 0
    rights = 0

    for email in emails:
        #debug
        email_dict = email_to_dict(email)
        print("\n=== Local email object (before POST) ===")
        print(json.dumps(email_dict, indent=2)[:2000])  # truncated safely for console

        # also fetch what the running API sees (helps detect DB mismatches)
        try:
            resp_get = requests.get(f"{api}/emails/{email.id}", timeout=5)
            print("Server GET /emails/{id} status:", resp_get.status_code)
            if resp_get.ok:
                print("Server sees email:", json.dumps(resp_get.json(), indent=2)[:2000])
            else:
                print("Server GET response:", resp_get.text)
        except Exception as e:
            print("Could not contact server GET /emails/{id}:", e)

        ## the tools getting called
        response_stub_agent = _classify_extract(email)
        intents_true.append(response_stub_agent.intent)

        t0 = time.perf_counter()
        response_llm = requests.post(f"{api}/run_agent/{email.id}", timeout=60)
        dt = (time.perf_counter() - t0)*1000
        latencies.append(dt)

        if response_llm.status_code != 200:
            print(f"Request of the LLM failed on email ID {email.id} and {response_llm.text}")
            continue

        response_llm_data = response_llm.json()
        intents_llm.append(response_llm_data.get("intent")) 

        ## Field extraction
        gt_metadata = response_stub_agent.metadata
        llm_metadata = response_llm_data.get("metadata", {})
        print("ground truth naive: ", gt_metadata)
        print("-"*10)
        print("LLM output: ", llm_metadata)

        print("*"*100)

        for key in ["company"]: ## optonally add "contact" here
            gt = (gt_metadata.company or "").strip().lower()
            pred = (llm_metadata.get("company", "") or "").strip().lower()

            if gt or pred:
                total+=1
                if gt==pred:
                    rights +=1

    f1_score = corrects(intents_llm, intents_true)
    lat_p50 = statistics.median(latencies) if latencies else 0.0
    lat_p95 = sorted(latencies)[int(0.95 * (len(latencies)-1))] if latencies else 0.0
    field_accuracy = rights / total if total > 0 else 0.0

    print(json.dumps({
        "n": len(emails),
        "intent_micro_f1": round(f1_score, 3),
        "field_exact_match_company_contact": round(field_accuracy, 3),
        "ext_latency_ms_p50_external": round(lat_p50, 1),
        "ext_latency_ms_p95_external": round(lat_p95, 1)
    }, indent=2))

if __name__ == "__main__":
    eval_loop()

