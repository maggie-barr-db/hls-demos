from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def get_last_processed_run_id(spark: SparkSession, catalog_name: str, table_name: str) -> str | None:
    """Get the last processed run ID for a silver table."""
    control_table = f"{catalog_name}.synthea.silver_load_control"
    
    # Create control table if it doesn't exist
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {control_table} (
            silver_table_name STRING,
            last_processed_run_id STRING,
            last_processed_timestamp TIMESTAMP
        ) USING DELTA
    """)
    
    result = spark.sql(f"""
        SELECT last_processed_run_id 
        FROM {control_table}
        WHERE silver_table_name = '{table_name}'
    """).collect()
    
    return result[0].last_processed_run_id if result else None


def update_last_processed_run_id(spark: SparkSession, catalog_name: str, table_name: str, run_id: str):
    """Update the last processed run ID for a silver table."""
    control_table = f"{catalog_name}.synthea.silver_load_control"
    
    spark.sql(f"""
        MERGE INTO {control_table} target
        USING (SELECT '{table_name}' as silver_table_name, 
                      '{run_id}' as last_processed_run_id,
                      current_timestamp() as last_processed_timestamp) source
        ON target.silver_table_name = source.silver_table_name
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
    """)


def get_new_run_ids(spark: SparkSession, catalog_name: str, bronze_table: str, last_processed_run_id: str | None) -> list[str]:
    """Get list of new run IDs to process from a bronze table."""
    if last_processed_run_id:
        df = spark.sql(f"""
            SELECT DISTINCT ingest_run_id
            FROM {catalog_name}.synthea.{bronze_table}
            WHERE ingest_timestamp > (
                SELECT MAX(ingest_timestamp)
                FROM {catalog_name}.synthea.{bronze_table}
                WHERE ingest_run_id = '{last_processed_run_id}'
            )
            ORDER BY ingest_run_id
        """)
    else:
        # First run - get all run IDs
        df = spark.sql(f"""
            SELECT DISTINCT ingest_run_id
            FROM {catalog_name}.synthea.{bronze_table}
            ORDER BY ingest_run_id
        """)
    
    return [row.ingest_run_id for row in df.collect()]

