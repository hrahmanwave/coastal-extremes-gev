"""Extreme value analysis of coastal water levels from tide gauge records."""

from .download import fetch_coops_hourly, fetch_uhslc_hourly, parse_coops_json, parse_uhslc_csv
from .qc import annual_maxima, completeness_by_year, to_regular_hourly

__version__ = "0.0.1"

__all__ = [
    "annual_maxima",
    "completeness_by_year",
    "fetch_coops_hourly",
    "fetch_uhslc_hourly",
    "parse_coops_json",
    "parse_uhslc_csv",
    "to_regular_hourly",
]
