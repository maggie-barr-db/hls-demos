#!/bin/bash

# Script to deploy a custom Databricks serverless environment with custom libraries
# Usage: ./deploy_environment.sh [environment_name] [catalog_name]

set -e  # Exit on error

# Configuration
ENV_NAME="${1:-serverless_environment_demo}"
CATALOG_NAME="${2:-}"
DISPLAY_NAME="Serverless Environment with Custom Libraries"
CLIENT_VERSION="4"
REQUIREMENTS_FILE="requirements.txt"
VOLUME_NAME="admin_configs"
VOLUME_PATH=""

echo "================================================="
echo "Deploying Serverless Environment with UC Volume"
echo "================================================="
echo "Environment Name: ${ENV_NAME}"
echo "Display Name: ${DISPLAY_NAME}"
echo "Client Version: ${CLIENT_VERSION}"
echo "Requirements File: ${REQUIREMENTS_FILE}"
echo ""

# Check if databricks CLI is installed
if ! command -v databricks &> /dev/null; then
    echo "❌ Error: Databricks CLI not found. Please install it first."
    echo "   pip install databricks-cli"
    exit 1
fi

# Check if requirements.txt exists
if [ ! -f "${REQUIREMENTS_FILE}" ]; then
    echo "❌ Error: ${REQUIREMENTS_FILE} not found in current directory"
    exit 1
fi

# Check authentication
echo "🔍 Checking authentication..."
if ! databricks auth whoami &> /dev/null; then
    echo "❌ Error: Not authenticated with Databricks."
    echo "   Run: databricks configure"
    exit 1
fi

echo "✅ Authentication successful"
echo ""

# Get catalog name if not provided
if [ -z "$CATALOG_NAME" ]; then
    if [ -f "variables.json" ]; then
        echo "📋 Reading catalog name from variables.json..."
        CATALOG_NAME=$(jq -r '.catalog_name' variables.json 2>/dev/null || echo "")
    fi
    
    if [ -z "$CATALOG_NAME" ]; then
        echo "❌ Error: Catalog name not provided and not found in variables.json"
        echo "   Usage: ./deploy_environment.sh [environment_name] [catalog_name]"
        echo "   Or add catalog_name to variables.json"
        exit 1
    fi
fi

echo "📦 Using catalog: ${CATALOG_NAME}"
echo ""

# Set volume path
SCHEMA_NAME="synthea"
VOLUME_PATH="/Volumes/${CATALOG_NAME}/${SCHEMA_NAME}/${VOLUME_NAME}"

# Check if volume exists, create if it doesn't
echo "🔍 Checking if volume exists..."
VOLUME_CHECK=$(databricks api get "/api/2.1/unity-catalog/volumes/${CATALOG_NAME}/${SCHEMA_NAME}/${VOLUME_NAME}" 2>&1 || echo "not_found")

if echo "$VOLUME_CHECK" | grep -q "RESOURCE_DOES_NOT_EXIST\|not_found"; then
    echo "📦 Volume doesn't exist. Creating volume: ${VOLUME_PATH}"
    
    # Create the volume
    CREATE_RESPONSE=$(databricks api post /api/2.1/unity-catalog/volumes \
      --json "{
        \"catalog_name\": \"${CATALOG_NAME}\",
        \"schema_name\": \"${SCHEMA_NAME}\",
        \"name\": \"${VOLUME_NAME}\",
        \"volume_type\": \"MANAGED\",
        \"comment\": \"Volume for admin configurations and custom libraries\"
      }" 2>&1) || true
    
    if echo "$CREATE_RESPONSE" | grep -q "error_code"; then
        echo "❌ Error creating volume:"
        echo "$CREATE_RESPONSE"
        exit 1
    fi
    
    echo "✅ Volume created successfully"
else
    echo "✅ Volume already exists"
fi

echo ""

# Upload requirements.txt to the volume
echo "📤 Uploading ${REQUIREMENTS_FILE} to ${VOLUME_PATH}/${REQUIREMENTS_FILE}..."

# Use dbfs cp to upload the file
databricks fs cp "${REQUIREMENTS_FILE}" "dbfs:${VOLUME_PATH}/${REQUIREMENTS_FILE}" --overwrite

echo "✅ Requirements file uploaded successfully"
echo ""

# Construct dependencies array with volume path
DEPENDENCIES="[\"-r ${VOLUME_PATH}/${REQUIREMENTS_FILE}\"]"

# Create the environment using Databricks API
echo "📦 Creating serverless environment..."

RESPONSE=$(databricks api post /api/2.0/serverless-compute/environments \
  --json "{
    \"name\": \"${ENV_NAME}\",
    \"display_name\": \"${DISPLAY_NAME}\",
    \"client\": \"${CLIENT_VERSION}\",
    \"dependencies\": ${DEPENDENCIES}
  }" 2>&1) || true

# Check if creation was successful
if echo "$RESPONSE" | grep -q "error_code"; then
    ERROR_CODE=$(echo "$RESPONSE" | grep -o '"error_code":"[^"]*"' | cut -d'"' -f4)
    ERROR_MSG=$(echo "$RESPONSE" | grep -o '"message":"[^"]*"' | cut -d'"' -f4)
    
    if [[ "$ERROR_CODE" == "RESOURCE_ALREADY_EXISTS" ]]; then
        echo "⚠️  Environment '${ENV_NAME}' already exists. Updating dependencies..."
        
        # Get environment ID
        ENV_ID=$(databricks api get /api/2.0/serverless-compute/environments \
          | jq -r ".environments[] | select(.name==\"${ENV_NAME}\") | .environment_id")
        
        if [ -z "$ENV_ID" ]; then
            echo "❌ Error: Could not find environment ID"
            exit 1
        fi
        
        # Update the environment
        databricks api patch "/api/2.0/serverless-compute/environments/${ENV_ID}" \
          --json "{
            \"dependencies\": ${DEPENDENCIES}
          }"
        
        echo "✅ Environment updated successfully!"
    else
        echo "❌ Error creating environment:"
        echo "   Error Code: ${ERROR_CODE}"
        echo "   Message: ${ERROR_MSG}"
        exit 1
    fi
else
    echo "✅ Environment created successfully!"
fi

echo ""
echo "================================================="
echo "Deployment Complete!"
echo "================================================="
echo ""
echo "📋 Environment Details:"
echo "   Name: ${ENV_NAME}"
echo "   Display Name: ${DISPLAY_NAME}"
echo "   Client: ${CLIENT_VERSION}"
echo "   Requirements File: ${VOLUME_PATH}/${REQUIREMENTS_FILE}"
echo ""
echo "📦 Volume Details:"
echo "   Volume Path: ${VOLUME_PATH}"
echo "   Catalog: ${CATALOG_NAME}"
echo "   Schema: ${SCHEMA_NAME}"
echo ""
echo "📚 Libraries Installed:"
echo "   - polars (DataFrame library)"
echo "   - duckdb (SQL engine)"
echo "   - pyarrow (columnar data)"
echo "   - great-expectations (data validation)"
echo "   - pandera (statistical validation)"
echo "   - hl7apy, fhir.resources (healthcare data)"
echo "   - scikit-learn, statsmodels (ML/stats)"
echo "   - And more... (see requirements.txt)"
echo ""
echo "🎯 Next Steps:"
echo "   1. View in UI: Compute → Environments"
echo "   2. Reference in jobs: environment_key: ${ENV_NAME}"
echo "   3. Use in notebooks: Select from environment dropdown"
echo "   4. Update requirements.txt and re-run to add more libraries"
echo ""

