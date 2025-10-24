# Databricks Jobs API Deployment

This directory contains JSON job definitions that can be deployed using the Databricks Jobs API as an alternative to Databricks Asset Bundles (DAB).

## Available Jobs

### Python Script Jobs (Serverless)

1. **`daily_bronze_ingestion_incr_py_serverless_api.json`**
   - Bronze layer ingestion and archiving using Python scripts
   - 2 tasks: bronze_ingest → bronze_archive
   - Runs on serverless compute with environment client 4

2. **`daily_silver_load_incr_py_serverless_api.json`**
   - Silver/Gold layer processing using Python scripts
   - 5 tasks: 4 silver tables + 1 gold table (with dependencies)
   - Runs on serverless compute with environment client 4

### Notebook Jobs (Serverless)

3. **`daily_bronze_ingestion_incr_nb_serverless_api.json`**
   - Bronze layer ingestion and archiving using Jupyter notebooks
   - 2 tasks: bronze_ingest → bronze_archive
   - Runs on serverless compute

4. **`daily_silver_load_incr_nb_serverless_api.json`**
   - Silver/Gold layer processing using Jupyter notebooks
   - 5 tasks: 4 silver tables + 1 gold table (with dependencies)
   - Runs on serverless compute

## Deployment Methods

### Method 1: Using Databricks CLI

#### Create a new job:
```bash
databricks jobs create --json-file api_jobs/daily_bronze_ingestion_incr_py_serverless_api.json
```

#### Update an existing job:
```bash
databricks jobs update <job_id> --json-file api_jobs/daily_bronze_ingestion_incr_py_serverless_api.json
```

#### Reset an existing job (full replacement):
```bash
databricks jobs reset <job_id> --json-file api_jobs/daily_bronze_ingestion_incr_py_serverless_api.json
```

### Method 2: Using Databricks REST API

#### Create a new job:
```bash
curl -X POST \
  https://<databricks-instance>/api/2.1/jobs/create \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d @api_jobs/daily_bronze_ingestion_incr_py_serverless_api.json
```

#### Update an existing job:
```bash
curl -X POST \
  https://<databricks-instance>/api/2.1/jobs/update \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "job_id": <job_id>,
    "new_settings": <paste json content>
  }'
```

### Method 3: Using Python SDK

```python
from databricks.sdk import WorkspaceClient
import json

w = WorkspaceClient()

# Load job definition
with open('api_jobs/daily_bronze_ingestion_incr_py_serverless_api.json', 'r') as f:
    job_config = json.load(f)

# Create job
job = w.jobs.create(**job_config)
print(f"Created job with ID: {job.job_id}")
```

## Deployment Script Example

Create a deployment script `deploy_api_jobs.sh`:

```bash
#!/bin/bash

# Set your Databricks workspace URL and token
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="your-token"

# Deploy all serverless API jobs
echo "Deploying Bronze Python job..."
databricks jobs create --json-file api_jobs/daily_bronze_ingestion_incr_py_serverless_api.json

echo "Deploying Silver Python job..."
databricks jobs create --json-file api_jobs/daily_silver_load_incr_py_serverless_api.json

echo "Deploying Bronze Notebook job..."
databricks jobs create --json-file api_jobs/daily_bronze_ingestion_incr_nb_serverless_api.json

echo "Deploying Silver Notebook job..."
databricks jobs create --json-file api_jobs/daily_silver_load_incr_nb_serverless_api.json

echo "All jobs deployed successfully!"
```

Make it executable:
```bash
chmod +x deploy_api_jobs.sh
./deploy_api_jobs.sh
```

## Configuration Notes

### File Paths
- **Python scripts**: Full workspace paths are required
  - `/Workspace/Shared/hls-demos/serverless-jobs-demo/files/scripts/bronze/bronze_ingest.py`
  - `/Workspace/Shared/hls-demos/serverless-jobs-demo/files/scripts/silver/load_fact_claims.py`
  - Must include `"source": "WORKSPACE"` in the task definition
- **Notebooks**: Full workspace paths are required
  - `/Workspace/Shared/hls-demos/serverless-jobs-demo/files/notebooks/bronze/bronze_ingest`
  - Must include `"source": "WORKSPACE"` in the task definition

**Important**: Before deploying, ensure your Python scripts and notebooks are uploaded to the specified workspace paths.

### Parameters
The JSON files include hardcoded parameters. To use variables, you can:

1. **Use environment variables** in your deployment script
2. **Template the JSON** using jq or sed before deployment
3. **Modify after creation** using the Jobs API

Example with jq templating:
```bash
export CATALOG_NAME="your_catalog"
jq --arg catalog "$CATALOG_NAME" \
   '.tasks[].spark_python_task.parameters[1] = $catalog' \
   api_jobs/daily_bronze_ingestion_incr_py_serverless_api.json \
   | databricks jobs create --json
```

## Comparison: DAB vs API

| Aspect | DAB (databricks.yml) | API (JSON files) |
|--------|---------------------|------------------|
| **Deployment** | `databricks bundle deploy` | `databricks jobs create` |
| **Variables** | Native support with `${var.}` | Manual templating needed |
| **Version Control** | YAML (human-readable) | JSON (machine-readable) |
| **Validation** | Built-in | Manual |
| **Lifecycle** | Managed by bundle | Manual tracking |
| **Updates** | Automatic sync | Manual update/reset |
| **Best For** | GitOps workflows | CI/CD pipelines, automation |

## Advantages of API Deployment

✅ **Flexibility**: Full control over when and how jobs are created/updated  
✅ **CI/CD Integration**: Easily integrate into existing CI/CD pipelines  
✅ **Programmatic**: Can be called from Python, shell scripts, or any language  
✅ **No Bundle Overhead**: Don't need to manage bundle state  
✅ **Conditional Logic**: Can apply logic before deployment  

## Advantages of DAB Deployment

✅ **Simplicity**: Single command deployment  
✅ **Variables**: Built-in variable substitution  
✅ **Validation**: Automatic syntax checking  
✅ **State Management**: Tracks what's deployed  
✅ **Multi-Resource**: Deploy jobs, pipelines, clusters together  

## Running Jobs

Once deployed, run jobs using:

```bash
# Get job ID
JOB_ID=$(databricks jobs list | grep "daily_bronze_ingestion_incr_py_serverless_api" | awk '{print $1}')

# Run the job
databricks jobs run-now --job-id $JOB_ID

# Check status
databricks jobs get-run --run-id <run_id>
```

## Cleaning Up

Delete jobs via API:
```bash
databricks jobs delete --job-id <job_id>
```

Or list and delete all:
```bash
databricks jobs list --output json | \
  jq -r '.jobs[] | select(.settings.name | contains("_api")) | .job_id' | \
  xargs -I {} databricks jobs delete --job-id {}
```

## Additional Resources

- [Databricks Jobs API Documentation](https://docs.databricks.com/api/workspace/jobs)
- [Databricks CLI Reference](https://docs.databricks.com/dev-tools/cli/)
- [Databricks SDK for Python](https://databricks-sdk-py.readthedocs.io/)

