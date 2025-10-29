#!/bin/bash

# =============================================================================
# Deploy Data Quality Serverless Environment
# =============================================================================
# This script creates a serverless environment for data quality profiling
# with html2text library dependency

set -e

CATALOG_NAME=${1:-"maggiedatabricksterraform_dbw"}
REQUIREMENTS_PATH="/Volumes/${CATALOG_NAME}/synthea/admin_configs/requirements_data_quality_serverless.txt"
ENV_NAME="data_quality_serverless_demo"

echo "=================================="
echo "Deploying Serverless Environment"
echo "=================================="
echo "Environment: ${ENV_NAME}"
echo "Requirements: ${REQUIREMENTS_PATH}"
echo ""

# Check if environment exists
echo "Checking for existing environment..."
EXISTING_ENV=$(databricks workspace-conf get-workspace-conf 2>&1 | grep -c "${ENV_NAME}" || true)

if [ "$EXISTING_ENV" -gt 0 ]; then
    echo "Environment ${ENV_NAME} may already exist. Proceeding with creation/update..."
fi

# Create the serverless environment using Environment Versions API
echo "Creating serverless environment..."

cat > /tmp/dq_serverless_env.json << EOF
{
  "name": "${ENV_NAME}",
  "description": "Serverless environment for data quality profiling with html2text",
  "base_environment_version": 4,
  "dependencies": [
    "-r ${REQUIREMENTS_PATH}"
  ]
}
EOF

# Create environment using Databricks API
RESPONSE=$(databricks api post /api/2.0/compute/environment-versions/create --json @/tmp/dq_serverless_env.json 2>&1)

if [ $? -eq 0 ]; then
    echo "✓ Environment created successfully"
    echo "$RESPONSE" | jq '.'
else
    echo "Response: $RESPONSE"
    echo "Note: Environment may already exist or requires manual creation via UI"
fi

rm /tmp/dq_serverless_env.json

echo ""
echo "=================================="
echo "Deployment Complete"
echo "=================================="

