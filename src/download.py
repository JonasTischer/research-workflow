#!/usr/bin/env python3
"""
Download papers from various sources.

Supports:
- Direct PDF URLs
- arXiv IDs
- Semantic Scholar paper IDs
- DOIs (when open access)

Usage:
    python download.py url "https://arxiv.org/pdf/1706.03762.pdf"
    python download.py arxiv "1706.03762"
    python download.py doi "10.48550/arXiv.1706.03762"
"""

import os
import sys
import re
import argparse
from pathlib import Path
from urllib.parse import urlparse

try:
    import httpx
except ImportError:
    print("Install httpx: uv pip install httpx")
    sys.exit(1)

from rich.console import Console
from rich.progress import Progress

console = Console()


def get_papers_dir() -> Path:
    """Get the papers directory from env or default."""
    papers_dir = os.environ.get("THESIS_PAPERS_DIR")
    if papers_dir:
        return Path(papers_dir)
    
    # Try to find config
    config_path = Path(__file__).parent.parent / "config.yaml"
    if config_path.exists():
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)
            return Path(config.get("paths", {}).get("papers", "./papers"))
    
    return Path("./papers")


def sanitize_filename(name: str) -> str:
    """Create a safe filename from a string."""
    # Remove/replace unsafe characters
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'\s+', '_', name)
    name = name[:100]  # Limit length
    return name


def download_pdf(url: str, output_path: Path) -> bool:
    """
    Download a PDF from a URL.
    
    Args:
        url: PDF URL
        output_path: Where to save
        
    Returns:
        True if successful
    """
    console.print(f"[blue]Downloading:[/blue] {url}")
    
    try:
        with httpx.Client(follow_redirects=True, timeout=60) as client:
            with client.stream("GET", url) as response:
                response.raise_for_status()
                
                total = int(response.headers.get("content-length", 0))
                
                with Progress() as progress:
                    task = progress.add_task("Downloading...", total=total or None)
                    
                    with open(output_path, "wb") as f:
                        for chunk in response.iter_bytes(8192):
                            f.write(chunk)
                            progress.update(task, advance=len(chunk))
        
        console.print(f"[green]✓ Saved:[/green] {output_path}")
        return True
        
    except Exception as e:
        console.print(f"[red]Download failed:[/red] {e}")
        if output_path.exists():
            output_path.unlink()
        return False


def download_from_url(url: str, name: str | None = None) -> Path | None:
    """Download a PDF from a direct URL."""
    papers_dir = get_papers_dir()
    papers_dir.mkdir(parents=True, exist_ok=True)
    
    if name:
        filename = sanitize_filename(name) + ".pdf"
    else:
        # Extract from URL
        parsed = urlparse(url)
        filename = Path(parsed.path).name
        if not filename.endswith(".pdf"):
            filename += ".pdf"
    
    output_path = papers_dir / filename
    
    if output_path.exists():
        console.print(f"[yellow]Already exists:[/yellow] {output_path}")
        return output_path
    
    if download_pdf(url, output_path):
        return output_path
    return None


