#!/bin/bash
# Install the paper watcher as a macOS launchd service
# Usage: ./install-watcher.sh /path/to/thesis-workflow

set -e

WORKFLOW_DIR="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
PLIST_NAME="com.research-workflow.watcher"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"

# Verify the workflow directory
if [ ! -f "$WORKFLOW_DIR/src/watcher.py" ]; then
    echo "Error: watcher.py not found in $WORKFLOW_DIR/src/"
    echo "Usage: $0 /path/to/thesis-workflow"
    exit 1
fi

# Find Python
PYTHON_PATH=$(which python3)
if [ -z "$PYTHON_PATH" ]; then
    echo "Error: python3 not found"
    exit 1
fi

echo "Installing watcher service..."
echo "  Workflow dir: $WORKFLOW_DIR"
echo "  Python: $PYTHON_PATH"

# Create the plist
cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>${PYTHON_PATH}</string>
        <string>${WORKFLOW_DIR}/src/watcher.py</string>
        <string>--config</string>
        <string>${WORKFLOW_DIR}/config.yaml</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>${WORKFLOW_DIR}</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <true/>
    
    <key>StandardOutPath</key>
    <string>${WORKFLOW_DIR}/logs/watcher.log</string>
    
    <key>StandardErrorPath</key>
    <string>${WORKFLOW_DIR}/logs/watcher.error.log</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
        <key>ANTHROPIC_API_KEY</key>
        <string>${ANTHROPIC_API_KEY}</string>
        <key>GOOGLE_API_KEY</key>
        <string>${GOOGLE_API_KEY}</string>
    </dict>
</dict>
</plist>
EOF

# Create logs directory
mkdir -p "$WORKFLOW_DIR/logs"

# Load the service
launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"

echo ""
echo "✓ Watcher service installed and started!"
echo ""
echo "Commands:"
echo "  Check status:  launchctl list | grep research-workflow"
echo "  View logs:     tail -f $WORKFLOW_DIR/logs/watcher.log"
echo "  Stop:          launchctl unload $PLIST_PATH"
echo "  Start:         launchctl load $PLIST_PATH"
echo "  Uninstall:     rm $PLIST_PATH"
