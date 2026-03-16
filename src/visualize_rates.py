import os
import pandas as pd
import matplotlib
import seaborn as sns

# ВАЖЛИВО: Налаштування бекенду для роботи без GUI
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pyathena import connect

# 1. Налаштування підключення
AWS_REGION = os.getenv("AWS_REGION", "eu-central-1")
S3_STAGING_DIR = os.getenv("S3_STAGING_DIR")


def get_data():
    conn = connect(s3_staging_dir=S3_STAGING_DIR, region_name=AWS_REGION)
    query = """
    SELECT 
        u.exchange_date, 
        u.currency_rate as usd_rate, 
        e.currency_rate as eur_rate
    FROM "omnip_db_dev_silver"."fct_currency_rates" u
    JOIN "omnip_db_dev_silver"."fct_currency_rates" e 
      ON u.exchange_date = e.exchange_date
    WHERE u.currency_code = 'USD' AND e.currency_code = 'EUR'
    """
    return pd.read_sql(query, conn)


df = get_data()

# 2. Налаштування стилю "White" з підписами
sns.set_theme(style="white")
f, ax = plt.subplots(figsize=(8, 8))

# Шар 1: Точки (Щоденні записи)
# Збільшуємо розмір (s=25) та робимо колір насиченим (black або darkblue)
# alpha=0.8 дозволяє бачити накладання точок, але залишає їх чіткими
sns.scatterplot(
    data=df,
    x="usd_rate",
    y="eur_rate",
    s=25,
    color="black",
    marker="o",
    label="Daily Rate Record",
    ax=ax,
    alpha=0.8,
    zorder=3,  # Виносимо точки на передній план
)

# Шар 2: Histplot (Теплова карта фоном)
sns.histplot(
    data=df,
    x="usd_rate",
    y="eur_rate",
    bins=30,
    pthresh=0.1,
    cmap="mako",
    ax=ax,
    zorder=1,
)

# Шар 3: KDE Plot (Контурні лінії)
sns.kdeplot(
    data=df,
    x="usd_rate",
    y="eur_rate",
    levels=5,
    color="#e74c3c",  # Зробимо контури червоними для контрасту з точками
    linewidths=1.5,
    ax=ax,
    zorder=2,
)

# Оформлення
ax.set_title(
    "Daily Currency Correlation: USD vs EUR", fontsize=16, fontweight="bold", pad=20
)
ax.set_xlabel("USD Exchange Rate (UAH)", fontsize=12)
ax.set_ylabel("EUR Exchange Rate (UAH)", fontsize=12)
ax.legend(loc="upper left")  # Додаємо легенду для пояснення, що точки — це записи

sns.despine()

# 4. Збереження
output_filename = "usd_eur_bivariate.png"
plt.savefig(output_filename, dpi=300, bbox_inches="tight")
print(f"✅ Графік з чіткими щоденними точками створено: {output_filename}")
