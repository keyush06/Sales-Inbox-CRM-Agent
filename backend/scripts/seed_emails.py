import os
import sys

print("present directory for me: ",os.getcwd())
print("system directory for me: ",sys.path)

from faker import Faker
import random
from sqlalchemy.orm import Session
from backend.app.db import SessionLocal, Base, engine
from backend.app import models

def seed(n=30):
    Base.metadata.create_all(bind=engine)
    fake = Faker()
    skus = [f"SKU-{fake.lexify(text='????-##')}" for _ in range(10)]
    subjects = [
        "Request for pricing on {sku}",
        "Renewal discussion for {quarter}",
        "Bulk order inquiry: {qty} units",
        "Need quote for {sku}",
        "Follow-up: {topic}",
        "Product availability for {sku}",
        "Spam offer - earn $$$ fast",
        "Exclusive deal for {company}",
        "Urgent: {sku} required",
        "Can you match competitor pricing?",
        "Interested in partnership",
        "Question about invoice #{invoice}",
        "Unsubscribe me from this list.",
        "Feedback on last shipment",
        "Order confirmation for {sku}"
    ]
    bodies = [
        "Hello {recipient},\nWe'd like a quote for {qty} units of {sku}. Our budget is ${budget}.\nRegards,\n{contact}",
        "Hi,\nWe're considering renewal for {quarter}. Could you share terms?\nThanks,\n{contact}",
        "Please send pricing for {qty} pcs of {sku} and expected lead time.\nSincerely,\n{contact}",
        "Unsubscribe me from this list.",
        "Looking to purchase {qty} pieces. Our target is ${budget}.\n- {contact}",
        "Can you confirm availability of {sku} for immediate shipment?",
        "We received the last shipment, but there were issues with {issue}.",
        "Spam: You have won a free iPhone! Click here.",
        "Please send invoice for last order.",
        "Interested in a partnership with {company}.",
        "Urgent: Need {qty} units of {sku} by next week.",
        "Can you match the price offered by {competitor}?",
        "Order confirmation for {sku}. Please process ASAP.",
        "Feedback: The packaging for {sku} could be improved.",
        "Hi {recipient},\nCan you provide a quote for {qty} units of {sku}?\nBest,\n{contact}"
    ]

    db: Session = SessionLocal()
    for _ in range(n):
        sender = f"{fake.user_name()}@{fake.domain_name()}"
        recipient = fake.first_name()
        contact = fake.name()
        company = fake.company()
        sku = random.choice(skus)
        qty = random.randint(10, 500)
        budget = random.randint(1000, 10000)
        quarter = random.choice(["Q1", "Q2", "Q3", "Q4"])
        topic = fake.bs().capitalize()
        invoice = fake.random_number(digits=5)
        issue = random.choice(["delay", "damage", "missing items", "wrong SKU"])
        competitor = fake.company()

        subject = random.choice(subjects).format(
            sku=sku, qty=qty, company=company, quarter=quarter, topic=topic, invoice=invoice
        )
        body = random.choice(bodies).format(
            recipient=recipient, contact=contact, company=company, sku=sku, qty=qty,
            budget=budget, quarter=quarter, topic=topic, invoice=invoice, issue=issue, competitor=competitor
        )
        db.add(models.Email(sender=sender, subject=subject, body=body))
    db.commit()
    db.close()

if __name__ == "__main__":
    seed(30)
    print("Seeded 30 diverse emails.")