def download_from_arxiv(arxiv_id: str) -> Path | None:
    """
    Download a paper from arXiv.
    
    Args:
        arxiv_id: arXiv ID (e.g., "1706.03762" or "2010.11929")
    """
    # Clean up ID
    arxiv_id = arxiv_id.replace("arXiv:", "").replace("arxiv:", "")
    if "/" in arxiv_id:
        arxiv_id = arxiv_id.split("/")[-1]
    
    # Get metadata first
    import xml.etree.ElementTree as ET
    
    api_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
    
    with httpx.Client() as client:
        response = client.get(api_url)
        response.raise_for_status()
    
    root = ET.fromstring(response.text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    
    entry = root.find("atom:entry", ns)
    if entry is None:
        console.print(f"[red]Paper not found:[/red] {arxiv_id}")
        return None
    
    title = entry.find("atom:title", ns)
    title_text = title.text.strip() if title is not None else arxiv_id
    
    # Get authors for filename
    authors = []
    for author in entry.findall("atom:author", ns):
        name = author.find("atom:name", ns)
        if name is not None:
            # Get last name
            parts = name.text.split()
            if parts:
                authors.append(parts[-1])
    
    first_author = authors[0] if authors else "unknown"
    
    # Create filename: AuthorYear_title
    # Extract year from ID (format: YYMM.NNNNN or category/YYMMNNN)
    year = "20" + arxiv_id[:2] if arxiv_id[0].isdigit() else "unknown"
    
    filename = f"{first_author}{year}_{sanitize_filename(title_text[:50])}"
    
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    return download_from_url(pdf_url, filename)


def download_from_doi(doi: str) -> Path | None:
    """
    Try to download open access PDF via DOI.
    
    Uses Unpaywall API to find open access versions.
    """
    # Clean DOI
    doi = doi.replace("https://doi.org/", "").replace("http://doi.org/", "")
    
    # Try Unpaywall API (free, no key needed for low volume)
    email = os.environ.get("EMAIL", "user@example.com")
    unpaywall_url = f"https://api.unpaywall.org/v2/{doi}?email={email}"
    
    try:
        with httpx.Client() as client:
            response = client.get(unpaywall_url)
            response.raise_for_status()
            data = response.json()
        
        # Find best open access location
        pdf_url = None
        
        # Check best_oa_location first
        best_oa = data.get("best_oa_location")
        if best_oa and best_oa.get("url_for_pdf"):
            pdf_url = best_oa["url_for_pdf"]
        
        # Fall back to any oa_location
        if not pdf_url:
            for loc in data.get("oa_locations", []):
                if loc.get("url_for_pdf"):
                    pdf_url = loc["url_for_pdf"]
                    break
        
        if not pdf_url:
            console.print(f"[yellow]No open access PDF found for DOI:[/yellow] {doi}")
            console.print(f"Paper URL: {data.get('doi_url', 'N/A')}")
            return None
        
        # Create filename from metadata
        title = data.get("title", "")
        authors = data.get("z_authors", [])
        year = data.get("year", "")
        
        first_author = authors[0].get("family", "unknown") if authors else "unknown"
        filename = f"{first_author}{year}_{sanitize_filename(title[:50])}"
        
        return download_from_url(pdf_url, filename)
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[red]DOI not found:[/red] {doi}")
        else:
            console.print(f"[red]API error:[/red] {e}")
        return None


def download_from_semantic_scholar(paper_id: str) -> Path | None:
    """
    Download from Semantic Scholar if open access PDF available.
    
    Args:
        paper_id: Semantic Scholar paper ID or URL
    """
    # Extract ID from URL if needed
    if "semanticscholar.org" in paper_id:
        paper_id = paper_id.rstrip("/").split("/")[-1]
    
    api_url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}"
    params = {"fields": "title,authors,year,openAccessPdf"}
    
    try:
        with httpx.Client() as client:
            response = client.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()
        
        pdf_info = data.get("openAccessPdf")
        if not pdf_info or not pdf_info.get("url"):
            console.print(f"[yellow]No open access PDF available[/yellow]")
            return None
        
        # Create filename
        title = data.get("title", "")
        authors = data.get("authors", [])
        year = data.get("year", "")
        
        first_author = authors[0].get("name", "").split()[-1] if authors else "unknown"
        filename = f"{first_author}{year}_{sanitize_filename(title[:50])}"
        
        return download_from_url(pdf_info["url"], filename)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Download research papers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s url "https://arxiv.org/pdf/1706.03762.pdf"
  %(prog)s url "https://example.com/paper.pdf" --name "Smith2024_attention"
  %(prog)s arxiv "1706.03762"
  %(prog)s arxiv "2010.11929"
  %(prog)s doi "10.48550/arXiv.1706.03762"
  %(prog)s scholar "649def34f8be52c8b66281af98ae884c09aef38b"
        """,
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # URL
    p_url = subparsers.add_parser("url", help="Download from direct URL")
    p_url.add_argument("url", help="PDF URL")
    p_url.add_argument("--name", "-n", help="Output filename (without .pdf)")
    
    # arXiv
    p_arxiv = subparsers.add_parser("arxiv", help="Download from arXiv")
    p_arxiv.add_argument("arxiv_id", help="arXiv ID (e.g., 1706.03762)")
    
    # DOI
    p_doi = subparsers.add_parser("doi", help="Download via DOI (open access)")
    p_doi.add_argument("doi", help="DOI")
    
    # Semantic Scholar
    p_scholar = subparsers.add_parser("scholar", help="Download from Semantic Scholar")
    p_scholar.add_argument("paper_id", help="Semantic Scholar paper ID or URL")
    
    args = parser.parse_args()
    
    result = None
    
    if args.command == "url":
        result = download_from_url(args.url, args.name)
    elif args.command == "arxiv":
        result = download_from_arxiv(args.arxiv_id)
    elif args.command == "doi":
        result = download_from_doi(args.doi)
    elif args.command == "scholar":
        result = download_from_semantic_scholar(args.paper_id)
    
    if result:
        console.print(f"\n[bold green]Paper saved to:[/bold green] {result}")
        console.print("[dim]The watcher will auto-convert to markdown if running[/dim]")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
