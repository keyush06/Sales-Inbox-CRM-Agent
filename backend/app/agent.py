import re 
from backend.app.schemas import AgentResponse, OpportunityCreate, EmailReceived

SKU_PATTERN = re.compile(r"\bSKU[- ]?([A-Z0-9\-]+)\b", re.IGNORECASE)
QTY_PATTERN = re.compile(r"\b(\d{1,4})\s*(units|pcs|pieces|qty)\b", re.IGNORECASE)
BUDGET_PATTERN = re.compile(r"\$\s?([0-9]+(?:\.[0-9]{2})?)")


# def _extract_company()
def _classify_extract(email: EmailReceived):
    search_text = f"{email.subject}{email.body}".lower()

    #check for various intent fields
    if "renewal" in search_text or "renew" in search_text:
        intent = "renewal"

    elif "price" in search_text or "quote" in search_text or "pricing" in search_text:
        intent = "pricing"
    elif "unsubscribe" in search_text or "spam" in search_text:
        intent = "spam"
    else:
        intent = "new_lead"

    # field extractions
    sku_match = SKU_PATTERN.search(search_text)
    quantity_match = QTY_PATTERN.search(search_text)
    budget_match = BUDGET_PATTERN.search(search_text)

    opportunity = OpportunityCreate(
        company=_extract_company(email),
        contact=_extract_contact(email),
        sku=sku_match.group(1).upper() if sku_match else None,
        qty=int(quantity_match.group(1)) if quantity_match else None,
        budget=float(budget_match.group(1)) if budget_match else None,
        notes=None

    )

    return AgentResponse(
        email=email,
        intent= intent,
        metadata=opportunity
    )

def _extract_company(email: EmailReceived) -> str:
    if "@" in email.sender:
        domain = email.sender.split("@")[-1].split(">")[-1]
        name = domain.split(".")[0]
        return name.capitalize()
    # fallback
    return "Unknown co."

def _extract_contact(email: EmailReceived)->str:
    for line in email.body.splitlines():
        if "regards" in line.lower() or "thanks" in line.lower():
            # return next non-empty line
            return next((l.strip() for l in email.body.splitlines() if l.strip()), None)
    return "Unknown contact"

    