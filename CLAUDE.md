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

**You verify directly** — read the paper and assess whether the claim is accurate:

1. Read the paper: `cat markdown/paper_name.md`
2. Understand what the paper actually claims
3. Compare to what the thesis says about it

### What to Check

| Check | Question |
|-------|----------|
| **Accuracy** | Does the claim correctly represent the paper's findings? |
| **Context** | Is the claim taken out of context? |
| **Scope** | Is the thesis overclaiming or overgeneralizing? |
| **Nuance** | Does the paper have caveats the thesis ignores? |
| **Attribution** | Is this the original source, or should an earlier paper be cited? |

### Examples

**Good citation:**
> "Transformers achieved state-of-the-art results on translation tasks \cite{vaswani2017}"

Check: Paper claims 28.4 BLEU on WMT 2014, which was SOTA at the time. ✅

**Overclaiming:**
> "Transformers are always better than RNNs \cite{vaswani2017}"

Check: Paper only tested on translation. Doesn't claim universal superiority. ❌

**Missing nuance:**
> "ViT outperforms CNNs on image classification \cite{dosovitskiy2020}"

Check: Paper says this only holds with large-scale pretraining. Needs qualifier. ⚠️

### Verification Process

1. Read the thesis claim carefully
2. Read the cited paper (especially abstract, results, limitations)
3. Ask: "Would the paper's authors agree with this characterization?"
4. If uncertain, quote directly or add qualifiers
5. If wrong, revise the claim or find a better source

If you can't verify → say so, suggest alternatives, or recommend reading a specific section.

## Workflow

1. **Search** → `python src/web_search.py scholar "topic"`
2. **Download** → `python src/download.py arxiv "id"`
3. **Read** → `cat markdown/paper_name.md`
4. **Write** → Draft paragraph with citation
5. **Verify** → Use verification subagent (see below)
6. **Commit** → Entire captures your reasoning

## Subagents

This project includes native Claude Code subagents in `.claude/agents/`:

### Verifier
Checks citation claims against papers. Claude auto-delegates when you ask to verify.

```
"Verify that vaswani2017 supports the claim 'achieved 28.4 BLEU'"
```

Returns: ✅ VERIFIED | ⚠️ NEEDS REVISION | ❌ INCORRECT

### Researcher  
Finds and summarizes papers. Claude auto-delegates for research tasks.

```
"Find papers about attention mechanisms in vision transformers"
"Summarize the dosovitskiy2020 paper"
```

Claude automatically chooses the right subagent based on your request.

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
