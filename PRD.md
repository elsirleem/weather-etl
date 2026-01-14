# Project Requirements Document (PRD): Weather ETL Pipeline

## 1. Executive Summary
Build a standalone, containerized ETL (Extract, Transform, Load) pipeline that fetches current weather from OpenWeather, cleans/transforms it with Python, and persists history into a local SQLite database mounted from the host. The application is wrapped in Docker/Compose for portability and reproducibility.

## 2. Objectives
- **Data Ingestion:** Automate the retrieval of weather data from the OpenWeather API.
- **Data Integrity:** Ensure data types and units are consistent before storage.
- **Portability:** Containerize the environment using Docker/Compose.
- **Persistence:** Use a mounted data directory so SQLite persists after the container stops.
- **Version Control:** Maintain a professional Git workflow.

## 3. Technology Stack
| Component | Technology | Description |
| :--- | :--- | :--- |
| **Language** | Python 3.9+ | Core logic scripting |
| **Extraction** | `requests` | HTTP library for API calls |
| **Transformation** | `pandas` | Data cleaning and dataframe manipulation |
| **Storage** | SQLite | Serverless, file-based database |
| **Containerization** | Docker + Compose | Image building and container runtime |
| **VCS** | Git / GitHub | Source code management |

## 4. Functional Requirements

### 4.1. Extract (Source)
- **Source:** [OpenWeather API](https://openweathermap.org/api)
- **Parameters:**
  - **Latitude/Longitude:** Configurable via `cities.json` (defaults: Amsterdam, Rotterdam, Eindhoven) or a single-city env override (`CITY_NAME/LATITUDE/LONGITUDE`).
  - **Units:** Metric; captures temperature and wind speed.
- **Behavior:** Supports continuous polling (default 24h) or single-run via `RUN_ONCE=true`.

### 4.2. Transform (Logic)
- **Data Cleaning:** Handle potential missing values.
- **Calculations:** Convert Celsius to Fahrenheit: $T_F = T_C \times 9/5 + 32$.
- **Timestamps:** Add `fetched_at` in UTC ISO format.
- **Types:** Ensure numeric columns are floats.

### 4.3. Load (Destination)
- **Target:** Local SQLite database file (`weather.db`).
- **Schema Definition:**
  - `id` (Integer, PK, Autoincrement)
  - `city_name` (String)
  - `temperature_c` (Float)
  - `temperature_f` (Float)
  - `wind_speed` (Float)
  - `fetched_at` (Datetime)
- **Operation:** Append mode (do not overwrite existing history).
- **Exports:** After each load, recent rows (default 7 days) exported to CSV (guaranteed) and Parquet if a compatible engine (`pyarrow` or `fastparquet`) is installed.

## 5. Non-Functional Requirements

### 5.1. Containerization & Environment
- **Base Image:** `python:3.9-slim`.
- **Persistence Strategy:** Database stored in `/app/data` mounted from host `./data` via Compose.
- **Reproducibility:** `requirements.txt` lists dependencies; Dockerfile and docker-compose ensure consistent runs.

### 5.2. Directory Structure
```
weather-etl/
├── data/                 # Mounted volume target (ignored by Git)
├── src/
│   └── etl_script.py     # Main logic
├── scripts/
│   └── plot_recent.py    # Quick visualization
├── cities.json           # Default cities config
├── schema.sql            # SQLite schema
├── Dockerfile            # Container definition
├── docker-compose.yml    # Compose config (mounts ./data, loads .env)
├── requirements.txt      # Python dependencies
├── .env.example          # Sample env
├── run.sh                # Convenience runner
└── README.md             # Documentation
```