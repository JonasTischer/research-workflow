# Research Workflow

Paper management for thesis writing.

## Setup

```bash
git clone https://github.com/JonasTischer/research-workflow.git
cd research-workflow
./scripts/setup.sh

# Add to ~/.zshrc:
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="..."

# Start watcher
./scripts/install-watcher.sh
```

## Commands

### Find & Download

```bash
python src/web_search.py scholar "query"      # Academic search
python src/web_search.py arxiv "query"        # Preprints
python src/download.py arxiv "1706.03762"     # Download
python src/download.py doi "10.1000/xyz"      # From DOI
```

### Read

```bash
python src/search.py list                     # All papers
python src/search.py read <name>              # Full text
python src/search.py summary <name>           # AI summary
python src/search.py find "query"             # Search
```

### Verify

```bash
python src/search.py verify <paper> "claim"   # Check citation
```

### Entire (Session Capture)

```bash
entire explain --commit HEAD                  # See AI reasoning
entire rewind                                 # Browse sessions
```

## Workflow

1. Search → `web_search.py scholar "topic"`
2. Download → `download.py arxiv "id"`
3. Read → `search.py read <name>`
4. Write → Draft with citations
5. Verify → `search.py verify <paper> "claim"`
6. Commit → Entire captures reasoning
