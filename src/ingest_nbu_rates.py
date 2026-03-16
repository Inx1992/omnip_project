import requests
import pandas as pd
import awswrangler as wr
import boto3
import subprocess
import sys
import time
import os
from datetime import datetime

# --- CONFIGURATION ---
BUCKET_NAME = os.getenv("BUCKET_NAME", "omnip-data-lake-dev-2026")
DATABASE = "omnip_db_dev"
TABLE = "nbu_rates_raw"
S3_BASE_PATH = f"s3://{BUCKET_NAME}/bronze/nbu_rates/"
REGION = os.getenv("AWS_REGION", "us-east-1")


def fetch_nbu_data():
    url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    print(f"📡 API Response: Received {len(data)} currency records.", flush=True)
    return data


def run_dbt():
    print("\n🚀 Starting dbt transformations (build)...", flush=True)
    result = subprocess.run(
        ["dbt", "build", "--project-dir", "./dbt"], capture_output=False, text=True
    )
    if result.returncode != 0:
        print(f"❌ dbt build failed with exit code {result.returncode}", flush=True)
        return False
    print("✅ dbt transformations and tests finished successfully!", flush=True)
    return True


def check_if_exists(session, path):
    """Перевіряє, чи існують уже файли у вказаній директорії S3"""
    files = wr.s3.list_objects(path=path, boto3_session=session)
    return len(files) > 0


def main():
    steps_ok = {
        "Check Duplicates": False,
        "API Fetch": "Skipped",
        "S3 Upload": "Skipped",
        "dbt Build": False,
    }

    try:
        session = boto3.Session(region_name=REGION)

        # 1. Визначаємо часові мітки та шлях
        now = datetime.now()
        year, month, day = now.strftime("%Y"), now.strftime("%m"), now.strftime("%d")
        daily_folder_path = f"{S3_BASE_PATH}year={year}/month={month}/day={day}/"

        # 2. Перевірка на дублікати в Bronze
        if check_if_exists(session, daily_folder_path):
            print(
                f"⚠️ Дані за {year}-{month}-{day} вже існують у Bronze. Завантаження пропущено."
            )
            steps_ok["Check Duplicates"] = True
        else:
            # 3. Екстракція (виконується тільки якщо даних ще немає)
            json_data = fetch_nbu_data()
            df = pd.DataFrame(json_data)
            steps_ok["API Fetch"] = "Success"

            # 4. Schema Enforcement
            ingested_at = now.strftime("%Y-%m-%d %H:%M:%S")
            df = df.astype(
                {
                    "r030": "int64",
                    "txt": "string",
                    "rate": "float64",
                    "cc": "string",
                    "exchangedate": "string",
                }
            )
            df["ingested_at"] = ingested_at

            # 5. Завантаження
            file_ts = now.strftime("%H%M%S")
            file_path = f"{daily_folder_path}nbu_ingest_{file_ts}.parquet"

            wr.s3.to_parquet(
                df=df,
                path=file_path,
                dataset=False,
                boto3_session=session,
            )
            print(f"✅ Data uploaded to: {file_path}")
            steps_ok["S3 Upload"] = "Success"
            steps_ok["Check Duplicates"] = True

        # 6. Запуск dbt (завжди запускаємо для консистентності Silver шару)
        time.sleep(2)
        if run_dbt():
            steps_ok["dbt Build"] = True

        # Резюме
        print("\n" + "=" * 35)
        print("🏁 PIPELINE EXECUTION SUMMARY")
        print("=" * 35)
        for step, status in steps_ok.items():
            print(
                f"{'✅' if status in [True, 'Success', 'Skipped'] else '❌'} {step}: {status}"
            )

        if steps_ok["Check Duplicates"] and steps_ok["dbt Build"]:
            print("\n🚀 PIPELINE FINISHED SUCCESSFULLY!", flush=True)
        else:
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Critical error: {e}", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
