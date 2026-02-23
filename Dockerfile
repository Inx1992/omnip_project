# Використовуємо легкий образ Python
FROM python:3.11-slim

# Встановлюємо uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Встановлюємо робочу директорію
WORKDIR /app

# Копіюємо файли залежностей
COPY pyproject.toml uv.lock ./

# Встановлюємо залежності (без створення віртуального середовища всередині контейнера)
RUN uv sync --frozen

# Копіюємо решту коду
COPY . .

# Команда за замовчуванням
CMD ["uv", "run", "src/main.py"]