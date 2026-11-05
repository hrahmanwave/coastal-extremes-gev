"""Plot annual maximum water levels and data completeness for one NOAA station.

Usage:
    python scripts/plot_annual_maxima.py
    python scripts/plot_annual_maxima.py --station 8771450 --name "Galveston Pier 21, TX" --start 1990 --end 2024

Output: figures/<station>_annual_maxima.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cextremes import (
    annual_maxima,
    completeness_by_year,
    fetch_coops_hourly,
    to_regular_hourly,
)


def make_figure(s: pd.Series, station_label: str, out: Path, min_completeness: float = 0.8) -> Path:
    s = to_regular_hourly(s)
    comp = completeness_by_year(s)
    amax = annual_maxima(s, min_completeness=min_completeness)
    if len(amax) < 3:
        raise ValueError("Fewer than 3 complete years; cannot plot a trend")

    years = amax.index.to_numpy(dtype=float)
    slope, intercept = np.polyfit(years, amax.to_numpy(), 1)

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(9, 5.6), sharex=True, gridspec_kw={"height_ratios": [3, 1]}
    )
    # reindex to every year so the line breaks at excluded years instead of bridging them
    amax_full = amax.reindex(range(comp.index.min(), comp.index.max() + 1))
    ax1.plot(amax_full.index, amax_full.values, "o-", color="#2f6fa8", lw=1.2, ms=4, label="Annual maximum")
    ax1.plot(years, slope * years + intercept, "--", color="#c07a12", lw=1.5,
             label=f"Linear trend: {slope * 1000:+.1f} mm/yr")
    top = amax.nlargest(3)
    for yr, val in top.items():
        ax1.annotate(str(yr), (yr, val), textcoords="offset points", xytext=(0, 7),
                     ha="center", fontsize=8, color="#3d4c5a")
    ax1.margins(y=0.12)
    ax1.set_ylabel("Water level (m)")
    ax1.set_title(f"Annual maximum hourly water level — {station_label}")
    ax1.legend(frameon=False, loc="upper left")
    ax1.grid(alpha=0.3)

    colors = np.where(comp >= min_completeness, "#3e8e41", "#c0392b")
    ax2.bar(comp.index, comp.values * 100, color=colors, width=0.8)
    ax2.axhline(min_completeness * 100, color="#5b6b7a", lw=1, ls=":")
    ax2.set_ylabel("Data (%)")
    ax2.set_ylim(0, 105)
    ax2.set_xlabel("Year")
    ax2.grid(alpha=0.3, axis="y")

    fig.text(0.99, 0.01, f"Years with < {min_completeness:.0%} data excluded (red). Source: NOAA CO-OPS.",
             ha="right", fontsize=7.5, color="#5b6b7a")
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--station", default="8771450")
    p.add_argument("--name", default="Galveston Pier 21, TX")
    p.add_argument("--start", type=int, default=1990)
    p.add_argument("--end", type=int, default=2024)
    p.add_argument("--datum", default="MSL")
    args = p.parse_args()

    s = fetch_coops_hourly(args.station, args.start, args.end, datum=args.datum)
    out = make_figure(s, args.name, Path("figures") / f"{args.station}_annual_maxima.png")
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
