"""AI-powered paper summarization using Claude.

NOTE: This is optional. Claude Code can summarize papers directly
by reading the markdown files - no API key needed.

This module is for automated batch summarization via the watcher.
Requires: pip install anthropic
"""

import os
from pathlib import Path
from rich.console import Console

console = Console()

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None
    console.print("[yellow]anthropic not installed. Auto-summarization disabled.[/yellow]")
    console.print("[dim]Claude Code can still summarize papers directly.[/dim]")

DEFAULT_PROMPT = """Summarize this academic paper concisely. Include:

1. **Main Contribution**: What's the key innovation/finding? (2-3 sentences)
2. **Method**: How did they do it? (2-3 sentences)  
3. **Results**: Key quantitative results or findings
4. **Relevance**: What problems does this solve? Who should read this?
5. **Citation**: Suggested BibTeX key (format: authorYYYYkeyword)

Be concise but precise. Use technical language appropriate for a PhD thesis.

---

PAPER CONTENT:

{content}
"""


def summarize_paper(
    markdown_path: Path,
    output_dir: Path,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 1500,
    prompt_template: str = DEFAULT_PROMPT,
    api_key: str | None = None,
) -> Path | None:
    """
    Generate an AI summary of a paper.
    
    Requires anthropic package. For manual summarization,
    use Claude Code directly to read and summarize papers.
    
    Args:
        markdown_path: Path to the markdown file
        output_dir: Directory to save the summary
        model: Claude model to use
        max_tokens: Maximum tokens in response
        prompt_template: Template with {content} placeholder
        api_key: Anthropic API key (or uses ANTHROPIC_API_KEY env)
        
    Returns:
        Path to the summary file, or None if failed
    """
    if Anthropic is None:
        console.print("[yellow]Skipping auto-summary (anthropic not installed)[/yellow]")
        return None
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Read markdown content
    try:
        content = markdown_path.read_text(encoding="utf-8")
    except Exception as e:
        console.print(f"[red]Failed to read {markdown_path}:[/red] {e}")
        return None
    
    # Truncate if too long (Claude context limits)
    max_chars = 150000  # ~40k tokens, leaving room for response
    if len(content) > max_chars:
        console.print(f"[yellow]Truncating {markdown_path.name} to {max_chars} chars[/yellow]")
        content = content[:max_chars] + "\n\n[TRUNCATED]"
    
    # Initialize client
    client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
    
    console.print(f"[blue]Summarizing:[/blue] {markdown_path.name}")
    
    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": prompt_template.format(content=content),
                }
            ],
        )
        
        summary = response.content[0].text
        
        # Save summary
        summary_path = output_dir / f"{markdown_path.stem}.summary.md"
        
        # Add header with source info
        header = f"# Summary: {markdown_path.stem}\n\n"
        header += f"> Source: `{markdown_path.name}`\n\n"
        
        summary_path.write_text(header + summary, encoding="utf-8")
        
        console.print(f"[green]✓ Summarized:[/green] {summary_path.name}")
        return summary_path
        
    except Exception as e:
        console.print(f"[red]Summarization failed:[/red] {e}")
        return None


def summarize_all(
    markdown_dir: Path,
    output_dir: Path,
    skip_existing: bool = True,
    **kwargs,
) -> list[Path]:
    """
    Summarize all markdown files in a directory.
    
    Args:
        markdown_dir: Directory containing markdown files
        output_dir: Directory for summary output
        skip_existing: Skip if summary already exists
        **kwargs: Passed to summarize_paper
        
    Returns:
        List of successfully created summary paths
    """
    summaries = []
    
    for md_path in sorted(markdown_dir.glob("*.md")):
        # Skip existing summaries
        if md_path.name.endswith(".summary.md"):
            continue
            
        summary_path = output_dir / f"{md_path.stem}.summary.md"
        
        if skip_existing and summary_path.exists():
            console.print(f"[dim]Skipping (exists):[/dim] {md_path.name}")
            continue
        
        result = summarize_paper(md_path, output_dir, **kwargs)
        if result:
            summaries.append(result)
    
    return summaries


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python summarizer.py <markdown_path> <output_dir>")
        sys.exit(1)
    
    md_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    
    result = summarize_paper(md_path, output_dir)
    if result:
        print(f"Success: {result}")
    else:
        sys.exit(1)
