import numpy as np
import pandas as pd
import pytest
from scipy import stats

from cextremes.detrend import detrend, msl_trend
from cextremes.fit import bootstrap_return_levels, empirical_return_periods, fit_gev

TRUE = {"loc": 1.2, "scale": 0.25, "xi": 0.1}


def sample(n, seed=0):
    return stats.genextreme.rvs(-TRUE["xi"], loc=TRUE["loc"], scale=TRUE["scale"],
                                size=n, random_state=seed)


def test_fit_recovers_parameters_with_long_record():
    fit = fit_gev(sample(2000))
    assert fit.loc == pytest.approx(TRUE["loc"], abs=0.03)
    assert fit.scale == pytest.approx(TRUE["scale"], abs=0.03)
    assert fit.xi == pytest.approx(TRUE["xi"], abs=0.06)


def test_return_levels_increase_with_period():
    rl = fit_gev(sample(60)).return_level([2, 10, 100])
    assert np.all(np.diff(rl) > 0)


def test_bootstrap_interval_brackets_truth():
    x = sample(40, seed=3)
    df = bootstrap_return_levels(x, periods=[10, 50], n_boot=300, seed=1)
    truth = stats.genextreme.ppf(1 - 1 / np.array([10, 50]), -TRUE["xi"],
                                 loc=TRUE["loc"], scale=TRUE["scale"])
    assert (df["lower"].to_numpy() < truth).all() and (truth < df["upper"].to_numpy()).all()
    assert (df["lower"] < df["level"]).all() and (df["level"] < df["upper"]).all()


def test_too_short_record_rejected():
    with pytest.raises(ValueError):
        fit_gev(sample(5))


def test_empirical_positions_sorted():
    e = empirical_return_periods(np.array([1.0, 3.0, 2.0]))
    assert e["level"].tolist() == [3.0, 2.0, 1.0]
    assert e["return_period"].is_monotonic_decreasing


def make_hourly(slope=0.004, years=(2000, 2019)):
    idx = pd.date_range(f"{years[0]}-01-01", f"{years[1]}-12-31 23:00", freq="h")
    t = idx.year + (idx.day_of_year - 0.5) / 365.25
    tide = 0.5 * np.sin(2 * np.pi * np.arange(len(idx)) / 12.42)
    return pd.Series(slope * (t - years[0]) + tide, index=idx)


def test_trend_estimated_and_removed():
    s = make_hourly(slope=0.004)
    slope, _ = msl_trend(s)
    assert slope == pytest.approx(0.004, abs=2e-4)
    adjusted, _ = detrend(s, ref_year=2019)
    annual = adjusted.groupby(adjusted.index.year).mean()
    assert abs(np.polyfit(annual.index, annual.values, 1)[0]) < 2e-4
    # later years unchanged near the reference year, earlier years raised
    assert adjusted["2019"].mean() == pytest.approx(s["2019"].mean(), abs=0.003)
    assert adjusted["2000"].mean() > s["2000"].mean() + 0.06
