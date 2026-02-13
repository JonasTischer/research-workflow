# Research Workflow

AI-powered research paper management for thesis writing with Claude Code.

## What It Does

```
Find papers → Download → Auto-convert to markdown → Search & cite → Verify claims
```

- **Search**: Semantic Scholar, arXiv, Brave, Google
- **Convert**: Marker + Gemini Flash (tables, math, complex layouts)
- **Cite**: Verification against actual paper content
- **Audit**: Entire captures AI reasoning with each commit

## Quick Start

```bash
# Clone
git clone https://github.com/JonasTischer/research-workflow.git
cd research-workflow

# Setup (installs uv, creates venv, installs deps)
./scripts/setup.sh

# Configure
cp config.example.yaml config.yaml
# Add your API keys (see below)

# Start watcher (processes PDFs automatically)
./scripts/install-watcher.sh
```

## API Keys

Add to `~/.zshrc` or `~/.bashrc`:

```bash
export GOOGLE_API_KEY="..."    # Required: PDF conversion + search
export BRAVE_API_KEY="..."     # Optional: web search
export S2_API_KEY="..."        # Optional: Semantic Scholar (higher rate limits)
```

Get them from:
- Google: https://aistudio.google.com/apikey
- Brave: https://brave.com/search/api/
- Semantic Scholar: https://www.semanticscholar.org/product/api

**Note:** Summaries and citation verification are done by Claude Code directly (uses your Claude Code subscription, no extra API key needed).

## Usage

### Find Papers

```bash
# Academic search (free, no API key)
python src/web_search.py scholar "attention mechanisms"
python src/web_search.py arxiv "vision transformer"

# Web search (needs Brave API key)
python src/web_search.py brave "topic" --academic
```

### Download Papers

```bash
python src/download.py arxiv "1706.03762"           # From arXiv
python src/download.py doi "10.1000/example"        # From DOI (open access)
python src/download.py url "https://..." --name x   # Direct URL
```

Downloaded papers are automatically processed by the watcher.

### Read Papers

```bash
python src/search.py list                           # All papers
python src/search.py read vaswani2017               # Full paper
python src/search.py read vaswani2017 -s "Results"  # Specific section
python src/search.py summary vaswani2017            # AI summary
python src/search.py find "attention mechanisms"    # Semantic search
```

### Verify Citations

Just ask Claude to verify — it automatically uses the verifier subagent:

```
"Verify that vaswani2017 supports 'achieved 28.4 BLEU on WMT 2014'"
```

Returns:
- ✅ VERIFIED — claim is accurate
- ⚠️ NEEDS REVISION — needs changes  
- ❌ INCORRECT — doesn't match paper

## Subagents

Native Claude Code subagents in `.claude/agents/`:

| Agent | Purpose | Model |
|-------|---------|-------|
| **verifier** | Check citation claims against papers | Haiku (fast) |
| **researcher** | Find and summarize papers | Sonnet |

Claude automatically delegates to the right subagent based on your request.

### Batch Check (Pre-commit)

Check all citation keys exist in .bib file:

```bash
python src/citation_checker.py ./chapters ./references.bib
```

This is also done automatically by the pre-commit hook.

## Zotero Integration (Recommended)

For automatic bibliography management:

1. Install [Zotero](https://www.zotero.org/download/)
2. Install [ZotFile](http://zotfile.com/) → auto-saves PDFs to `papers/`
3. Install [Better BibTeX](https://retorque.re/zotero-better-bibtex/) → auto-exports `.bib`

Then: Find paper → Click Zotero extension → PDF saved → Watcher converts → Ready to cite

## Entire (AI Session Capture)

Track the reasoning behind your AI-assisted writing:

```bash
# In your thesis repo
entire init

# After commits, see the AI session
entire explain --commit HEAD
entire rewind
```

## Git Hook

Block commits with missing citation keys:

```bash
cp hooks/pre-commit .git/hooks/
chmod +x .git/hooks/pre-commit
```

The hook checks that every `\cite{key}` has a matching entry in `.bib`.

## PDF Conversion Quality

Uses **Marker + Gemini 2.0 Flash** for high accuracy:
- ✅ Multi-page tables merged correctly
- ✅ Inline math → LaTeX
- ✅ Complex academic layouts

Configure in `config.yaml`:

```yaml
converter:
  use_llm: true           # Gemini Flash (default)
  force_ocr: false        # For scanned PDFs
  redo_inline_math: false # Highest quality math
```

## Watcher Service

The watcher runs in background, processing new PDFs automatically:

```bash
# Install as service (runs on login)
./scripts/install-watcher.sh

# Check status
launchctl list | grep research-workflow

# Logs
tail -f logs/watcher.log

# Uninstall
./scripts/uninstall-watcher.sh
```

## Project Structure

```
research-workflow/
├── .claude/agents/   # Native Claude Code subagents
│   ├── verifier.md   # Citation verification
│   └── researcher.md # Paper search & summary
├── papers/           # PDFs (Zotero or manual)
├── markdown/         # Converted text (auto-generated)
├── summaries/        # AI summaries
├── sample-thesis/    # Example LaTeX thesis for testing
├── src/
│   ├── search.py     # List/read local papers
│   ├── web_search.py # Web search (Scholar/arXiv/Brave)
│   ├── download.py   # Download papers
│   ├── watcher.py    # PDF processor daemon
│   ├── converter.py  # Marker + Gemini PDF conversion
│   └── ...
├── hooks/pre-commit  # Block commits with missing citations
├── scripts/          # Setup & service scripts
├── config.yaml       # Your settings
└── CLAUDE.md         # Instructions for Claude Code
```

## Sample Thesis

A minimal LaTeX thesis is included for testing:

```bash
cd sample-thesis

# Download a paper cited in the thesis
python ../src/download.py arxiv "1706.03762"

# Verify the citation
python ../src/search.py verify vaswani2017 "achieved 28.4 BLEU"

# Check all citations
python ../src/citation_checker.py . references.bib --no-verify

# Build PDF (requires LaTeX)
latexmk -pdf main.tex
```

See `sample-thesis/README.md` for full testing guide.

## Troubleshooting

**Watcher not running:**
```bash
launchctl list | grep research-workflow
cat logs/watcher.error.log
```

**Paper not converting:**
```bash
# Check Marker is installed
marker_single --help

# Try manually
python src/watcher.py --once
```

**Search not working:**
```bash
# Check API key
echo $GOOGLE_API_KEY
python src/search.py list
```

## License

MIT
