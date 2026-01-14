# Weather ETL Pipeline

Containerized Python ETL that fetches current weather from OpenWeather, cleans/transforms it with pandas, and persists history into a SQLite database mounted via Docker volume.

## Features
- Configurable city list via `cities.json` or `CITIES_CONFIG` env override; single-city override via `CITY_NAME/LATITUDE/LONGITUDE`.
- Persists snapshots to `data/weather.db` (SQLite).
- Exports recent rows to `data/exports/weather_last_<days>d.csv` (and Parquet if `pyarrow` is installed).
- Quick PNG plot of recent temperatures via `scripts/plot_recent.py`.
- Default polling every 24 hours; `RUN_ONCE` supports single-run mode.

## Project Layout
```
├── data/                 # SQLite DB and exports (gitignored)
├── src/
│   └── etl_script.py     # Main ETL script
├── scripts/
│   └── plot_recent.py    # Plot recent temperatures
├── cities.json           # Default city list
├── .env.example          # Sample environment file
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── run.sh
└── README.md
```

## Quickstart (local Python)
1) Optional: create/activate a virtualenv.
2) Install deps:
   ```bash
   pip install -r requirements.txt
   ```
3) Copy the sample env and add your API key:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` to set `OPENWEATHER_API_KEY` and any overrides.
4) Run once:
   ```bash
   python src/etl_script.py
   ```
5) Continuous polling (every 24h by default):
   ```bash
   RUN_ONCE=false python src/etl_script.py
   ```

Inspect data:
```bash
sqlite3 data/weather.db "SELECT * FROM weather ORDER BY id DESC LIMIT 5;"
```

## Configuration
Required:
- `OPENWEATHER_API_KEY` (https://openweathermap.org/appid#apikey)

Optional overrides:
- Single-city override (all three required): `CITY_NAME`, `LATITUDE`, `LONGITUDE`
- Cities file (JSON list) path: `CITIES_CONFIG` (defaults to `cities.json` if present)
- Poll interval seconds: `POLL_INTERVAL_SECONDS` (default 86400)
- Single-run flag: `RUN_ONCE=true`
- Export lookback window (days): `EXPORT_LATEST_DAYS` (default 7)

### Configuration via cities file
Default cities live in `cities.json`. To change the list, edit that file or point `CITIES_CONFIG` to another JSON file shaped like:
```json
[
  {"city_name": "Paris", "latitude": 48.8566, "longitude": 2.3522},
  {"city_name": "Berlin", "latitude": 52.52, "longitude": 13.405}
]
```
Env overrides (`CITY_NAME/LATITUDE/LONGITUDE`) take priority when all three are provided.

## Exports
- After each load, recent rows (default last 7 days) are exported to `data/exports/weather_last_<days>d.csv`.
- Parquet export is attempted if `pyarrow` is available; otherwise it’s skipped with a log message.

## Quick visualization
Generate a PNG plot of recent temperatures by city:
python scripts/plot_recent.py --days 7
```
The plot is saved to `data/exports/weather_plot.png`.

## Dockerized Run
Build and run with a mounted volume so the DB persists:
```bash
docker build -t weather-etl .
docker run --rm -v "$(pwd)/data:/app/data" --env-file .env weather-etl
```
You can also pass env vars directly instead of an env file:
```bash
docker run --rm -v "$(pwd)/data:/app/data" \
  -e OPENWEATHER_API_KEY="<your-key>" \
  -e CITY_NAME="Paris" -e LATITUDE=48.8566 -e LONGITUDE=2.3522 \
  weather-etl
```

## Docker Compose
```bash
docker compose up --build
```
The compose file builds the image (if needed), mounts `./data` to `/app/data`, loads env vars from `.env`, and runs continuously (`RUN_ONCE=false` in the service env). Stop with `Ctrl+C` or `docker compose down`. For a single-run container, set `RUN_ONCE=true` via env: `docker compose run --rm -e RUN_ONCE=true etl`.

## Data Model
`weather` table schema:
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `city_name` TEXT
- `temperature_c` REAL
- `temperature_f` REAL
- `wind_speed` REAL
- `fetched_at` TEXT (UTC ISO timestamp)

SQL definition (also saved in `schema.sql`):
```sql
CREATE TABLE IF NOT EXISTS weather (
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   city_name TEXT NOT NULL,
   temperature_c REAL NOT NULL,
   temperature_f REAL NOT NULL,
   wind_speed REAL NOT NULL,
   fetched_at TEXT NOT NULL
);
```

## Notes
- Each run appends one current-weather snapshot (batch mode).
- Network access to OpenWeather is required.
- Keep the `data/` volume mounted to persist history.
