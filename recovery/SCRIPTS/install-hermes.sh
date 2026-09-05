#!/bin/bash
# install-hermes.sh - Install Hermes Agent from upstream repository
# This script clones and installs Hermes Agent v0.21.0

set -e

echo "=========================================="
echo "Hermes Agent Installation"
echo "=========================================="

HERMES_HOME="$HOME/.hermes"
HERMES_REPO="https://github.com/NousResearch/hermes-agent.git"
HERMES_VERSION="63279301"  # Local commit with patches

echo ""
echo "Step 1: Clone Hermes Agent repository..."
if [ -d "$HERMES_HOME/hermes-agent" ]; then
  echo "Hermes Agent already exists at $HERMES_HOME/hermes-agent"
  read -p "Remove and re-clone? (y/N): " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "$HERMES_HOME/hermes-agent"
  else
    echo "Skipping clone, using existing installation"
  fi
fi

if [ ! -d "$HERMES_HOME/hermes-agent" ]; then
  git clone "$HERMES_REPO" "$HERMES_HOME/hermes-agent"
fi

echo ""
echo "Step 2: Checkout specific commit..."
cd "$HERMES_HOME/hermes-agent"
git checkout "$HERMES_VERSION"

echo ""
echo "Step 3: Install Python dependencies..."
# Check if venv exists
if [ ! -d "venv" ]; then
  python3.11 -m venv venv
fi

source venv/bin/activate

echo "Installing Python packages..."
# Install from requirements if available, otherwise install key packages
if [ -f "../../recovery/PYTHON/requirements-hermes.txt" ]; then
  pip install -r "../../recovery/PYTHON/requirements-hermes.txt"
else
  echo "Warning: requirements-hermes.txt not found"
  echo "Installing core dependencies manually..."
  pip install --upgrade pip
  pip install torch torchaudio transformers openai pydantic \
    discord.py fastapi uvicorn httpx aiohttp \
    python-dotenv pyyaml rich click typer
fi

echo ""
echo "Step 4: Install Node dependencies..."
npm install

echo ""
echo "Step 5: Install Hermes CLI..."
# Create symlink in ~/.local/bin
mkdir -p "$HOME/.local/bin"
ln -sf "$HERMES_HOME/hermes-agent/venv/bin/python" "$HOME/.local/bin/hermes-python"

# Create hermes wrapper script
cat > "$HOME/.local/bin/hermes" << 'WRAPPER'
#!/bin/bash
export HERMES_HOME="$HOME/.hermes"
cd "$HERMES_HOME/hermes-agent"
exec "$HERMES_HOME/hermes-agent/venv/bin/python" run_agent.py "$@"
WRAPPER

chmod +x "$HOME/.local/bin/hermes"

echo ""
echo "Step 6: Verify installation..."
if command -v hermes &> /dev/null; then
  echo "✓ Hermes CLI installed"
  hermes --version || echo "(version check may require config)"
else
  echo "✗ Hermes CLI not found in PATH"
  echo "  Add ~/.local/bin to PATH: export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo ""
echo "=========================================="
echo "Installation complete!"
echo ""
echo "Next steps:"
echo "  1. Restore configuration: ./restore-hermes.sh"
echo "  2. Apply patches: cd ~/.hermes/hermes-agent && git apply ~/recovery/PATCHES/*.patch"
echo "  3. Configure secrets: see recovery/SECRETS/README.md"
echo "=========================================="