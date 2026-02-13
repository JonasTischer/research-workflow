# Research Workflow

AI-powered research paper management for academic writing with Claude Code.

## Overview

A complete workflow for managing research papers during thesis/dissertation writing:

- **Automatic processing**: PDFs → Markdown → AI summaries
- **Smart search**: Semantic search via Google's File Search API  
- **Citation verification**: Verify claims against actual paper content
- **Session capture**: Track AI reasoning with Entire
- **Git hooks**: Block commits with invalid citations

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Zotero    │────▶│   Watcher   │────▶│  Markdown   │
│  (ZotFile)  │     │  (Marker)   │     │  + Summary  │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Google    │
                    │ File Search │
                    └─────────────┘
                           │
                           ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Claude    │────▶│    Write    │────▶│   Commit    │
│    Code     │     │  + Verify   │     │  (Entire)   │
└─────────────┘     └─────────────┘     └─────────────┘
```

## Requirements

- macOS (for launchd service) or Linux
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (modern Python package manager)
- [Claude Code](https://claude.ai/code) subscription
- Google Cloud account (for File Search API)
- [Zotero](https://www.zotero.org/) with ZotFile and Better BibTeX

## Installation

### 1. Install System Dependencies

```bash
# macOS
brew install python@3.11

# Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Marker for PDF conversion
uv tool install marker-pdf

# Install Entire for session capture
curl -fsSL https://entire.io/install.sh | bash
```

### 2. Clone and Setup

```bash
git clone https://github.com/JonasTischer/research-workflow.git
cd research-workflow

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # or: source .venv/bin/activate.fish
uv pip install -r requirements.txt

# Copy and configure
cp config.example.yaml config.yaml
```

### 3. Configure `config.yaml`

```yaml
paths:
  papers: ~/Papers          # Where Zotero/ZotFile saves PDFs
  markdown: ./markdown      # Converted markdown output
  summaries: ./summaries    # AI-generated summaries

# Add your API keys (or set as environment variables)
# ANTHROPIC_API_KEY: sk-ant-...
# GOOGLE_API_KEY: ...
```

### 4. Setup Zotero

1. **Install Zotero**: https://www.zotero.org/download/

2. **Install ZotFile** (auto-saves PDFs to folder):
   - Download from http://zotfile.com/
   - Zotero → Tools → Add-ons → Install from file
   - Configure: Tools → ZotFile Preferences → Location of Files → `~/Papers`

3. **Install Better BibTeX** (auto-exports .bib):
   - Download from https://retorque.re/zotero-better-bibtex/
   - Install same way as ZotFile
   - Right-click library → Export Library → Better BibLaTeX
   - Check "Keep updated" → Save as `references.bib` in thesis folder

### 5. Setup Google File Search

```bash
# Install gcloud CLI
brew install google-cloud-sdk

# Authenticate
gcloud auth application-default login

# Enable APIs
gcloud services enable aiplatform.googleapis.com

# Set your project
export GOOGLE_CLOUD_PROJECT=your-project-id
```

### 6. Initialize Entire

In your thesis repository:

```bash
cd ~/thesis
entire init
```

This captures Claude Code sessions with every commit.

### 7. Install Git Hooks

```bash
# In your thesis repo
cp /path/to/research-workflow/hooks/pre-commit .git/hooks/
chmod +x .git/hooks/pre-commit
```

The pre-commit hook blocks commits if citations are missing from `.bib`.

### 8. Start the Watcher Service

```bash
# Process existing papers first
source .venv/bin/activate
python src/watcher.py --once

# Install as background service (macOS)
./scripts/install-watcher.sh

# Verify it's running
launchctl list | grep research-workflow

# View logs
tail -f logs/watcher.log
```

The watcher:
- Runs automatically on login
- Watches `~/Papers` for new PDFs
- Converts to markdown via Marker
- Generates AI summaries via Claude
- Uploads to Google for search indexing

## Usage

### CLI Commands

All commands available via `src/search.py`:

```bash
# Activate environment
cd research-workflow
source .venv/bin/activate

# Search for papers
python src/search.py find "attention mechanisms in transformers"

# List all papers in library
python src/search.py list

# Read full paper
python src/search.py read vaswani2017

# Read specific section
python src/search.py read vaswani2017 --section "Results"

# Read AI summary
python src/search.py summary vaswani2017

# Verify a citation claim
python src/search.py verify vaswani2017 "achieved 28.4 BLEU on WMT 2014"

# Upload papers to Google (for search)
python src/search.py upload
```

### Citation Verification

```bash
# Verify single claim
python src/search.py verify vaswani2017 "Transformers achieved 28.4 BLEU"
# ✅ VERIFIED (95% confidence)
# Quote: "The big transformer model achieves 28.4 BLEU..."

