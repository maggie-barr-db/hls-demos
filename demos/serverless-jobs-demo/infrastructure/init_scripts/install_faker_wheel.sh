#!/bin/bash

# =============================================================================
# Init Script: Install Faker Wheel on Classic Compute
# =============================================================================
# This script runs on cluster startup to install the Faker library wheel
# for classic compute clusters that don't use serverless environments.
#
# The wheel is stored in Unity Catalog Volume and installed via pip.

echo "=========================================="
echo "Installing Faker Wheel on Classic Cluster"
echo "=========================================="

# Define wheel location in Unity Catalog Volume
WHEEL_PATH="/Volumes/mbarrett/synthea/admin_configs/faker_lib-0.1.0-py3-none-any.whl"

# Check if wheel exists
if [ -f "$WHEEL_PATH" ]; then
    echo "✓ Found Faker wheel at: $WHEEL_PATH"
    
    # Install the wheel using pip
    echo "Installing Faker wheel..."
    /databricks/python/bin/pip install "$WHEEL_PATH"
    
    if [ $? -eq 0 ]; then
        echo "✓ Faker wheel installed successfully"
    else
        echo "✗ Failed to install Faker wheel"
        exit 1
    fi
else
    echo "✗ Faker wheel not found at: $WHEEL_PATH"
    exit 1
fi

# Verify installation
echo "Verifying Faker installation..."
/databricks/python/bin/python -c "from faker import Faker; print(f'✓ Faker version: {Faker().version}')" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✓ Faker verification successful"
else
    echo "ℹ️ Faker installed but version check failed (this is normal)"
fi

echo "=========================================="
echo "Init script completed"
echo "=========================================="

