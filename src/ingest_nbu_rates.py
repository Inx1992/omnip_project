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
    # Використовуємо subprocess.run, щоб Python чекав на завершення dbt
    # Вказуємо шлях до проектної папки dbt
    result = subprocess.run(
        ["dbt", "run", "--project-dir", "./dbt"],
        capture_output=False, # Виводити логи dbt прямо в консоль
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
        
        # 2. DATA EXTRACTION & TRANSFORMATION
        json_data = fetch_nbu_data()
        df = pd.DataFrame(json_data)
        
        # Rename columns and add audit metadata
        df['ingested_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 3. PARTITIONING & PATHING
        now = datetime.now()
        year, month, day = now.year, f"{now.month:02d}", f"{now.day:02d}"
        
        partition_path = f"{S3_BASE_PATH}year={year}/month={month}/day={day}/"
        full_path = f"{partition_path}daily_snapshot.parquet"
        
        df_save = df.drop(columns=['year', 'month', 'day'], errors='ignore')

        # 4. S3 LOADING
        print(f"Uploading to S3: {full_path}")
        wr.s3.to_parquet(
            df=df_save,
            path=full_path,
            dataset=False,
            boto3_session=session
        )
        
        print(f"✅ Success! Data updated for {year}-{month}-{day}")

        # 5. DBT RUN
        # Тепер запускаємо dbt і чекаємо результату
        run_dbt()

    except Exception as e:
        print(f"❌ Critical error occurred: {e}")
        sys.exit(1) # Повідомляємо GitHub Actions, що робота провалена

if __name__ == "__main__":
    main()