# Research Workflow

Paper management for thesis writing with Claude Code.

## Setup

```bash
git clone https://github.com/JonasTischer/research-workflow.git
cd research-workflow
./scripts/setup.sh

# Add to ~/.zshrc:
export GOOGLE_API_KEY="..."    # Get from aistudio.google.com/apikey
export BRAVE_API_KEY="..."     # Optional, from brave.com/search/api

# Start watcher
./scripts/install-watcher.sh
```

No Anthropic API key needed — Claude Code does summaries and verification directly.

## Scripts (For Search & Download)

```bash
# Find papers
python src/web_search.py scholar "query"
python src/web_search.py arxiv "query"

# Download
python src/download.py arxiv "1706.03762"
python src/download.py doi "10.1000/xyz"
```

## Claude Code Does Directly

**Read papers:**
```bash
cat markdown/paper_name.md
ls markdown/
```

**Summarize:** Read the markdown, write to `summaries/paper_name.summary.md`

**Verify citations:** Read the paper, check if claim matches source

**Search within papers:**
```bash
grep -r "attention" markdown/
```

## Workflow

1. Search → `python src/web_search.py scholar "topic"`
2. Download → `python src/download.py arxiv "id"`
3. Read → `cat markdown/paper_name.md`
4. Summarize → Claude writes to `summaries/`
5. Write → Draft with citations
6. Verify → Claude re-reads paper, confirms claim
7. Commit → Entire captures reasoning

## Key Principle

Claude Code reads the markdown files directly — no API calls needed for understanding, summarizing, or verifying papers. Scripts are only for external operations (web search, downloads, PDF conversion).
