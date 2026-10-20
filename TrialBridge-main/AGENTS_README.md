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

| Agent | Where in Streamlit | What it is for |
|---|---|---|
| **Text-to-SQL** | Text-to-SQL | Ask in English, get SQL and results. First filter when matching a trial. |
| **Root word search** | Root Word Search | Find patients by condition even if wording differs. Second check after SQL. |
| **Orchestrator** | Orchestrator | Match patients to a trial (NCT ID) or to typed criteria. |
| **Scoring** | Scoring Agent | Rank matched patients 0–100 and show why they were included or excluded. |

Typical flow: pick a trial → orchestrator (SQL, then root word search) → scoring.

## Trying each agent

### Text-to-SQL

- Open the **Text-to-SQL** tab
- Example: `How many patients have diabetes?`
- Click **Run Query**

### Root word search

- Open the **Root Word Search** tab
- Example: `diabetes cardiac`
- Click **Search Patients**

### Orchestrator

- Open the **Orchestrator** tab
- Enter a trial ID such as `NCT06230718`
- Click **Match Patients**

### Scoring

- Open the **Scoring Agent** tab
- Try `NCT06230718` (stroke) or `NCT07003997` (depression)
- Click **Run Scoring**
- Check the score distribution, radar chart, ranked table, and exclusion details
