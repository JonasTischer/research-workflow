# Research Workflow - Claude Code Instructions

This is a research paper management system for academic thesis writing.

## Available Commands

Run these from the project root (ensure venv is active):

### Web Search (Finding New Papers)

```bash
# Brave Search (needs BRAVE_API_KEY)
python src/web_search.py brave "query" --academic

# Semantic Scholar (free, no API key)
python src/web_search.py scholar "attention is all you need"

# arXiv (free, no API key)
python src/web_search.py arxiv "vision transformer"

# Resolve DOI
python src/web_search.py doi "10.1234/example"
```

### Download Papers

```bash
# From arXiv (recommended - auto-names files)
python src/download.py arxiv "1706.03762"

# From DOI (finds open access version)
python src/download.py doi "10.48550/arXiv.1706.03762"

# From URL
python src/download.py url "https://example.com/paper.pdf"
```

### Search & Read Local Papers

```bash
# Find relevant papers
python src/search.py find "your search query"

# List all papers
python src/search.py list

# Read full paper
python src/search.py read <paper_name>

# Read specific section
python src/search.py read <paper_name> --section "Results"

# Read AI summary
python src/search.py summary <paper_name>
```

### Citation Verification

```bash
# Verify a claim against a paper (ALWAYS do this before citing)
python src/search.py verify <paper_name> "claim to verify"

# Check all citations in LaTeX
python src/citation_checker.py <tex_dir> <bib_file>
```

### Paper Management

```bash
# Process new papers (usually runs as service)
python src/watcher.py --once

# Upload to Google search index
python src/search.py upload
```

## Workflow Guidelines

1. **Finding papers**: Use `search.py find` to discover relevant papers
2. **Reading**: Use `search.py read` to get full content, `summary` for overview
3. **Writing**: Help write paragraphs using paper content
4. **ALWAYS verify**: Before any `\cite{}`, run `search.py verify` to confirm the claim
5. **Commit**: After verification passes, commit with descriptive message

## Citation Rules

- NEVER invent citation details
- ALWAYS verify claims against actual paper content before citing
- Use citation keys from the `.bib` file (managed by Zotero/Better BibTeX)
- If unsure about a claim, say so and suggest verification

## Directory Structure

- `papers/` - Raw PDFs
- `markdown/` - Converted markdown (full text)
- `summaries/` - AI-generated summaries
- `references.bib` - Citation database (auto-managed by Zotero)

## Example Session

User: "Help me write about attention mechanisms"

1. Search: `python src/search.py find "attention mechanisms transformers"`
2. Read top result: `python src/search.py read vaswani2017`
3. Write paragraph using the content
4. Verify: `python src/search.py verify vaswani2017 "the claim you wrote"`
5. If verified, include `\cite{vaswani2017}` in the text
