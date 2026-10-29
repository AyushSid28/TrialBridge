"""Create FHIR tables (fhir_patients, fhir_conditions, fhir_observations)
and seed 117 FHIR-compliant patient records with conditions and vitals.
"""

import asyncio
import logging
import random
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import text
from src.db.session import AsyncSessionLocal, engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("seed_fhir")

FHIR_CONDITIONS_CATALOG = [
    {"name": "Diabetes Mellitus, Type 2", "snomed": "44054006", "icd10": "E11"},
    {"name": "Hypertension", "snomed": "38341003", "icd10": "I10"},
    {"name": "Myocardial Infarction", "snomed": "22298006", "icd10": "I21"},
    {"name": "Asthma", "snomed": "195967001", "icd10": "J45"},
    {"name": "Stroke", "snomed": "230690007", "icd10": "I63"},
    {"name": "Chronic Kidney Disease", "snomed": "709044004", "icd10": "N18"},
    {"name": "Arthritis", "snomed": "3723001", "icd10": "M19"},
    {"name": "COPD", "snomed": "13645005", "icd10": "J44"},
    {"name": "Skin Cancer", "snomed": "372244006", "icd10": "C44"},
    {"name": "Major Depressive Disorder", "snomed": "370143000", "icd10": "F32"},
    {"name": "Obesity", "snomed": "414915002", "icd10": "E66"},
    {"name": "Angina Pectoris", "snomed": "194828000", "icd10": "I20"},
]

US_STATES = [
    "California", "Texas", "Florida", "New York", "Pennsylvania",
    "Illinois", "Ohio", "Georgia", "North Carolina", "Michigan",
]

