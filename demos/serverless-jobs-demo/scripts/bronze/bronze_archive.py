from pyspark.sql import SparkSession
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


def move_to_archive(spark: SparkSession, folder_path: str):
    try:
        from pyspark.dbutils import DBUtils  # type: ignore

        dbutils = DBUtils(spark)
    except Exception:
        raise RuntimeError("dbutils is required to move files to archive")

    files = dbutils.fs.ls(folder_path)
    archive_dir = folder_path.rstrip("/") + "/archive"
    try:
        dbutils.fs.mkdirs(archive_dir)
    except Exception:
        pass

    moved_count = 0
    for f in files:
        # Only move files (not directories) and skip archive itself
        if f.path.endswith("/archive/"):
            continue
        if f.path.endswith("/"):
            continue
        target = archive_dir + "/" + f.name
        dbutils.fs.mv(f.path, target, True)
        moved_count += 1
    
    return moved_count


def main():
    spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_volume_path", type=str, required=False)
    args, _ = parser.parse_known_args()
    cli_args = {
        "base_volume_path": args.base_volume_path or "",
    }

    base_volume_path = get_param_or_widget(spark, "base_volume_path", cli_args=cli_args)

    total_moved = 0
    for folder in list_folders():
        landing_dir = f"{base_volume_path.rstrip('/')}/{folder}"
        try:
            moved = move_to_archive(spark, landing_dir)
            if moved > 0:
                print(f"✓ Archived {moved} file(s) from {folder}")
                total_moved += moved
        except Exception as e:
            print(f"⚠ Warning: Could not archive files from {folder}: {e}")
            continue
    
    print(f"\nTotal files archived: {total_moved}")


if __name__ == "__main__":
    main()



