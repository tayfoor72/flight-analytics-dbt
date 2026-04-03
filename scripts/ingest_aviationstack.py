"""
AviationStack → BigQuery ingestion script.

Fetches airlines, airports, cities, countries, and flights from the
AviationStack API and loads them into BigQuery as raw source tables,
matching the schema expected by the dbt staging models.

Environment variables:
  AVIATIONSTACK_API_KEY   required
  GCP_PROJECT_ID          defaults to 'flight-analytics-dbt'

Free-tier note:
  - HTTP only (not HTTPS) — set USE_HTTPS=true if you have a paid plan
  - 100 requests/month
  - Real-time flights only (no historical date filtering)
  Tune MAX_REF_PAGES and MAX_FLIGHT_PAGES to stay within your quota.
  Defaults consume roughly 25–35 requests total.
"""

import os
import time
import requests
import pandas as pd
from google.cloud import bigquery

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
API_KEY = os.environ["AVIATIONSTACK_API_KEY"]
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "flight-analytics-dbt")
DATASET_ID = "flight_analytics"
LOCATION = "EU"

SCHEME = "https" if os.environ.get("USE_HTTPS", "").lower() == "true" else "http"
BASE_URL = f"{SCHEME}://api.aviationstack.com/v1"

MAX_REF_PAGES = 3    # airlines, airports, cities, countries  (100 rows/page)
MAX_FLIGHT_PAGES = 5  # flights                               (100 rows/page)
REQUEST_DELAY = 0.4   # seconds between paginated requests

# ---------------------------------------------------------------------------
# BigQuery client
# ---------------------------------------------------------------------------
bq = bigquery.Client(project=PROJECT_ID)
dataset = bigquery.Dataset(f"{PROJECT_ID}.{DATASET_ID}")
dataset.location = LOCATION
bq.create_dataset(dataset, exists_ok=True)
print(f"Dataset '{PROJECT_ID}.{DATASET_ID}' ready\n")

LOAD_CFG = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")


def load(table_name: str, df: pd.DataFrame) -> None:
    if df.empty:
        print(f"  [skip] {table_name} — no rows")
        return
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    bq.load_table_from_dataframe(df, table_id, job_config=LOAD_CFG).result()
    print(f"  [ok]   {table_name}: {len(df):,} rows → {table_id}")


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------
def fetch(endpoint: str, params: dict = None, max_pages: int = 5) -> list[dict]:
    rows = []
    base = {"access_key": API_KEY, "limit": 100, **(params or {})}
    for page in range(max_pages):
        r = requests.get(
            f"{BASE_URL}/{endpoint}",
            params={**base, "offset": page * 100},
            timeout=30,
        )
        r.raise_for_status()
        body = r.json()

        if "error" in body:
            print(f"  [warn] /{endpoint}: API error — {body['error'].get('message', body['error'])}")
            break

        batch = body.get("data", [])
        rows.extend(batch)
        total = body.get("pagination", {}).get("total", len(rows))
        print(f"  /{endpoint}: page {page + 1} — {len(rows)}/{total} rows fetched")

        if not batch or len(rows) >= total:
            break
        time.sleep(REQUEST_DELAY)

    return rows


# ---------------------------------------------------------------------------
# Reference tables
# ---------------------------------------------------------------------------
def ingest_countries() -> dict[str, int]:
    """Returns {country_iso2: country_id}."""
    print("Fetching countries...")
    raw = fetch("countries", max_pages=MAX_REF_PAGES)
    if not raw:
        print("  [warn] No countries data — skipping")
        return {}

    rows = []
    iso2_to_id: dict[str, int] = {}
    for r in raw:
        cid = r.get("country_id") or (len(rows) + 1)
        iso2 = r.get("country_iso2", "")
        iso2_to_id[iso2] = cid
        rows.append({
            "country_id":       cid,
            "country_iso3":     r.get("country_iso3"),
            "country_name":     r.get("country_name"),
            "capital":          r.get("capital"),
            "continent":        r.get("continent"),
            "population":       r.get("population"),
            "currency_name":    r.get("currency_name"),
            "currency_code":    r.get("currency_code"),
        })

    load("countries", pd.DataFrame(rows))
    return iso2_to_id


