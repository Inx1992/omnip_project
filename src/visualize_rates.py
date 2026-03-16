import os
import pandas as pd
import matplotlib

# ВАЖЛИВО: встановлюємо бекенд ДО імпорту pyplot
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from pyathena import connect

# 1. Налаштування підключення
AWS_REGION = os.getenv("AWS_REGION", "eu-central-1")
S3_STAGING_DIR = os.getenv("S3_STAGING_DIR")


def get_data():
    # Перевірка наявності S3_STAGING_DIR
    if not S3_STAGING_DIR:
        raise ValueError("❌ Енвайронмент змінна S3_STAGING_DIR не встановлена!")

    conn = connect(s3_staging_dir=S3_STAGING_DIR, region_name=AWS_REGION)

    # Додаємо динамічний коментар (Timestamp), щоб обійти кешування результатів Athena в хмарі
    query = f"""
    -- cache_buster: {pd.Timestamp.now()}
    SELECT exchange_date, currency_rate 
    FROM "omnip_db_dev_silver"."fct_currency_rates" 
    WHERE currency_code = 'USD' 
    ORDER BY exchange_date ASC
    """
    df = pd.read_sql(query, conn)
    print(f"📊 DEBUG: Отримано рядків з Athena: {len(df)}")
    return df


# 2. Отримуємо дані
df = get_data()

if df.empty:
    print("⚠️ Попередження: Дані порожні. Анімація не буде створена.")
    exit(0)

df["exchange_date"] = pd.to_datetime(df["exchange_date"])

# 3. Налаштування графіка
fig, ax = plt.subplots(figsize=(10, 6))

# Додаємо трохи "повітря" по краях дат, щоб маркер не зникав
x_min = df["exchange_date"].min() - pd.Timedelta(days=1)
x_max = df["exchange_date"].max() + pd.Timedelta(days=1)

ax.set_xlim(x_min, x_max)
# Динамічні межі Y на основі отриманих даних
ax.set_ylim(df["currency_rate"].min() - 0.5, df["currency_rate"].max() + 0.5)
ax.set_title("USD Exchange Rate History (March 2026)", fontsize=14)
ax.grid(True, linestyle="--", alpha=0.7)

(line,) = ax.plot([], [], lw=3, color="#1f77b4", marker="o")
text = ax.text(
    0.02,
    0.95,
    "",
    transform=ax.transAxes,
    fontweight="bold",
    bbox=dict(facecolor="white", alpha=0.8),
)


def animate(i):
    current_data = df.iloc[: i + 1]
    # Matplotlib animation працює краще з датами, якщо їх явно передати як об'єкти
    line.set_data(current_data["exchange_date"], current_data["currency_rate"])

    latest_rate = current_data["currency_rate"].iloc[-1]
    latest_date = current_data["exchange_date"].iloc[-1].strftime("%Y-%m-%d")

    text.set_text(f"Date: {latest_date}\nRate: {latest_rate:.2f} UAH")
    return line, text


# 4. Створення анімації
# interval=400 (0.4 сек на кадр). frames=len(df) - по одному кадру на кожен день
ani = animation.FuncAnimation(fig, animate, frames=len(df), interval=400, blit=True)

# 5. Збереження
ani.save("usd_trend.gif", writer="pillow")
print(f"✅ GIF створена успішно для {len(df)} днів історії.")
