from pyspark.sql import functions as F
from pyspark.sql import SparkSession
import uuid
import argparse


def get_param_or_widget(spark: SparkSession, key: str, default: str | None = None, cli_args: dict[str, str] | None = None) -> str:
    # Priority: CLI args > spark conf > widgets > default
    if cli_args and key in cli_args and cli_args[key]:
        return cli_args[key]
    val = spark.conf.get(f"job.param.{key}", None)
    if val is not None and val != "":
        return val
    try:
        from pyspark.dbutils import DBUtils  # type: ignore

        dbutils = DBUtils(spark)
        w = dbutils.widgets.get(key)
        if w:
            return w
    except Exception:
        pass
    if default is None:
        raise ValueError(f"Missing required parameter: {key}")
    return default


def list_folders() -> list[str]:
    return [
        "allergies",
        "careplans",
        "claims",
        "claims_transactions",
        "conditions",
        "devices",
        "encounters",
        "imaging_studies",
        "immunizations",
        "medications",
        "observations",
        "organizations",
        "patients",
        "payer_transitions",
        "payers",
        "procedures",
        "providers",
        "supplies",
    ]


def read_csv_with_metadata(spark: SparkSession, path: str, run_id: str):
    df = (
        spark.read.option("header", True)
        .option("inferSchema", True)
        .csv(path)
        .withColumn("ingest_timestamp", F.current_timestamp())
        .withColumn("source_file", F.input_file_name())
        .withColumn("ingest_run_id", F.lit(run_id))
    )
    return df


def write_bronze(df, full_table_name: str):
    (
        df.write.mode("append")
        .format("delta")
        .option("mergeSchema", "true")
        .saveAsTable(full_table_name)
    )


def main():
    spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog_name", type=str, required=False)
    parser.add_argument("--base_volume_path", type=str, required=False)
    args, _ = parser.parse_known_args()
    cli_args = {
        "catalog_name": args.catalog_name or "",
        "base_volume_path": args.base_volume_path or "",
    }

    catalog_name = get_param_or_widget(spark, "catalog_name", cli_args=cli_args)
    base_volume_path = get_param_or_widget(spark, "base_volume_path", cli_args=cli_args)

    run_id = str(uuid.uuid4())

    for folder in list_folders():
        landing_dir = f"{base_volume_path.rstrip('/')}/{folder}"
        table_name = f"{catalog_name}.synthea.{folder}_bronze"

        # Read all CSVs directly under the folder (exclude archive)
        csv_glob = landing_dir + "/*.csv"
        try:
            df = read_csv_with_metadata(spark, csv_glob, run_id)
        except Exception:
            # If no files present, skip quietly
            continue

        # Create database if needed
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog_name}.synthea")
        write_bronze(df, table_name)
        
        print(f"✓ Ingested data from {folder} into {table_name}")


if __name__ == "__main__":
    main()


