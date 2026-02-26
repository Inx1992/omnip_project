import pandas as pd
import awswrangler as wr
import boto3
import ssl
from datetime import datetime, timedelta

# --- CONFIGURATION ---
ssl._create_default_https_context = ssl._create_unverified_context
BUCKET = "omnip-data-lake-dev-2026"
START_DATE = datetime(2026, 2, 1)
END_DATE = datetime.now()

def fetch_and_save_historical():
    current_date = START_DATE
    session = boto3.Session()
    
    while current_date <= END_DATE:
        date_str = current_date.strftime('%Y%m%d')
        url = f"https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json&date={date_str}"
        
        try:
            # 1. Extraction
            df = pd.read_json(url)
            if df.empty:
                print(f"⚠️ No data for {date_str}")
                current_date += timedelta(days=1)
                continue

            # 2. Transformation
            df['ingested_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            year = current_date.year
            month = f"{current_date.month:02d}"
            day = f"{current_date.day:02d}"
            
            df_save = df.drop(columns=['year', 'month', 'day'], errors='ignore')

            # 3. Loading to S3
            path = f"s3://{BUCKET}/bronze/nbu_rates/year={year}/month={month}/day={day}/daily_snapshot.parquet"
            wr.s3.to_parquet(
                df=df_save, 
                path=path, 
                dataset=False, 
                boto3_session=session
            )
            print(f"✅ Processed: {year}-{month}-{day}")

        except Exception as e:
            print(f"❌ Error at {date_str}: {e}")

        current_date += timedelta(days=1)

    print("\n🚀 Backfill completed successfully!")

if __name__ == "__main__":
    fetch_and_save_historical()