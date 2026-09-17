# Razorpay Build

AI-native commerce platform for merchants, built around a multi-agent orchestration layer and Razorpay payment flows. The project combines a FastAPI backend, PostgreSQL + pgvector storage, policy-aware recommendation logic, and a buyer-side agent test harness.

## Overview

This repository models an agentic storefront where a merchant orchestrator coordinates specialist agents for:

- catalog browsing and product lookup
- policy and FAQ retrieval
- recommendation and upsell/cross-sell logic
- checkout, cart actions, and Razorpay payment flow
- audit logging and revenue tracking

The backend exposes an A2A-compatible JSON-RPC endpoint for agent-based commerce interactions, while the `client/` directory provides a simulated buyer interface for testing the workflow.

## Project Structure

```text
.
├── .env.example
├── .gitignore
├── Makefile
├── README.md
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml
├── list_models.py
├── test_rzp_link.py
├── test_rzp_orders.py
├── backend/
│   ├── agents/
│   │   ├── base_agent.py
│   │   ├── catalog_agent.py
│   │   ├── checkout_agent.py
│   │   ├── knowledge_agent.py
│   │   ├── merchant_orchestrator.py
│   │   ├── recommendation_agent.py
│   │   └── ...
│   ├── api/
│   │   ├── main.py
│   │   └── routes.py
│   ├── audit/
│   ├── db/
│   │   ├── knowledge_docs/
│   │   ├── migrate.py
│   │   ├── pool.py
│   │   ├── schema.sql
│   │   └── seed.sql
│   ├── policies/
│   ├── razorpay/
│   └── revenue/
├── client/
│   ├── buyer_agent.py
│   └── cli.py
├── scripts/
│   ├── debug_tools.py
│   ├── test_phase1.py
│   ├── test_phase2.py
│   ├── test_phase3.py
│   ├── test_phase4.py
│   ├── test_phase5.py
│   └── test_phase6.py
└──
```

## Core Components

### Backend API

The app is built with FastAPI and starts from `backend/api/main.py`.

Key features:

- `app = FastAPI(...)` entry point
- CORS enabled for frontend testing
- A2A endpoint exposure via `add_a2a_routes_to_fastapi(...)`
- merchant request handler wired to the orchestrator
- dashboard-style endpoints for audit trail and revenue metrics

### Agent Orchestration

The merchant side is orchestrated by `MerchantOrchestratorAgent`. It delegates specialized tasks to:

- `CatalogAgent` for products and promos
- `KnowledgeAgent` for FAQs and policies
- `RecommendationAgent` for upsells/cross-sells
- `CheckoutAgent` for cart, order, and payment actions

### Data Layer

The database layer uses:

- PostgreSQL with `pgvector`
- SQL schema and seed scripts under `backend/db/`
- vector knowledge documents stored in `backend/db/knowledge_docs/`

### Payment Integration

The project integrates with Razorpay using the `razorpay` client and requires test credentials for local development.

## Requirements

- Python 3.12+
- Docker and Docker Compose
- A Gemini API key
- Razorpay test credentials

## Environment Setup

1. Copy the example environment file:

```bash
cp .env.example .env
```

2. Update `.env` with your values:

```env
APP_ENV=development
PORT=8000
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/commerce
GEMINI_API_KEY=your_gemini_api_key_here
RAZORPAY_KEY_ID=rzp_test_dummy_key_id
RAZORPAY_KEY_SECRET=dummy_key_secret
```

## Local Development

### 1) Create a virtual environment

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

### 2) Start PostgreSQL

```bash
make up
```

Or manually:

```bash
docker compose up -d
```

### 3) Run the database migration

```bash
make migrate
```

### 4) Start the API server

```bash
make dev
```

This runs:

```bash
uvicorn backend.api.main:app --reload --port 8000
```

The API will be available at:

- `http://localhost:8000`
- A2A discovery route under `/.well-known/agent.json`
- JSON-RPC route under `/api/jsonrpc`

## Buyer Test Harness

A CLI buyer agent is included for an interactive flow:

```bash
python client/cli.py
```

This launches a test harness that lets you describe a shopping request and observe how the merchant orchestrator handles catalog, policy, and checkout tasks.

## Useful Make Commands

```bash
make setup
make up
make down
make migrate
make dev
```

## Testing and Scripts

The repository includes a set of phase-specific scripts under `scripts/` and a few direct payment tests such as:

- `test_rzp_link.py`
- `test_rzp_orders.py`
- `scripts/test_phase1.py` through `scripts/test_phase6.py`

These can be used to validate the flow as the project evolves.

## Notes

This repo is designed for experimentation and local development of an agentic storefront. It focuses on the interaction between AI agents, merchant policy enforcement, and external payments, rather than a traditional monolithic storefront application.

## License

This project does not currently declare a license in the repository. If you plan to distribute or use it publicly, add an appropriate open-source license before publication.
