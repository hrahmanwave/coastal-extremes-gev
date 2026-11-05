"""Quality control for hourly sea level series."""

from __future__ import annotations

import pandas as pd


def to_regular_hourly(s: pd.Series) -> pd.Series:
    """Put the series on a regular hourly grid; gaps become NaN."""
    return s.sort_index().resample("h").mean()


def completeness_by_year(s: pd.Series) -> pd.Series:
    """Fraction of a full calendar year's hours that have valid data, per year."""
    valid = s.dropna()
    counts = valid.groupby(valid.index.year).size()
    years = range(s.index.year.min(), s.index.year.max() + 1)
    expected = pd.Series(
        {y: 8784 if pd.Timestamp(year=y, month=1, day=1).is_leap_year else 8760 for y in years}
    )
    frac = (counts.reindex(expected.index, fill_value=0) / expected).rename("completeness")
    frac.index.name = "year"
    return frac


def annual_maxima(s: pd.Series, min_completeness: float = 0.8) -> pd.Series:
    """Annual maximum water level, keeping only years with enough valid data.

    A year with large gaps can miss its true maximum, which biases a GEV fit low,
    so years below ``min_completeness`` are dropped.
    """
    if not 0 < min_completeness <= 1:
        raise ValueError("min_completeness must be in (0, 1]")
    comp = completeness_by_year(s)
    good_years = comp.index[comp >= min_completeness]
    amax = s.groupby(s.index.year).max()
    amax = amax.reindex(good_years).dropna().rename("annual_max_m")
    amax.index.name = "year"
    return amax
