"""Generalized extreme value (GEV) fits to annual maxima, return levels and uncertainty.

Sign convention: ``xi`` is the usual GEV shape parameter (xi > 0 heavy upper tail,
xi = 0 Gumbel, xi < 0 bounded upper tail). SciPy's ``genextreme`` uses c = -xi.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

DEFAULT_PERIODS = (2, 5, 10, 25, 50, 100)


@dataclass
class GEVFit:
    loc: float
    scale: float
    xi: float
    n_years: int

    def return_level(self, period: float | np.ndarray) -> np.ndarray:
        """Water level exceeded on average once every ``period`` years."""
        p = 1 - 1 / np.asarray(period, dtype=float)
        return stats.genextreme.ppf(p, -self.xi, loc=self.loc, scale=self.scale)

    def as_dict(self) -> dict:
        return {"loc": self.loc, "scale": self.scale, "xi": self.xi, "n_years": self.n_years}


def fit_gev(annual_max: pd.Series | np.ndarray) -> GEVFit:
    """Maximum likelihood GEV fit.

    Starts from Gumbel moment estimates, which keeps the optimiser stable for the short
    records (20-50 years) typical of tide gauges.
    """
    x = np.asarray(annual_max, dtype=float)
    x = x[~np.isnan(x)]
    if len(x) < 10:
        raise ValueError("Need at least 10 annual maxima for a GEV fit")
    scale0 = x.std() * np.sqrt(6) / np.pi
    loc0 = x.mean() - 0.5772 * scale0
    c, loc, scale = stats.genextreme.fit(x, 0.0, loc=loc0, scale=scale0)
    return GEVFit(loc=float(loc), scale=float(scale), xi=float(-c), n_years=len(x))


def bootstrap_return_levels(
    annual_max: pd.Series | np.ndarray,
    periods=DEFAULT_PERIODS,
    n_boot: int = 1000,
    ci: float = 0.90,
    seed: int = 0,
) -> pd.DataFrame:
    """Return levels with nonparametric bootstrap confidence intervals.

    Annual maxima are resampled with replacement and refitted; the interval is the spread
    of the refitted return levels. Rows are return periods; columns: level, lower, upper.
    """
    x = np.asarray(annual_max, dtype=float)
    x = x[~np.isnan(x)]
    rng = np.random.default_rng(seed)
    periods = np.asarray(periods, dtype=float)
    best = fit_gev(x).return_level(periods)
    samples = []
    for _ in range(n_boot):
        try:
            samples.append(fit_gev(rng.choice(x, size=len(x), replace=True)).return_level(periods))
        except (ValueError, RuntimeError):
            continue
    samples = np.array(samples)
    a = (1 - ci) / 2
    return pd.DataFrame({
        "level": best,
        "lower": np.quantile(samples, a, axis=0),
        "upper": np.quantile(samples, 1 - a, axis=0),
    }, index=pd.Index(periods, name="return_period_years"))


def empirical_return_periods(annual_max: pd.Series | np.ndarray) -> pd.DataFrame:
    """Observed maxima with Gringorten plotting positions, for plotting against the fit."""
    x = np.sort(np.asarray(annual_max, dtype=float)[~np.isnan(annual_max)])[::-1]
    n = len(x)
    rank = np.arange(1, n + 1)
    exceed_prob = (rank - 0.44) / (n + 0.12)
    return pd.DataFrame({"level": x, "return_period": 1 / exceed_prob})
