# Faker Library Wheel

This wheel package provides the Faker library for generating fake data in HLS demos.

## Contents

- **Faker**: Python library for generating fake data (names, addresses, dates, etc.)

## Installation

This wheel is automatically installed on classic compute clusters via init script.

## Usage

```python
from faker import Faker

fake = Faker()
print(fake.name())
print(fake.address())
```

## Build Instructions

To rebuild the wheel:

```bash
cd faker_wheel
python setup.py bdist_wheel
```

The wheel will be available in the `dist/` directory.

