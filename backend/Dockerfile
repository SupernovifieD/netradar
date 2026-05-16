FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NETRADAR_DATABASE_PATH=/data/netradar.db \
    NETRADAR_DAILY_DATABASE_PATH=/data/netradar_daily.db \
    NETRADAR_SERVICES_FILE=/app/services.json \
    NETRADAR_SETTINGS_FILE=/app/netradar.config.json \
    NETRADAR_HOST=0.0.0.0 \
    NETRADAR_PORT=5001 \
    TZ=UTC

WORKDIR /app/backend

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates iputils-ping tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./
COPY services.json /app/services.json
COPY frontend/netradar.config.json /app/netradar.config.json

RUN mkdir -p /data

EXPOSE 5001

CMD ["python", "run.py"]
