# Weather ETL Pipeline

Containerized Python ETL that fetches current weather from OpenWeather, cleans/transforms it with pandas, and persists history into a SQLite database mounted via Docker volume.

## Features
- Extracts current weather for three Netherlands cities by default: Amsterdam, Rotterdam, Eindhoven.
- Cleans and enriches data (UTC timestamp, °F conversion) before load.
- Appends to a persistent SQLite DB at `data/weather.db`.
- Ships with Dockerfile for reproducible runs.
- Polls every 24 hours by default; optional single-run mode via `RUN_ONCE`.

## Project Layout
```
weather_prediction/
├── data/                 # SQLite file lives here (gitignored)
├── src/
│   └── etl_script.py     # Main ETL script
├── Dockerfile
├── requirements.txt
├── .gitignore
└── README.md
```

## Quickstart (local Python)
1. Create/activate a virtualenv (optional but recommended).
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Run the ETL (single run):
```bash
python src/etl_script.py
```
For continuous polling every 24 hours, omit `RUN_ONCE` or set it to `false` (default):
```bash
RUN_ONCE=false python src/etl_script.py
```
4. Inspect the data:
```bash
sqlite3 data/weather.db "SELECT * FROM weather ORDER BY id DESC LIMIT 5;"
```

## Dockerized Run
Build and run with a mounted volume so the DB persists:
```bash
docker build -t weather-etl .
```

Recommended: use an env file so you don’t retype the key each run.
1) Copy the sample and add your key:
```bash
cp .env.example .env
```
Edit `.env` to set `OPENWEATHER_API_KEY` (and optional overrides).

2) Run the container with the env file and a mounted data volume:
```bash
docker run --rm -v "$(pwd)/data:/app/data" --env-file .env weather-etl
```

## Configuration
Required:
- `OPENWEATHER_API_KEY` (from https://openweathermap.org/appid#apikey)

Override defaults via environment variables:
  - To override the default three-city set, provide a single custom target via:
    - `CITY_NAME`
    - `LATITUDE`
    - `LONGITUDE`
- Poll interval override (seconds): `POLL_INTERVAL_SECONDS` (default 86400)
- Single run (no loop): `RUN_ONCE=true`
- Example:
```bash
docker run --rm -v "$(pwd)/data:/app/data" \
  -e OPENWEATHER_API_KEY="<your-key>" \
  -e CITY_NAME="Paris" -e LATITUDE=48.8566 -e LONGITUDE=2.3522 \
  weather-etl
```

## Data Model
`weather` table schema:
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `city_name` TEXT
- `temperature_c` REAL
- `temperature_f` REAL
- `wind_speed` REAL
- `fetched_at` TEXT (UTC ISO timestamp)

## Notes
- Each run appends one current-weather snapshot (batch mode).
- Network access to OpenWeather is required for the extract step.
- The `data/` directory is gitignored; keep the mount to persist history.
