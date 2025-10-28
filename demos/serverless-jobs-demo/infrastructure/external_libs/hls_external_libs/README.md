# HLS External Libraries Bundle

Meta-package that bundles external libraries useful for healthcare data processing.

## Included Libraries

This wheel installs the following external PyPI packages:

1. **ydata-profiling** (formerly pandas-profiling) - Automated exploratory data analysis
   - Generate comprehensive data quality reports
   - Identify missing data, duplicates, correlations
   - Statistical summaries and visualizations

2. **missingno** - Missing data visualization
   - Matrix visualizations of missing data patterns
   - Heatmaps and dendrograms
   - Understand data completeness

3. **Faker** - Synthetic data generation
   - Generate realistic test data for healthcare scenarios
   - Names, addresses, dates, medical codes
   - Useful for testing pipelines without PHI

## Installation

```bash
pip install hls_external_libs-0.1.0-py3-none-any.whl
```

This single wheel file will install all three external libraries and their dependencies.

## Usage

```python
# Data profiling
import pandas as pd
from ydata_profiling import ProfileReport

df = spark.table("catalog.schema.table").toPandas()
profile = ProfileReport(df, title="Data Quality Report")
profile.to_file("report.html")

# Missing data visualization
import missingno as msno
import matplotlib.pyplot as plt

msno.matrix(df)
plt.savefig("missing_data.png")

# Generate synthetic data
from faker import Faker

fake = Faker()
fake.name()  # Generate random name
fake.date_of_birth()  # Generate random DOB
fake.address()  # Generate random address
```

## Why Bundle These?

- **Single dependency reference**: One wheel installs multiple libraries
- **Version control**: Pin all libraries together for consistency
- **Simplified deployment**: Upload one wheel file to UC volume
- **Common healthcare use cases**: Data quality, testing, analysis

