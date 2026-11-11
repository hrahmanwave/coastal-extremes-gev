"""Return levels of extreme water level for one NOAA tide gauge.

Steps: download hourly water levels, regular hourly grid, remove the linear mean sea level
trend (relative to the last year), annual maxima from complete years, GEV fit, bootstrap
confidence intervals, and a return level plot.

Usage:
    python scripts/return_levels.py
    python scripts/return_levels.py --station 8771450 --name "Galveston Pier 21, TX" --start 1990 --end 2024

Writes figures/<station>_return_levels.png and figures/<station>_gev.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cextremes import (
    annual_maxima,
    bootstrap_return_levels,
    detrend,
    empirical_return_periods,
    fetch_coops_hourly,
    fit_gev,
    to_regular_hourly,
)

PERIODS = np.array([2, 5, 10, 25, 50, 100])


def make_figure(amax: pd.Series, label: str, slope: float, ref_year: int,
                out_png: Path, n_boot: int = 1000) -> dict:
    fit = fit_gev(amax)
    table = bootstrap_return_levels(amax, periods=PERIODS, n_boot=n_boot)
    curve_t = np.logspace(np.log10(1.05), np.log10(200), 200)
    curve_ci = bootstrap_return_levels(amax, periods=curve_t, n_boot=n_boot)
    emp = empirical_return_periods(amax)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.fill_between(curve_t, curve_ci["lower"], curve_ci["upper"], color="#2f6fa8", alpha=0.18,
                    label="90% bootstrap interval")
    ax.plot(curve_t, fit.return_level(curve_t), color="#2f6fa8", lw=2, label="GEV fit")
    ax.scatter(emp["return_period"], emp["level"], s=18, color="#c07a12", zorder=3,
               label="Observed annual maxima")
    top = amax.sort_values(ascending=False).head(3)
    for year, val in top.items():
        row = emp.loc[(emp["level"] - val).abs().idxmin()]
        ax.annotate(str(year), (row["return_period"], val), textcoords="offset points",
                    xytext=(5, 4), fontsize=8, color="#3d4c5a")
    for T in (10, 50, 100):
        lvl = table.loc[T, "level"]
        ax.axvline(T, color="0.85", lw=0.8, zorder=0)
        ax.text(T, ax.get_ylim()[0], f" {T}-yr\n {lvl:.2f} m", fontsize=8, va="bottom",
                color="#1b2a38")
    ax.set_xscale("log")
    ax.set_xlabel("Return period (years)")
    ax.set_ylabel(f"Water level (m, MSL datum, adjusted to {ref_year})")
    ax.set_title(f"Extreme water levels — {label}\n"
                 f"GEV: ξ = {fit.xi:+.2f}, {fit.n_years} complete years, "
                 f"MSL trend removed ({slope * 1000:+.1f} mm/yr)", fontsize=10)
    ax.grid(alpha=0.3, which="both")
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=150)
    plt.close(fig)

    return {
        "station": label, "ref_year": ref_year, "msl_trend_mm_per_year": round(slope * 1000, 2),
        "gev": {k: round(v, 4) if isinstance(v, float) else v for k, v in fit.as_dict().items()},
        "return_levels_m": {int(T): {c: round(float(table.loc[T, c]), 3) for c in table.columns}
                            for T in PERIODS},
        "largest_annual_maxima": {int(y): round(float(v), 3) for y, v in top.items()},
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--station", default="8771450")
    p.add_argument("--name", default="Galveston Pier 21, TX")
    p.add_argument("--start", type=int, default=1990)
    p.add_argument("--end", type=int, default=2024)
    p.add_argument("--n-boot", type=int, default=1000)
    args = p.parse_args()

    s = to_regular_hourly(fetch_coops_hourly(args.station, args.start, args.end))
    adjusted, slope = detrend(s, ref_year=args.end)
    amax = annual_maxima(adjusted)
    print(f"{len(amax)} complete years, MSL trend {slope * 1000:+.1f} mm/yr")

    out = Path("figures")
    summary = make_figure(amax, args.name, slope, args.end,
                          out / f"{args.station}_return_levels.png", args.n_boot)
    (out / f"{args.station}_gev.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary["return_levels_m"], indent=2))
    print(f"Saved figures/{args.station}_return_levels.png")


if __name__ == "__main__":
    main()
