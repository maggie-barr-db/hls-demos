# Serverless Jobs Demo: Healthcare Data Pipelines

This demo showcases building bronze and silver data pipelines for healthcare/life sciences data using Databricks batch jobs with both classic and serverless compute.

## Table of Contents

1. [Overview](#overview)
2. [Quick Decision Guide](#quick-decision-guide)
3. [Prerequisites](#prerequisites)
4. [Batch Jobs Architecture](#batch-jobs-architecture)
5. [Silver Fact Tables Reference](#silver-fact-tables-reference)
6. [Next Steps](#next-steps)

---

## Overview

This demo creates **18 bronze tables** and **5 silver/gold tables** for healthcare insurance analytics from synthetic healthcare data (Synthea format).

### What You'll Build

**Bronze Layer (18 tables)**
- Raw ingestion from CSV files in UC Volumes
- Metadata tracking (ingest timestamp, source file, run ID)
- Schema inference and evolution

**Silver Layer (4 tables) + Gold Layer (1 table)**
- `claims_silver` - Claims transactions for financial analysis
- `patient_encounters_silver` - Healthcare utilization metrics
- `medications_silver` - Pharmacy benefit management
- `procedures_silver` - Procedure cost and utilization
- `member_monthly_snapshot_gold` - Member risk and PMPM metrics (gold layer)

### Compute Options

This demo supports two compute types:

1. **Classic Compute** - Traditional Databricks clusters
   - Full control over cluster configuration
   - Better for development and debugging
   - Explicit cluster configuration

2. **Serverless Compute** - Databricks serverless execution
   - Instant startup, auto-scaling
   - Pay only for what you use
   - Simplified configuration with environments
   - Performance optimized by default

**Both compute options use the same Python scripts** located in `scripts/` directory.

**Jobs available:**
- Bronze ingestion (classic & serverless)
- Silver/Gold loading (classic & serverless)

---

## Quick Decision Guide

### Choose Classic Compute if you:
- ✅ Need full control over cluster configuration
- ✅ Want to use spot instances for cost savings
- ✅ Require specific Spark configurations
- ✅ Prefer familiar cluster management
- ✅ Need to debug with granular control
- ✅ Want predictable resource allocation

### Choose Serverless Compute if you:
- ✅ Want instant startup times (no cluster provisioning)
- ✅ Prefer simplified configuration (no cluster sizing)
- ✅ Want automatic scaling based on workload
- ✅ Pay only for actual compute time used
- ✅ Need faster iteration during development
- ✅ Want simplified operations and maintenance

**Note:** Serverless is generally recommended for most use cases. Classic provides more control when needed.

---

## Prerequisites

### Required
- ✅ **Databricks workspace** with Unity Catalog enabled
- ✅ **Databricks CLI** installed and authenticated
  ```bash
  brew install databricks/tap/databricks
  databricks auth login --host https://<your-workspace-url>
  ```
- ✅ **Synthetic healthcare data** in UC Volumes
  - Use [synthea-on-dbx](https://github.com/matthew-gigl-db/synthea-on-dbx) to generate data
  - Data should be in `/Volumes/<catalog>/<schema>/synthea/landing/` structure

### Configuration

Create `variables.json` in this directory:

   ```bash
   cp variables.example.json variables.json
```

Edit with your values:
```json
{
  "catalog_name": "maggiedatabricksterraform_dbw",
  "base_volume_path": "/Volumes/maggiedatabricksterraform_dbw/synthea/synthea/landing"
}
```

---

## Batch Jobs Architecture

Traditional Databricks Jobs with PySpark for explicit control over the pipeline.

### Architecture

```
CSV Files → Bronze Ingest Job → Bronze Tables → Archive Job
                                      ↓
                                Silver Load Jobs → Silver Fact Tables
```

**Two jobs created:**
1. `daily_bronze_ingestion_incr` - Ingests CSVs and archives files (2 tasks)
2. `daily_silver_load_incr` - Transforms bronze to silver/gold (5 tasks)

### How It Works

#### Bronze Job (2 tasks)

**Task 1: Bronze Ingest**
- Reads CSV files from each landing subfolder
- Generates unique `ingest_run_id` per run
- Adds metadata columns: `ingest_timestamp`, `source_file`, `ingest_run_id`
- Writes to bronze Delta tables with schema merge

**Task 2: Bronze Archive**
- Moves processed CSV files to `<folder>/archive/`
- Runs after ingestion completes successfully
- Prevents reprocessing of same files

#### Silver Job (5 tasks)

Each task loads one fact table:
- Queries control table for last processed `ingest_run_id`
- Identifies new run IDs to process
- Joins bronze tables to create enriched fact tables
- Appends to silver Delta tables
- Updates control table with latest processed run ID

Tasks run in parallel where possible (member snapshot waits for others).

### File Structure

**Python Scripts** (used by both classic and serverless):
- `scripts/bronze/bronze_ingest.py` - CSV ingestion logic
- `scripts/bronze/bronze_archive.py` - File archiving logic
- `scripts/silver/silver_control.py` - Incremental tracking helper
- `scripts/silver/` - 4 silver fact table loaders
- `scripts/gold/` - 1 gold table loader (member monthly snapshot)

**Configuration:**
- `databricks.yml` - 4 batch jobs (2 bronze + 2 silver, classic + serverless)

### Deployment

```bash
cd demos/serverless-jobs-demo

# Deploy all jobs (classic + serverless)
databricks bundle deploy --target development \
  --var catalog_name=$(jq -r .catalog_name variables.json) \
  --var base_volume_path=$(jq -r .base_volume_path variables.json)
```

This deploys:
- `daily_bronze_ingestion_incr` (classic compute)
- `daily_silver_load_incr` (classic compute)
- `daily_bronze_ingestion_incr_serverless` (serverless compute)
- `daily_silver_load_incr_serverless` (serverless compute)

### Running

**Classic Compute Jobs:**
```bash
# Run bronze job (ingest + archive)
databricks bundle run --target development daily_bronze_ingestion_incr \
  --var catalog_name=$(jq -r .catalog_name variables.json) \
  --var base_volume_path=$(jq -r .base_volume_path variables.json)

# Run silver job (4 silver + 1 gold table)
databricks bundle run --target development daily_silver_load_incr \
  --var catalog_name=$(jq -r .catalog_name variables.json)
```

**Serverless Compute Jobs:**
```bash
# Run bronze job (serverless)
databricks bundle run --target development daily_bronze_ingestion_incr_serverless \
  --var catalog_name=$(jq -r .catalog_name variables.json) \
  --var base_volume_path=$(jq -r .base_volume_path variables.json)

# Run silver job (serverless)
databricks bundle run --target development daily_silver_load_incr_serverless \
  --var catalog_name=$(jq -r .catalog_name variables.json)
```

### Scheduling

All jobs include schedule configuration (paused by default):
- **Bronze jobs**: Daily at 2:00 AM UTC
- **Silver jobs**: Daily at 2:30 AM UTC (30 min after bronze)

Enable by updating `pause_status: "UNPAUSED"` in `databricks.yml`.

**Recommendation**: Enable either classic OR serverless jobs, not both simultaneously (they produce the same tables).

### Incremental Processing

**Bronze**: Uses file archiving
- New files → processed → moved to archive
- Next run only sees new files

**Silver**: Uses run ID tracking
- Control table stores last processed `ingest_run_id` per fact table
- Only processes rows with newer run IDs
- Idempotent - safe to rerun

---


## Silver/Gold Tables Reference

Detailed reference for the 4 silver tables and 1 gold table created by either approach.

### 1. claims_silver

**Grain:** One row per claim transaction/line item

**Sources:** `claims_transactions_bronze`, `claims_bronze`, `encounters_bronze`, `patients_bronze`, `providers_bronze`, `organizations_bronze`

**Key Metrics:**
- `claim_amount`, `payment_amount`, `adjustment_amount`, `outstanding_amount`
- `units`, `unit_amount`
- `base_encounter_cost`, `total_claim_cost`, `payer_coverage`

**Key Dimensions:**
- Patient demographics (gender, birthdate, state, zip)
- Provider details (specialty, name)
- Organization details (name, city, state)
- Service dates and diagnosis codes
- Transaction type and place of service

**Use Cases:**
- Claims cost analysis by provider/specialty
- Payment and adjustment tracking
- Denial rate analysis
- Reimbursement reporting

**Example Query:**
```sql
SELECT 
    provider_specialty,
    COUNT(DISTINCT claim_id) as claim_count,
    SUM(claim_amount) as total_billed,
    SUM(payment_amount) as total_paid
FROM <catalog>.synthea.claims_silver
WHERE service_date >= '2024-01-01'
GROUP BY provider_specialty
ORDER BY total_paid DESC;
```

---

### 2. patient_encounters_silver

**Grain:** One row per patient encounter

**Sources:** `encounters_bronze`, `patients_bronze`, `providers_bronze`, `organizations_bronze`, `conditions_bronze`

**Key Metrics:**
- `base_encounter_cost`, `total_claim_cost`, `payer_coverage`, `patient_responsibility`
- `encounter_duration_minutes`
- `encounter_count` (always 1, for aggregation)

**Key Dimensions:**
- Patient demographics (age at encounter, gender, race, ethnicity, location)
- Provider details (name, specialty, gender)
- Organization details (name, city, state)
- Primary diagnosis (code, description)
- Encounter type (inpatient, outpatient, emergency, wellness)

**Use Cases:**
- Utilization management and trending
- Network adequacy analysis
- ER visit and admission rates
- Cost per encounter by type/provider
- Geographic utilization patterns

**Example Query:**
```sql
SELECT 
    encounter_class,
    COUNT(*) as encounter_count,
    AVG(encounter_duration_minutes) as avg_duration,
    AVG(total_claim_cost) as avg_cost
FROM <catalog>.synthea.patient_encounters_silver
WHERE encounter_date_key >= '2024-01-01'
GROUP BY encounter_class
ORDER BY encounter_count DESC;
```

---

### 3. medications_silver

**Grain:** One row per medication prescription fill

**Sources:** `medications_bronze`, `patients_bronze`, `encounters_bronze`, `providers_bronze`

**Key Metrics:**
- `base_cost`, `payer_coverage`, `patient_copay`, `total_cost`
- `dispenses`, `days_supply`

**Key Dimensions:**
- Medication details (code, description)
- Patient demographics (age at prescription, gender, location)
- Prescriber details (name, specialty)
- Indication (reason code/description)
- Encounter class

**Use Cases:**
- Pharmacy cost analysis
- Formulary compliance tracking
- Medication adherence monitoring
- High-cost specialty drug identification
- Generic vs brand utilization rates

**Example Query:**
```sql
SELECT 
    medication_description,
    COUNT(*) as prescription_count,
    SUM(total_cost) as total_cost,
    AVG(patient_copay) as avg_copay,
    AVG(days_supply) as avg_days_supply
FROM <catalog>.synthea.medications_silver
WHERE prescription_date_key >= '2024-01-01'
GROUP BY medication_description
HAVING SUM(total_cost) > 10000
ORDER BY total_cost DESC;
```

---

### 4. procedures_silver

**Grain:** One row per procedure performed

**Sources:** `procedures_bronze`, `encounters_bronze`, `patients_bronze`, `providers_bronze`, `organizations_bronze`

**Key Metrics:**
- `procedure_cost`
- `procedure_duration_minutes`
- `procedure_count` (always 1, for aggregation)

**Key Dimensions:**
- Procedure details (code, description, system)
- Patient demographics (age at procedure, gender, location)
- Provider details (name, specialty)
- Organization details (name, city, state)
- Indication (reason code/description)
- Encounter class and payer

**Use Cases:**
- Procedure cost variation analysis
- High-cost diagnostic and imaging tracking
- Medical necessity review
- Provider efficiency analysis
- Quality metrics (procedure appropriateness)

**Example Query:**
```sql
SELECT 
    procedure_description,
    provider_specialty,
    COUNT(*) as procedure_count,
    AVG(procedure_cost) as avg_cost,
    STDDEV(procedure_cost) as cost_stddev
FROM <catalog>.synthea.procedures_silver
WHERE procedure_date_key >= '2024-01-01'
GROUP BY procedure_description, provider_specialty
HAVING COUNT(*) >= 10
ORDER BY avg_cost DESC;
```

---

### 5. member_monthly_snapshot_gold

**Grain:** One row per member per month

**Sources:** Aggregated from `encounters_bronze`, `medications_bronze`, `conditions_bronze`, `patients_bronze`

**Key Metrics:**
- `total_encounters`, `total_medications`
- `total_medical_cost`, `total_pharmacy_cost`, `total_cost`
- `total_medical_coverage`, `total_pharmacy_coverage`
- `er_visits`, `inpatient_admits`, `preventive_visits`
- `chronic_condition_count`
- `member_months` (always 1)
- `risk_tier` (High/Medium/Low based on utilization)

**Key Dimensions:**
- Member demographics (age, gender, race, ethnicity, location)
- Year and month
- Risk tier

**Use Cases:**
- PMPM (Per Member Per Month) cost trending
- Member risk stratification
- High utilizer identification
- Care gap analysis
- Population health management
- Actuarial reporting
- Member retention analysis

**Example Queries:**

```sql
-- PMPM cost trend
SELECT 
    year,
    month,
    SUM(member_months) as member_months,
    SUM(total_cost) / SUM(member_months) as pmpm_cost,
    SUM(total_medical_cost) / SUM(member_months) as medical_pmpm,
    SUM(total_pharmacy_cost) / SUM(member_months) as pharmacy_pmpm
FROM <catalog>.synthea.member_monthly_snapshot_gold
GROUP BY year, month
ORDER BY year, month;

-- High utilizers by risk tier
SELECT 
    risk_tier,
    COUNT(DISTINCT patient_id) as member_count,
    AVG(total_encounters) as avg_encounters,
    AVG(er_visits) as avg_er_visits,
    AVG(total_cost) as avg_total_cost
FROM <catalog>.synthea.member_monthly_snapshot_gold
WHERE year = 2024
GROUP BY risk_tier
ORDER BY avg_total_cost DESC;
```

---

### Common Patterns Across All Silver/Gold Tables

**Metadata Columns:**
- `ingest_timestamp` - When data entered bronze layer
- `silver_load_timestamp` - When data was transformed to silver
- `ingest_run_id` (Batch) or implicit via streaming (DLT)

**Design Principles:**
- **Star schema** - Facts contain metrics, dimensions for slicing
- **Date keys** - For efficient date-based filtering and joins
- **Additive metrics** - Can be summed across dimensions
- **Foreign keys** - Enable joins to dimension tables (future enhancement)
- **Degenerate dimensions** - Low-cardinality attributes in fact table

---


## Next Steps

### Immediate
1. ✅ **Deploy your chosen approach** (or both!)
2. ✅ **Run initial load** with your synthetic data
3. ✅ **Verify tables** created successfully
4. ✅ **Run example queries** to explore data

### Enhancements

**Data Quality:**
- Add more expectations/validations based on business rules
- Create data quality dashboards
- Set up alerts on quality failures

**Dimension Tables:**
- `dim_date` - Date dimension with fiscal calendars
- `dim_patient` - Patient SCD Type 2 with history
- `dim_provider` - Provider SCD Type 2
- `dim_diagnosis` - ICD-10/SNOMED mappings
- `dim_medication` - NDC/RxNorm mappings

**Gold Layer:**
- Pre-aggregated monthly/yearly summaries
- Business KPIs and metrics
- Executive dashboards
- Actuarial reports

**Optimization:**
- **Partitioning** - Partition by date for large tables
- **Z-Ordering** - Optimize for common query patterns
- **Liquid Clustering** - For evolving query patterns
- **Table maintenance** - VACUUM, OPTIMIZE schedules

**Data Governance:**
- Row/column-level security
- PII masking and encryption
- Audit logging
- Data catalog integration

**Testing:**
- Unit tests for transformations
- Data validation tests
- Reconciliation checks
- Performance benchmarks

---

## Complete Directory Structure

```
demos/serverless-jobs-demo/
├── databricks.yml                        # 4 batch jobs (2 bronze + 2 silver)
├── variables.json                        # Your config (create from example)
├── variables.example.json                # Config template
├── README.md                            # This file
│
└── scripts/                             # Python scripts (shared by all jobs)
    ├── bronze/                          # Bronze layer scripts
    │   ├── bronze_ingest.py             # CSV ingestion logic
    │   └── bronze_archive.py            # File archiving logic
    ├── silver/                          # Silver layer scripts
    │   ├── silver_control.py            # Incremental tracking helper
    │   ├── load_fact_claims.py
    │   ├── load_fact_patient_encounters.py
    │   ├── load_fact_medications.py
    │   └── load_fact_procedures.py
    └── gold/                            # Gold layer scripts
        └── load_fact_member_monthly_snapshot.py
```

**Jobs Created:**
- `daily_bronze_ingestion_incr_classic`
- `daily_bronze_ingestion_incr_serverless`
- `daily_silver_load_incr_classic`
- `daily_silver_load_incr_serverless`

---

## Useful Resources

- [Databricks Delta Live Tables Docs](https://docs.databricks.com/delta-live-tables/)
- [Auto Loader Documentation](https://docs.databricks.com/ingestion/auto-loader/)
- [Databricks Jobs Documentation](https://docs.databricks.com/workflows/jobs/)
- [Unity Catalog Volumes](https://docs.databricks.com/data-governance/unity-catalog/volumes.html)
- [Synthea Synthetic Data Generator](https://github.com/matthew-gigl-db/synthea-on-dbx)

---

## Support & Contributing

Questions or issues? Please refer to:
- Main repo README
- Databricks documentation
- Community forums

Happy data engineering! 🚀
