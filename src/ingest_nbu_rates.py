import requests
import pandas as pd
import awswrangler as wr
import boto3
import subprocess
import sys
import time
from datetime import datetime

# --- CONFIGURATION ---
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
    # Переконайся, що шлях до dbt проекту правильний
    result = subprocess.run(
        ["dbt", "build", "--project-dir", "./dbt"], capture_output=False, text=True
    )
    if result.returncode != 0:
        print(f"❌ dbt build failed with exit code {result.returncode}", flush=True)
        return False
    print("✅ dbt transformations and tests finished successfully!", flush=True)
    return True


def main():
    steps_ok = {
        "API Fetch": False,
        "Schema Prep": False,
        "S3 Upload": False,
        "dbt Build": False,
    }

    try:
        session = boto3.Session(region_name=REGION)

        # 1. Екстракція
        json_data = fetch_nbu_data()
        df = pd.DataFrame(json_data)
        steps_ok["API Fetch"] = True

        # 2. Фіксація часу для всього процесу (Single Source of Truth)
        now = datetime.now()
        ingested_at = now.strftime("%Y-%m-%d %H:%M:%S")
        year, month, day = now.strftime("%Y"), now.strftime("%m"), now.strftime("%d")
        file_ts = now.strftime("%H%M%S")  # Мітка часу для назви файлу

        # 3. Приведення типів та метадані (Schema Enforcement)
        # Це гарантує, що Athena не "виб'є" помилку через зміну типів у Parquet
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
        steps_ok["Schema Prep"] = True

        # Визначаємо шлях (унікальний файл для кожного запуску, щоб не перетирати дані)
        daily_file_path = f"{S3_BASE_PATH}year={year}/month={month}/day={day}/nbu_ingest_{file_ts}.parquet"

        # 4. Завантаження (БЕЗ оновлення Glue Catalog - працює Partition Projection)
        wr.s3.to_parquet(
            df=df.drop(columns=["year", "month", "day"], errors="ignore"),
            path=daily_file_path,
            dataset=False,
            boto3_session=session,
        )

        print(f"✅ Data uploaded to: {daily_file_path}", flush=True)
        steps_ok["S3 Upload"] = True

        # Невелика пауза перед dbt для консистентності S3 (S3 consistency is strong, but safety first)
        time.sleep(2)

        # 5. Запуск dbt
        if run_dbt():
            steps_ok["dbt Build"] = True

        # Резюме
        print("\n" + "=" * 35)
        print("🏁 PIPELINE EXECUTION SUMMARY")
        print("=" * 35)
        for step, success in steps_ok.items():
            print(f"{'✅' if success else '❌'} {step}", flush=True)

        if all(steps_ok.values()):
            print("\n🚀 ALL SYSTEMS GO!", flush=True)
        else:
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Critical error: {e}", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
