import requests
import pandas as pd
import boto3
from datetime import datetime
from io import BytesIO

BUCKET_NAME = "omnip-data-lake-dev-2026"
S3_PATH = "bronze/nbu_rates/"

def fetch_nbu_data():
    print("Fetching data from NBU API...")
    url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def transform_to_parquet(json_data):
    print("Processing data with Pandas...")
    df = pd.DataFrame(json_data)
    
    df['ingested_at'] = datetime.now().isoformat()
    df['extraction_date'] = datetime.now().strftime('%Y-%m-%d')
    
    buffer = BytesIO()
    df.to_parquet(buffer, engine='pyarrow', index=False)
    return buffer

def upload_to_s3(file_buffer):
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    file_name = f"{S3_PATH}year={now.year}/month={now.month}/rates_{today_str}.parquet"
    
    print(f"Uploading file to s3://{BUCKET_NAME}/{file_name}")
    
    s3 = boto3.client('s3')
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=file_name,
        Body=file_buffer.getvalue()
    )
    print("Upload complete.")

def main():
    try:
        data = fetch_nbu_data()
        parquet_file = transform_to_parquet(data)
        upload_to_s3(parquet_file)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()