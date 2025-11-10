from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType
import argparse
import sys
import os

# =============================================================================
# DEMONSTRATION: Custom Library Imports
# =============================================================================
# This script demonstrates importing custom libraries from two sources:
# 1. requirements.txt (tqdm) - via UC Volume in serverless environments
# 2. Custom wheel (Faker) - packaged library deployed to UC Volume
#
# On classic compute without these libraries, graceful fallbacks are provided

# Import tqdm from requirements.txt (for progress bars)
try:
    from tqdm import tqdm
    HAS_TQDM = True
    print("✓ Using tqdm from requirements.txt for progress tracking")
except ImportError:
    HAS_TQDM = False
    print("ℹ️  tqdm not available - using simple progress output")
    # Simple fallback context manager when tqdm is not available
    class tqdm:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def set_description(self, desc):
            print(f"  {desc}...")
        def update(self, n):
            pass

# Add src directory to path to import utils
# Use sys.argv[0] which is available both locally and in Databricks
script_path = sys.argv[0] if sys.argv and sys.argv[0] else __file__
script_dir = os.path.dirname(os.path.abspath(script_path))
# Navigate up from scripts/gold/ to src/
src_dir = os.path.dirname(os.path.dirname(script_dir))

if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from utils import get_last_processed_run_id, update_last_processed_run_id, get_new_run_ids, get_all_run_ids

# Import Faker from hls_external_libs wheel (for anonymized ID generation)
try:
    from faker import Faker
    HAS_FAKER = True
    print("✓ Using Faker from hls_external_libs wheel for data anonymization")
except ImportError:
    HAS_FAKER = False
    print("ℹ️  Faker not available - using simple hash-based anonymization")
    # Simple fallback for anonymization when Faker is not available
    import hashlib
    class Faker:
        @staticmethod
        def uuid4():
            # Generate a simple hash-based ID as fallback
            return hashlib.md5(str(id(object())).encode()).hexdigest()[:8]


def load_fact_member_monthly_snapshot_incremental(spark: SparkSession, catalog_name: str, run_ids: list[str]):
    """Load fact_member_monthly_snapshot table incrementally."""
    
    # Initialize Faker for generating anonymized identifiers
    fake = Faker()
    Faker.seed(42)  # Set seed for reproducibility
    
    # Create UDF to generate anonymized patient identifiers using Faker from external libs wheel
    def generate_anonymized_id(patient_id):
        """Generate a consistent anonymized ID for privacy."""
        if patient_id:
            # Use hash to ensure same patient_id always gets same fake UUID
            import hashlib
            hash_val = int(hashlib.md5(str(patient_id).encode()).hexdigest(), 16)
            fake.seed_instance(hash_val)
            return fake.uuid4()
        return None
    
    anonymize_id_udf = F.udf(generate_anonymized_id, StringType())
    
    run_ids_str = "', '".join(run_ids)
    
    # This is more complex as it aggregates data at monthly level
    # We'll rebuild the entire snapshot for affected months
    df = spark.sql(f"""
        WITH patient_months AS (
            SELECT DISTINCT
                e.PATIENT as patient_id,
                year(e.START) as year,
                month(e.START) as month,
                date_trunc('month', e.START) as month_start_date
            FROM {catalog_name}.synthea.encounters_bronze e
            WHERE e.ingest_run_id IN ('{run_ids_str}')
        ),
        encounter_metrics AS (
            SELECT
                e.PATIENT as patient_id,
                year(e.START) as year,
                month(e.START) as month,
                count(*) as total_encounters,
                sum(e.BASE_ENCOUNTER_COST) as total_medical_cost,
                sum(e.PAYER_COVERAGE) as total_payer_coverage,
                sum(CASE WHEN e.ENCOUNTERCLASS = 'emergency' THEN 1 ELSE 0 END) as er_visits,
                sum(CASE WHEN e.ENCOUNTERCLASS = 'inpatient' THEN 1 ELSE 0 END) as inpatient_admits,
                sum(CASE WHEN e.ENCOUNTERCLASS IN ('wellness', 'urgentcare') THEN 1 ELSE 0 END) as preventive_visits
            FROM {catalog_name}.synthea.encounters_bronze e
            GROUP BY e.PATIENT, year(e.START), month(e.START)
        ),
        medication_metrics AS (
            SELECT
                m.PATIENT as patient_id,
                year(m.START) as year,
                month(m.START) as month,
                count(*) as total_medications,
                sum(m.TOTALCOST) as total_pharmacy_cost,
                sum(m.PAYER_COVERAGE) as total_pharmacy_coverage
            FROM {catalog_name}.synthea.medications_bronze m
            GROUP BY m.PATIENT, year(m.START), month(m.START)
        ),
        condition_metrics AS (
            SELECT
                c.PATIENT as patient_id,
                year(c.START) as year,
                month(c.START) as month,
                count(DISTINCT c.CODE) as chronic_condition_count
            FROM {catalog_name}.synthea.conditions_bronze c
            WHERE c.STOP IS NULL OR c.STOP > current_date()
            GROUP BY c.PATIENT, year(c.START), month(c.START)
        )
        SELECT
            md5(concat(pm.patient_id, cast(pm.year as string), cast(pm.month as string))) as member_month_id,
            pm.patient_id,
            pm.month_start_date,
            pm.year,
            pm.month,
            DATE(pm.month_start_date) as month_date_key,
            p.GENDER as patient_gender,
            p.BIRTHDATE as patient_birthdate,
            pm.year - year(p.BIRTHDATE) as patient_age,
            p.RACE as patient_race,
            p.ETHNICITY as patient_ethnicity,
            p.STATE as patient_state,
            p.CITY as patient_city,
            p.ZIP as patient_zip,
            coalesce(em.total_encounters, 0) as total_encounters,
            coalesce(em.total_medical_cost, 0) as total_medical_cost,
            coalesce(em.total_payer_coverage, 0) as total_medical_coverage,
            coalesce(em.er_visits, 0) as er_visits,
            coalesce(em.inpatient_admits, 0) as inpatient_admits,
            coalesce(em.preventive_visits, 0) as preventive_visits,
            coalesce(mm.total_medications, 0) as total_medications,
            coalesce(mm.total_pharmacy_cost, 0) as total_pharmacy_cost,
            coalesce(mm.total_pharmacy_coverage, 0) as total_pharmacy_coverage,
            coalesce(cm.chronic_condition_count, 0) as chronic_condition_count,
            coalesce(em.total_medical_cost, 0) + coalesce(mm.total_pharmacy_cost, 0) as total_cost,
            1 as member_months,
            CASE
                WHEN coalesce(em.inpatient_admits, 0) > 0 OR coalesce(em.er_visits, 0) > 2 THEN 'High'
                WHEN coalesce(cm.chronic_condition_count, 0) >= 3 THEN 'Medium'
                ELSE 'Low'
            END as risk_tier,
            current_timestamp() as silver_load_timestamp
        FROM patient_months pm
        LEFT JOIN {catalog_name}.synthea.patients_bronze p ON pm.patient_id = p.Id
        LEFT JOIN encounter_metrics em ON pm.patient_id = em.patient_id AND pm.year = em.year AND pm.month = em.month
        LEFT JOIN medication_metrics mm ON pm.patient_id = mm.patient_id AND pm.year = mm.year AND pm.month = mm.month
        LEFT JOIN condition_metrics cm ON pm.patient_id = cm.patient_id AND pm.year = cm.year AND pm.month = cm.month
    """)
    
    # Add anonymized patient ID using Faker from external libraries wheel
    # This demonstrates using an external library bundled in the wheel
    df = df.withColumn(
        "anonymized_patient_id",
        anonymize_id_udf(F.col("patient_id"))
    )
    
    return df


