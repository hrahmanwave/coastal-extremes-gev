"""Download hourly sea level from UHSLC and NOAA CO-OPS.

All functions return a pandas Series of sea level in metres, indexed by UTC time,
named ``sea_level_m``. Missing values are NaN.
"""

from __future__ import annotations

import io
import warnings
from pathlib import Path

import pandas as pd
import requests

UHSLC_HOURLY_URL = "https://uhslc.soest.hawaii.edu/data/csv/rqds/global/hourly/h{station:03d}a.csv"
UHSLC_MISSING = -32767

COOPS_URL = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
APPLICATION_NAME = "coastal-extremes-gev"


# ---------------------------------------------------------------- UHSLC
def parse_uhslc_csv(text: str) -> pd.Series:
    """Parse a UHSLC research-quality hourly CSV (year, month, day, hour, sea level in mm)."""
    df = pd.read_csv(
        io.StringIO(text),
        header=None,
        names=["year", "month", "day", "hour", "sea_level_mm"],
        skipinitialspace=True,
    )
    time = pd.to_datetime(df[["year", "month", "day", "hour"]])
    level = df["sea_level_mm"].where(df["sea_level_mm"] != UHSLC_MISSING).astype(float) / 1000.0
    return pd.Series(level.to_numpy(), index=pd.DatetimeIndex(time, name="time"), name="sea_level_m")


def fetch_uhslc_hourly(station: int, cache_dir: str | Path = "data") -> pd.Series:
    """Download (or read from cache) the UHSLC research-quality hourly record for ``station``.

    Levels are relative to the station's own datum (not mean sea level).
    """
    cache = Path(cache_dir) / f"uhslc_h{station:03d}a.csv"
    if cache.exists():
        text = cache.read_text()
    else:
        resp = requests.get(UHSLC_HOURLY_URL.format(station=station), timeout=120)
        resp.raise_for_status()
        text = resp.text
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(text)
    return parse_uhslc_csv(text)


# ---------------------------------------------------------------- NOAA CO-OPS
def parse_coops_json(payload: dict) -> pd.Series:
    """Parse a CO-OPS ``hourly_height`` JSON response."""
    if "error" in payload:
        raise ValueError(payload["error"].get("message", "CO-OPS returned an error"))
    records = payload.get("data", [])
    if not records:
        return pd.Series(dtype=float, name="sea_level_m",
                         index=pd.DatetimeIndex([], name="time"))
    df = pd.DataFrame(records)
    time = pd.to_datetime(df["t"], format="%Y-%m-%d %H:%M")
    level = pd.to_numeric(df["v"], errors="coerce")
    return pd.Series(level.to_numpy(), index=pd.DatetimeIndex(time, name="time"), name="sea_level_m")


def fetch_coops_hourly(
    station: str,
    start_year: int,
    end_year: int,
    datum: str = "MSL",
    cache_dir: str | Path = "data",
) -> pd.Series:
    """Download NOAA CO-OPS verified hourly heights, one year per request (API limit).

    Years with no data are skipped with a warning. Each year is cached as CSV.
    """
    if end_year < start_year:
        raise ValueError("end_year must be >= start_year")
    parts = []
    for year in range(start_year, end_year + 1):
        cache = Path(cache_dir) / f"coops_{station}_{datum}_{year}.csv"
        if cache.exists():
            s = pd.read_csv(cache, index_col="time", parse_dates=["time"])["sea_level_m"]
        else:
            params = {
                "product": "hourly_height",
                "application": APPLICATION_NAME,
                "begin_date": f"{year}0101",
                "end_date": f"{year}1231",
                "datum": datum,
                "station": station,
                "time_zone": "GMT",
                "units": "metric",
                "format": "json",
            }
            resp = requests.get(COOPS_URL, params=params, timeout=120)
            resp.raise_for_status()
            try:
                s = parse_coops_json(resp.json())
            except ValueError as err:
                warnings.warn(f"{station} {year}: {err}", stacklevel=2)
                continue
            cache.parent.mkdir(parents=True, exist_ok=True)
            s.to_csv(cache)
        parts.append(s)
    if not parts:
        raise ValueError(f"No data returned for station {station}, {start_year}-{end_year}")
    out = pd.concat(parts).sort_index()
    return out[~out.index.duplicated(keep="first")]
