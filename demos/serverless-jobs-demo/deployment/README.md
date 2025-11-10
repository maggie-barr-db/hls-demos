# Multi-Environment Deployment Guide

This guide explains how to deploy jobs across different environments (dev, uat, prod) without modifying job JSON files.

## Quick Navigation

- [Overview](#overview)
- [Directory Structure](#directory-structure)
- [Configuration Files](#configuration-files)
- [Usage](#usage)
- [CI/CD Integration](#cicd-integration)
- [Best Practices](#best-practices)

## Overview

The deployment system uses **template placeholders** in job JSON files that are replaced with environment-specific values at deployment time.

### Placeholders

- `{{CATALOG_NAME}}` - Unity Catalog name (e.g., dev, uat, prod)
- `{{BASE_VOLUME_PATH}}` - Base volume path for data
- `{{ADMIN_VOLUME_PATH}}` - Admin volume path for configs/libraries

## Directory Structure

```
demos/serverless-jobs-demo/
├── config/                     # Environment-specific configurations
│   ├── variables.json          # Default/local development config
│   ├── variables.dev.json      # Development environment config
│   ├── variables.uat.json      # UAT environment config  
│   └── variables.prod.json     # Production environment config
│
├── deployment/                 # Deployment scripts (you are here!)
│   ├── deploy_jobs.sh         # Multi-environment job deployment
│   ├── deploy_all.sh          # Full stack deployment
│   └── README.md              # This file
│
└── infrastructure/
    └── api_jobs/              # Job definitions with placeholders
        ├── daily_bronze_ingestion_incr_classic_api.json
        ├── daily_bronze_ingestion_incr_serverless_api.json
        ├── daily_silver_load_incr_classic_api.json
        └── daily_silver_load_incr_serverless_api.json
```

## Configuration Files

### Example: variables.dev.json
```json
{
  "catalog_name": "dev",
  "base_volume_path": "/Volumes/dev/synthea/landing",
  "admin_volume_path": "/Volumes/dev/synthea/admin_configs"
}
```

### Example: variables.prod.json
```json
{
  "catalog_name": "prod",
  "base_volume_path": "/Volumes/prod/synthea/landing",
  "admin_volume_path": "/Volumes/prod/synthea/admin_configs"
}
```

## Usage

**Note:** Run all deployment commands from the `deployment/` directory.

```bash
cd deployment
```

### Deploy to Default Environment
```bash
./deploy_jobs.sh
```
Uses `config/variables.json`

### Deploy to Development
```bash
./deploy_jobs.sh dev
```
Uses `config/variables.dev.json`

### Deploy to UAT
```bash
./deploy_jobs.sh uat
```
Uses `config/variables.uat.json`

### Deploy to Production
```bash
./deploy_jobs.sh prod
```
Uses `config/variables.prod.json`

### Full Stack Deployment
```bash
./deploy_all.sh
```
Deploys volumes, uploads code, and creates all jobs using default config

## How It Works

1. **Template Placeholders** - Job JSON files use placeholders:
   ```json
   {
     "spark_env_vars": {
       "catalog_name": "{{CATALOG_NAME}}",
       "base_volume_path": "{{BASE_VOLUME_PATH}}"
     },
     "init_scripts": [
       {
         "volumes": {
           "destination": "{{ADMIN_VOLUME_PATH}}/install_faker_wheel.sh"
         }
       }
     ]
   }
   ```

2. **Environment Selection** - Script reads the appropriate variables file

3. **Placeholder Replacement** - Script replaces placeholders with actual values

4. **Job Deployment** - Processed JSON is deployed to Databricks

## Example Job Definition

### Before Deployment (with placeholders)
```json
{
  "name": "daily_bronze_ingestion_incr_classic_api",
  "job_clusters": [{
    "new_cluster": {
      "spark_env_vars": {
        "catalog_name": "{{CATALOG_NAME}}",
        "base_volume_path": "{{BASE_VOLUME_PATH}}"
      },
      "init_scripts": [{
        "volumes": {
          "destination": "{{ADMIN_VOLUME_PATH}}/install_faker_wheel.sh"
        }
      }]
    }
  }]
}
```

### After Deployment to Prod (placeholders replaced)
```json
{
  "name": "daily_bronze_ingestion_incr_classic_api",
  "job_clusters": [{
    "new_cluster": {
      "spark_env_vars": {
        "catalog_name": "prod",
        "base_volume_path": "/Volumes/prod/synthea/landing"
      },
      "init_scripts": [{
        "volumes": {
          "destination": "/Volumes/prod/synthea/admin_configs/install_faker_wheel.sh"
        }
      }]
    }
  }]
}
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Deploy to Production
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Databricks CLI
        run: |
          pip install databricks-cli
          databricks configure --token <<EOF
          ${{ secrets.DATABRICKS_HOST }}
          ${{ secrets.DATABRICKS_TOKEN }}
          EOF
      
      - name: Deploy Jobs to Production
        run: |
          cd demos/serverless-jobs-demo
          ./deploy_jobs.sh prod
```

### Azure DevOps Pipeline Example
```yaml
trigger:
  branches:
    include:
      - main

pool:
  vmImage: 'ubuntu-latest'

variables:
  - group: databricks-prod

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '3.x'
  
  - script: |
      pip install databricks-cli
      databricks configure --token <<EOF
      $(DATABRICKS_HOST)
      $(DATABRICKS_TOKEN)
      EOF
    displayName: 'Setup Databricks CLI'
  
  - script: |
      cd demos/serverless-jobs-demo
      ./deploy_jobs.sh prod
    displayName: 'Deploy Jobs to Production'
```

## Best Practices

### 1. Version Control
- ✅ Commit job JSON files with placeholders
- ✅ Commit all variables.*.json files
- ❌ Don't commit credentials or secrets

### 2. Environment Parity
- Keep variable files in sync (same structure)
- Only values should differ between environments
- Use same job definitions across all environments

### 3. Deployment Strategy
```
dev → uat → prod
```
- Test in `dev` first
- Promote to `uat` for validation
- Deploy to `prod` after approval

### 4. Rollback Plan
- Tag releases in git
- Keep previous job IDs documented
- Test rollback procedure

## Prerequisites

Each environment must have:
- Unity Catalog with name matching `catalog_name`
- Schema: `synthea`
- Volumes:
  - `landing` (for data)
  - `admin_configs` (for scripts, wheels, requirements.txt)

## Troubleshooting

### Error: Variables file not found
```
✗ Error: Variables file not found: variables.prod.json
```
**Solution**: Create the missing variables file for that environment

### Error: Catalog not found
```
✗ Error: Catalog 'prod' not found
```
**Solution**: Verify the catalog exists in the target workspace

### Error: Volume not found
```
✗ Error: Volume '/Volumes/prod/synthea/admin_configs' not found
```
**Solution**: Create the required volumes in Unity Catalog

## Support

For issues or questions, contact the data engineering team.

