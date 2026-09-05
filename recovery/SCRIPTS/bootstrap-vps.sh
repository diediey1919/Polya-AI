#!/bin/bash
# bootstrap-vps.sh - Prepare a fresh Ubuntu VPS for Hermes Agent installation
# This script installs system dependencies and prepares the environment

set -e

echo "=========================================="
echo "Hermes Agent VPS Bootstrap"
echo "=========================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
  echo "Please run as normal user (not root)"
  exit 1
fi

echo ""
echo "Step 1: Update system packages..."
sudo apt update
sudo apt upgrade -y

echo ""
echo "Step 2: Install essential packages..."
sudo apt install -y \
  git \
  curl \
  wget \
  build-essential \
  cmake \
  pkg-config \
  python3.11 \
  python3.11-venv \
  python3.11-dev \
  ffmpeg \
  libasound2-dev \
  portaudio19-dev \
  libssl-dev \
  libffi-dev \
  libxml2-dev \
  libxslt1-dev \
  zlib1g-dev \
  libjpeg-dev \
  libpng-dev \
  sqlite3 \
  ca-certificates \
  gnupg

echo ""
echo "Step 3: Install Node.js v22..."
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs

echo ""
echo "Step 4: Install uv (Python package manager)..."
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"

echo ""
echo "Step 5: Configure PATH..."
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc

echo ""
echo "Step 6: Create Hermes directory..."
mkdir -p ~/.hermes
chmod 700 ~/.hermes

echo ""
echo "=========================================="
echo "Bootstrap complete!"
echo ""
echo "Next steps:"
echo "  1. Reload shell: source ~/.bashrc"
echo "  2. Install Hermes: ./install-hermes.sh"
echo "  3. Restore config: ./restore-hermes.sh"
echo "=========================================="