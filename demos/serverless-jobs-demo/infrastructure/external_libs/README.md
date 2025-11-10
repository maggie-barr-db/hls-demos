# External Libraries

This directory contains custom Python wheel packages used across the HLS demo.

## Structure

```
external_libs/
├── hls_external_libs/     # Meta-package with multiple libraries
│   ├── setup.py
│   ├── dist/              # Built wheel
│   └── README.md
└── faker_wheel/           # Standalone Faker library wheel
    ├── setup.py
    ├── dist/              # Built wheel
    └── README.md
```

## Packages

### 1. hls_external_libs

**Location**: `hls_external_libs/dist/hls_external_libs-0.1.0-py3-none-any.whl`

A meta-package that bundles multiple data science libraries:
- `ydata-profiling` - Advanced data profiling
- `missingno` - Missing data visualization
- `Faker` - Fake data generation

**Usage**:
- Installed in serverless environments via `requirements.txt`
- Uploaded to Unity Catalog Volume: `/Volumes/.../admin_configs/hls_external_libs-0.1.0-py3-none-any.whl`

### 2. faker_wheel

**Location**: `faker_wheel/dist/faker_lib-0.1.0-py3-none-any.whl`

A lightweight package containing only the Faker library.

**Usage**:
- Installed on classic compute clusters via init script
- Uploaded to Unity Catalog Volume: `/Volumes/.../admin_configs/faker_lib-0.1.0-py3-none-any.whl`
- Init script: `infrastructure/init_scripts/install_faker_wheel.sh`

## Building Wheels

### hls_external_libs
```bash
cd infrastructure/external_libs/hls_external_libs
python3 setup.py bdist_wheel
```

### faker_wheel
```bash
cd infrastructure/external_libs/faker_wheel
python3 setup.py bdist_wheel
```

## Deployment

After building, upload wheels to Unity Catalog Volume:

```bash
# hls_external_libs
databricks fs cp infrastructure/external_libs/hls_external_libs/dist/hls_external_libs-0.1.0-py3-none-any.whl \
  dbfs:/Volumes/maggiedatabricksterraform_dbw/synthea/admin_configs/hls_external_libs-0.1.0-py3-none-any.whl \
  --overwrite

# faker_wheel
databricks fs cp infrastructure/external_libs/faker_wheel/dist/faker_lib-0.1.0-py3-none-any.whl \
  dbfs:/Volumes/maggiedatabricksterraform_dbw/synthea/admin_configs/faker_lib-0.1.0-py3-none-any.whl \
  --overwrite
```

## Why Two Separate Wheels?

1. **hls_external_libs**: Used in serverless environments where we can leverage `requirements.txt` with UC Volumes
2. **faker_wheel**: Used in classic compute via init scripts to demonstrate alternative installation methods

This separation demonstrates different deployment patterns for custom libraries in Databricks.

