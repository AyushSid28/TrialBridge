# TrialBridge agents

How to run the matching pipeline and try each agent from the Streamlit UI.

## Setup

```bash
cp .env.example .env
uv sync
```

Required `.env` keys:

```
DATABASE_URL=postgresql://user:pass@host:port/db
OPENROUTER_API_KEY=sk-or-v1-...
API_KEY=your-api-key
```

The dashboard reads two of these from the environment:

| Variable | Default | Purpose |
|---|---|---|
| `API_KEY` | _(none)_ | Sent as the `X-API-Key` header. Must match the backend, or every request returns 401. |
| `TRIALBRIDGE_API_URL` | `http://localhost:8000` | Where the backend is listening. Override when it is not local. |

## Start the backend

```bash
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)

## Start Streamlit

```bash
uv run streamlit run streamlit_app.py
```

Opens at [http://localhost:8501](http://localhost:8501)

## Agent pipeline

For a ranked shortlist, scoring calls the orchestrator first. The orchestrator uses text-to-SQL, then root word search.

| Agent | Endpoint | What it is for |
|---|---|---|
| **Text-to-SQL** | `POST /api/v1/agents/text-to-sql` | Ask in English, get SQL and results. First filter when matching a trial. |
| **Root word search** | `POST /api/v1/agents/root-word-search` | Find patients by condition even if wording differs. Second check after SQL. |
| **Orchestrator** | `POST /api/v1/agents/match-patients` | Match patients to a trial (NCT ID) or to typed criteria. |
| **Scoring** | `POST /api/v1/agents/score-patients` | Rank matched patients 0-100 and show why they were included or excluded. |

Typical flow: pick a trial -> orchestrator (SQL, then root word search) -> scoring.

The Streamlit dashboard is a single screen that drives the **scoring**
endpoint, which runs the whole pipeline for you. The other three agents are
exposed over the API and are easiest to try from Swagger at
[http://localhost:8000/docs](http://localhost:8000/docs).

## Trying each agent

### From the dashboard

- **Data source** - Kaggle (4K patients) or FHIR
- **Input mode** - *Select Trial* for a registry trial, or *Custom Input* to
  describe criteria in plain language
- **Max patients** - caps how many candidates are scored
- Click **Run Scoring**

The results show the score distribution, a per-factor radar chart for the top
candidate, ranked Eligible / Excluded tables, a Pipeline panel with per-stage
timings and the generated SQL, and an inspector for any single patient.

Good trials to start with: `NCT06230718` (stroke) or `NCT07003997` (depression).

### From Swagger

Open [http://localhost:8000/docs](http://localhost:8000/docs), click
**Authorize** and enter your `API_KEY`, then try:

- `POST /api/v1/agents/text-to-sql` - `{"query": "How many patients have diabetes?"}`
- `POST /api/v1/agents/root-word-search` - `{"query": "diabetes cardiac"}`
- `POST /api/v1/agents/extract-root-words` - preview how a phrase is stemmed
- `POST /api/v1/agents/match-patients` - `{"trial_id": "NCT06230718"}`
- `POST /api/v1/agents/score-patients` - same, with ranking and exclusions
