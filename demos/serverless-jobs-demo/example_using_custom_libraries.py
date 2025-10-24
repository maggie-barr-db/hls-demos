"""
Example script demonstrating the use of custom libraries from requirements.txt
This showcases various data processing libraries available in the custom environment.
"""

from pyspark.sql import SparkSession
import polars as pl
import duckdb
import pandas as pd
from great_expectations.dataset import SparkDFDataset

def example_polars_operations():
    """Demonstrate Polars for fast DataFrame operations"""
    print("\n=== Polars Example ===")
    
    # Create a Polars DataFrame
    df = pl.DataFrame({
        "patient_id": [1, 2, 3, 4, 5],
        "age": [45, 32, 67, 54, 29],
        "diagnosis": ["diabetes", "hypertension", "cancer", "diabetes", "hypertension"],
        "total_cost": [5000, 3000, 15000, 4500, 2800]
    })
    
    # Perform aggregations
    summary = df.group_by("diagnosis").agg([
        pl.count().alias("patient_count"),
        pl.mean("age").alias("avg_age"),
        pl.sum("total_cost").alias("total_cost")
    ])
    
    print("Diagnosis Summary:")
    print(summary)
    
    return df

def example_duckdb_sql():
    """Demonstrate DuckDB for in-memory SQL analytics"""
    print("\n=== DuckDB Example ===")
    
    # Create a connection
    conn = duckdb.connect()
    
    # Create a sample table
    conn.execute("""
        CREATE TABLE patients AS 
        SELECT * FROM (
            VALUES 
                (1, 'John Doe', 45, 'diabetes'),
                (2, 'Jane Smith', 32, 'hypertension'),
                (3, 'Bob Johnson', 67, 'cancer'),
                (4, 'Alice Williams', 54, 'diabetes')
        ) AS t(patient_id, name, age, diagnosis)
    """)
    
    # Run a query
    result = conn.execute("""
        SELECT diagnosis, 
               COUNT(*) as patient_count,
               AVG(age) as avg_age
        FROM patients
        GROUP BY diagnosis
        ORDER BY patient_count DESC
    """).fetchdf()
    
    print("DuckDB Query Result:")
    print(result)
    
    return result

def example_spark_with_polars():
    """Demonstrate Spark and Polars interoperability"""
    print("\n=== Spark + Polars Integration ===")
    
    spark = SparkSession.builder.getOrCreate()
    
    # Create Spark DataFrame
    spark_df = spark.createDataFrame([
        (1, "diabetes", 5000),
        (2, "hypertension", 3000),
        (3, "cancer", 15000),
    ], ["patient_id", "diagnosis", "cost"])
    
    print("Original Spark DataFrame:")
    spark_df.show()
    
    # Convert to Polars for fast operations
    pandas_df = spark_df.toPandas()
    polars_df = pl.from_pandas(pandas_df)
    
    # Perform Polars operations
    filtered = polars_df.filter(pl.col("cost") > 4000)
    
    print("\nFiltered in Polars (cost > 4000):")
    print(filtered)
    
    # Convert back to Spark
    result_spark = spark.createDataFrame(filtered.to_pandas())
    
    return result_spark

def example_great_expectations():
    """Demonstrate data quality validation with Great Expectations"""
    print("\n=== Great Expectations Validation ===")
    
    spark = SparkSession.builder.getOrCreate()
    
    # Create sample data
    spark_df = spark.createDataFrame([
        (1, 45, "diabetes", 5000),
        (2, 32, "hypertension", 3000),
        (3, None, "cancer", 15000),  # Missing age
        (4, 150, "diabetes", -500),  # Invalid age and negative cost
    ], ["patient_id", "age", "diagnosis", "cost"])
    
    # Wrap with Great Expectations
    ge_df = SparkDFDataset(spark_df)
    
    # Run expectations
    print("\nValidation Results:")
    
    # Age should be between 0 and 120
    age_result = ge_df.expect_column_values_to_be_between("age", 0, 120)
    print(f"Age validation: {age_result['success']}")
    
    # Cost should be positive
    cost_result = ge_df.expect_column_values_to_be_between("cost", 0, None)
    print(f"Cost validation: {cost_result['success']}")
    
    # Patient ID should be unique
    unique_result = ge_df.expect_column_values_to_be_unique("patient_id")
    print(f"Patient ID uniqueness: {unique_result['success']}")
    
    return ge_df

def example_healthcare_libraries():
    """Demonstrate healthcare-specific libraries"""
    print("\n=== Healthcare Libraries Example ===")
    
    # HL7 example (commented out as it requires actual HL7 messages)
    print("HL7apy available for parsing HL7 messages")
    print("FHIR.resources available for FHIR resource models")
    
    # Example of what you could do:
    print("""
    Example usage:
    
    # Parse HL7 message
    from hl7apy.parser import parse_message
    msg = parse_message(hl7_string)
    
    # Work with FHIR resources
    from fhir.resources.patient import Patient
    patient = Patient(id="example", ...)
    """)

def main():
    """Run all examples"""
    print("=" * 60)
    print("Custom Libraries Demo")
    print("Demonstrating libraries from requirements.txt")
    print("=" * 60)
    
    # Run examples
    example_polars_operations()
    example_duckdb_sql()
    example_spark_with_polars()
    example_great_expectations()
    example_healthcare_libraries()
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()

