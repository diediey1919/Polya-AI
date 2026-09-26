#!/usr/bin/env bash
# ==============================================================================
# VPS Infrastructure Orchestration & Deployment Engine
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.orchestrator.yml"
ENV_FILE="${SCRIPT_DIR}/.env.orchestrator"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_ok() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_err() { echo -e "${RED}[ERROR]${NC} $1"; }

check_prerequisites() {
    log_info "Memeriksa dependensi sistem & Docker engine..."
    if ! command -v docker &>/dev/null; then
        log_err "Docker belum terpasang. Pasang dengan: sudo apt install docker.io"
        exit 1
    fi
    if ! docker compose version &>/dev/null; then
        log_err "Docker Compose V2 belum terpasang."
        exit 1
    fi

    # Cek ketersediaan ruang penyimpanan (disk space threshold: 1.5GB)
    AVAIL_KB=$(df --output=avail "$SCRIPT_DIR" | tail -n 1)
    if [ "$AVAIL_KB" -lt 1500000 ]; then
        log_warn "Kapasitas disk tersisa kurang dari 1.5GB (${AVAIL_KB}KB tersisa). Pertimbangkan pembersihan image usang."
    else
        log_ok "Kapasitas disk aman: $((AVAIL_KB / 1024)) MB tersedia."
    fi

    log_ok "Docker engine & Compose siap."
}

validate_configs() {
    log_info "Memvalidasi sintaks Docker Compose orchestrator..."
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" config > /dev/null
    log_ok "Konfigurasi Docker Compose valid."
}

build_images() {
    local target="${1:-}"
    log_info "Memulai proses build container images..."
    if [ -n "$target" ]; then
        docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" build "$target"
    else
        docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" build
    fi
    log_ok "Build container selesai."
}

migrate_systemd() {
    log_warn "Menonaktifkan unit systemd bare-metal untuk menghindari konflik port..."
    sudo systemctl stop 9router.service || true
    sudo systemctl stop polya-web.service || true
    log_ok "Layanan bare-metal dimatikan untuk migrasi modular ke Docker."
}

deploy_services() {
    local target="${1:-}"
    check_prerequisites
    validate_configs

    log_info "Menjalankan deployment container orchestrator..."
    if [ -n "$target" ]; then
        docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d "$target"
    else
        docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d
    fi

    log_info "Memverifikasi status container yang berjalan..."
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps
    log_ok "Otomatisasi deployment berhasil dieksekusi."
}

stop_services() {
    log_info "Menghentikan semua container orchestrator..."
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" down
    log_ok "Container dihentikan secara aman."
}

show_status() {
    log_info "Status Container Orchestrator:"
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps
    echo ""
    log_info "Statistik Resource Penggunaan:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" || true
}

case "${1:-status}" in
    check)
        check_prerequisites
        validate_configs
        ;;
    build)
        check_prerequisites
        validate_configs
        build_images "${2:-}"
        ;;
    migrate)
        migrate_systemd
        ;;
    up|deploy)
        deploy_services "${2:-}"
        ;;
    down|stop)
        stop_services
        ;;
    status)
        show_status
        ;;
    *)
        echo "Penggunaan: $0 {check|build|migrate|up|deploy|down|status} [service_name]"
        exit 1
        ;;
esac
