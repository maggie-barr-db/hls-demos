# Serverless Jobs Demo: Healthcare Data Pipelines

This demo showcases building bronze and silver data pipelines for healthcare/life sciences data using Databricks batch jobs with both classic and serverless compute, plus custom Python environments.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Prerequisites](#prerequisites)
4. [Deployment Options](#deployment-options)
5. [Custom Environment Setup](#custom-environment-setup)
6. [Architecture & Data Flow](#architecture--data-flow)
7. [Silver/Gold Tables Reference](#silver-gold-tables-reference)
8. [Classic vs Serverless Compute](#classic-vs-serverless-compute)
9. [API Deployment](#api-deployment)
10. [Next Steps](#next-steps)

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

**Custom Libraries**
- 15+ data processing, validation, and healthcare-specific Python libraries
- Centrally managed via UC Volume
- Available to all serverless jobs and notebooks

---

## Key Features

This demo showcases modern Databricks best practices and capabilities:

### 🔧 **Dual Code Format Support**
- **Python Scripts** (`.py`) for production workloads
- **Jupyter Notebooks** (`.ipynb`) for interactive development
- Jobs configured to call both Python tasks AND notebook tasks
- **Same business logic**, different execution contexts
- Compare performance, debugging, and maintenance between formats

### 🚀 **Serverless Environment Configuration**
- Custom serverless environment (`serverless_environment_demo`) with 15+ additional libraries
- Environment specified at the **job level** via `environment_key`
- Dependencies managed centrally via **`requirements.txt` hosted on UC Volume**
- All serverless jobs and notebooks reference: `/Volumes/{catalog}/synthea/admin_configs/requirements.txt`
- No per-task dependency management needed

### 📦 **Custom Wheel Packaging & Deployment**
- **Two custom wheels** demonstrate different library deployment patterns:
  1. **`hls_external_libs`** (`infrastructure/external_libs/hls_external_libs/`)
     - Meta-package bundling: `ydata-profiling`, `missingno`, `Faker`
     - Used in serverless environments via `requirements.txt`
  2. **`faker_wheel`** (`infrastructure/external_libs/faker_wheel/`)
     - Standalone Faker library package
     - Installed on classic compute via init script
- Wheels deployed to UC Volume and managed centrally
- **Demonstrated in**: `load_fact_member_monthly_snapshot` (gold layer)
  - Imports `Faker` library from the wheel
  - Generates anonymized patient IDs with cryptographic hashing
  - Shows seamless integration of bundled external libraries
- **Demonstrated in**: `functional_testing` notebook (data quality job)
  - Uses both `Faker` (from wheel) and `html2text` (from requirements.txt)
  - Shows different library installation methods working together

### 🏗️ **Medallion Architecture**
- **Bronze**: Raw ingestion with metadata tracking (`ingest_run_id`, `ingest_timestamp`, `source_file`)
- **Silver**: Cleaned fact tables with incremental loading
- **Gold**: Aggregated business metrics (monthly member snapshots)

### ⚡ **Full Load Configuration for Performance Comparison**
- **Silver jobs are configured to run FULL loads** (processing all data each time)
- This enables side-by-side comparison of classic vs serverless compute with identical data volumes
- Allows for accurate cost and performance analysis between compute options
- Each silver script/notebook supports both `full` and `incremental` load modes via `--load_type` parameter
- **Bronze layer** still uses incremental loading with automatic archiving

**Note**: The silver layer infrastructure supports incremental processing capabilities (run ID-based tracking with control tables). To switch to incremental mode, change `load_type` parameter from `"full"` to `"incremental"` in job configurations.

### 🎯 **Multiple Compute Options**
- **Classic Compute**: Single-node jobs for cost-sensitive workloads
- **Serverless Compute**: Instant startup, auto-scaling for dynamic workloads
- Same code works on both - just configuration changes

### 🛠️ **Flexible Deployment Methods**
- **Databricks Asset Bundles (DAB)**: GitOps-friendly YAML configuration
- **Jobs API**: JSON-based programmatic deployment for CI/CD
- **Workspace-based**: Code deployed to `/Workspace/Shared/` for easy access
- Side-by-side comparison of deployment approaches

### 📊 **Modular Code Structure**
- Reusable utilities in `src/utils/` (`silver_control.py`)
- Clear separation: scripts, notebooks, infrastructure
- Consistent patterns across bronze, silver, and gold layers

### 🔄 **Production-Ready Patterns**
- Job dependencies and task orchestration
- Control tables for state management
- Schema evolution with merge operations
- Error handling and data validation

---

## Quick Start

```bash
cd demos/serverless-jobs-demo

# 1. Configure your environment
cp variables.example.json variables.json
# Edit variables.json with your catalog and volume paths

# 2. Deploy custom Python environment (optional but recommended)
./deploy_environment.sh

# 3. Deploy jobs
databricks bundle deploy --target development \
  --var catalog_name=$(jq -r .catalog_name variables.json) \
  --var base_volume_path=$(jq -r .base_volume_path variables.json)

# 4. Run bronze ingestion (serverless recommended)
databricks jobs run-now --job-id <job_id>
```

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
- ✅ **jq** for JSON processing
  ```bash
  brew install jq
  ```

### Configuration

Create `variables.json`:
```json
{
  "catalog_name": "your_catalog",
  "base_volume_path": "/Volumes/your_catalog/synthea/landing"
}
```

---

## Deployment Options

This demo provides three deployment methods:

### 1. Databricks Asset Bundles (DAB) - Recommended

Deploy all jobs with a single command:
```bash
databricks bundle deploy --target development \
  --var catalog_name=$(jq -r .catalog_name variables.json) \
  --var base_volume_path=$(jq -r .base_volume_path variables.json)
```

**Jobs deployed:**
- `daily_bronze_ingestion_incr_py_classic` - Bronze (Python, Classic)
- `daily_bronze_ingestion_incr_py_serverless_dab` - Bronze (Python, Serverless)
- `daily_bronze_ingestion_incr_nb_serverless_dab` - Bronze (Notebook, Serverless)
- `daily_silver_load_incr_py_classic` - Silver (Python, Classic)
- `daily_silver_load_incr_py_serverless_dab` - Silver (Python, Serverless)
- `daily_silver_load_incr_nb_serverless_dab` - Silver (Notebook, Serverless)

###2. API Deployment

Use the Jobs API for CI/CD integration:
```bash
cd api_jobs
./deploy_jobs.sh
```

**Advantages:**
- ✅ Full control over deployment timing
- ✅ Easy CI/CD integration
- ✅ Programmatic deployment from any language
- ✅ No bundle state to manage

### 3. Manual Deployment

Deploy individual jobs via Databricks UI or API calls.

---

## Custom Environment Setup

### Unity Catalog Volumes

This demo uses three UC volumes for different purposes:

1. **`landing`** - Source data for bronze ingestion
   - Location: `/Volumes/{catalog}/synthea/landing/`
   - Contains: Synthea CSV files

2. **`admin_configs`** - Configuration and library management
   - Location: `/Volumes/{catalog}/synthea/admin_configs/`
   - Contains: `requirements.txt`, custom wheels, init scripts

3. **`functional_testing`** - Test artifacts storage
   - Location: `/Volumes/{catalog}/synthea/functional_testing/`
   - Contains: Parquet files and test data from functional testing job

**Create volumes:**
```bash
databricks workspace import-dir infrastructure/setup_volumes.sql
# Or run the SQL directly in a notebook
```

### Deploy Serverless Environment

Deploy a custom serverless environment with 15+ additional Python libraries:

```bash
./deploy_environment.sh
```

This creates:
1. UC volume `/Volumes/{catalog}/synthea/admin_configs` (if not exists)
2. Uploads `requirements.txt` with custom libraries
3. Creates environment `serverless_environment_demo`

**Libraries included:**
- **Data Processing**: polars, duckdb, pyarrow
- **Data Validation**: great-expectations, pandera
- **Healthcare**: hl7apy, fhir.resources
- **ML/Stats**: scikit-learn, statsmodels
- **Utilities**: python-dotenv, tenacity, tqdm, funcy, toolz

**Custom environment name or catalog:**
```bash
./deploy_environment.sh my-custom-env my_catalog
```

**Add more libraries:**
1. Edit `requirements.txt`
2. Run `./deploy_environment.sh` again

---

## Architecture & Data Flow

### Bronze Layer

```
CSV Files → Bronze Ingest → Bronze Tables → Archive
```

**Task 1: Bronze Ingest**
- Reads CSV files from landing folders
- Adds metadata: `ingest_timestamp`, `source_file`, `ingest_run_id`
- Writes to Delta tables with schema merge

**Task 2: Bronze Archive**
- Moves processed files to `archive/` subdirectory
- Prevents reprocessing

### Silver/Gold Layer

```
Bronze Tables → Silver Transform → Fact Tables → Gold Aggregation
```

**Tasks:**
- 4 parallel silver fact table loads
- 1 gold aggregation table (depends on silver)
- Incremental processing via run ID tracking
- Control table maintains processing state

### Incremental Processing

**Bronze**: File-based
- New files → process → archive
- Next run only sees new files

**Silver**: Run ID-based
- Control table tracks last processed `ingest_run_id`
- Only new data is transformed
- Idempotent and rerunnable

---

## Silver/Gold Tables Reference

### 1. claims_silver
**Grain**: One row per claim transaction/line item  
**Key Metrics**: claim_amount, payment_amount, units  
**Use Cases**: Claims cost analysis, reimbursement reporting

### 2. patient_encounters_silver
**Grain**: One row per patient encounter  
**Key Metrics**: encounter_cost, duration, patient_responsibility  
**Use Cases**: Utilization management, network adequacy

### 3. medications_silver
**Grain**: One row per medication fill  
**Key Metrics**: cost, payer_coverage, patient_copay, days_supply  
**Use Cases**: Pharmacy cost, formulary compliance, adherence

### 4. procedures_silver
**Grain**: One row per procedure  
**Key Metrics**: procedure_cost, duration  
**Use Cases**: Cost variation, medical necessity, quality metrics

### 5. member_monthly_snapshot_gold
**Grain**: One row per member per month  
**Key Metrics**: PMPM costs, utilization, risk tier  
**Use Cases**: Population health, risk stratification, actuarial reporting

**Example PMPM Query:**
```sql
SELECT 
    year, month,
    SUM(total_cost) / SUM(member_months) as pmpm_cost
FROM <catalog>.synthea.member_monthly_snapshot_gold
GROUP BY year, month
ORDER BY year, month;
```

---

## Classic vs Serverless Compute

### Full Load Configuration for Fair Comparison

**All silver jobs are configured to run FULL loads** to enable accurate side-by-side performance and cost comparisons:
- Same data volumes processed across classic and serverless jobs
- Identical SQL transformations and business logic
- Run jobs simultaneously or sequentially to compare:
  - Total execution time
  - DBU consumption
  - Cost per run
  - Resource utilization patterns

This configuration allows you to make data-driven decisions about which compute option best fits your workload characteristics.

### Quick Decision Guide

**Choose Serverless if:**
- ✅ You want instant startup (no cluster provisioning)
- ✅ Jobs run on schedule or ad-hoc
- ✅ You prefer simplified configuration
- ✅ Pay only for actual compute used
- ✅ Development/testing phase

**Choose Classic if:**
- ✅ Jobs run continuously 24/7
- ✅ Need specific Spark tuning
- ✅ Cost optimization via spot instances important
- ✅ Network/security restrictions

### Cost Comparison

| Aspect | Classic | Serverless |
|--------|---------|------------|
| **Startup** | 5-10 minutes | Instant (seconds) |
| **Idle Charges** | Yes | No |
| **Scaling** | Manual | Automatic |
| **Best For** | Long-running | Short/variable jobs |

### Configuration Differences

**Classic:**
```yaml
job_clusters:
  - job_cluster_key: classic_single_node
    new_cluster:
      spark_version: "13.3.x-scala2.12"
      node_type_id: "Standard_DS3_v2"
      num_workers: 0
```

**Serverless:**
```yaml
tasks:
  - task_key: my_task
    environment_key: serverless_environment_demo
environments:
  - environment_key: serverless_environment_demo
    spec:
      client: "4"
      dependencies:
        - "-r /Volumes/{catalog}/synthea/admin_configs/requirements.txt"
```

**Key Point**: Both use the same Python code from `scripts/` - only configuration differs!

### Migration

**From Classic to Serverless:**
1. Deploy serverless jobs (already configured)
2. Test and compare performance
3. Pause classic jobs if satisfied

**From Serverless to Classic:**
1. Deploy classic jobs (already configured)
2. Test and compare performance
3. Pause serverless jobs if satisfied

**Recommendation**: Start with serverless for simplicity and faster iteration.

---

## API Deployment

Deploy jobs programmatically using the Databricks Jobs API.

### Quick Deploy

```bash
cd api_jobs
./deploy_jobs.sh
```

### Manual Deployment

```bash
# Create a job
databricks jobs create --json @api_jobs/daily_bronze_ingestion_incr_py_serverless_api.json

# Update existing job
databricks jobs reset <job_id> --json @api_jobs/daily_bronze_ingestion_incr_py_serverless_api.json
```

### API vs DAB Comparison

| Aspect | DAB | API |
|--------|-----|-----|
| **Deployment** | `databricks bundle deploy` | `databricks jobs create` |
| **Variables** | Native `${var.}` support | Manual templating |
| **Version Control** | YAML (human-readable) | JSON (machine-readable) |
| **Validation** | Built-in | Manual |
| **Best For** | GitOps workflows | CI/CD automation |

### Available API Jobs

**Python Scripts:**
- `daily_bronze_ingestion_incr_py_serverless_api.json`
- `daily_silver_load_incr_py_serverless_api.json`

**Notebooks:**
- `daily_bronze_ingestion_incr_nb_serverless_api.json`
- `daily_silver_load_incr_nb_serverless_api.json`

---

## Directory Structure

```
demos/serverless-jobs-demo/
├── databricks.yml                        # DAB configuration
├── deploy_environment.sh                 # Environment deployment script
├── requirements.txt                      # Custom Python libraries
├── variables.json                        # Your configuration
│
├── scripts/                              # Python scripts (Python jobs)
│   ├── bronze/
│   │   ├── bronze_ingest.py
│   │   └── bronze_archive.py
│   ├── silver/
│   │   ├── silver_control.py
│   │   └── load_fact_*.py (4 files)
│   └── gold/
│       └── load_fact_member_monthly_snapshot.py
│
├── notebooks/                            # Jupyter notebooks (Notebook jobs)
│   ├── bronze/
│   │   ├── bronze_ingest.ipynb
│   │   └── bronze_archive.ipynb
│   ├── silver/
│   │   ├── silver_control.py
│   │   └── load_fact_*.ipynb (4 files)
│   └── gold/
│       ├── silver_control.py
│       └── load_fact_member_monthly_snapshot.ipynb
│
└── api_jobs/                             # API deployment
    ├── deploy_jobs.sh
    └── *.json (4 job definitions)
```

---

## Next Steps

### Immediate
1. ✅ Deploy custom environment: `./deploy_environment.sh`
2. ✅ Deploy jobs: `databricks bundle deploy`
3. ✅ Run bronze ingestion
4. ✅ Verify tables created
5. ✅ Run example queries

### Enhancements

**Data Quality:**
- Add business-specific validations
- Create data quality dashboards
- Set up alerts on failures

**Dimension Tables:**
- `dim_date` - Date dimension
- `dim_patient` - Patient SCD Type 2
- `dim_provider` - Provider SCD Type 2
- `dim_diagnosis` - ICD-10/SNOMED mappings

**Optimization:**
- Partitioning by date
- Z-Ordering for common queries
- Liquid Clustering
- Table maintenance schedules

**Governance:**
- Row/column-level security
- PII masking
- Audit logging

---

## Useful Resources

- [Databricks Jobs Documentation](https://docs.databricks.com/workflows/jobs/)
- [Unity Catalog Volumes](https://docs.databricks.com/data-governance/unity-catalog/volumes.html)
- [Serverless Compute](https://docs.databricks.com/en/serverless-compute/index.html)
- [Synthea Synthetic Data](https://github.com/matthew-gigl-db/synthea-on-dbx)

---

## Support & Contributing

Questions or issues? Please refer to:
- Main repo README
- Databricks documentation
- Community forums

Happy data engineering! 🚀
