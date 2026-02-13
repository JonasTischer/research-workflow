# Research Workflow

You're helping write an academic thesis. Papers are stored as markdown files you can read directly.

## Folders

```
papers/      → PDFs 
markdown/    → Full paper text (read these directly)
summaries/   → Your summaries (write here)
```

## Finding Papers

```bash
# Academic search (free)
python src/web_search.py scholar "attention mechanisms"
python src/web_search.py arxiv "vision transformer"

# Web search (needs BRAVE_API_KEY)
python src/web_search.py brave "topic" --academic
```

## Downloading Papers

```bash
python src/download.py arxiv "1706.03762"
python src/download.py doi "10.1000/example"
```

Downloads go to `papers/` → watcher converts to `markdown/` automatically.

## Reading Papers

**Read the markdown files directly** — no script needed:

```bash
cat markdown/vaswani2017.md
```

Or read specific sections by searching within the file.

To see all papers:
```bash
ls markdown/
```

## Summarizing Papers

**You summarize directly** — read the file and write a summary:

1. Read: `cat markdown/paper_name.md`
2. Write summary to: `summaries/paper_name.summary.md`

Format:
```markdown
# Summary: Paper Title

**Main Contribution:** ...
**Method:** ...
**Key Results:** ...
**Relevance:** ...
**Citation Key:** author2024keyword
```

## Verifying Citations

**You verify directly** — read the paper and check the claim:

1. Read the paper: `cat markdown/paper_name.md`
2. Search for relevant section
3. Confirm the claim matches the source

Before writing any `\cite{key}`:
- Read the actual paper
- Find the supporting quote
- Ensure your claim accurately reflects the source

If you can't verify → say so, suggest alternatives.

## Workflow

1. **Search** → `python src/web_search.py scholar "topic"`
2. **Download** → `python src/download.py arxiv "id"`
3. **Read** → `cat markdown/paper_name.md`
4. **Write** → Draft paragraph with citation
5. **Verify** → Re-read paper, confirm claim matches
6. **Commit** → Entire captures your reasoning

## Citation Rules

- **Only cite papers in `markdown/`** — you must have read them
- **Verify every claim** — re-read the source before citing
- **Use exact quotes** — when paraphrasing, check accuracy
- **Cite conservatively** — if unsure, say so

## Batch Operations (if needed)

```bash
# List all papers
ls markdown/*.md

# Search within papers
grep -r "attention" markdown/

# Check which papers mention a topic
grep -l "transformer" markdown/*.md
```

## Tools That Still Need Scripts

| Task | Command |
|------|---------|
| Web search | `python src/web_search.py scholar "query"` |
| Download | `python src/download.py arxiv "id"` |
| Re-convert PDF | `python src/watcher.py --once` |
