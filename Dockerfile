FROM python:3.11-slim

# 1. Встановлюємо uv (це залишаємо, це база)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 2. Системні залежності (додаємо --no-install-recommends для ваги)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    libxml2-dev \
    libxslt-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 3. КЕШУВАННЯ ЗАЛЕЖНОСТЕЙ (Найважливіший крок)
# Копіюємо ТІЛЬКИ конфіги бібліотек. 
# Якщо ти зміниш код у src/, цей шар НЕ буде перезбиратися.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

# 4. DBT DEPS (Окремий шар)
# Копіюємо тільки папку dbt, щоб встановити пакети dbt до копіювання всього коду.
COPY dbt/packages.yml dbt/dbt_project.yml ./dbt/
RUN .venv/bin/dbt deps --project-dir ./dbt

# 5. КОПІЮЄМО РЕШТУ КОДУ
# Тепер будь-яка зміна в Python-скриптах займе 1 секунду при збірці.
COPY . .

# 6. НАЛАШТУВАННЯ PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV DBT_PROFILES_DIR=/app/dbt
ENV DBT_SEND_ANONYMOUS_USAGE_STATS=False

CMD ["python", "src/ingest_nbu_rates.py"]