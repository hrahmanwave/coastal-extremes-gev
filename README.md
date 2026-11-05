# coastal-extremes-gev

Extreme value analysis of coastal water levels from tide gauge records.
Download hourly sea level, quality-control it, extract extremes, and fit
GEV (annual maxima) and GPD (peaks over threshold) distributions to estimate return levels.

The goal is a side-by-side comparison of a Bay of Bengal station and a US Gulf Coast station.

> **Status:** early development. Data download and quality control are in place;
> detrending and distribution fitting are next.

## Installation

```bash
git clone https://github.com/hrahmanwave/coastal-extremes-gev.git
cd coastal-extremes-gev
pip install -e ".[dev]"
```

## Usage (so far)

```python
from cextremes import fetch_coops_hourly, to_regular_hourly, completeness_by_year, annual_maxima

s = fetch_coops_hourly("8771450", 1990, 2024)    # Galveston Pier 21, TX (MSL datum)
s = to_regular_hourly(s)
print(completeness_by_year(s).tail())
amax = annual_maxima(s, min_completeness=0.8)
```

Downloads are cached in `data/` (not tracked by git).

## Roadmap

- [x] UHSLC research-quality hourly download
- [x] NOAA CO-OPS hourly download (year-by-year, cached)
- [x] Quality control: regular hourly grid, yearly completeness, annual maxima
- [ ] Remove linear mean sea level trend, compute non-tidal residual
- [ ] GEV fit to annual maxima with bootstrap confidence intervals
- [ ] Peaks over threshold + GPD, threshold selection
- [ ] Return level plots, Bay of Bengal vs. Gulf Coast comparison
- [ ] Non-stationary GEV (time-varying location)

## Data

- University of Hawaii Sea Level Center (UHSLC), research-quality hourly data
- NOAA CO-OPS Tides & Currents, verified hourly heights

## License

MIT
