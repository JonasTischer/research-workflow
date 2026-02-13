#!/bin/bash
# Uninstall the paper watcher service

PLIST_NAME="com.research-workflow.watcher"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"

if [ -f "$PLIST_PATH" ]; then
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    rm "$PLIST_PATH"
    echo "✓ Watcher service uninstalled"
else
    echo "Service not installed"
fi
