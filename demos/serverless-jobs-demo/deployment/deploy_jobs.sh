#!/bin/bash

# =============================================================================
# Deploy Databricks Jobs with Environment-Specific Configuration
# =============================================================================
# Usage: ./deploy_jobs.sh [environment]
#   environment: dev|uat|prod (default: current variables.json)
#
# This script:
# 1. Loads environment-specific variables
# 2. Replaces placeholders in job JSON files
# 3. Deploys jobs to Databricks workspace
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get environment parameter
ENVIRONMENT=${1:-""}

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  DATABRICKS JOBS DEPLOYMENT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Determine which variables file to use
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if [ -z "$ENVIRONMENT" ]; then
    VARS_FILE="$PROJECT_ROOT/config/variables.json"
    echo -e "${BLUE}ℹ️  Using default configuration: config/variables.json${NC}"
else
    VARS_FILE="$PROJECT_ROOT/config/variables.${ENVIRONMENT}.json"
    if [ ! -f "$VARS_FILE" ]; then
        echo -e "${RED}✗ Error: Variables file not found: config/variables.${ENVIRONMENT}.json${NC}"
        echo ""
        echo "Available environments:"
        ls "$PROJECT_ROOT/config/variables."*.json 2>/dev/null | xargs -n1 basename | sed 's/variables\.\(.*\)\.json/  - \1/'
        echo ""
        exit 1
    fi
    echo -e "${GREEN}✓ Using ${ENVIRONMENT} configuration: config/variables.${ENVIRONMENT}.json${NC}"
fi

echo ""

# Read variables from JSON
CATALOG_NAME=$(python3 -c "import json; print(json.load(open('$VARS_FILE'))['catalog_name'])")
BASE_VOLUME_PATH=$(python3 -c "import json; print(json.load(open('$VARS_FILE'))['base_volume_path'])")
ADMIN_VOLUME_PATH=$(python3 -c "import json; print(json.load(open('$VARS_FILE'))['admin_volume_path'])")

echo "Configuration:"
echo "  Catalog:           $CATALOG_NAME"
echo "  Base Volume:       $BASE_VOLUME_PATH"
echo "  Admin Volume:      $ADMIN_VOLUME_PATH"
echo ""

# Create temporary directory for processed job files
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  PROCESSING JOB DEFINITIONS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Process each job JSON file
cd "$PROJECT_ROOT/infrastructure/api_jobs"
JOB_COUNT=0

for job_file in *.json; do
    if [ -f "$job_file" ]; then
        # Replace placeholders
        python3 << EOF
import json
import sys

with open('$job_file', 'r') as f:
    content = f.read()

# Replace placeholders
content = content.replace('{{CATALOG_NAME}}', '$CATALOG_NAME')
content = content.replace('{{BASE_VOLUME_PATH}}', '$BASE_VOLUME_PATH')
content = content.replace('{{ADMIN_VOLUME_PATH}}', '$ADMIN_VOLUME_PATH')

# Remove any remaining budget policy placeholders
content = content.replace('"budget_policy_id": "{{USAGE_POLICY_ID}}",', '')

with open('$TEMP_DIR/$job_file', 'w') as f:
    f.write(content)
EOF
        echo "  ✓ Processed: $job_file"
        JOB_COUNT=$((JOB_COUNT + 1))
    fi
done

echo ""
echo "  Total: $JOB_COUNT job definitions processed"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  DEPLOYING JOBS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

DEPLOYED_COUNT=0
FAILED_COUNT=0

for processed_file in $TEMP_DIR/*.json; do
    job_name=$(basename "$processed_file" .json)
    echo "  Deploying: $job_name"
    
    # Create job
    if databricks jobs create --json @"$processed_file" > /dev/null 2>&1; then
        echo -e "    ${GREEN}✓ Success${NC}"
        DEPLOYED_COUNT=$((DEPLOYED_COUNT + 1))
    else
        echo -e "    ${RED}✗ Failed${NC}"
        FAILED_COUNT=$((FAILED_COUNT + 1))
    fi
    echo ""
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  DEPLOYMENT SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Environment:       ${ENVIRONMENT:-default}"
echo "  Catalog:           $CATALOG_NAME"
echo -e "  ${GREEN}Deployed:          $DEPLOYED_COUNT${NC}"
if [ $FAILED_COUNT -gt 0 ]; then
    echo -e "  ${RED}Failed:            $FAILED_COUNT${NC}"
fi
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $FAILED_COUNT -gt 0 ]; then
    exit 1
fi

