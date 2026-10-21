"""Seed initial demo clinical trials and synthetic patient cohort.

Runs automatically if the database has 0 patients or 0 clinical trials.
Idempotent and safe to run on startup.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import secrets
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import bcrypt
from sqlalchemy import func, select, text

from src.core.config import settings
from src.db.models.clinical_trial import ClinicalTrial
from src.db.models.patient import Patient
from src.db.models.user import User
from src.db.session import AsyncSessionLocal, engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("seed_demo_data")

DEMO_CONDITIONS_POOL = [
    {"name": "Diabetes Mellitus, Type 2", "icd10": "E11"},
    {"name": "Hypertension", "icd10": "I10"},
    {"name": "Myocardial Infarction", "icd10": "I21"},
    {"name": "Asthma", "icd10": "J45"},
    {"name": "Stroke", "icd10": "I63"},
    {"name": "Chronic Kidney Disease", "icd10": "N18"},
    {"name": "Arthritis", "icd10": "M19"},
    {"name": "COPD", "icd10": "J44"},
    {"name": "Skin Cancer", "icd10": "C44"},
    {"name": "Major Depressive Disorder", "icd10": "F32"},
    {"name": "Obesity", "icd10": "E66"},
    {"name": "Angina Pectoris", "icd10": "I20"},
]

US_STATES = [
    "California", "Texas", "Florida", "New York", "Pennsylvania",
    "Illinois", "Ohio", "Georgia", "North Carolina", "Michigan",
]

ETHNICITIES = ["White", "Black", "Hispanic", "Asian", "Other"]
SMOKER_STATUSES = ["Never smoked", "Former smoker", "Current smoker"]
HEALTH_STATUSES = ["excellent", "very good", "good", "fair"]


def _hash_demo_password() -> str:
    secret = secrets.token_bytes(16)
    return bcrypt.hashpw(secret, bcrypt.gensalt(rounds=4)).decode("utf-8")


async def seed_trials_if_needed(session) -> int:
    trial_count = await session.scalar(select(func.count()).select_from(ClinicalTrial))
    if trial_count > 0:
        logger.info("Database already has %s clinical trials; skipping trial seed.", trial_count)
        return trial_count

    logger.info("Database has 0 clinical trials. Seeding trials...")
    valid_ids_file = Path(__file__).resolve().parent.parent / "data" / "valid_trial_ids.json"
    trials_to_seed = []
    if valid_ids_file.exists():
        try:
            with open(valid_ids_file, "r", encoding="utf-8") as f:
                raw_trials = json.load(f)
                trials_to_seed = raw_trials[:100]  # seed top 100 trials
        except Exception as e:
            logger.warning("Failed to load valid_trial_ids.json: %s", e)

    count = 0
    now = datetime.now(timezone.utc)
    for t in trials_to_seed:
        nct_id = t.get("nct_id")
        if not nct_id:
            continue
        title = t.get("title", "Clinical Trial")
        status = t.get("status", "RECRUITING")
        conditions = t.get("conditions", [])

        payload = {
            "nct_id": nct_id,
            "title": title,
            "status": status,
            "conditions": conditions,
            "keywords": conditions,
            "eligibility": {
                "sex": "ALL",
                "healthyVolunteers": False,
                "eligibilityCriteria": f"Inclusion Criteria:\n- Diagnosis of {', '.join(conditions)}\n- Age 18 and older\n\nExclusion Criteria:\n- Severe end-stage complications",
            },
            "source": "ClinicalTrials.gov",
            "region": "US",
            "scraped_at": now.isoformat(),
        }

        trial_obj = ClinicalTrial(
            registry="US",
            nct_id=nct_id,
            title=title,
            sponsor="Clinical Research Network",
            status=status,
            source="ClinicalTrials.gov",
            source_url=f"https://clinicaltrials.gov/study/{nct_id}",
            scraped_at=now,
            payload=payload,
        )
        session.add(trial_obj)
        count += 1

    await session.commit()
    logger.info("Successfully seeded %s clinical trials.", count)
    return count


async def seed_patients_if_needed(session) -> int:
    patient_count = await session.scalar(select(func.count()).select_from(Patient))
    if patient_count > 0:
        logger.info("Database already has %s patients; skipping patient seed.", patient_count)
        return patient_count

    logger.info("Database has 0 patients. Seeding 150 synthetic patients...")
    pw_hash = _hash_demo_password()
    random.seed(42)

    count = 0
    for i in range(1, 151):
        uid = uuid4()
        gender = "male" if i % 2 == 0 else "female"
        age = random.randint(22, 82)
        state = random.choice(US_STATES)
        ethnicity = random.choice(ETHNICITIES)
        smoker = random.choices(SMOKER_STATUSES, weights=[0.55, 0.30, 0.15])[0]
        health = random.choice(HEALTH_STATUSES)

        # Assign 1 to 3 conditions
        num_conds = random.choices([1, 2, 3], weights=[0.4, 0.4, 0.2])[0]
        chosen_cond_objs = random.sample(DEMO_CONDITIONS_POOL, k=num_conds)
        cond_names = [c["name"] for c in chosen_cond_objs]
        icd_codes = [c["icd10"] for c in chosen_cond_objs]

        height_cm = random.randint(155, 190)
        weight_kg = random.randint(55, 110)
        bmi = round(weight_kg / ((height_cm / 100) ** 2), 1)

        age_cat = f"{age//5 * 5}-{age//5 * 5 + 4}" if age < 80 else "80+"

        p = Patient(
            id=uid,
            email=f"patient_{i:04d}@trialbridge.demo",
            password_hash=pw_hash,
            name=f"Patient {i:04d}",
            user_type="patient",
            display_patient_id=f"PT-{i:04d}",
            gender=gender,
            age=age,
            age_category=age_cat,
            ethnicity=ethnicity,
            anthropometrics={"height": {"number": height_cm, "unit": "cm"}, "weight": {"number": weight_kg, "unit": "kg"}},
            geography={"country": "United States", "state": state, "city": "Springfield"},
            conditions=cond_names,
            icd10_codes=icd_codes,
            clinical_trial_consent={"consented": True, "consent_date": "2026-01-01"},
            trial_preferences={"max_travel_distance_km": 100},
            patient_metadata={
                "bmi": bmi,
                "smokerStatus": smoker,
                "generalHealth": health,
                "covidPos": random.choice(["Yes", "No"]),
            },
        )
        session.add(p)
        count += 1

    await session.commit()
    logger.info("Successfully seeded %s synthetic patients.", count)
    return count


async def main():
    async with AsyncSessionLocal() as session:
        await seed_trials_if_needed(session)
        await seed_patients_if_needed(session)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
