from backend.app.schemas import AgentResponse, OpportunityCreate, EmailReceived
import openai
import time, os
from typing import Dict, List, Tuple, Any
import json
from backend.app.agent import _classify_extract
from dotenv import load_dotenv
from pathlib import Path

_root = Path(__file__).resolve().parents[2]  # repo root
_env = _root / ".env"
if _env.exists():
    load_dotenv(_env)
    print("environment loaded")

## Here we will use an LLM to classify intent and extract the fields from the emails 
## replacing the naive agent stub that leveraged regex

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def _classify_intent_llm(email: EmailReceived) -> Tuple[str, Dict[str, Any]]:

    """
    Use an LLM to classify the intent of the email.
    """
    if  not OPENAI_API_KEY:
        response = _classify_extract(email)
        return response.intent, {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "cost_usd": 0.0}
    
    client = openai.OpenAI(
        api_key=OPENAI_API_KEY
    )
    system_prompt = f"""
    You are a helpful email assistant. Your task is to see assess the email and classify the intent
    of the email. Output the intent one of the following: -
        new_lead
        pricing
        renewal
        spam

    You must only output the intent, nothing else.
    """

    user_prompt = f"Email text: \n{email.body}\n\n Return the intent as mentioned in the system prompt."
    t0 = time.perf_counter() ## this will start the timer

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0
    )

    dt = (time.perf_counter() - t0) * 1000 # this will give us the response time in ms

    ## we extract the label
    label = response.choices[0].message.content.strip().lower()
    usage = getattr(response, 'usage', {})
    tokens = usage.total_tokens if usage else 0
    cost = tokens * 0.0004
    return label, {"total_tokens": tokens, "latency_milliseconds": dt, "cost": cost}

def _extract_metadata_llm(email:EmailReceived):
    ## checking openai key
    if not OPENAI_API_KEY:
        response = _classify_extract(email)
        return response.metadata
    
    client = openai.OpenAI(
        api_key=OPENAI_API_KEY
    )

    # enforcing the scehma
    schema = {
        "type": "object",
        "properties": {
            "company": {
                "type": "string",
                "description": "The name of the company"
            },
            "contact":{
                "type": "string",
                "description": "The email address or the phone number of the company (email address is preferred)."
            },
            "sku": {
                "type": "string",
                "description": "The SKU of the product"
            },
            "qty": {
                "type": "integer",
                "description": "The quantity of the product"
            },
            "budget": {
                "type": "number",
                "description": "The budget for the purchase"
            },
            "notes": {
                "type": "string",
                "description": "Any additional notes or comments"
            }
        },
        "additionalProperties": False
    }

    system_prompt = "Extract the structured fields from the email. If Unknown, omit the field. Also notes is not the same as the body of the email text."
    user_prompt = f"Email text: \n{email.body}\n\n Return the structured fields as a JSON object with keys: company, contact, sku, qty, budget, notes."

    t0 = time.perf_counter() ## this will start the timer

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0,
        response_format={"type":"json_schema", "json_schema": {"name": "Extract", "schema": schema}}
    )

    dt = (time.perf_counter() - t0) * 1000 # this will give us the response time in ms

    ## we extract the label
    fields = response.choices[0].message.content.strip()
    try:
        data = json.loads(fields)
    except:
        data = {}
    usage = getattr(response, 'usage', {})
    tokens = usage.total_tokens if usage else 0
    cost = tokens * 0.0004

    ## creating the Opportunitycreate object
    data = OpportunityCreate(
        company=data.get("company") if data.get("company") else "Unknown company (llm)",
        contact=data.get("contact"),
        sku=data.get("sku"),
        qty=data.get("qty"),
        budget=data.get("budget"),
        notes=data.get("notes")
    )
    print("this is our data fetched by LLM", data)
    return data, {"total_tokens": tokens, "latency_milliseconds": dt, "cost": cost}
