.PHONY: run build seed test

run:
\tdocker-compose up --build

build:
\tdocker-compose build

seed:
\tpython backend/scripts/seed_emails.py

test:
\tcurl -s http://127.0.0.1:8000/health | jq .
