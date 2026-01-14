-- Schema for weather ETL SQLite database
CREATE TABLE IF NOT EXISTS weather (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city_name TEXT NOT NULL,
    temperature_c REAL NOT NULL,
    temperature_f REAL NOT NULL,
    wind_speed REAL NOT NULL,
    fetched_at TEXT NOT NULL
);
