#!/bin/bash

# Databricks Jobs API Deployment Script
# This script deploys the serverless jobs using the Databricks Jobs API

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Databricks CLI is configured
if ! command -v databricks &> /dev/null; then
    echo -e "${RED}Error: Databricks CLI is not installed${NC}"
    echo "Install with: pip install databricks-cli"
    exit 1
fi

# Check authentication
if ! databricks auth whoami &> /dev/null; then
    echo -e "${RED}Error: Databricks CLI is not authenticated${NC}"
    echo "Run: databricks auth login --host https://your-workspace.cloud.databricks.com"
    exit 1
fi

echo -e "${GREEN}=== Databricks Jobs API Deployment ===${NC}\n"

# Function to deploy a job
deploy_job() {
    local json_file=$1
    local job_name=$(jq -r '.name' "$json_file")
    
    echo -e "${YELLOW}Deploying: ${job_name}${NC}"
    
    # Check if job already exists
    existing_job_id=$(databricks jobs list --output json 2>/dev/null | \
        jq -r --arg name "$job_name" '.[] | select(.settings.name == $name) | .job_id' | head -n 1)
    
    if [ -n "$existing_job_id" ]; then
        echo "  → Job already exists with ID: $existing_job_id"
        read -p "  → Do you want to update it? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "  → Updating job..."
            databricks jobs reset --job-id "$existing_job_id" --json @"$json_file"
            echo -e "  ${GREEN}✓ Updated successfully${NC}\n"
        else
            echo -e "  ${YELLOW}⊘ Skipped${NC}\n"
        fi
    else
        echo "  → Creating new job..."
        job_id=$(databricks jobs create --json @"$json_file" | jq -r '.job_id')
        echo -e "  ${GREEN}✓ Created successfully with ID: ${job_id}${NC}\n"
    fi
}

# Deploy all jobs
echo "Found the following job definitions:"
ls -1 *.json | nl
echo

read -p "Deploy all jobs? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

echo

# Deploy Python script jobs
if [ -f "daily_bronze_ingestion_incr_py_serverless_api.json" ]; then
    deploy_job "daily_bronze_ingestion_incr_py_serverless_api.json"
fi

if [ -f "daily_silver_load_incr_py_serverless_api.json" ]; then
    deploy_job "daily_silver_load_incr_py_serverless_api.json"
fi

# Deploy Notebook jobs
if [ -f "daily_bronze_ingestion_incr_nb_serverless_api.json" ]; then
    deploy_job "daily_bronze_ingestion_incr_nb_serverless_api.json"
fi

if [ -f "daily_silver_load_incr_nb_serverless_api.json" ]; then
    deploy_job "daily_silver_load_incr_nb_serverless_api.json"
fi

echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo
echo "View your jobs in Databricks workspace at: Compute → Jobs"
echo
echo "To run a job:"
echo "  databricks jobs run-now --job-id <job_id>"
echo
echo "To list all jobs:"
echo "  databricks jobs list"

