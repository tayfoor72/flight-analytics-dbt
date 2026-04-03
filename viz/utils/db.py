import os
import streamlit as st
from google.cloud import bigquery

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "flight-analytics-dbt")


@st.cache_data
def query(sql_query: str):
    client = bigquery.Client(project=PROJECT_ID)
    return client.query(sql_query).to_dataframe()
