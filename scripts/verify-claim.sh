#!/bin/bash
# Spawn a verification subagent for a specific claim
#
# Usage: ./scripts/verify-claim.sh <paper> "claim to verify"
#
# Example:
#   ./scripts/verify-claim.sh vaswani2017 "achieved 28.4 BLEU on WMT 2014"

set -e

PAPER="$1"
CLAIM="$2"

if [ -z "$PAPER" ] || [ -z "$CLAIM" ]; then
    echo "Usage: $0 <paper_name> \"claim to verify\""
    echo ""
    echo "Example:"
    echo "  $0 vaswani2017 \"achieved 28.4 BLEU on WMT 2014\""
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Check paper exists
if [ ! -f "$PROJECT_DIR/markdown/${PAPER}.md" ]; then
    # Try fuzzy match
    MATCH=$(ls "$PROJECT_DIR/markdown/" 2>/dev/null | grep -i "$PAPER" | head -1)
    if [ -n "$MATCH" ]; then
        PAPER="${MATCH%.md}"
        echo "Matched paper: $PAPER"
    else
        echo "Error: Paper not found: $PAPER"
        echo "Available papers:"
        ls "$PROJECT_DIR/markdown/"
        exit 1
    fi
fi

# Spawn verification subagent
cd "$PROJECT_DIR"
claude --print "Verify this citation claim:

PAPER: $PAPER
CLAIM: $CLAIM

Read the paper at markdown/${PAPER}.md and verify the claim following agents/verifier/CLAUDE.md guidelines."
