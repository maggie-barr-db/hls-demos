# Serverless Jobs Demo

A comprehensive demonstration of Databricks serverless compute for jobs, showcasing the differences between classic and serverless architectures.

## 📁 Project Structure

```
serverless-jobs-demo/
├── config/                      # Environment configurations
│   ├── variables.json           # Default/local config
│   ├── variables.dev.json       # Development environment
│   ├── variables.uat.json       # UAT environment
│   └── variables.prod.json      # Production environment
│
├── deployment/                  # Deployment scripts and docs
│   ├── deploy_jobs.sh          # Multi-environment job deployment
│   ├── deploy_all.sh           # Full stack deployment
│   └── README.md               # Detailed deployment guide
│
├── infrastructure/             # Databricks infrastructure
│   ├── api_jobs/              # Job definitions (JSON)
│   ├── init_scripts/          # Cluster init scripts
│   ├── requirements.txt       # Python dependencies
│   └── setup_volumes.sql      # Unity Catalog setup
│
└── src/                       # Source code
    ├── classic/               # Classic compute implementations
    │   ├── bronze/           # Bronze layer (notebooks + scripts)
    │   ├── silver/           # Silver layer (notebooks + scripts)
    │   ├── gold/             # Gold layer (notebooks + scripts)
    │   └── utils/            # Shared utilities
    │
    └── serverless/           # Serverless compute implementations
        ├── bronze/           # Bronze layer (notebooks + scripts)
        ├── silver/           # Silver layer (notebooks + scripts)
        ├── gold/             # Gold layer (notebooks + scripts)
        └── utils/            # Shared utilities
```

## 🚀 Quick Start

### 1. Configure Your Environment

Create/edit `config/variables.json` with your settings:

```json
{
  "catalog_name": "your_catalog",
  "base_volume_path": "/Volumes/your_catalog/synthea/landing",
  "admin_volume_path": "/Volumes/your_catalog/synthea/admin_configs"
}
```

### 2. Deploy

```bash
# Deploy everything (volumes, code, jobs)
cd deployment
./deploy_all.sh

# Or deploy just jobs to a specific environment
./deploy_jobs.sh prod
```

## 📚 Documentation

- **[Deployment Guide](deployment/README.md)** - Complete deployment instructions and multi-environment setup
- **Job Definitions** - See `infrastructure/api_jobs/` for JSON job configurations

## 🏗️ Architecture

### Classic vs Serverless

This demo showcases both **classic compute** and **serverless compute** approaches:

| Feature | Classic | Serverless |
|---------|---------|------------|
| **Startup Time** | Minutes | Seconds |
| **Libraries** | Init scripts + volume mounting | Environment definitions |
| **Config** | Environment variables | Job parameters |
| **Cost Model** | Per-cluster | Per-task execution |
| **Scaling** | Manual configuration | Automatic |

### Job Types

**Bronze Jobs** - Data ingestion (mixed: notebook + Python)
- `daily_bronze_ingestion_incr_classic_api` - Classic compute
- `daily_bronze_ingestion_incr_serverless_api` - Serverless compute

**Silver Jobs** - Data transformation (mixed: notebooks + Python)
- `daily_silver_load_incr_classic_api` - Classic compute  
- `daily_silver_load_incr_serverless_api` - Serverless compute

## 🔧 Configuration Management

The project uses template placeholders for multi-environment deployment:

```json
{
  "spark_env_vars": {
    "catalog_name": "{{CATALOG_NAME}}"
  },
  "init_scripts": [{
    "volumes": {
      "destination": "/Volumes/{{CATALOG_NAME}}/synthea/admin_configs/install_faker_wheel.sh"
    }
  }]
}
```

At deployment time, `{{CATALOG_NAME}}` is replaced with environment-specific values.

## 🌍 Multi-Environment Support

Deploy to different environments without code changes:

```bash
cd deployment

# Development
./deploy_jobs.sh dev

# UAT
./deploy_jobs.sh uat

# Production
./deploy_jobs.sh prod
```

Each environment uses its own configuration file in `config/`.

## 📋 Prerequisites

- Databricks workspace with Unity Catalog enabled
- Databricks CLI configured (`databricks configure`)
- Unity Catalog with:
  - Schema: `synthea`
  - Volumes: `landing`, `admin_configs`
- Python 3.x with `jq` installed

## 🔗 Related Resources

- [Databricks Serverless Compute](https://docs.databricks.com/serverless-compute/index.html)
- [Unity Catalog Volumes](https://docs.databricks.com/data-governance/unity-catalog/volumes.html)
- [Jobs API 2.1](https://docs.databricks.com/api/workspace/jobs)

## 📝 License

Internal demo for customer engagements.

