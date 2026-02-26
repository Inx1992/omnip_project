import requests
import pandas as pd
import awswrangler as wr
import boto3
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

def main():
    try:
        # 0. Initialize AWS session
        session = boto3.Session(region_name=REGION)
        
        # 1. DATABASE CHECK
        # Ensure the Glue database exists before writing data
        existing_dbs = wr.catalog.databases(boto3_session=session)
        if DATABASE not in existing_dbs.values:
            print(f"Database {DATABASE} not found. Creating...")
            wr.catalog.create_database(name=DATABASE, boto3_session=session)
        
        # 2. DATA EXTRACTION & TRANSFORMATION
        json_data = fetch_nbu_data()
        df = pd.DataFrame(json_data)
        
        # Rename columns to match Athena/dbt schema and add audit metadata
        df = df.rename(columns={'rate': 'currency_rate'})
        df['ingested_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 3. PARTITIONING & PATHING
        now = datetime.now()
        year, month, day = now.year, f"{now.month:02d}", f"{now.day:02d}"
        
        # Define partition path and fixed filename for idempotency
        partition_path = f"{S3_BASE_PATH}year={year}/month={month}/day={day}/"
        full_path = f"{partition_path}daily_snapshot.parquet"
        
        # Remove partition columns from the dataframe to avoid duplication in Athena
        df_save = df.drop(columns=['year', 'month', 'day'], errors='ignore')

        # 4. S3 LOADING
        # Use dataset=False because Terraform manages metadata via Partition Projection
        print(f"Uploading to S3: {full_path}")
        wr.s3.to_parquet(
            df=df_save,
            path=full_path,
            dataset=False,
            boto3_session=session
        )
        
        print(f"✅ Success! Data updated for {year}-{month}-{day}")

    except Exception as e:
        print(f"❌ Error occurred: {e}")

if __name__ == "__main__":
    main()