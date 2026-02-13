# Research Workflow

Paper management for thesis writing with Claude Code.

## Setup

```bash
git clone https://github.com/JonasTischer/research-workflow.git
cd research-workflow
./scripts/setup.sh

# Add to ~/.zshrc:
export GOOGLE_API_KEY="..."    # aistudio.google.com/apikey
export BRAVE_API_KEY="..."     # Optional: brave.com/search/api

# Start watcher
./scripts/install-watcher.sh
```

## Subagents

Native Claude Code subagents in `.claude/agents/`:

| Agent | Purpose | Trigger |
|-------|---------|---------|
| **verifier** | Check citation claims | "Verify this claim..." |
| **researcher** | Find & summarize papers | "Find papers about..." |

Claude auto-delegates based on your request.

## CLI Tools (External Operations)

```bash
# Web search
python src/web_search.py scholar "query"
python src/web_search.py arxiv "query"

# Download papers
python src/download.py arxiv "1706.03762"
python src/download.py doi "10.1000/xyz"

# List/read local papers
python src/search.py list
python src/search.py read <name>
```

## Workflow

1. **Search** → "Find papers about transformers" (researcher subagent)
2. **Download** → `python src/download.py arxiv "id"`
3. **Read** → `cat markdown/paper_name.md`
4. **Write** → Draft with citations
5. **Verify** → "Verify this claim against paper" (verifier subagent)
6. **Commit** → Entire captures reasoning

## Key Principle

- **Subagents** handle research and verification
- **CLI tools** handle external operations (downloads, web search)
- **Claude Code** reads files directly for understanding