def ingest_cities(country_iso2_to_id: dict[str, int]) -> dict[str, int]:
    """Returns {city_iata_code: city_id}."""
    print("Fetching cities...")
    raw = fetch("cities", max_pages=MAX_REF_PAGES)
    if not raw:
        print("  [warn] No cities data — skipping")
        return {}

    rows = []
    iata_to_id: dict[str, int] = {}
    for r in raw:
        cid = r.get("city_id") or (len(rows) + 1)
        iata = r.get("iata_code", "")
        iso2 = r.get("country_iso2", "")
        iata_to_id[iata] = cid
        rows.append({
            "city_id":      cid,
            "country_id":   country_iso2_to_id.get(iso2),
            "city_name":    r.get("city_name"),
            "latitude":     r.get("latitude"),
            "longitude":    r.get("longitude"),
            "timezone":     r.get("timezone"),
            "gmt_offset":   r.get("gmt_offset"),
        })

    load("cities", pd.DataFrame(rows))
    return iata_to_id


def ingest_airlines(country_iso2_to_id: dict[str, int]) -> dict[str, int]:
    """Returns {airline_iata: airline_id}."""
    print("Fetching airlines...")
    raw = fetch("airlines", max_pages=MAX_REF_PAGES)
    if not raw:
        print("  [warn] No airlines data — skipping")
        return {}

    rows = []
    iata_to_id: dict[str, int] = {}
    for r in raw:
        aid = r.get("airline_id") or (len(rows) + 1)
        iata = r.get("iata_code", "")
        iso2 = r.get("country_iso2", "")
        iata_to_id[iata] = aid
        rows.append({
            "airline_id":           aid,
            "airline_iata":         iata or None,
            "airline_icao":         r.get("icao_code"),
            "airline_name":         r.get("airline_name"),
            "airline_type":         r.get("type"),
            "country_name":         r.get("country_name"),
            "country_id":           country_iso2_to_id.get(iso2),
            "fleet_size":           r.get("fleet_size"),
            "fleet_average_age":    r.get("fleet_average_age"),
            "date_founded":         r.get("date_founded"),
        })

    load("airline", pd.DataFrame(rows))
    return iata_to_id


def ingest_airports(
    city_iata_to_id: dict[str, int],
    country_iso2_to_id: dict[str, int],
) -> dict[str, int]:
    """Returns {airport_iata: airport_id}."""
    print("Fetching airports...")
    raw = fetch("airports", max_pages=MAX_REF_PAGES)
    if not raw:
        print("  [warn] No airports data — skipping")
        return {}

    rows = []
    iata_to_id: dict[str, int] = {}
    for r in raw:
        apid = r.get("airport_id") or (len(rows) + 1)
        iata = r.get("iata_code", "")
        city_iata = r.get("city_iata_code", "")
        iata_to_id[iata] = apid
        rows.append({
            "airport_id":       apid,
            "airport_iata":     iata or None,
            "airport_icao":     r.get("icao_code"),
            "airport_name":     r.get("airport_name"),
            "airport_city_id":  city_iata_to_id.get(city_iata),
            "timezone_name":    r.get("timezone"),
            "gmt_offset":       r.get("gmt"),
            "latitude":         r.get("latitude"),
            "longitude":        r.get("longitude"),
        })

    load("airports", pd.DataFrame(rows))
    return iata_to_id


