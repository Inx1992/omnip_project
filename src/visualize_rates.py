import os
import pandas as pd
import matplotlib
import seaborn as sns

# ВАЖЛИВО: встановлюємо бекенд ДО імпорту pyplot
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from pyathena import connect

# 1. Налаштування підключення
AWS_REGION = os.getenv("AWS_REGION", "eu-central-1")
S3_STAGING_DIR = os.getenv("S3_STAGING_DIR")


def get_data():
    if not S3_STAGING_DIR:
        raise ValueError("❌ Енвайронмент змінна S3_STAGING_DIR не встановлена!")

    conn = connect(s3_staging_dir=S3_STAGING_DIR, region_name=AWS_REGION)

    # Беремо топ-15 валют за зміною курсу з Gold шару
    query = f"""
    -- cache_buster: {pd.Timestamp.now()}
    SELECT 
        currency_code, 
        total_monthly_growth_pct, 
        market_trend
    FROM "omnip_db_dev_gold"."fct_currency_growth"
    WHERE currency_code NOT IN ('XPD', 'XPT', 'XAU', 'XAG') -- прибираємо метали для кращого масштабу
    ORDER BY ABS(total_monthly_growth_pct) DESC
    LIMIT 15
    """
    df = pd.read_sql(query, conn)
    print(f"📊 DEBUG: Отримано {len(df)} валют з Gold шару")
    return df


# 2. Отримуємо та готуємо дані
df = get_data()

if df.empty:
    print("⚠️ Попередження: Дані порожні.")
    exit(0)

# Сортуємо для красивого вигляду на графіку
df = df.sort_values("total_monthly_growth_pct", ascending=False)

# 3. Налаштування стилю Seaborn
sns.set_theme(style="whitegrid")
fig, ax = plt.subplots(figsize=(12, 7))


def animate(i):
    ax.clear()

    # Створюємо ефект "виростання" стовпчиків
    temp_df = df.copy()
    temp_df["current_val"] = (
        temp_df["total_monthly_growth_pct"] * (i + 1) / 20
    )  # 20 кадрів на ріст

    # Кольори: зелений для UP, червоний для DOWN
    colors = [
        "#2ecc71" if x >= 0 else "#e74c3c" for x in temp_df["total_monthly_growth_pct"]
    ]

    barplot = sns.barplot(
        data=temp_df,
        x="currency_code",
        y="current_val",
        palette=colors,
        ax=ax,
        hue="currency_code",
        legend=False,
    )

    # Налаштування осей
    y_limit = max(df["total_monthly_growth_pct"].abs()) + 0.5
    ax.set_ylim(-y_limit, y_limit)

    ax.set_title(
        "Market Dynamics: Monthly Growth % (March 2026)",
        fontsize=16,
        fontweight="bold",
        pad=20,
    )
    ax.set_ylabel("Growth Percentage (%)", fontsize=12)
    ax.set_xlabel("Currency Code", fontsize=12)

    # Додаємо підписи відсотків над/під стовпчиками
    for p in barplot.patches:
        height = p.get_height()
        ax.annotate(
            f"{height:.2f}%",
            (p.get_x() + p.get_width() / 2.0, height),
            ha="center",
            va="bottom" if height > 0 else "top",
            xytext=(0, 7 if height > 0 else -7),
            textcoords="offset points",
            fontsize=10,
            fontweight="bold",
        )


# 4. Створення анімації (20 кадрів для плавного виростання)
ani = animation.FuncAnimation(fig, animate, frames=20, interval=100, repeat=False)

# 5. Збереження
output_filename = "usd_trend.gif"
ani.save(output_filename, writer="pillow")
print(f"✅ Аналітичний GIF створено успішно: {output_filename}")