ETHNICITIES = ["White", "Black", "Hispanic", "Asian", "Other"]
SMOKER_OPTIONS = ["Never smoked", "Former smoker", "Current smoker"]

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS fhir_patients (
    id UUID PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    birth_date DATE NOT NULL,
    gender VARCHAR(50) NOT NULL,
    ethnicity VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100) DEFAULT 'United States',
    deceased BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fhir_conditions (
    id UUID PRIMARY KEY,
    patient_id UUID NOT NULL REFERENCES fhir_patients(id) ON DELETE CASCADE,
    display_name VARCHAR(255) NOT NULL,
    snomed_code VARCHAR(50),
    icd10_code VARCHAR(50),
    category VARCHAR(50) DEFAULT 'encounter-diagnosis',
    clinical_status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fhir_conditions_patient ON fhir_conditions(patient_id);
CREATE INDEX IF NOT EXISTS idx_fhir_conditions_display ON fhir_conditions(display_name);

CREATE TABLE IF NOT EXISTS fhir_observations (
    id UUID PRIMARY KEY,
    patient_id UUID NOT NULL REFERENCES fhir_patients(id) ON DELETE CASCADE,
    display_name VARCHAR(255) NOT NULL,
    loinc_code VARCHAR(50) NOT NULL,
    value_numeric DOUBLE PRECISION,
    value_text VARCHAR(255),
    value_unit VARCHAR(50),
    bp_systolic DOUBLE PRECISION,
    bp_diastolic DOUBLE PRECISION,
    effective_date TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fhir_obs_patient ON fhir_observations(patient_id);
CREATE INDEX IF NOT EXISTS idx_fhir_obs_loinc ON fhir_observations(loinc_code);
"""


async def seed_fhir_patients():
    async with AsyncSessionLocal() as session:
        logger.info("Ensuring FHIR tables exist...")
        statements = [stmt.strip() for stmt in CREATE_TABLES_SQL.split(";") if stmt.strip()]
        for stmt in statements:
            await session.execute(text(stmt))
        await session.commit()

        # Check existing count
        existing = await session.scalar(text("SELECT COUNT(*) FROM fhir_patients"))
        if existing and existing >= 117:
            logger.info("FHIR database already has %s patients; skipping seed.", existing)
            return existing

        # Reset or insert up to 117 patients
        await session.execute(text("DELETE FROM fhir_patients"))
        await session.commit()

        logger.info("Seeding exactly 117 FHIR patients...")
        random.seed(117)
        now = datetime.now(timezone.utc)
        today = date.today()

        for i in range(1, 118):
            pid = uuid4()
            gender = "male" if i % 2 == 0 else "female"
            age = random.randint(24, 79)
            birth_year = today.year - age
            birth_date = date(birth_year, random.randint(1, 12), random.randint(1, 28))
            state = random.choice(US_STATES)
            ethnicity = random.choice(ETHNICITIES)
            full_name = f"FHIR-PT-{i:03d}"

            # Insert patient
            await session.execute(
                text("""
                    INSERT INTO fhir_patients (id, full_name, birth_date, gender, ethnicity, state, country, deceased)
                    VALUES (:id, :full_name, :birth_date, :gender, :ethnicity, :state, 'United States', FALSE)
                """),
                {
                    "id": pid,
                    "full_name": full_name,
                    "birth_date": birth_date,
                    "gender": gender,
                    "ethnicity": ethnicity,
                    "state": state,
                },
            )

            # Assign 1 to 3 conditions
            num_conds = random.choices([1, 2, 3], weights=[0.4, 0.4, 0.2])[0]
            chosen_conds = random.sample(FHIR_CONDITIONS_CATALOG, k=num_conds)

            for c in chosen_conds:
                cid = uuid4()
                await session.execute(
                    text("""
                        INSERT INTO fhir_conditions (id, patient_id, display_name, snomed_code, icd10_code, category, clinical_status)
                        VALUES (:id, :patient_id, :display_name, :snomed_code, :icd10_code, 'encounter-diagnosis', 'active')
                    """),
                    {
                        "id": cid,
                        "patient_id": pid,
                        "display_name": c["name"],
                        "snomed_code": c["snomed"],
                        "icd10_code": c["icd10"],
                    },
                )

            # Observations: BMI (LOINC 39156-5)
            height_m = random.randint(155, 188) / 100.0
            weight_kg = random.randint(52, 105)
            bmi_val = round(weight_kg / (height_m ** 2), 1)

            await session.execute(
                text("""
                    INSERT INTO fhir_observations (id, patient_id, display_name, loinc_code, value_numeric, value_unit, effective_date)
                    VALUES (:id, :patient_id, 'Body mass index (BMI) [Ratio]', '39156-5', :val, 'kg/m2', :effective_date)
                """),
                {
                    "id": uuid4(),
                    "patient_id": pid,
                    "val": bmi_val,
                    "effective_date": now - timedelta(days=random.randint(5, 90)),
                },
            )

            # Observations: Smoking Status (LOINC 72166-2)
            smoker_val = random.choices(SMOKER_OPTIONS, weights=[0.55, 0.30, 0.15])[0]
            await session.execute(
                text("""
                    INSERT INTO fhir_observations (id, patient_id, display_name, loinc_code, value_text, effective_date)
                    VALUES (:id, :patient_id, 'Tobacco smoking status', '72166-2', :val, :effective_date)
                """),
                {
                    "id": uuid4(),
                    "patient_id": pid,
                    "val": smoker_val,
                    "effective_date": now - timedelta(days=random.randint(5, 90)),
                },
            )

            # Observations: Blood Pressure (LOINC 85354-9)
            systolic = random.randint(110, 160)
            diastolic = random.randint(70, 95)
            await session.execute(
                text("""
                    INSERT INTO fhir_observations (id, patient_id, display_name, loinc_code, bp_systolic, bp_diastolic, effective_date)
                    VALUES (:id, :patient_id, 'Blood pressure panel', '85354-9', :sys, :dia, :effective_date)
                """),
                {
                    "id": uuid4(),
                    "patient_id": pid,
                    "sys": systolic,
                    "dia": diastolic,
                    "effective_date": now - timedelta(days=random.randint(5, 90)),
                },
            )

        await session.commit()
        logger.info("Successfully populated 117 FHIR patients with conditions & observations.")
        return 117


async def main():
    await seed_fhir_patients()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
