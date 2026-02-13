# Research Workflow

You're helping write an academic thesis. This workspace has tools for finding, reading, and citing papers correctly.

## Quick Reference

```bash
# Always run from project root with venv active
cd /path/to/research-workflow && source .venv/bin/activate
```

### Find Papers (Web)

```bash
python src/web_search.py scholar "attention mechanisms"     # Academic papers
python src/web_search.py arxiv "vision transformer"         # Preprints  
python src/web_search.py brave "topic" --academic           # Web search
```

### Download Papers

```bash
python src/download.py arxiv "1706.03762"                   # From arXiv
python src/download.py doi "10.1000/example"                # From DOI
```

Downloads go to `papers/` → watcher auto-converts to markdown.

### Read Papers (Local)

```bash
python src/search.py list                                   # All papers
python src/search.py read <name>                            # Full paper
python src/search.py read <name> --section "Methods"        # One section
python src/search.py summary <name>                         # AI summary
python src/search.py find "query"                           # Semantic search
```

### Verify Citations (REQUIRED)

**Before citing anything, verify the claim:**

```bash
python src/search.py verify <paper> "exact claim you're making"
```

Example:
```bash
python src/search.py verify vaswani2017 "achieved 28.4 BLEU on WMT 2014"
# ✅ VERIFIED (95% confidence)
# Quote: "The big transformer model achieves 28.4 BLEU..."
```

If verification fails → revise the claim or find a different source.

## Workflow

1. **Search** → `web_search.py scholar "topic"` to find relevant papers
2. **Download** → `download.py arxiv "id"` to get the PDF
3. **Read** → `search.py read <name>` to understand the paper  
4. **Write** → Draft paragraph with citation
5. **Verify** → `search.py verify <paper> "claim"` before committing
6. **Commit** → Git commit (Entire captures your reasoning)

## Rules

- **Never invent citations** — only cite papers in the library
- **Always verify claims** — run `search.py verify` before any `\cite{}`
- **Use .bib keys** — citation keys come from `references.bib` (Zotero manages this)
- **Check your work** — if unsure about a claim, say so

## Folders

```
papers/      → PDFs (add here or via download.py)
markdown/    → Full text (auto-converted by Marker + Gemini)
summaries/   → AI summaries
```

## Re-processing

If a paper's markdown looks wrong:
```bash
rm markdown/<paper>.md
python src/watcher.py --once
```
