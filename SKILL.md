# Research Workflow Skill

AI-powered research paper management for academic writing.

## Quick Setup

```bash
# Clone
git clone https://github.com/JonasTischer/research-workflow.git
cd research-workflow

# Install with uv
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt

# Configure
cp config.example.yaml config.yaml
# Edit config.yaml

# Initialize Entire
entire init

# Start watcher service
./scripts/install-watcher.sh
```

## Commands

### AI Session Tracing (Entire)

```bash
entire explain --commit HEAD   # See AI reasoning
entire rewind                  # Browse sessions
entire status                  # Check status
```

### Paper Search & Read

```bash
python src/search.py find "query"              # Semantic search
python src/search.py list                       # List all papers
python src/search.py read <name>                # Full paper
python src/search.py read <name> -s "Results"   # Specific section
python src/search.py summary <name>             # AI summary
```

### Citation Verification

```bash
# Verify single claim
python src/search.py verify <paper> "claim"

# Check all LaTeX citations
python src/citation_checker.py ./chapters ./refs.bib

# Quick check (keys only)
python src/citation_checker.py ./chapters ./refs.bib --no-verify
```

### Watcher Service

```bash
python src/watcher.py --once           # Process existing
./scripts/install-watcher.sh           # Install service
launchctl list | grep research         # Check status
tail -f logs/watcher.log               # View logs
./scripts/uninstall-watcher.sh         # Remove service
```

## Environment Variables

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="..."
export GOOGLE_CLOUD_PROJECT="your-project"
```

## Workflow

1. Add paper to Zotero → PDF auto-saves → Watcher converts to markdown
2. `search.py find` → discover relevant papers
3. `search.py read` → get full content
4. Write with Claude → verify citations → commit
5. Entire captures the AI reasoning
