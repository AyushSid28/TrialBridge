# TrialBridge

TrialBridge helps match patients to clinical trials using eligibility rules instead of going through records by hand.

It stores trial listings from public registries (US NCT / ClinicalTrials.gov and EU EudraCT) alongside patient records (conditions, ICD-10 codes, demographics). A set of agents then finds likely candidates and ranks them with a short explanation of why they fit or were excluded.

This is a screening helper for recruitment — not a diagnosis or treatment tool.

## What it does

- Search and browse trials by condition, title, or NCT ID
- Ask questions in plain English against the patient database
- Match patients to a trial (or to typed criteria)
- Score and rank candidates from 0–100 (condition, age, sex, geography, health)

## How the agents work

The usual path is a pipeline, not a single model:

1. **Text-to-SQL** — first cut: turn trial rules or a question into a database query
2. **Root word search** — second cut: match diagnoses even when the wording differs, plus age / sex / location filters
3. **Orchestrator** — loads a trial or free-text criteria and runs the two steps above
4. **Scoring** — ranks the remaining patients and flags exclusion criteria

You can also run each agent on its own from the API or the Streamlit UI. See [AGENTS_README.md](AGENTS_README.md) for how to try them.

## Tech stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI, Python 3.11+ |
| Database | PostgreSQL, SQLAlchemy (async), Alembic |
| LLM | OpenRouter (`gpt-4o-mini`), optional Groq |
| Dashboard | Streamlit, Plotly |
| Infra | Docker, Gunicorn |

## Prerequisites

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- PostgreSQL

## Quick start

```bash
uv sync
cp .env.example .env
# set DATABASE_URL, SECRET_KEY, API_KEY, OPENROUTER_API_KEY

uv run alembic upgrade head
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

Streamlit UI:

```bash
uv run streamlit run streamlit_app.py
```

Opens at [http://localhost:8501](http://localhost:8501)

### Docker

```bash
cp .env.example .env
# set SECRET_KEY, API_KEY, and at least one LLM key in .env
docker compose up --build
```

This starts Postgres on port **5432** and the API on port **8000**. The API container is pointed at the `db` service automatically, so you do not need to change `DATABASE_URL` in `.env` for Docker.

After the database is up, apply migrations once:

```bash
docker compose exec api alembic upgrade head
```

Or from the host (with `DATABASE_URL` pointing at `localhost:5432`):

```bash
uv run alembic upgrade head
```

## Project layout

| Path | Purpose |
|------|---------|
| `src/main.py` | FastAPI entry |
| `src/api/` | REST routes (`/api/v1/agents/...`) |
| `src/agents/` | Text-to-SQL, root word search, orchestrator, scoring |
| `src/db/` | SQLAlchemy models and session |
| `src/scrappers/` | Trial scrapers and patient import |
| `src/schemas/` | Pydantic request/response models |
| `src/services/` | Pipeline cache and rate limiting |
| `streamlit_app.py` | Dashboard for matching and scoring |
| `migrations/` | Alembic migrations |
| `tests/` | Pytest suite |

## Configuration

Copy `.env.example` to `.env` and set:

- `DATABASE_URL` — PostgreSQL connection string
- `SECRET_KEY` — application signing key
- `API_KEY` — value for the `X-API-Key` header
- `OPENROUTER_API_KEY` / `GROQ_API_KEY` — LLM keys

## Development

```bash
uv run pytest
uv run ruff check .
uv run black .
uv run alembic revision --autogenerate -m "describe change"
```

Pull requests and branch pushes run `.github/workflows/ci.yml` (unit tests plus model tests against Postgres).

## Production notes

- Set `DEBUG=False` and use a strong `SECRET_KEY`
- Run behind a reverse proxy with TLS
- Prefer `uv sync --frozen` in CI/Docker
