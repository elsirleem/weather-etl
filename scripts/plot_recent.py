#!/usr/bin/env python
"""Quick visualization of recent weather data from SQLite.

Usage:
    python scripts/plot_recent.py --days 7
Saves PNG to data/exports/weather_plot.png
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "weather.db"
EXPORT_DIR = ROOT / "data" / "exports"


def load_recent(days: int) -> pd.DataFrame:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(
            "SELECT city_name, temperature_c, fetched_at FROM weather WHERE fetched_at >= ? ORDER BY fetched_at",
            conn,
            params=[cutoff.isoformat()],
        )
    if not df.empty:
        df["fetched_at"] = pd.to_datetime(df["fetched_at"], utc=True)
    return df


def plot(df: pd.DataFrame, out_path: Path) -> None:
    plt.style.use("seaborn-v0_8")
    fig, ax = plt.subplots(figsize=(8, 5))
    for city, sub in df.groupby("city_name"):
        ax.plot(sub["fetched_at"], sub["temperature_c"], marker="o", label=city)
    ax.set_xlabel("Timestamp (UTC)")
    ax.set_ylabel("Temperature (°C)")
    ax.set_title("Recent Temperatures")
    ax.legend()
    fig.autofmt_xdate()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    print(f"Saved plot -> {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7, help="Lookback window in days")
    args = parser.parse_args()

    df = load_recent(args.days)
    if df.empty:
        print(f"No data found in the last {args.days} day(s). Run the ETL first.")
        return

    out_path = EXPORT_DIR / "weather_plot.png"
    plot(df, out_path)


if __name__ == "__main__":
    main()
