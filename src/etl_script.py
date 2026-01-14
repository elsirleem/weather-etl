"""Standalone ETL to fetch current weather and persist to SQLite."""
from __future__ import annotations

import json
import os
import sqlite3
import time
import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import requests

API_URL = "https://api.openweathermap.org/data/2.5/weather"
API_KEY = os.getenv("OPENWEATHER_API_KEY")
# default poll interval: 24 hours
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "86400"))
RUN_ONCE = os.getenv("RUN_ONCE", "false").lower() in {"1", "true", "yes"}
EXPORT_LATEST_DAYS = int(os.getenv("EXPORT_LATEST_DAYS", "7"))
DEFAULT_CITIES: List[Dict[str, float | str]] = [
    {"city_name": "Amsterdam", "latitude": 52.3676, "longitude": 4.9041},
    {"city_name": "Rotterdam", "latitude": 51.9244, "longitude": 4.4777},
    {"city_name": "Eindhoven", "latitude": 51.4416, "longitude": 5.4697},
]
DB_PATH = Path(__file__).resolve().parents[1] / "data" / "weather.db"
CITIES_CONFIG_DEFAULT = Path(__file__).resolve().parents[1] / "cities.json"
EXPORT_DIR = Path(__file__).resolve().parents[1] / "data" / "exports"


def fetch_weather(latitude: float, longitude: float) -> Dict[str, Any]:
    """Fetch current weather from OpenWeather for the given coordinates."""
    if not API_KEY:
        raise RuntimeError("OPENWEATHER_API_KEY is required")

    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": API_KEY,
        "units": "metric",
    }
    response = requests.get(API_URL, params=params, timeout=15)
    response.raise_for_status()
    payload = response.json()

    if "main" not in payload or "temp" not in payload.get("main", {}):
        raise ValueError("API response missing 'main.temp'")
    if "wind" not in payload or "speed" not in payload.get("wind", {}):
        raise ValueError("API response missing 'wind.speed'")

    return payload


def transform_weather(raw: Dict[str, Any], city_name: str) -> pd.DataFrame:
    """Clean and enrich raw payload into a typed DataFrame."""
    main_block = raw.get("main", {})
    wind_block = raw.get("wind", {})

    required_fields = ["temp", "speed"]
    missing = [field for field in required_fields if field not in {**main_block, **wind_block}]
    if missing:
        raise ValueError(f"Missing required fields in response: {missing}")

    temperature_c = float(main_block["temp"])
    wind_speed = float(wind_block["speed"])
    temperature_f = temperature_c * 9 / 5 + 32
    fetched_at = datetime.now(timezone.utc)

    df = pd.DataFrame(
        [
            {
                "city_name": city_name,
                "temperature_c": temperature_c,
                "temperature_f": temperature_f,
                "wind_speed": wind_speed,
                "fetched_at": fetched_at,
            }
        ]
    )

    return df


def get_city_targets() -> List[Dict[str, float | str]]:
    """Return city targets from env override, config file, or defaults."""
    city = os.getenv("CITY_NAME")
    lat = os.getenv("LATITUDE")
    lon = os.getenv("LONGITUDE")

    if city and lat and lon:
        return [
            {
                "city_name": city,
                "latitude": float(lat),
                "longitude": float(lon),
            }
        ]

    config_path_env = os.getenv("CITIES_CONFIG")
    config_path = Path(config_path_env) if config_path_env else CITIES_CONFIG_DEFAULT

    if config_path.exists():
        try:
            with config_path.open() as f:
                data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("cities config must be a list of objects")
            cities: List[Dict[str, float | str]] = []
            for idx, item in enumerate(data):
                if not all(key in item for key in ("city_name", "latitude", "longitude")):
                    raise ValueError(f"City entry at index {idx} missing required keys")
                cities.append(
                    {
                        "city_name": str(item["city_name"]),
                        "latitude": float(item["latitude"]),
                        "longitude": float(item["longitude"]),
                    }
                )
            if cities:
                return cities
        except Exception as exc:  # noqa: BLE001
            print(f"Failed to load cities config {config_path}: {exc}. Falling back to defaults.")

    return DEFAULT_CITIES


def init_db(db_path: Path) -> None:
    """Create the weather table if it doesn't exist."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS weather (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city_name TEXT NOT NULL,
                temperature_c REAL,
                temperature_f REAL,
                wind_speed REAL,
                fetched_at TEXT NOT NULL
            );
            """
        )
        conn.commit()


def load_to_sqlite(df: pd.DataFrame, db_path: Path) -> None:
    """Append the transformed data into SQLite."""
    if df.empty:
        print("No rows to insert.")
        return

    with sqlite3.connect(db_path) as conn:
        df.to_sql("weather", conn, if_exists="append", index=False)


def export_recent(db_path: Path, export_dir: Path, days: int) -> None:
    """Export recent rows to CSV (and Parquet if available) for sharing/analysis."""
    if days <= 0:
        return

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(
            "SELECT id, city_name, temperature_c, temperature_f, wind_speed, fetched_at FROM weather WHERE fetched_at >= ? ORDER BY fetched_at DESC",
            conn,
            params=[cutoff.isoformat()],
        )

    if df.empty:
        print(f"No rows to export for the last {days} day(s).")
        return

    export_dir.mkdir(parents=True, exist_ok=True)
    csv_path = export_dir / f"weather_last_{days}d.csv"
    df.to_csv(csv_path, index=False)
    print(f"Exported CSV -> {csv_path}")

    # Parquet is optional; skip quietly if no engine is available
    has_pyarrow = importlib.util.find_spec("pyarrow") is not None
    has_fastparquet = importlib.util.find_spec("fastparquet") is not None
    if not (has_pyarrow or has_fastparquet):
        print("Parquet export skipped (install pyarrow or fastparquet to enable).")
        return

    parquet_path = export_dir / f"weather_last_{days}d.parquet"
    try:
        df.to_parquet(parquet_path, index=False)
        print(f"Exported Parquet -> {parquet_path}")
    except Exception as exc:  # noqa: BLE001
        print(f"Parquet export skipped: {exc}")


def run_pipeline() -> None:
    """Execute extract -> transform -> load steps."""
    init_db(DB_PATH)

    while True:
        frames: List[pd.DataFrame] = []
        errors: List[str] = []

        for target in get_city_targets():
            city_name = target["city_name"]
            latitude = float(target["latitude"])
            longitude = float(target["longitude"])

            try:
                raw = fetch_weather(latitude, longitude)
                transformed = transform_weather(raw, city_name)
                frames.append(transformed)
                print(f"Fetched weather for {city_name} ({latitude}, {longitude})")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{city_name}: {exc}")

        if frames:
            combined = pd.concat(frames, ignore_index=True)
            load_to_sqlite(combined, DB_PATH)
            print(
                f"Inserted {len(combined)} row(s) for {[c['city_name'] for c in get_city_targets()]} into {DB_PATH}"
            )
            export_recent(DB_PATH, EXPORT_DIR, EXPORT_LATEST_DAYS)
        else:
            print("No data inserted; all fetches failed.")

        if errors:
            print("Errors:")
            for err in errors:
                print(f" - {err}")

        if RUN_ONCE:
            break

        print(f"Sleeping {POLL_INTERVAL_SECONDS} seconds before next poll...")
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    run_pipeline()
