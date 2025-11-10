"""HLS External Libraries Bundle - Meta-package for healthcare data processing libraries."""

__version__ = "0.1.0"

# This meta-package bundles the following external libraries:
# - pandas-profiling (ydata-profiling): Automated EDA for data quality
# - missingno: Visualization of missing data patterns  
# - faker: Generate synthetic test data

# Re-export commonly used functions for convenience
try:
    from ydata_profiling import ProfileReport
    __all__ = ['ProfileReport']
except ImportError:
    __all__ = []

