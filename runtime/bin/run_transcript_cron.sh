#!/usr/bin/env bash
# Polya Zuma Debate Corpus Automated Cron Ingestion Runner
# Processes batches of transcripts safely with lockfile protection

LOCK_FILE="/home/ubuntu/.polya/fetcher.lock"
LOG_FILE="/home/ubuntu/.polya/logs/batch_transcript_cron.log"
PYTHON_BIN="/home/ubuntu/venv/bin/python3"
SCRIPT_PATH="/home/ubuntu/Polya-AI/runtime/bin/batch_transcript_fetcher.py"

mkdir -p /home/ubuntu/.polya/logs

exec 200>"$LOCK_FILE"
flock -n 200 || {
    echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Another fetcher instance is already running. Exiting." >> "$LOG_FILE"
    exit 0
}

echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Starting scheduled transcript ingestion batch..." >> "$LOG_FILE"
$PYTHON_BIN "$SCRIPT_PATH" --limit 30 >> "$LOG_FILE" 2>&1
echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Scheduled batch complete." >> "$LOG_FILE"
