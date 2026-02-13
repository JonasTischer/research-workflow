# Sample Thesis

A minimal LaTeX thesis structure for testing the research-workflow.

## Structure

```
sample-thesis/
├── main.tex              # Main document
├── references.bib        # Bibliography
├── chapters/
│   ├── introduction.tex
│   ├── related-work.tex  # Has sample citations to test
│   ├── methodology.tex
│   ├── results.tex
│   └── conclusion.tex
└── figures/              # For images
```

## Building

```bash
# Build PDF (requires LaTeX installation)
cd sample-thesis
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

Or use `latexmk`:
```bash
latexmk -pdf main.tex
```

## Testing the Workflow

### 1. Download a cited paper

```bash
# Download the Attention paper cited in related-work.tex
python src/download.py arxiv "1706.03762"

# Wait for watcher to convert, or run manually:
python src/watcher.py --once
```

### 2. Verify a citation

```bash
# Check the claim in related-work.tex
python src/search.py verify vaswani2017 "achieved 28.4 BLEU on WMT 2014"
```

### 3. Check all citations

```bash
# Run citation checker on the thesis
python src/citation_checker.py sample-thesis sample-thesis/references.bib --no-verify
```

### 4. Add a new citation

```bash
# Find a paper
python src/web_search.py scholar "vision transformer"

# Download it
python src/download.py arxiv "2010.11929"

# Read and understand it
cat markdown/dosovitskiy2020*.md

# Add citation to your chapter and references.bib
# Then verify your claim
```

## Tips

- Keep `references.bib` synced with Zotero (Better BibTeX)
- Run citation check before committing: `python src/citation_checker.py sample-thesis sample-thesis/references.bib`
- Use git hooks to automate verification
