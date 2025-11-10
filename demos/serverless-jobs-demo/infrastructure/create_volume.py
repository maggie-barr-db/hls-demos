#!/usr/bin/env python3
"""
Create the functional_testing volume
"""
from pyspark.sql import SparkSession

# Get or create Spark session
spark = SparkSession.builder.getOrCreate()

# Create the volume
volume_sql = """
CREATE VOLUME IF NOT EXISTS maggiedatabricksterraform_dbw.synthea.functional_testing
COMMENT 'Stores test files created during functional testing job'
"""

print("Creating functional_testing volume...")
try:
    spark.sql(volume_sql)
    print("✓ Volume created successfully: maggiedatabricksterraform_dbw.synthea.functional_testing")
except Exception as e:
    print(f"Note: {e}")
    print("Volume may already exist")

# Verify volumes
print("\nVerifying volumes in maggiedatabricksterraform_dbw.synthea:")
spark.sql("SHOW VOLUMES IN maggiedatabricksterraform_dbw.synthea").show(truncate=False)

