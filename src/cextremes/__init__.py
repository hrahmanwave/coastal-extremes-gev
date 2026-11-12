"""Extreme value analysis of coastal water levels from tide gauge records."""

from .detrend import detrend, msl_trend
from .download import fetch_coops_hourly, fetch_uhslc_hourly, parse_coops_json, parse_uhslc_csv
from .fit import GEVFit, bootstrap_return_levels, empirical_return_periods, fit_gev
from .qc import annual_maxima, completeness_by_year, to_regular_hourly

__version__ = "0.0.1"

__all__ = [
    "GEVFit",
    "annual_maxima",
    "bootstrap_return_levels",
    "completeness_by_year",
    "detrend",
    "empirical_return_periods",
    "fetch_coops_hourly",
    "fetch_uhslc_hourly",
    "fit_gev",
    "msl_trend",
    "parse_coops_json",
    "parse_uhslc_csv",
    "to_regular_hourly",
]
