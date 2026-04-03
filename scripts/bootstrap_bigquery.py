import os
import pandas as pd
from pathlib import Path
from google.cloud import bigquery

# --- paths ---
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

# --- config ---
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "flight-analytics-dbt")
DATASET_ID = "flight_analytics"
LOCATION = "EU"

# --- connect ---
client = bigquery.Client(project=PROJECT_ID)
print(f"Connected to BigQuery project '{PROJECT_ID}'")

# --- create dataset if not exists ---
dataset_ref = bigquery.Dataset(f"{PROJECT_ID}.{DATASET_ID}")
dataset_ref.location = LOCATION
client.create_dataset(dataset_ref, exists_ok=True)
print(f"Dataset '{DATASET_ID}' ready")

TABLES = {
    "airline": "airline.csv",
    "airports": "airports.csv",
    "arrivals": "arrivals.csv",
    "cities": "cities.csv",
    "codeshare": "codeshare.csv",
    "countries": "countries.csv",
    "departure": "departure.csv",
    "flight_details": "flight_details.csv",
    "routes": "routes.csv",
}

job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")

for table_name, file_name in TABLES.items():
    file_path = DATA_DIR / file_name
    df = pd.read_csv(file_path)
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    client.load_table_from_dataframe(df, table_id, job_config=job_config).result()
    print(f"Loaded {len(df):,} rows into '{table_id}'")

print("Done.")
