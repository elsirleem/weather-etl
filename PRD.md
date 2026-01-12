# Project Requirements Document (PRD): Weather ETL Pipeline

## 1. Executive Summary
The goal is to build a standalone, containerized ETL (Extract, Transform, Load) pipeline. This application will fetch real-time weather data from a public API, clean/transform the data using Python, and persist it into a local SQLite database. The entire application will be wrapped in Docker to ensure portability and reproducibility.

## 2. Objectives
* **Data Ingestion:** Automate the retrieval of weather data from the Open-Meteo API.
* **Data Integrity:** Ensure data types and units are consistent before storage.
* **Portability:** Containerize the environment using Docker.
* **Persistence:** Utilize Docker Volumes to ensure data persists after the container stops.
* **Version Control:** Maintain a professional Git workflow.

## 3. Technology Stack
| Component | Technology | Description |
| :--- | :--- | :--- |
| **Language** | Python 3.9+ | Core logic scripting |
| **Extraction** | `requests` | HTTP library for API calls |
| **Transformation** | `pandas` | Data cleaning and dataframe manipulation |
| **Storage** | SQLite | Serverless, file-based database |
| **Containerization** | Docker | Image building and container runtime |
| **VCS** | Git / GitHub | Source code management |

## 4. Functional Requirements

### 4.1. Extract (Source)
* **Source:** [Open-Meteo API](https://open-meteo.com/)
* **Parameters:**
    * **Latitude/Longitude:** Hardcoded to a specific city (e.g., London: 51.5074, -0.1278).
    * **Metrics:** `current_weather=true` (Temperature, Windspeed, Wind Direction).
* **Behavior:** The script runs once per execution (Batch processing).

### 4.2. Transform (Logic)
* **Data Cleaning:** Handle potential missing values (drop rows with null critical fields).
* **Calculations:** * Convert Temperature from Celsius to Fahrenheit ($T_F = T_C \times 9/5 + 32$).
    * Add a timestamp column (`fetched_at`) in UTC.
* **Formatting:** Ensure numeric columns are strictly `float` or `int`.

### 4.3. Load (Destination)
* **Target:** Local SQLite database file (`weather.db`).
* **Schema Definition:**
    * `id` (Integer, PK, Autoincrement)
    * `city_name` (String)
    * `temperature_c` (Float)
    * `temperature_f` (Float)
    * `wind_speed` (Float)
    * `fetched_at` (Datetime)
* **Operation:** Append mode (do not overwrite existing history).

## 5. Non-Functional Requirements

### 5.1. Containerization & Environment
* **Base Image:** `python:3.9-slim` (for lightweight footprint).
* **Persistence Strategy:** The database file must be stored in a directory mounted via Docker Volumes (e.g., `/app/data`) to prevent data loss on container exit.
* **Reproducibility:** A `requirements.txt` file must list all dependencies with version numbers.

### 5.2. Directory Structure
```text
weather-etl-docker/
├── data/                 # Mounted volume target (Ignored by Git)
├── src/
│   └── etl_script.py     # Main logic
├── Dockerfile            # Container definition
├── requirements.txt      # Python dependencies
├── .gitignore            # Security & cleanup rules
└── README.md             # Documentation