import numpy as np
import pytest

from cextremes.download import parse_coops_json, parse_uhslc_csv

UHSLC_TEXT = """2000,1,1,0,1520
2000,1,1,1,1610
2000,1,1,2,-32767
"""


def test_parse_uhslc_converts_mm_and_missing():
    s = parse_uhslc_csv(UHSLC_TEXT)
    assert len(s) == 3
    assert s.iloc[0] == pytest.approx(1.52)
    assert np.isnan(s.iloc[2])
    assert str(s.index[1]) == "2000-01-01 01:00:00"


def test_parse_coops_json():
    payload = {"data": [
        {"t": "2020-01-01 00:00", "v": "0.321", "s": "0.003", "f": "0,0"},
        {"t": "2020-01-01 01:00", "v": "", "s": "", "f": "0,0"},
    ]}
    s = parse_coops_json(payload)
    assert s.iloc[0] == pytest.approx(0.321)
    assert np.isnan(s.iloc[1])


def test_parse_coops_error():
    with pytest.raises(ValueError, match="No data"):
        parse_coops_json({"error": {"message": "No data was found."}})
