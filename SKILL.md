# Thesis Workflow Skill

AI-powered research paper management for academic writing.

## Setup

```bash
cd /path/to/thesis-workflow
pip install -r requirements.txt
cp config.example.yaml config.yaml
# Edit config.yaml with your paths

# Initialize Entire for session capture
entire init
```

## Commands

### AI Session Tracing (Entire)

```bash
# See AI reasoning behind a commit
entire explain --commit HEAD

# Browse captured sessions
entire rewind

# Check status
entire status
```

### Paper Management

```bash
# Watch for new PDFs and process automatically
python src/watcher.py

# Process existing PDFs once
python src/watcher.py --once

# Upload papers to Google for search indexing
python src/search.py upload
```

### Search & Read

```bash
# Search for relevant papers
python src/search.py find "attention mechanisms in transformers"

# List all papers in library
python src/search.py list

# Read full paper
python src/search.py read vaswani2017

# Read specific section
python src/search.py read vaswani2017 --section "Results"

# Read AI-generated summary
python src/search.py summary vaswani2017
```

### Citation Verification

```bash
# Verify a specific claim
python src/search.py verify vaswani2017 "Transformers achieved 28.4 BLEU"

# Check all citations in LaTeX files
python src/citation_checker.py ./chapters ./references.bib --markdown-dir ./markdown

# Quick check (keys only, no claim verification)
python src/citation_checker.py ./chapters ./references.bib --no-verify
```

## Workflow

1. **Find paper** → Add to Zotero → PDF auto-saves to `papers/`
2. **Watcher detects** → Converts to markdown → Generates summary → Uploads to Google
3. **Writing** → Search papers → Read relevant ones → Write with citations
4. **Before commit** → Pre-commit hook verifies all citations

## Environment Variables

```bash
export THESIS_DIR=/path/to/thesis-workflow
export THESIS_PAPERS_DIR=/path/to/papers
export THESIS_MARKDOWN_DIR=/path/to/markdown
export THESIS_SUMMARIES_DIR=/path/to/summaries
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_API_KEY=...
```

## Git Hooks

Install pre-commit hook to catch citation issues:

```bash
cp hooks/pre-commit .git/hooks/
chmod +x .git/hooks/pre-commit
```
