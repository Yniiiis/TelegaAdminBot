# Образ для запуска бота в контейнере (передайте BOT_TOKEN через env / secrets).
FROM python:3.12-slim-bookworm

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini .
COPY alembic/ ./alembic/
COPY bot/ ./bot/
COPY main.py .

# Том для SQLite при необходимости: -v bot-data:/app/data
RUN mkdir -p /app/data

CMD ["python", "main.py"]
