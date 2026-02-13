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

### 6. Claude Code MCP Setup

Add to your Claude Code MCP config (`~/.claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "thesis": {
      "command": "python",
      "args": ["/path/to/thesis-workflow/src/mcp_server.py"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/credentials.json"
      }
    }
  }
}
```

Now Claude Code can use `search_papers("query")` to find relevant papers.

## Usage

### Adding Papers

1. Find paper (Google Scholar, Semantic Scholar, Elicit)
2. Click Zotero browser extension → saves to library
3. ZotFile auto-moves PDF to `papers/`
4. Watcher detects new PDF:
   - Converts to markdown → `markdown/paper-name.md`
   - Generates summary → `summaries/paper-name.summary.md`
   - Uploads to Google corpus for search indexing

### Writing with Claude

```
You: "Find papers about attention mechanisms in vision transformers"

Claude: [calls search_papers tool]
        Found 3 relevant papers:
        1. dosovitskiy2020-image-worth-16x16.md (0.92)
        2. vaswani2017-attention-is-all-you-need.md (0.87)
        3. liu2021-swin-transformer.md (0.84)
        
        Let me read the most relevant one...
        [reads markdown/dosovitskiy2020-image-worth-16x16.md]
        
        Based on this paper, here's a paragraph for your related work section:
        
        "Vision Transformers (ViT) demonstrated that pure transformer 
        architectures can achieve state-of-the-art results on image 
        classification \cite{dosovitskiy2020image}..."
```

## Folder Structure

```
thesis-workflow/
├── papers/              # Raw PDFs (Zotero/ZotFile managed)
├── markdown/            # Converted markdown (full papers)
├── summaries/           # AI-generated summaries
├── src/
│   ├── watcher.py       # PDF watcher + processor
│   ├── mcp_server.py    # MCP server for Claude Code
│   ├── converter.py     # Marker wrapper
│   ├── summarizer.py    # Claude summarization
│   └── google_search.py # Google File Search client
├── config.yaml          # Your configuration
├── config.example.yaml  # Template
├── requirements.txt
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
