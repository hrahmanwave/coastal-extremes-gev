import numpy as np
import pandas as pd
import pytest

from cextremes.qc import annual_maxima, completeness_by_year, to_regular_hourly


def make_series():
    idx = pd.date_range("2001-01-01", "2003-12-31 23:00", freq="h")
    s = pd.Series(np.sin(np.arange(len(idx)) / 12.42 * 2 * np.pi), index=idx)
    s[s.index.year == 2002] = np.nan          # 2002 almost empty
    s[(s.index.year == 2002) & (s.index.month == 1)] = 0.5
    s["2003-06-01 00:00"] = 3.0               # a clear extreme
    return s


def test_completeness():
    comp = completeness_by_year(make_series())
    assert comp[2001] == pytest.approx(1.0)
    assert comp[2002] < 0.1


def test_annual_maxima_drops_incomplete_years():
    amax = annual_maxima(make_series())
    assert list(amax.index) == [2001, 2003]
    assert amax[2003] == pytest.approx(3.0)


def test_regular_hourly_fills_gaps():
    idx = pd.to_datetime(["2020-01-01 00:00", "2020-01-01 03:00"])
    s = to_regular_hourly(pd.Series([1.0, 2.0], index=idx))
    assert len(s) == 4 and s.isna().sum() == 2


def test_bad_threshold():
    with pytest.raises(ValueError):
        annual_maxima(make_series(), min_completeness=0)
