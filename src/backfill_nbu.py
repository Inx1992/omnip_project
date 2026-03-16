import pandas as pd
import awswrangler as wr
import boto3
import ssl
import time
from datetime import datetime, timedelta

# --- CONFIGURATION ---
# Вимикаємо перевірку SSL лише якщо це необхідно для твого середовища
ssl._create_default_https_context = ssl._create_unverified_context

BUCKET = "omnip-data-lake-dev-2026"
# Початкова дата березень 2026 (згідно з твоїм попереднім логом)
START_DATE = datetime(2026, 3, 1)
END_DATE = datetime.now()


def fetch_and_save_historical():
    current_date = START_DATE
    session = boto3.Session()

    print(f"🔄 Starting backfill from {START_DATE.date()} to {END_DATE.date()}...")

    while current_date <= END_DATE:
        date_str = current_date.strftime("%Y%m%d")
        url = f"https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json&date={date_str}"

        try:
            # 1. Extraction
            df = pd.read_json(url)
            if df.empty:
                print(f"⚠️ No data for {date_str}")
                current_date += timedelta(days=1)
                continue

            # 2. Transformation & Schema Enforcement
            # Важливо: Типи даних мають бути ідентичні ingest_nbu_rates.py
            df = df.astype(
                {
                    "r030": "int64",
                    "txt": "string",
                    "rate": "float64",
                    "cc": "string",
                    "exchangedate": "string",
                }
            )

            # Мітка часу інжесту (коли ми запускаємо цей бекфіл)
            df["ingested_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Партиції для шляху в S3
            year = current_date.year
            month = f"{current_date.month:02d}"
            day = f"{current_date.day:02d}"

            # Видаляємо зайві колонки, якщо вони раптом з'явилися в API
            df_save = df.drop(columns=["year", "month", "day"], errors="ignore")

            # 3. Loading to S3
            # Використовуємо таку ж логіку назв файлів, як в інджесті
            path = f"s3://{BUCKET}/bronze/nbu_rates/year={year}/month={month}/day={day}/backfill_snapshot.parquet"

            wr.s3.to_parquet(
                df=df_save, path=path, dataset=False, boto3_session=session
            )
            print(f"✅ Processed: {year}-{month}-{day}")

            # Невелика пауза, щоб не перевантажувати API НБУ
            time.sleep(0.5)

        except Exception as e:
            print(f"❌ Error at {date_str}: {e}")

        current_date += timedelta(days=1)

    print("\n🚀 Backfill completed successfully!")


if __name__ == "__main__":
    fetch_and_save_historical()