def main():
    spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog_name", type=str, required=False)
    args, _ = parser.parse_known_args()
    
    # Read from environment variables first, then fall back to CLI args
    catalog_name = os.environ.get("catalog_name") or args.catalog_name
    if not catalog_name:
        raise ValueError("catalog_name is required (set as environment variable or pass as --catalog_name)")
    table_name = "member_monthly_snapshot_gold"
    
    last_run_id = get_last_processed_run_id(spark, catalog_name, table_name)
    print(f"Last processed run ID: {last_run_id}")
    
    new_run_ids = get_new_run_ids(spark, catalog_name, "encounters_bronze", last_run_id)
    
    if not new_run_ids:
        print("No new data to process.")
        return
    
    print(f"Processing {len(new_run_ids)} new run(s): {new_run_ids}")
    
    # =============================================================================
    # DEMONSTRATION: Custom Library Usage in Action
    # =============================================================================
    # This section demonstrates:
    # - tqdm (from requirements.txt) for progress tracking
    # - Faker (from hls_external_libs wheel) for data anonymization
    
    print("\n" + "="*70)
    print("GOLD LAYER: Member Monthly Snapshot")
    print("="*70)
    print(f"Custom Libraries Status:")
    print(f"  - tqdm (requirements.txt):  {'✓ Available' if HAS_TQDM else '✗ Using fallback'}")
    print(f"  - Faker (wheel package):     {'✓ Available' if HAS_FAKER else '✗ Using fallback'}")
    print("="*70 + "\n")
    
    with tqdm(total=4, desc="Processing", unit="step") as pbar:
        pbar.set_description("Querying bronze tables")
        df = load_fact_member_monthly_snapshot_incremental(spark, catalog_name, new_run_ids)
        pbar.update(1)
        
        pbar.set_description("Creating schema")
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog_name}.synthea")
        pbar.update(1)
        
        pbar.set_description("Writing to Delta table")
        # For monthly snapshot, we'll use append mode
        # In production, you might want to use MERGE to handle updates
        (df.write
            .mode("append")
            .format("delta")
            .option("mergeSchema", "true")
            .saveAsTable(f"{catalog_name}.synthea.{table_name}"))
        pbar.update(1)
        
        pbar.set_description("Updating control table")
        update_last_processed_run_id(spark, catalog_name, table_name, new_run_ids[-1])
        pbar.update(1)
    
    record_count = df.count()
    print(f"✓ Loaded {record_count} records into {table_name}")
    
    # Demonstrate Faker from external libraries wheel
    if record_count > 0:
        sample_rows = df.select("patient_id", "anonymized_patient_id").limit(3).collect()
        print(f"  Sample anonymized IDs (using Faker from hls_external_libs wheel):")
        for row in sample_rows:
            print(f"    Original: {row['patient_id']} → Anonymized: {row['anonymized_patient_id']}")


if __name__ == "__main__":
    main()

