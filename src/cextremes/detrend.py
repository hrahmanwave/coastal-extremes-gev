"""Remove the long-term mean sea level trend before extreme value analysis.

Sea level rise shifts every year's water levels upward, so annual maxima from the 1990s
and the 2020s are not samples from the same distribution. A stationary GEV fit needs that
drift removed first. The trend is estimated from annual means (complete years only), and
the series is shifted to a reference year so the results describe that year's sea level.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .qc import completeness_by_year


def msl_trend(s: pd.Series, min_completeness: float = 0.8) -> tuple[float, float]:
    """Linear trend of annual mean sea level: (slope in m/year, intercept in m)."""
    comp = completeness_by_year(s)
    good = comp.index[comp >= min_completeness]
    annual_mean = s.groupby(s.index.year).mean().reindex(good).dropna()
    if len(annual_mean) < 5:
        raise ValueError("Need at least 5 complete years to estimate a sea level trend")
    slope, intercept = np.polyfit(annual_mean.index.to_numpy(float), annual_mean.to_numpy(), 1)
    return float(slope), float(intercept)


def detrend(s: pd.Series, ref_year: float | None = None,
            min_completeness: float = 0.8) -> tuple[pd.Series, float]:
    """Remove the linear MSL trend, relative to ``ref_year`` (default: the last year).

    Returns the adjusted series and the trend in m/year.
    """
    slope, _ = msl_trend(s, min_completeness)
    if ref_year is None:
        ref_year = float(s.index.year.max())
    t = s.index.year + (s.index.dayofyear - 0.5) / 365.25
    adjusted = s - slope * (t - ref_year)
    return adjusted.rename(s.name), slope
