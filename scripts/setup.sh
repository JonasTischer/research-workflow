#!/bin/bash
# Quick setup script for research-workflow
set -e

echo "🔬 Research Workflow Setup"
echo "=========================="
echo ""

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Check for Entire
if ! command -v entire &> /dev/null; then
    echo "Installing Entire..."
    curl -fsSL https://entire.io/install.sh | bash
fi

# Create venv and install deps
echo ""
echo "Setting up Python environment..."
uv venv
source .venv/bin/activate
uv pip install -e .

# Create config if not exists
if [ ! -f config.yaml ]; then
    echo ""
    echo "Creating config.yaml from template..."
    cp config.example.yaml config.yaml
    echo "⚠️  Edit config.yaml with your paths and API keys"
fi

# Create directories
mkdir -p papers markdown summaries logs

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit config.yaml with your settings"
echo "  2. Set environment variables:"
echo "     export ANTHROPIC_API_KEY='sk-ant-...'"
echo "     export GOOGLE_API_KEY='...'"
echo "  3. Setup Zotero with ZotFile (see README)"
echo "  4. Initialize Entire in your thesis repo:"
echo "     cd ~/thesis && entire init"
echo "  5. Start the watcher:"
echo "     ./scripts/install-watcher.sh"
echo ""
echo "Run 'source .venv/bin/activate' to activate the environment"
