"""Setup configuration for hls_external_libs meta-package."""

from setuptools import setup, find_packages

setup(
    name="hls_external_libs",
    version="0.1.0",
    description="Meta-package bundling external libraries for healthcare data processing",
    author="HLS Demo Team",
    packages=find_packages(),
    python_requires=">=3.8",
    # These external libraries will be installed when this wheel is installed
    install_requires=[
        "ydata-profiling>=4.5.0",  # Automated EDA and data quality profiling
        "missingno>=0.5.0",         # Visualization of missing data patterns
        "Faker>=20.0.0",            # Generate synthetic healthcare test data
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)

