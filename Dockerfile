FROM python:3.11-slim

# 1. Встановлюємо uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 2. Встановлюємо системні залежності для dbt-athena (потрібен git)
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 3. Встановлюємо залежності (використовуємо кешування uv)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

# 4. Копіюємо проект
COPY . .

# 5. Налаштовуємо оточення
ENV PATH="/app/.venv/bin:$PATH"
ENV DBT_PROFILES_DIR=/app/dbt
# Вимикаємо анонімну статистику dbt для швидкості
ENV DBT_SEND_ANONYMOUS_USAGE_STATS=False

# За замовчуванням запускаємо скрейпер, 
# але в Airflow ми будемо перебивати цю команду
CMD ["python", "src/ingest_nbu_rates.py"]