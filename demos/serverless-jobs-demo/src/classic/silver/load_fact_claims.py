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


def load_fact_claims_incremental(spark: SparkSession, catalog_name: str, run_ids: list[str]):
    """Load fact_claims table incrementally."""
    
    # Filter for new run IDs
    run_ids_str = "', '".join(run_ids)
    
    df = spark.sql(f"""
        SELECT
            ct.ID as claim_transaction_id,
            ct.CLAIMID as claim_id,
            ct.PATIENTID as patient_id,
            ct.PROVIDERID as provider_id,
            e.ORGANIZATION as organization_id,
            e.PAYER as payer_id,
            ct.FROMDATE as service_date,
            ct.TODATE as service_end_date,
            DATE(ct.FROMDATE) as service_date_key,
            ct.TYPE as transaction_type,
            ct.PROCEDURECODE as procedure_code,
            ct.AMOUNT as claim_amount,
            ct.UNITAMOUNT as unit_amount,
            ct.UNITS as units,
            ct.PAYMENTS as payment_amount,
            ct.ADJUSTMENTS as adjustment_amount,
            ct.TRANSFERS as transfer_amount,
            ct.OUTSTANDING as outstanding_amount,
            ct.PLACEOFSERVICE as place_of_service,
            c.DIAGNOSIS1 as primary_diagnosis_code,
            c.SERVICEDATE as claim_service_date,
            c.STATUS1 as claim_status,
            e.ENCOUNTERCLASS as encounter_class,
            e.BASE_ENCOUNTER_COST as base_encounter_cost,
            e.TOTAL_CLAIM_COST as total_claim_cost,
            e.PAYER_COVERAGE as payer_coverage,
            p.GENDER as patient_gender,
            p.BIRTHDATE as patient_birthdate,
            p.STATE as patient_state,
            p.ZIP as patient_zip,
            prov.SPECIALITY as provider_specialty,
            prov.NAME as provider_name,
            org.NAME as organization_name,
            org.CITY as organization_city,
            org.STATE as organization_state,
            ct.ingest_run_id,
            ct.ingest_timestamp,
            current_timestamp() as silver_load_timestamp
        FROM {catalog_name}.synthea.claims_transactions_bronze ct
        LEFT JOIN {catalog_name}.synthea.claims_bronze c 
            ON ct.CLAIMID = c.Id
        LEFT JOIN {catalog_name}.synthea.encounters_bronze e 
            ON c.APPOINTMENTID = e.Id
        LEFT JOIN {catalog_name}.synthea.patients_bronze p 
            ON ct.PATIENTID = p.Id
        LEFT JOIN {catalog_name}.synthea.providers_bronze prov 
            ON ct.PROVIDERID = prov.Id
        LEFT JOIN {catalog_name}.synthea.organizations_bronze org 
            ON e.ORGANIZATION = org.Id
        WHERE ct.ingest_run_id IN ('{run_ids_str}')
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
    table_name = "claims_silver"
    
    # Get run IDs to process based on load type
    if load_type == "full":
        print("Running FULL load - processing all data")
        run_ids = get_all_run_ids(spark, catalog_name, "claims_transactions_bronze")
    else:
        # Incremental load
        last_run_id = get_last_processed_run_id(spark, catalog_name, table_name)
        print(f"Running INCREMENTAL load - Last processed run ID: {last_run_id}")
        run_ids = get_new_run_ids(spark, catalog_name, "claims_transactions_bronze", last_run_id)
    
    if not run_ids:
        print("No data to process.")
        return
    
    print(f"Processing {len(run_ids)} run(s): {run_ids}")
    
    # Load and write data
    df = load_fact_claims_incremental(spark, catalog_name, run_ids)
    
    # Create schema if needed
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog_name}.synthea")
    
    # Write to silver table - use overwrite for full loads, append for incremental
    write_mode = "overwrite" if load_type == "full" else "append"
    (df.write
        .mode(write_mode)
        .format("delta")
        .option("mergeSchema", "true")
        .saveAsTable(f"{catalog_name}.synthea.{table_name}"))
    
    # Update control table with the latest run ID
    update_last_processed_run_id(spark, catalog_name, table_name, run_ids[-1])
    
    record_count = df.count()
    print(f"✓ Loaded {record_count} records into {table_name} (mode: {load_type})")


if __name__ == "__main__":
    main()

