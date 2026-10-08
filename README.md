# TrialBridge

**AI-powered clinical trial patient-matching platform.**

TrialBridge scrapes clinical trials from [ClinicalTrials.gov](https://clinicaltrials.gov), imports patient records, and uses LLM-based agents to score and rank patients against trial eligibility criteria — helping researchers find the right patients faster.

## ✨ Features

-  **Trial Search** — Browse and search recruiting US clinical trials by condition, keyword, or NCT ID
-  **AI Matching** — LLM-powered orchestrator chains Text-to-SQL, root-word search, and demographic filters
-  **Patient Scoring** — Multi-factor eligibility scoring (condition, age, sex, geography, health) with ICD-10 mapping
-  **Natural Language Criteria** — Describe patient requirements in plain English and let the AI handle the rest
-  **Analytics Dashboard** — Streamlit UI with score distributions, radar charts, and patient inspector
-  **Docker Ready** — Multi-stage Dockerfile for production deployment

##  Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI, Python 3.11+ |
| **Database** | PostgreSQL, SQLAlchemy (async), Alembic |
| **AI/LLM** | OpenAI, Groq (via OpenRouter) |
| **Dashboard** | Streamlit, Plotly, Matplotlib |
| **Infra** | Docker, Gunicorn, Logfire |

##  Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- PostgreSQL

##  Quick Start

### Local

```bash
uv sync
cp .env.example .env
uv run alembic upgrade head
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

API docs → [http://localhost:8000/docs](http://localhost:8000/docs)

### Docker

```bash
cp .env.example .env
docker compose build
docker compose up api
```

The API listens on port **8000**.

##  Project Structure

| Path | Purpose |
|------|---------|
| `src/main.py` | FastAPI application entry |
| `src/api/` | REST API routes |
| `src/agents/` | LLM agents — scoring, matching, text-to-SQL |
| `src/db/` | SQLAlchemy models and async session |
| `src/scrappers/` | ClinicalTrials.gov scraper, Kaggle patient importer |
| `src/schemas/` | Pydantic request/response schemas |
| `src/services/` | Pipeline caching and rate limiting |
| `src/core/` | Settings and logging |
| `streamlit_app.py` | Analytics dashboard |
| `migrations/` | Alembic migration scripts |
| `tests/` | Pytest suite |

##  Development

```bash
uv run pytest
uv run ruff check .
uv run black .
uv run alembic revision --autogenerate -m "describe change"
```

##  Configuration

Copy `.env.example` to `.env` and set:

- `DATABASE_URL` — PostgreSQL connection string
- `SECRET_KEY` — Application signing key
- `API_KEY` — API authentication key
- `OPENROUTER_API_KEY` / `GROQ_API_KEY` — LLM provider keys

##  Production

- Set `DEBUG=False` and use a strong `SECRET_KEY`
- Run behind a reverse proxy with TLS
- Use `uv sync --frozen` in CI/Docker
