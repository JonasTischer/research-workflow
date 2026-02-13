# Thesis Workflow

AI-powered research paper management for PhD thesis writing with Claude Code.

## Architecture

```
PDF → Zotero → ZotFile saves to papers/
                    ↓
              Marker converts → markdown/
                    ↓
              Claude summarizes → summaries/
                    ↓
              Upload to Google (search index)
                    ↓
        Claude Code searches via MCP tool
                    ↓
        Claude reads full markdown locally
```

**Search:** Google's File Search API (smart semantic search)  
**Read:** Local markdown files (full context for Claude)  
**Cite:** Zotero-managed .bib file (verified citations)

## Setup

### 0. Entire (Recommended)

Capture AI reasoning alongside your commits with [Entire](https://entire.io):

```bash
# Install
curl -fsSL https://entire.io/install.sh | bash

# Initialize in your thesis repo
cd ~/thesis
entire init

# That's it — sessions auto-capture on commit
```

**Why:** When Claude helps write a paragraph or suggests a citation, Entire captures the full conversation. Months later you can trace back *why* something was written that way.

```bash
# See what AI session produced a commit
entire explain --commit HEAD

# Browse all checkpoints
entire rewind
```

### 1. Prerequisites

```bash
# Python 3.11+
brew install python@3.11

# Marker for PDF conversion
pip install marker-pdf

# Dependencies
cd thesis-workflow
pip install -r requirements.txt
```

### 2. Zotero Setup

1. Install [Zotero](https://www.zotero.org/download/)
2. Install [ZotFile](http://zotfile.com/) addon
   - Preferences → Set "Location of Files" to `~/thesis-workflow/papers/`
3. Install [Better BibTeX](https://retorque.re/zotero-better-bibtex/)
   - Right-click library → Export → Better BibLaTeX → Keep updated
   - Save as `references.bib` in your thesis folder

### 3. Google Cloud Setup (for search)

```bash
# Install gcloud CLI
brew install google-cloud-sdk

# Authenticate
gcloud auth application-default login

# Enable APIs
gcloud services enable aiplatform.googleapis.com
```

Create a corpus for your papers in Vertex AI Search, or use the Gemini File API directly.

### 4. Configure

```bash
cp config.example.yaml config.yaml
# Edit config.yaml with your paths and API settings
```

### 5. Run the Watcher

```bash
# Start watching for new PDFs
python src/watcher.py

# Or run once on existing files
python src/watcher.py --once
```

### 6. Start the Watcher

```bash
# Process existing papers and watch for new ones
python src/watcher.py

# Or just process existing papers once
python src/watcher.py --once
```

## Usage

### Adding Papers

1. Find paper (Google Scholar, Semantic Scholar, Elicit)
2. Click Zotero browser extension → saves to library
3. ZotFile auto-moves PDF to `papers/`
4. Watcher detects new PDF:
   - Converts to markdown → `markdown/paper-name.md`
   - Generates summary → `summaries/paper-name.summary.md`
   - Uploads to Google corpus for search indexing

### CLI Commands

```bash
# Search for papers
python src/search.py find "attention mechanisms in vision transformers"
# Found 3 relevant papers:
# 1. dosovitskiy2020 (0.92) - Vision transformer architecture
# 2. vaswani2017 (0.87) - Original transformer paper
# 3. liu2021-swin (0.84) - Hierarchical vision transformer

# List all papers
python src/search.py list

# Read a paper
python src/search.py read dosovitskiy2020

# Read specific section
python src/search.py read dosovitskiy2020 --section "Results"

# Read summary
python src/search.py summary dosovitskiy2020

# Verify a citation
python src/search.py verify vaswani2017 "Transformers achieved 28.4 BLEU on WMT 2014"
# ✅ VERIFIED (95% confidence)
# Quote: "The big transformer model achieves 28.4 BLEU..."
```

### Writing with Claude Code

Claude can use these CLI tools directly:

```
You: "Find papers about attention in vision transformers and help me write a related work paragraph"

Claude: Let me search the papers...
        [runs: python src/search.py find "attention vision transformers"]
        
        Found dosovitskiy2020 as most relevant. Reading it...
        [runs: python src/search.py read dosovitskiy2020]
        
        Here's a paragraph for your related work:
        
        "Vision Transformers (ViT) demonstrated that pure transformer 
        architectures can achieve state-of-the-art results on image 
        classification \cite{dosovitskiy2020image}..."
        
        Let me verify this citation...
        [runs: python src/search.py verify dosovitskiy2020 "pure transformer..."]
        ✅ Verified
```

## Citation Verification

The workflow includes automatic citation checking to prevent hallucinated or incorrect citations.

### Git Hooks

Install the pre-commit hook to catch issues before they're committed:

```bash
cp hooks/pre-commit .git/hooks/
chmod +x .git/hooks/pre-commit
```

**What it checks:**
- Every `\cite{key}` has a matching entry in `.bib`
- Optionally verifies claims against paper content (set `VERIFY_CLAIMS=1`)

### On-Demand Verification

Verify any claim before finalizing a citation:

```bash
python src/search.py verify vaswani2017 "Transformers achieved 28.4 BLEU on WMT 2014"

# ✅ VERIFIED
# Confidence: 95%
#
# Claim:
#   Transformers achieved 28.4 BLEU on WMT 2014
#
# Supporting quote:
#   "The big transformer model achieves 28.4 BLEU on the WMT 2014 
#   English-to-German translation task"
#
# Notes: Exact match found in Results section
```

### CLI Usage

```bash
# Quick check: verify all citation keys exist
python src/citation_checker.py ./chapters ./references.bib --no-verify

# Full check: verify claims against papers (slower)
python src/citation_checker.py ./chapters ./references.bib --markdown-dir ./markdown

# JSON output for CI
python src/citation_checker.py ./chapters ./references.bib --json
```

## Folder Structure

```
thesis-workflow/
├── papers/              # Raw PDFs (Zotero/ZotFile managed)
├── markdown/            # Converted markdown (full papers)
├── summaries/           # AI-generated summaries
├── hooks/               # Git hooks for citation verification
│   ├── pre-commit       # Blocks commits with missing citations
│   └── post-commit      # Async full verification
├── src/
│   ├── watcher.py       # PDF watcher + processor
│   ├── search.py        # CLI for search/read/verify
│   ├── converter.py     # Marker PDF→MD wrapper
│   ├── summarizer.py    # Claude summarization
│   ├── citation_checker.py  # Citation verification
│   └── google_search.py # Google File Search client
├── config.yaml          # Your configuration
├── config.example.yaml  # Template
├── requirements.txt
├── SKILL.md             # Quick reference for Claude
└── README.md
```

## Configuration

See `config.example.yaml` for all options:

- `watch_dir`: Where PDFs land (Zotero/ZotFile target)
- `markdown_dir`: Converted markdown output
- `summary_dir`: AI summaries output
- `anthropic_api_key`: For summarization
- `google_project_id`: For Vertex AI Search
- `google_corpus_id`: Your paper corpus

## License

MIT
