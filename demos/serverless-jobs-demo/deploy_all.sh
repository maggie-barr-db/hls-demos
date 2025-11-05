#!/bin/bash

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Unified Deployment Script for HLS Serverless Jobs Demo
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
#  This script deploys:
#    1. Base environment YAML files to workspace
#    2. API jobs (via Databricks CLI)
#
#  Usage:
#    ./deploy_all.sh [all|envs|api]
#
#  Options:
#    all   - Deploy everything (default)
#    envs  - Only upload base environment YAML files
#    api   - Only deploy API jobs
#
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Deployment mode
DEPLOY_MODE="${1:-all}"

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}${BOLD}  HLS Serverless Jobs Demo - API Deployment${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Deployment mode: ${DEPLOY_MODE}"
echo ""

# Validate deployment mode
if [[ ! "$DEPLOY_MODE" =~ ^(all|envs|api)$ ]]; then
    echo -e "${RED}❌ Error: Invalid deployment mode${NC}"
    echo ""
    echo "Usage: $0 [all|envs|api]"
    echo ""
    echo "Options:"
    echo "  all   - Deploy everything (default)"
    echo "  envs  - Only upload base environment YAML files"
    echo "  api   - Only deploy API jobs"
    exit 1
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Pre-flight Checks
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Pre-flight Checks${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check Databricks CLI
if ! command -v databricks &> /dev/null; then
    echo -e "${RED}❌ Error: Databricks CLI not found${NC}"
    echo "   Install with: pip install databricks-cli"
    exit 1
fi
echo -e "${GREEN}✓${NC} Databricks CLI found"

# Check authentication
if ! databricks auth whoami &> /dev/null; then
    echo -e "${RED}❌ Error: Not authenticated with Databricks${NC}"
    echo "   Run: databricks configure"
    exit 1
fi
echo -e "${GREEN}✓${NC} Authenticated with Databricks"

# Check for required files
if [ ! -f "variables.json" ]; then
    echo -e "${RED}❌ Error: variables.json not found${NC}"
    echo "   Create it from variables.example.json"
    exit 1
fi
echo -e "${GREEN}✓${NC} Configuration file found"

# Read configuration
CATALOG_NAME=$(jq -r '.catalog_name' variables.json)
BASE_VOLUME_PATH=$(jq -r '.base_volume_path' variables.json)

if [ -z "$CATALOG_NAME" ] || [ "$CATALOG_NAME" = "null" ]; then
    echo -e "${RED}❌ Error: catalog_name not set in variables.json${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Configuration valid"

echo ""
echo "Configuration:"
echo "  Catalog: ${CATALOG_NAME}"
echo "  Volume: ${BASE_VOLUME_PATH}"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Function: Deploy Usage Policy
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

deploy_usage_policy() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  Step 0: Usage Policy Setup${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    echo -e "${YELLOW}⚠️  Serverless usage policies must be created via the Databricks UI${NC}"
    echo ""
    echo "📋 To create the usage policy:"
    echo "   1. Go to: Workspace settings → Compute → Serverless usage policies"
    echo "   2. Click 'Create usage policy'"
    echo "   3. Enter name: data_lake_hydration_policy"
    echo "   4. Add tags:"
    echo "      • Key: workload_type, Value: data_lake_hydration"
    echo "      • Key: cost_center, Value: data_engineering"
    echo "   5. Click 'Create'"
    echo "   6. Copy the Policy ID and run:"
    echo "      echo '<policy_id>' > infrastructure/.usage_policy_id"
    echo ""
    
    # Check if policy ID already exists
    if [ -f "infrastructure/.usage_policy_id" ]; then
        POLICY_ID=$(cat infrastructure/.usage_policy_id)
        echo -e "${GREEN}✓${NC} Usage policy ID found: ${POLICY_ID}"
        echo -e "${GREEN}✓${NC} Jobs will be attached to this policy"
    else
        echo -e "${YELLOW}ℹ️  No policy ID found. Jobs will deploy without usage policy.${NC}"
        echo -e "${YELLOW}   Create the policy in UI and redeploy to attach it.${NC}"
        # Create empty file so deployments don't fail
        echo "" > infrastructure/.usage_policy_id
    fi
    echo ""
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Function: Setup Git Repository (one-time)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

setup_git_repo() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  Git Repository Setup${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    echo -e "${YELLOW}ℹ️  This deployment uses Workspace files.${NC}"
    echo ""
    echo "📋 Code Location:"
    echo "   /Workspace/Shared/hls-demos/demos/serverless-jobs-demo"
    echo ""
    echo "💡 To sync code to workspace:"
    echo "   databricks workspace import-dir src \\"
    echo "     /Workspace/Shared/hls-demos/demos/serverless-jobs-demo/src --overwrite"
    echo ""
    echo -e "${GREEN}✓${NC} Jobs will reference code from: /Workspace/Shared/hls-demos"
    echo ""
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Function: Deploy Base Environment YAML Files
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

deploy_base_environments() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  Step 1: Deploy Base Environment YAML Files${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    WORKSPACE_BASE_PATH="/Shared/hls-demos/serverless-jobs-demo"
    
    # Create directory if it doesn't exist
    echo "Creating workspace directory..."
    databricks workspace mkdirs ${WORKSPACE_BASE_PATH} 2>/dev/null || true
    
    # Upload environment YAML files
    cd infrastructure
    
    if [ -f "demo_environment.yml" ]; then
        echo "Uploading demo_environment.yml..."
        databricks workspace import --file demo_environment.yml --format RAW --overwrite ${WORKSPACE_BASE_PATH}/demo_environment.yml
        echo -e "${GREEN}✓${NC} demo_environment.yml uploaded"
        echo "  → ${WORKSPACE_BASE_PATH}/demo_environment.yml"
    fi
    
    if [ -f "base_environment.yml" ]; then
        echo "Uploading base_environment.yml..."
        databricks workspace import --file base_environment.yml --format RAW --overwrite ${WORKSPACE_BASE_PATH}/base_environment.yml
        echo -e "${GREEN}✓${NC} base_environment.yml uploaded"
        echo "  → ${WORKSPACE_BASE_PATH}/base_environment.yml"
    fi
    
    cd ..
    
    echo ""
    echo -e "${YELLOW}📝 To create base environments in UI:${NC}"
    echo "   1. Go to: Workspace settings → Compute → Base environments"
    echo "   2. Click 'Create' and use:"
    echo "      • Name: serverless_environment_demo"
    echo "      • Path: ${WORKSPACE_BASE_PATH}/demo_environment.yml"
    echo ""
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Function: Deploy API Jobs
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

deploy_api_jobs() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  Step 2: Deploy API Jobs${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    echo -e "${YELLOW}ℹ️  Jobs will reference code from Workspace${NC}"
    echo "   Workspace path: /Workspace/Shared/hls-demos/demos/serverless-jobs-demo"
    echo ""
    
    # Read usage policy ID
    USAGE_POLICY_ID=""
    if [ -f "infrastructure/.usage_policy_id" ] && [ -s "infrastructure/.usage_policy_id" ]; then
        USAGE_POLICY_ID=$(cat infrastructure/.usage_policy_id | tr -d '[:space:]')
        if [ -n "$USAGE_POLICY_ID" ]; then
            echo "Using usage policy ID: ${USAGE_POLICY_ID}"
        fi
    fi
    
    if [ -z "$USAGE_POLICY_ID" ]; then
        echo -e "${YELLOW}⚠️  No usage policy ID found. Jobs will deploy without usage policy.${NC}"
    fi
    echo ""
    
    cd infrastructure/api_jobs
    
    for json_file in *.json; do
        if [ -f "$json_file" ]; then
            job_name=$(jq -r '.name' "$json_file")
            echo "Deploying: ${job_name}"
            
            # If no policy ID, remove the budget_policy_id field from JSON
            if [ -z "$USAGE_POLICY_ID" ]; then
                job_json=$(cat "$json_file" | jq 'del(.budget_policy_id)')
            else
                # Replace {{USAGE_POLICY_ID}} placeholder with actual policy ID
                job_json=$(cat "$json_file" | sed "s/{{USAGE_POLICY_ID}}/$USAGE_POLICY_ID/g")
            fi
            
            # Check if job already exists
            existing_job_id=$(databricks jobs list --output json 2>/dev/null | \
                jq -r --arg name "$job_name" '.[] | select(.settings.name == $name) | .job_id' | head -n 1)
            
            if [ -n "$existing_job_id" ]; then
                echo "  → Deleting existing job (ID: $existing_job_id)"
                databricks jobs delete $existing_job_id 2>&1 > /dev/null
                echo "  → Creating new job"
                result=$(echo "$job_json" | databricks jobs create --json @/dev/stdin 2>&1)
                if [ $? -eq 0 ]; then
                    new_job_id=$(echo "$result" | jq -r '.job_id')
                    echo -e "  ${GREEN}✓${NC} Created successfully (ID: $new_job_id)"
                else
                    echo -e "  ${RED}✗${NC} Failed: $result"
                fi
            else
                echo "  → Creating new job"
                result=$(echo "$job_json" | databricks jobs create --json @/dev/stdin 2>&1)
                if [ $? -eq 0 ]; then
                    new_job_id=$(echo "$result" | jq -r '.job_id')
                    echo -e "  ${GREEN}✓${NC} Created successfully (ID: $new_job_id)"
                else
                    echo -e "  ${RED}✗${NC} Failed: $result"
                fi
            fi
            echo ""
        fi
    done
    
    cd ../..
    
    echo -e "${GREEN}✓${NC} API jobs deployed successfully"
    echo ""
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Main Deployment Logic
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Show Git setup info first
setup_git_repo

case "$DEPLOY_MODE" in
    all)
        deploy_usage_policy
        deploy_base_environments
        deploy_api_jobs
        ;;
    envs)
        deploy_base_environments
        ;;
    api)
        deploy_api_jobs
        ;;
esac

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Deployment Complete
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}${BOLD}  ✓ Deployment Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ "$DEPLOY_MODE" = "all" ] || [ "$DEPLOY_MODE" = "envs" ]; then
    echo "📋 Next Steps:"
    echo "   Create base environments in Databricks UI using uploaded YAML files"
    echo ""
fi

echo "🔗 Quick Links:"
echo "   • View jobs: databricks jobs list"
echo "   • View workspace files: databricks workspace ls /Shared/hls-demos/serverless-jobs-demo"
echo ""
echo "📊 To run a job:"
echo "   databricks jobs run-now --job-id <JOB_ID>"
echo ""

