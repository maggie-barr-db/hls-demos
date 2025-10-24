from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import argparse
import sys
import os

# Add src directory to path to import utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.silver_control import get_last_processed_run_id, update_last_processed_run_id, get_new_run_ids


def load_fact_patient_encounters_incremental(spark: SparkSession, catalog_name: str, run_ids: list[str]):
    """Load fact_patient_encounters table incrementally."""
    
    run_ids_str = "', '".join(run_ids)
    
    df = spark.sql(f"""
        SELECT
            e.Id as encounter_id,
            e.PATIENT as patient_id,
            e.PROVIDER as provider_id,
            e.ORGANIZATION as organization_id,
            e.PAYER as payer_id,
            e.START as encounter_start_timestamp,
            e.STOP as encounter_stop_timestamp,
            DATE(e.START) as encounter_date_key,
            (unix_timestamp(e.STOP) - unix_timestamp(e.START)) / 60 as encounter_duration_minutes,
            e.ENCOUNTERCLASS as encounter_class,
            e.CODE as encounter_code,
            e.DESCRIPTION as encounter_description,
            e.REASONCODE as reason_code,
            e.REASONDESCRIPTION as reason_description,
            e.BASE_ENCOUNTER_COST as base_encounter_cost,
            e.TOTAL_CLAIM_COST as total_claim_cost,
            e.PAYER_COVERAGE as payer_coverage,
            e.TOTAL_CLAIM_COST - e.PAYER_COVERAGE as patient_responsibility,
            1 as encounter_count,
            p.GENDER as patient_gender,
            p.BIRTHDATE as patient_birthdate,
            p.RACE as patient_race,
            p.ETHNICITY as patient_ethnicity,
            p.STATE as patient_state,
            p.CITY as patient_city,
            p.ZIP as patient_zip,
            year(e.START) - year(p.BIRTHDATE) as patient_age_at_encounter,
            prov.NAME as provider_name,
            prov.SPECIALITY as provider_specialty,
            prov.GENDER as provider_gender,
            org.NAME as organization_name,
            org.CITY as organization_city,
            org.STATE as organization_state,
            c.CODE as primary_diagnosis_code,
            c.DESCRIPTION as primary_diagnosis_description,
            e.ingest_run_id,
            e.ingest_timestamp,
            current_timestamp() as silver_load_timestamp
        FROM {catalog_name}.synthea.encounters_bronze e
        LEFT JOIN {catalog_name}.synthea.patients_bronze p 
            ON e.PATIENT = p.Id
        LEFT JOIN {catalog_name}.synthea.providers_bronze prov 
            ON e.PROVIDER = prov.Id
        LEFT JOIN {catalog_name}.synthea.organizations_bronze org 
            ON e.ORGANIZATION = org.Id
        LEFT JOIN (
            SELECT ENCOUNTER, CODE, DESCRIPTION,
                   ROW_NUMBER() OVER (PARTITION BY ENCOUNTER ORDER BY START) as rn
            FROM {catalog_name}.synthea.conditions_bronze
        ) c ON e.Id = c.ENCOUNTER AND c.rn = 1
        WHERE e.ingest_run_id IN ('{run_ids_str}')
    """)
    
    return df


def main():
    spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog_name", type=str, required=True)
    args, _ = parser.parse_known_args()
    
    catalog_name = args.catalog_name
    table_name = "patient_encounters_silver"
    
    last_run_id = get_last_processed_run_id(spark, catalog_name, table_name)
    print(f"Last processed run ID: {last_run_id}")
    
    new_run_ids = get_new_run_ids(spark, catalog_name, "encounters_bronze", last_run_id)
    
    if not new_run_ids:
        print("No new data to process.")
        return
    
    print(f"Processing {len(new_run_ids)} new run(s): {new_run_ids}")
    
    df = load_fact_patient_encounters_incremental(spark, catalog_name, new_run_ids)
    
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog_name}.synthea")
    
    (df.write
        .mode("append")
        .format("delta")
        .option("mergeSchema", "true")
        .saveAsTable(f"{catalog_name}.synthea.{table_name}"))
    
    update_last_processed_run_id(spark, catalog_name, table_name, new_run_ids[-1])
    
    record_count = df.count()
    print(f"✓ Loaded {record_count} records into {table_name}")


if __name__ == "__main__":
    main()

