#!/bin/bash

# =============================================================================
# Init Script: Install html2text on Classic Compute
# =============================================================================
# This script runs on cluster startup to install the html2text library
# for data quality and testing workloads on classic compute clusters.
#
# html2text is used for parsing HTML content from healthcare documentation.

echo "=========================================="
echo "Installing html2text on Classic Cluster"
echo "=========================================="

echo ""
echo "Installing html2text library..."

# Install html2text using pip
/databricks/python/bin/pip install html2text>=2020.1.16 --quiet

if [ $? -eq 0 ]; then
    echo "✓ html2text installed successfully"
else
    echo "✗ Failed to install html2text"
    exit 1
fi

# Verify installation
echo ""
echo "Verifying html2text installation..."
/databricks/python/bin/python -c "import html2text; print('✓ html2text available - version:', html2text.__version__ if hasattr(html2text, '__version__') else 'unknown')" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✓ html2text verification successful"
else
    echo "✗ html2text verification failed"
    exit 1
fi

echo ""
echo "=========================================="
echo "Init script completed"
echo "=========================================="

