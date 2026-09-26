# Lean Python 3.11 runtime for Polya Dialectical Web Arena
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV POLYA_RUNTIME_DIR=/app/runtime
ENV POLYA_DB_PATH=/data/polya/polya_index.db
ENV POLYA_AUDIO_CACHE=/data/polya/audio_cache
ENV NINE_ROUTER_URL=http://9router:20128/v1/chat/completions

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and runtime assets
COPY web /app/web
COPY runtime /app/runtime
COPY schemas /app/schemas

WORKDIR /app/web

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -f http://127.0.0.1:8000/ || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
