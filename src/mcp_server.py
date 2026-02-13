#!/usr/bin/env python3
"""
MCP Server for Claude Code integration.

Provides tools for searching and reading research papers.
"""

import os
import sys
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from google_search import GooglePaperSearch, SearchResult
from citation_checker import verify_claim_against_paper, Citation

# Initialize server
server = Server("thesis-workflow")

# Configuration from environment
PAPERS_DIR = Path(os.environ.get("THESIS_PAPERS_DIR", "./papers"))
MARKDOWN_DIR = Path(os.environ.get("THESIS_MARKDOWN_DIR", "./markdown"))
SUMMARIES_DIR = Path(os.environ.get("THESIS_SUMMARIES_DIR", "./summaries"))

# Lazy-load Google client
_google_client: GooglePaperSearch | None = None

def get_google_client() -> GooglePaperSearch:
    """Get or create Google search client."""
    global _google_client
    if _google_client is None:
        _google_client = GooglePaperSearch()
    return _google_client


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="search_papers",
            description="Search research papers by semantic query. Returns ranked list of relevant papers.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'attention mechanisms in transformers')",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return (default: 5)",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="list_papers",
            description="List all available papers in the library.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="read_paper",
            description="Read the full markdown content of a paper.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Paper name (filename without extension)",
                    },
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="read_summary",
            description="Read the AI-generated summary of a paper.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Paper name (filename without extension)",
                    },
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="search_in_paper",
            description="Search for specific content within a single paper.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Paper name to search in",
                    },
                    "query": {
                        "type": "string",
                        "description": "What to search for",
                    },
                },
                "required": ["name", "query"],
            },
        ),
        Tool(
            name="verify_citation",
            description="Verify that a claim is actually supported by the cited paper. Use before finalizing any citation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "paper_name": {
                        "type": "string",
                        "description": "Name of the paper being cited",
                    },
                    "claim": {
                        "type": "string",
                        "description": "The claim/statement being attributed to this paper",
                    },
                },
                "required": ["paper_name", "claim"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    
    if name == "search_papers":
        query = arguments["query"]
        top_k = arguments.get("top_k", 5)
        
        try:
            client = get_google_client()
            results = client.search(query, top_k=top_k)
            
            if not results:
                return [TextContent(
                    type="text",
                    text="No relevant papers found for this query.",
                )]
            
            # Format results
            lines = [f"Found {len(results)} relevant papers:\n"]
            for i, r in enumerate(results, 1):
                lines.append(f"{i}. **{r.filename}** (relevance: {r.score:.2f})")
                if r.snippet:
                    lines.append(f"   {r.snippet}")
                lines.append("")
            
            lines.append("\nUse `read_paper` or `read_summary` to get details.")
            
            return [TextContent(type="text", text="\n".join(lines))]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Search error: {e}")]
    
    elif name == "list_papers":
        papers = []
        
        # Check markdown dir
        if MARKDOWN_DIR.exists():
            for md in MARKDOWN_DIR.glob("*.md"):
                if not md.name.endswith(".summary.md"):
                    papers.append(md.stem)
        
        # Also check summaries
        summaries = set()
        if SUMMARIES_DIR.exists():
            for s in SUMMARIES_DIR.glob("*.summary.md"):
                summaries.add(s.stem.replace(".summary", ""))
        
        if not papers:
            return [TextContent(type="text", text="No papers in library yet.")]
        
        lines = [f"Papers in library ({len(papers)}):\n"]
        for p in sorted(papers):
            has_summary = "✓" if p in summaries else " "
            lines.append(f"  [{has_summary}] {p}")
        
        lines.append("\n[✓] = has AI summary")
        
        return [TextContent(type="text", text="\n".join(lines))]
    
    elif name == "read_paper":
        paper_name = arguments["name"]
        md_path = MARKDOWN_DIR / f"{paper_name}.md"
        
        if not md_path.exists():
            # Try fuzzy match
            matches = list(MARKDOWN_DIR.glob(f"*{paper_name}*.md"))
            if matches:
                md_path = matches[0]
            else:
                return [TextContent(
                    type="text",
                    text=f"Paper not found: {paper_name}\n\nUse `list_papers` to see available papers.",
                )]
        
        try:
            content = md_path.read_text(encoding="utf-8")
            # Truncate if very long
            if len(content) > 100000:
                content = content[:100000] + "\n\n[TRUNCATED - paper is very long]"
            
            return [TextContent(type="text", text=content)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error reading paper: {e}")]
    
    elif name == "read_summary":
        paper_name = arguments["name"]
        summary_path = SUMMARIES_DIR / f"{paper_name}.summary.md"
        
        if not summary_path.exists():
            # Try fuzzy match
            matches = list(SUMMARIES_DIR.glob(f"*{paper_name}*.summary.md"))
            if matches:
                summary_path = matches[0]
            else:
                return [TextContent(
                    type="text",
                    text=f"Summary not found for: {paper_name}\n\nThe paper may not have been summarized yet.",
                )]
        
        try:
            content = summary_path.read_text(encoding="utf-8")
            return [TextContent(type="text", text=content)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error reading summary: {e}")]
    
    elif name == "search_in_paper":
        paper_name = arguments["name"]
        query = arguments["query"]
        
        try:
            client = get_google_client()
            passages = client.search_with_context(query, paper_name)
            
            if not passages:
                return [TextContent(
                    type="text",
                    text=f"No relevant passages found for '{query}' in {paper_name}",
                )]
            
            lines = [f"Relevant passages from **{paper_name}**:\n"]
            for i, p in enumerate(passages, 1):
                lines.append(f"### Passage {i}\n{p}\n")
            
            return [TextContent(type="text", text="\n".join(lines))]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Search error: {e}")]
    
    elif name == "verify_citation":
        paper_name = arguments["paper_name"]
        claim = arguments["claim"]
        
        # Find paper markdown
        md_path = MARKDOWN_DIR / f"{paper_name}.md"
        if not md_path.exists():
            matches = list(MARKDOWN_DIR.glob(f"*{paper_name}*.md"))
            if matches:
                md_path = matches[0]
            else:
                return [TextContent(
                    type="text",
                    text=f"❌ Cannot verify: paper '{paper_name}' not found in markdown directory.\n\nAdd the paper first, then verify.",
                )]
        
        try:
            paper_content = md_path.read_text(encoding="utf-8")
            
            # Create a mock citation for verification
            citation = Citation(
                key=paper_name,
                context=claim,
                file=Path("thesis.tex"),
                line=0,
            )
            
            verified, confidence, quote, notes = verify_claim_against_paper(
                citation, paper_content
            )
            
            # Format result
            if verified is True:
                status = "✅ VERIFIED"
            elif verified is False:
                status = "❌ NOT VERIFIED"
            else:
                status = "⚠️ UNCLEAR"
            
            result = f"""## Citation Verification: {paper_name}

**Status:** {status}
**Confidence:** {confidence:.0%}

**Claim being checked:**
> {claim}

**Supporting quote from paper:**
> {quote}

**Notes:** {notes}
"""
            
            if verified is False:
                result += "\n\n⚠️ **Action needed:** Revise the claim or find a different source."
            
            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Verification error: {e}")]
    
    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
