from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import argparse
import sys
import os

# Add src directory to path to import utils
# Use sys.argv[0] which is available both locally and in Databricks
script_path = sys.argv[0] if sys.argv and sys.argv[0] else __file__
script_dir = os.path.dirname(os.path.abspath(script_path))
# Navigate up from scripts/silver/ to src/
src_dir = os.path.dirname(os.path.dirname(script_dir))

if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from utils import get_last_processed_run_id, update_last_processed_run_id, get_new_run_ids, get_all_run_ids


def load_fact_medications_incremental(spark: SparkSession, catalog_name: str, run_ids: list[str]):
    """Load fact_medications table incrementally."""
    
    run_ids_str = "', '".join(run_ids)
    
    df = spark.sql(f"""
        SELECT
            md5(concat(m.PATIENT, m.ENCOUNTER, cast(m.CODE as string), cast(m.START as string))) as medication_id,
            m.PATIENT as patient_id,
            m.ENCOUNTER as encounter_id,
            m.PAYER as payer_id,
            m.START as prescription_start_date,
            m.STOP as prescription_stop_date,
            DATE(m.START) as prescription_date_key,
            datediff(m.STOP, m.START) as days_supply,
            m.CODE as medication_code,
            m.DESCRIPTION as medication_description,
            m.DISPENSES as dispenses,
            m.BASE_COST as base_cost,
            m.PAYER_COVERAGE as payer_coverage,
            m.BASE_COST - m.PAYER_COVERAGE as patient_copay,
            m.TOTALCOST as total_cost,
            m.REASONCODE as reason_code,
            m.REASONDESCRIPTION as reason_description,
            p.GENDER as patient_gender,
            p.BIRTHDATE as patient_birthdate,
            year(m.START) - year(p.BIRTHDATE) as patient_age_at_prescription,
            p.STATE as patient_state,
            p.ZIP as patient_zip,
            e.ENCOUNTERCLASS as encounter_class,
            e.PROVIDER as provider_id,
            e.ORGANIZATION as organization_id,
            prov.SPECIALITY as provider_specialty,
            prov.NAME as provider_name,
            m.ingest_run_id,
            m.ingest_timestamp,
            current_timestamp() as silver_load_timestamp
        FROM {catalog_name}.synthea.medications_bronze m
        LEFT JOIN {catalog_name}.synthea.patients_bronze p 
            ON m.PATIENT = p.Id
        LEFT JOIN {catalog_name}.synthea.encounters_bronze e 
            ON m.ENCOUNTER = e.Id
        LEFT JOIN {catalog_name}.synthea.providers_bronze prov 
            ON e.PROVIDER = prov.Id
        WHERE m.ingest_run_id IN ('{run_ids_str}')
    """)
    
    return df


def main():
    spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog_name", type=str, required=False)
    parser.add_argument("--load_type", type=str, default="full", choices=["full", "incremental"])
    args, _ = parser.parse_known_args()
    
    # Read from environment variables first, then fall back to CLI args
    catalog_name = os.environ.get("catalog_name") or args.catalog_name
    if not catalog_name:
        raise ValueError("catalog_name is required (set as environment variable or pass as --catalog_name)")
    load_type = args.load_type
    table_name = "medications_silver"
    
    # Get run IDs to process based on load type
    if load_type == "full":
        print("Running FULL load - processing all data")
        run_ids = get_all_run_ids(spark, catalog_name, "medications_bronze")
    else:
        # Incremental load
        last_run_id = get_last_processed_run_id(spark, catalog_name, table_name)
        print(f"Running INCREMENTAL load - Last processed run ID: {last_run_id}")
        run_ids = get_new_run_ids(spark, catalog_name, "medications_bronze", last_run_id)
    
    if not run_ids:
        print("No data to process.")
        return
    
    print(f"Processing {len(run_ids)} run(s): {run_ids}")
    
    df = load_fact_medications_incremental(spark, catalog_name, run_ids)
    
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog_name}.synthea")
    
    # Write to silver table - use overwrite for full loads, append for incremental
    write_mode = "overwrite" if load_type == "full" else "append"
    (df.write
        .mode(write_mode)
        .format("delta")
        .option("mergeSchema", "true")
        .saveAsTable(f"{catalog_name}.synthea.{table_name}"))
    
    update_last_processed_run_id(spark, catalog_name, table_name, run_ids[-1])
    
    record_count = df.count()
    print(f"✓ Loaded {record_count} records into {table_name} (mode: {load_type})")


if __name__ == "__main__":
    main()