# Check all citations in LaTeX files
python src/citation_checker.py ./chapters ./references.bib

# Quick check (keys only, skip claim verification)
python src/citation_checker.py ./chapters ./references.bib --no-verify

# JSON output (for CI)
python src/citation_checker.py ./chapters ./references.bib --json
```

### Writing with Claude Code

```bash
cd ~/thesis
claude
```

Example session:

```
You: Find papers about vision transformers

Claude: [runs: python search.py find "vision transformers"]
        Found 3 relevant papers:
        1. dosovitskiy2020 (0.94) - Vision Transformer architecture
        2. liu2021-swin (0.89) - Hierarchical vision transformer
        ...

You: Read the dosovitskiy paper and help me write about their approach

Claude: [runs: python search.py read dosovitskiy2020]
        [reads full markdown]
        
        Here's a paragraph for your related work:
        
        "Dosovitskiy et al. demonstrated that pure transformer 
        architectures can match CNN performance on image classification
        when trained on sufficient data \cite{dosovitskiy2020vit}..."

You: Verify that citation before I commit

Claude: [runs: python search.py verify dosovitskiy2020 "match CNN performance"]
        ✅ VERIFIED (92% confidence)
```

### AI Session Capture (Entire)

Every commit captures the AI conversation that produced it:

```bash
# See AI reasoning behind a commit
entire explain --commit HEAD

# Browse all captured sessions  
entire rewind

# Check status
entire status
```

Example output:

```bash
$ entire explain --commit HEAD

Commit: 683bbbf "Add results section with transformer comparison"
Session: https://entire.io/s/abc123xyz

Claude searched for: "transformer attention visualization"
Found papers: vaswani2017, dosovitskiy2020
Read: markdown/vaswani2017.md (section: Results)
Verified: "28.4 BLEU" claim → ✅ 

Reasoning: "Based on the original transformer paper, I added
a comparison table showing BLEU scores across model sizes..."
```

### Watcher Service Management

```bash
# Check status
launchctl list | grep research-workflow

# View logs
tail -f logs/watcher.log
tail -f logs/watcher.error.log

# Stop service
launchctl unload ~/Library/LaunchAgents/com.research-workflow.watcher.plist

# Start service
launchctl load ~/Library/LaunchAgents/com.research-workflow.watcher.plist

# Uninstall completely
./scripts/uninstall-watcher.sh
```

## Project Structure

```
research-workflow/
├── config.yaml              # Your configuration (git-ignored)
├── config.example.yaml      # Configuration template
├── requirements.txt         # Python dependencies
├── SKILL.md                 # Quick reference for Claude
│
├── papers/                  # Raw PDFs (Zotero/ZotFile managed)
├── markdown/                # Converted markdown (full papers)
├── summaries/               # AI-generated summaries
├── logs/                    # Watcher service logs
│
├── hooks/
│   ├── pre-commit           # Blocks invalid citations
│   └── post-commit          # Async claim verification
│
├── scripts/
│   ├── install-watcher.sh   # Install macOS launchd service
│   └── uninstall-watcher.sh # Remove service
│
└── src/
    ├── search.py            # Main CLI (find/read/verify)
    ├── watcher.py           # PDF watcher + processor
    ├── converter.py         # Marker PDF→MD wrapper
    ├── summarizer.py        # Claude summarization
    ├── citation_checker.py  # Citation verification
    └── google_search.py     # Google File Search client
```

## Environment Variables

Set these in your shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="..."
export GOOGLE_CLOUD_PROJECT="your-project-id"

# Optional: Override default paths
export THESIS_PAPERS_DIR="$HOME/Papers"
export THESIS_MARKDOWN_DIR="$HOME/thesis/research-workflow/markdown"
export THESIS_SUMMARIES_DIR="$HOME/thesis/research-workflow/summaries"
```

## Troubleshooting

### Watcher not processing files

```bash
# Check if running
launchctl list | grep research-workflow

# Check logs for errors
cat logs/watcher.error.log

# Test manually
python src/watcher.py --once
```

### Marker conversion fails

```bash
# Ensure Marker is installed
uv tool install marker-pdf

# Test on single file
marker_single path/to/paper.pdf --output_dir ./test/
```

### Google search not working

```bash
# Check authentication
gcloud auth application-default print-access-token

# Verify API is enabled
gcloud services list --enabled | grep aiplatform
```

### Citation verification fails

```bash
# Check paper exists
python src/search.py list

# Check markdown was generated
ls -la markdown/

# Run with debug output
python src/citation_checker.py ./chapters ./refs.bib 2>&1 | head -50
```

## License

MIT
