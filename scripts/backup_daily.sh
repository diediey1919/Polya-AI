#!/usr/bin/env bash
set -euo pipefail

# Konfigurasi Lokasi
DB_SOURCE="/home/ubuntu/.polya/polya_index.db"
BACKUP_ROOT="/home/ubuntu/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
TARGET_DIR="${BACKUP_ROOT}/polya_daily_${TIMESTAMP}"
RETENTION_DAYS=7

echo "[$(date --iso-8601=seconds)] Memulai backup harian polya_index.db..."

# 1. Pastikan database sumber ada
if [[ ! -f "$DB_SOURCE" ]]; then
    echo "[ERROR] Database tidak ditemukan di $DB_SOURCE" >&2
    exit 1
fi

mkdir -p "$TARGET_DIR"

# 2. Backup Atomik SQLite (tunggu hingga 30 detik jika sedang ada transaksi aktif)
sqlite3 "$DB_SOURCE" -cmd ".timeout 30000" ".backup '${TARGET_DIR}/polya_index.db'"

# 3. Kompresi ke .gz (dan otomatis hapus file .db mentah untuk menghemat disk)
gzip -9 "${TARGET_DIR}/polya_index.db"

# 4. Buat checksum SHA-256
sha256sum "${TARGET_DIR}/polya_index.db.gz" > "${TARGET_DIR}/polya_index.db.gz.sha256"

# 5. Cadangkan konfigurasi Nginx jika terbaca (dukung 'apologets' dan 'apologets.com')
if [[ -r "/etc/nginx/sites-available/apologets" ]]; then
    cp "/etc/nginx/sites-available/apologets" "${TARGET_DIR}/apologets.nginx.conf"
elif [[ -r "/etc/nginx/sites-available/apologets.com" ]]; then
    cp "/etc/nginx/sites-available/apologets.com" "${TARGET_DIR}/apologets.nginx.conf"
fi

# 6. Hapus folder backup harian (polya_daily_*) yang lebih tua dari 7 hari
DELETED_COUNT=$(find "$BACKUP_ROOT" -maxdepth 1 -type d -name "polya_daily_*" -mtime +${RETENTION_DAYS} -print -exec rm -rf {} + | wc -l)

echo "[$(date --iso-8601=seconds)] Backup sukses: ${TARGET_DIR}/polya_index.db.gz | Backup lama dihapus: ${DELETED_COUNT} folder."
