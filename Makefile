.PHONY: setup dev up down migrate simulate

setup:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

up:
	docker compose up -d

down:
	docker compose down

migrate:
	.venv/bin/python backend/db/migrate.py

dev:
	.venv/bin/uvicorn backend.api.main:app --reload --port 8000

simulate:
	.venv/bin/python cli/simulate_batch.py

cli:
	.venv/bin/python cli/interactive_buyer.py