# ---------------------------------------------------------------------------
# Flight tables
# ---------------------------------------------------------------------------
def ingest_flights(
    airline_iata_to_id: dict[str, int],
    airport_iata_to_id: dict[str, int],
) -> None:
    print("Fetching flights (status=landed)...")
    raw = fetch(
        "flights",
        params={"flight_status": "landed"},
        max_pages=MAX_FLIGHT_PAGES,
    )

    # Also fetch cancelled flights
    print("Fetching flights (status=cancelled)...")
    raw += fetch(
        "flights",
        params={"flight_status": "cancelled"},
        max_pages=MAX_FLIGHT_PAGES,
    )

    if not raw:
        print("  [warn] No flight data — skipping flight tables")
        return

    flight_details_rows = []
    departures_rows = []
    arrivals_rows = []
    routes_rows = []
    codeshare_rows = []

    codeshare_counter = 1

    for flight_id, r in enumerate(raw, start=1):
        dep = r.get("departure") or {}
        arr = r.get("arrival") or {}
        aln = r.get("airline") or {}
        flt = r.get("flight") or {}
        cs  = flt.get("codeshared")

        dep_iata = dep.get("iata", "")
        arr_iata = arr.get("iata", "")
        aln_iata = aln.get("iata", "")

        dep_airport_id = airport_iata_to_id.get(dep_iata)
        arr_airport_id = airport_iata_to_id.get(arr_iata)
        airline_id     = airline_iata_to_id.get(aln_iata)

        # flight_details
        flight_details_rows.append({
            "flight_id":            flight_id,
            "airline_id":           airline_id,
            "departure_airport_id": dep_airport_id,
            "arrival_airport_id":   arr_airport_id,
            "flight_date":          r.get("flight_date"),
            "flight_status":        r.get("flight_status"),
            "flight_number":        flt.get("number"),
            "flight_iata":          flt.get("iata"),
            "flight_icao":          flt.get("icao"),
        })

        # departure
        departures_rows.append({
            "departure_id":                 flight_id,
            "flight_id":                    flight_id,
            "departure_airport_id":         dep_airport_id,
            "airport_iata":                 dep_iata or None,
            "airport_icao":                 dep.get("icao"),
            "airport_name":                 dep.get("airport"),
            "terminal":                     dep.get("terminal"),
            "gate":                         dep.get("gate"),
            "timezone":                     dep.get("timezone"),
            "scheduled":                    dep.get("scheduled"),
            "estimated":                    dep.get("estimated"),
            "actual":                       dep.get("actual"),
            "estimated_runway":             dep.get("estimated_runway"),
            "actual_runway":                dep.get("actual_runway"),
            "delay":                        dep.get("delay"),
        })

        # arrival
        arrivals_rows.append({
            "arrival_id":                   flight_id,
            "flight_id":                    flight_id,
            "arrival_airport_id":           arr_airport_id,
            "airport_iata":                 arr_iata or None,
            "airport_icao":                 arr.get("icao"),
            "airport_name":                 arr.get("airport"),
            "terminal":                     arr.get("terminal"),
            "gate":                         arr.get("gate"),
            "baggage":                      arr.get("baggage"),
            "timezone":                     arr.get("timezone"),
            "scheduled":                    arr.get("scheduled"),
            "estimated":                    arr.get("estimated"),
            "actual":                       arr.get("actual"),
            "estimated_runway":             arr.get("estimated_runway"),
            "actual_runway":                arr.get("actual_runway"),
            "delay":                        arr.get("delay"),
        })

        # routes (distance and duration not provided by the API)
        routes_rows.append({
            "route_id":                     flight_id,
            "flight_id":                    flight_id,
            "airline_id":                   airline_id,
            "departure_airport_id":         dep_airport_id,
            "arrival_airport_id":           arr_airport_id,
            "distance":                     None,
            "duration":                     None,
            "scheduled_departure_time":     dep.get("scheduled"),
            "scheduled_arrival_time":       arr.get("scheduled"),
        })

        # codeshare (only when present)
        if cs:
            cs_iata = cs.get("airline_iata", "")
            codeshare_rows.append({
                "codeshare_id":     codeshare_counter,
                "flight_id":        flight_id,
                "flight_number":    cs.get("flight_number"),
                "airline_id":       airline_iata_to_id.get(cs_iata),
                "airline_name":     cs.get("airline_name"),
            })
            codeshare_counter += 1

    print("Loading flight tables...")
    load("flight_details", pd.DataFrame(flight_details_rows))
    load("departure", pd.DataFrame(departures_rows))
    load("arrivals", pd.DataFrame(arrivals_rows))
    load("routes", pd.DataFrame(routes_rows))
    load("codeshare", pd.DataFrame(codeshare_rows) if codeshare_rows else pd.DataFrame(
        columns=["codeshare_id", "flight_id", "flight_number", "airline_id", "airline_name"]
    ))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    country_iso2_to_id = ingest_countries()
    city_iata_to_id    = ingest_cities(country_iso2_to_id)
    airline_iata_to_id = ingest_airlines(country_iso2_to_id)
    airport_iata_to_id = ingest_airports(city_iata_to_id, country_iso2_to_id)
    ingest_flights(airline_iata_to_id, airport_iata_to_id)

    print("\nIngestion complete.")
