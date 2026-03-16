import os
import pandas as pd
import matplotlib
import seaborn as sns

# ВАЖЛИВО: Agg для хмарного середовища
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pyathena import connect

# 1. Налаштування підключення
AWS_REGION = os.getenv("AWS_REGION", "eu-central-1")
S3_STAGING_DIR = os.getenv("S3_STAGING_DIR")


def get_data():
    if not S3_STAGING_DIR:
        raise ValueError("❌ S3_STAGING_DIR не встановлена!")

    conn = connect(s3_staging_dir=S3_STAGING_DIR, region_name=AWS_REGION)

    # Запит для порівняння двох валют (USD та EUR) по днях
    query = f"""
    -- cache_buster: {pd.Timestamp.now()}
    SELECT 
        u.exchange_date, 
        u.currency_rate as usd_rate, 
        e.currency_rate as eur_rate
    FROM "omnip_db_dev_silver"."fct_currency_rates" u
    JOIN "omnip_db_dev_silver"."fct_currency_rates" e 
      ON u.exchange_date = e.exchange_date
    WHERE u.currency_code = 'USD' AND e.currency_code = 'EUR'
    """
    df = pd.read_sql(query, conn)
    return df


# 2. Отримуємо дані
df = get_data()

if df.empty:
    print("⚠️ Попередження: Дані порожні.")
    exit(0)

# 3. Налаштування стилю (як на скріншоті)
sns.set_theme(style="dark")
fig, ax = plt.subplots(figsize=(8, 8))

# Малюємо 3 шари:
# 1. Scatterplot (точки)
sns.scatterplot(data=df, x="usd_rate", y="eur_rate", s=15, color=".15", ax=ax)

# 2. Histplot (2D теплова карта щільності)
sns.histplot(
    data=df, x="usd_rate", y="eur_rate", bins=30, pthresh=0.1, cmap="mako", ax=ax
)

# 3. KDE Plot (білі контурні лінії)
sns.kdeplot(
    data=df, x="usd_rate", y="eur_rate", levels=5, color="w", linewidths=1, ax=ax
)

# Оформлення
ax.set_title(
    "USD vs EUR: Bivariate Distribution Analysis",
    fontsize=14,
    fontweight="bold",
    color="white",
    pad=20,
)
fig.patch.set_facecolor("#212529")  # Темний фон навколо графіка
ax.set_facecolor("#212529")

# 4. Збереження (ВАЖЛИВО: .png, бо це не анімація)
output_filename = "usd_eur_bivariate.png"
plt.savefig(output_filename, dpi=300, bbox_inches="tight")
print(f"✅ Bivariate графік створено успішно: {output_filename}")
