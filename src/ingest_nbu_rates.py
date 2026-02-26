import requests
import pandas as pd
import awswrangler as wr
import boto3
import subprocess
import sys
import time
from datetime import datetime

BUCKET_NAME = "omnip-data-lake-dev-2026"
DATABASE = "omnip_db_dev"
TABLE = "nbu_rates_raw"
S3_BASE_PATH = f"s3://{BUCKET_NAME}/bronze/nbu_rates/"
REGION = "us-east-1"

def fetch_nbu_data():
    url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    print(f"📡 API Response: Received {len(data)} currency records.", flush=True)
    return data

def run_dbt():
    print("\n🚀 Starting dbt transformations (build)...", flush=True)
    
    # Видаляємо capture_output, щоб dbt писав у консоль наживо
    result = subprocess.run(
        ["dbt", "build", "--project-dir", "./dbt"],
        capture_output=False,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ dbt build failed with exit code {result.returncode}", flush=True)
        return False
    print("✅ dbt transformations and tests finished successfully!", flush=True)
    return True

def main():
    steps_ok = {
        "API Fetch": False,
        "S3/Glue Upload": False,
        "dbt Build": False
    }

    try:
        session = boto3.Session(region_name=REGION)
        
        json_data = fetch_nbu_data()
        df = pd.DataFrame(json_data)
        steps_ok["API Fetch"] = True
        
        now = datetime.now()
        df['ingested_at'] = now.strftime('%Y-%m-%d %H:%M:%S')
        df['year'] = now.strftime('%Y')
        df['month'] = now.strftime('%m')
        df['day'] = now.strftime('%d')
        
        wr.catalog.delete_table_if_exists(database=DATABASE, table=TABLE, boto3_session=session)
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
        print(f"✅ Data synced to S3 and Glue Catalog.", flush=True)
        steps_ok["S3/Glue Upload"] = True

        # Невелика пауза для синхронізації виводу в консолі GitHub
        time.sleep(2)

        if run_dbt():
            steps_ok["dbt Build"] = True

        print("\n" + "="*35)
        print("🏁 PIPELINE EXECUTION SUMMARY")
        print("="*35)
        
        for step, success in steps_ok.items():
            status_icon = "✅" if success else "❌"
            print(f"{status_icon} {step}", flush=True)
        
        if all(steps_ok.values()):
            print("\n🚀 DEPLOYMENT REACHED ORBIT! ALL SYSTEMS GO!", flush=True)
        else:
            print("\n⚠️ SOME STEPS FAILED. CHECK LOGS ABOVE.", flush=True)
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Critical error occurred: {e}", flush=True)
        sys.exit(1)

if __name__ == "__main__":
    main()