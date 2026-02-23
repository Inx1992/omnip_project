import psycopg2
import os
from dotenv import load_dotenv


load_dotenv()

def test_connection():
    try:
        print("🔗 Спроба встановити з'єднання з Redshift...")
        print(f"📍 Хост: {os.getenv('REDSHIFT_HOST')}")
        
        conn = psycopg2.connect(
            host=os.getenv('REDSHIFT_HOST'),
            port=os.getenv('REDSHIFT_PORT'),
            database=os.getenv('REDSHIFT_DB'),
            user=os.getenv('REDSHIFT_USER'),
            password=os.getenv('REDSHIFT_PASSWORD'),
            connect_timeout=10,
            sslmode='require'
        )
        
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        
        print("\n🎉 ВІТАЮ! З'єднання успішне.")
        print(f"📊 База відповіла: {version[:45]}...")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print("\n❌ ПОМИЛКА:")
        print(e)
        print("\n🤔 Що це може бути?")
        print("1. Твій IP не додано в Security Group кластера (найімовірніше).")
        print("2. Пароль у .env не збігається з тим, що в Terraform.")

if __name__ == "__main__":
    test_connection()