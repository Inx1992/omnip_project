import requests
import pandas as pd
import awswrangler as wr
import boto3
import subprocess
import sys
import os
from datetime import datetime

# --- CONFIGURATION ---
BUCKET_NAME = "omnip-data-lake-dev-2026"
DATABASE = "omnip_db_dev"
TABLE = "nbu_rates_raw"
S3_BASE_PATH = f"s3://{BUCKET_NAME}/bronze/nbu_rates/"
REGION = "us-east-1"

def fetch_nbu_data():
    """Fetch current exchange rates from NBU public API"""
    print("Fetching data from NBU API...")
    url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def run_dbt():
    """Execute dbt transformations and wait for completion"""
    print("\n🚀 Starting dbt transformations...")
    result = subprocess.run(
        ["dbt", "run", "--project-dir", "./dbt"],
        capture_output=False,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ dbt run failed with exit code {result.returncode}")
        sys.exit(1)
    
    print("✅ dbt transformations finished successfully!")

def main():
    try:
        # 0. Initialize AWS session
        session = boto3.Session(region_name=REGION)
        
        # 1. DATABASE CHECK
        existing_dbs = wr.catalog.databases(boto3_session=session)
        if DATABASE not in existing_dbs.values:
            print(f"Database {DATABASE} not found. Creating...")
            wr.catalog.create_database(name=DATABASE, boto3_session=session)

        # --- КРОК 1.5: ОЧИЩЕННЯ СТАРИХ МЕТАДАНИХ ---
        # Видаляємо лише опис таблиці, щоб Wrangler створив його заново з правильними колонками
        print(f"Cleaning up old metadata for {DATABASE}.{TABLE}...")
        wr.catalog.delete_table_if_exists(database=DATABASE, table=TABLE, boto3_session=session)
        
        # 2. DATA EXTRACTION & TRANSFORMATION
        json_data = fetch_nbu_data()
        df = pd.DataFrame(json_data)
        
        # Add audit metadata and time components for partitioning
        now = datetime.now()
        df['ingested_at'] = now.strftime('%Y-%m-%d %H:%M:%S')
        df['year'] = now.strftime('%Y')
        df['month'] = now.strftime('%m')
        df['day'] = now.strftime('%d')
        
        # 3. S3 LOADING & CATALOG SYNC
        # Використовуємо dataset=True, щоб Wrangler сам зареєстрував всі колонки в Glue
        print(f"Uploading data and syncing Glue Catalog for {now.date()}...")
        wr.s3.to_parquet(
            df=df,
            path=S3_BASE_PATH,
            dataset=True,
            database=DATABASE,
            table=TABLE,
            partition_cols=['year', 'month', 'day'],
            mode="overwrite_partitions",
            boto3_session=session
        )
        
        print(f"✅ Success! Data synced to S3 and Glue Catalog.")

        # 4. DBT RUN
        run_dbt()

    except Exception as e:
        print(f"❌ Critical error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()