#!/usr/bin/env python3
"""
Web search tools for finding academic papers and research.

Supports:
- Brave Search (general web + academic)
- Semantic Scholar (academic papers)
- arXiv (preprints)

Usage:
    python web_search.py brave "transformer attention mechanisms"
    python web_search.py scholar "attention is all you need"
    python web_search.py arxiv "vision transformer"
    python web_search.py doi "10.1234/example"
"""

import os
import sys
import json
import argparse
from urllib.parse import quote
from pathlib import Path

try:
    import httpx
except ImportError:
    print("Install httpx: uv pip install httpx")
    sys.exit(1)

from rich.console import Console
from rich.table import Table

console = Console()


def brave_search(query: str, count: int = 10, academic: bool = False) -> list[dict]:
    """
    Search using Brave Search API.
    
    Args:
        query: Search query
        count: Number of results
        academic: If True, adds academic search terms
        
    Returns:
        List of search results
    """
    api_key = os.environ.get("BRAVE_API_KEY")
    if not api_key:
        console.print("[red]BRAVE_API_KEY not set[/red]")
        console.print("Get one at: https://brave.com/search/api/")
        sys.exit(1)
    
    if academic:
        query = f"{query} site:arxiv.org OR site:semanticscholar.org OR site:scholar.google.com OR filetype:pdf"
    
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "X-Subscription-Token": api_key,
        "Accept": "application/json",
    }
    params = {
        "q": query,
        "count": count,
    }
    
    with httpx.Client() as client:
        response = client.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
    
    results = []
    for item in data.get("web", {}).get("results", []):
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "description": item.get("description", ""),
            "source": "brave",
        })
    
    return results


def semantic_scholar_search(query: str, count: int = 10) -> list[dict]:
    """
    Search Semantic Scholar for academic papers.
    
    Args:
        query: Search query
        count: Number of results
        
    Returns:
        List of paper results
    
    Note: Set S2_API_KEY env var for higher rate limits.
          Get a key at: https://www.semanticscholar.org/product/api
    """
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": count,
        "fields": "title,authors,year,abstract,url,citationCount,openAccessPdf",
    }
    
    headers = {}
    api_key = os.environ.get("S2_API_KEY")
    if api_key:
        headers["x-api-key"] = api_key
    
    with httpx.Client() as client:
        response = client.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
    
    results = []
    for paper in data.get("data", []):
        authors = ", ".join(a.get("name", "") for a in paper.get("authors", [])[:3])
        if len(paper.get("authors", [])) > 3:
            authors += " et al."
        
        pdf_url = None
        if paper.get("openAccessPdf"):
            pdf_url = paper["openAccessPdf"].get("url")
        
        results.append({
            "title": paper.get("title", ""),
            "authors": authors,
            "year": paper.get("year"),
            "url": paper.get("url", ""),
            "pdf_url": pdf_url,
            "citations": paper.get("citationCount", 0),
            "abstract": paper.get("abstract", "")[:300] + "..." if paper.get("abstract") else "",
            "source": "semantic_scholar",
        })
    
    return results


def arxiv_search(query: str, count: int = 10) -> list[dict]:
    """
    Search arXiv for preprints.
    
    Args:
        query: Search query
        count: Number of results
        
    Returns:
        List of paper results
    """
    import xml.etree.ElementTree as ET
    
    url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": count,
        "sortBy": "relevance",
    }
    
    with httpx.Client() as client:
        response = client.get(url, params=params)
        response.raise_for_status()
    
    # Parse Atom XML
    root = ET.fromstring(response.text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    
    results = []
    for entry in root.findall("atom:entry", ns):
        title = entry.find("atom:title", ns)
        summary = entry.find("atom:summary", ns)
        
        authors = []
        for author in entry.findall("atom:author", ns):
            name = author.find("atom:name", ns)
            if name is not None:
                authors.append(name.text)
        
        # Get PDF link
        pdf_url = None
        for link in entry.findall("atom:link", ns):
            if link.get("title") == "pdf":
                pdf_url = link.get("href")
        
        # Get arXiv ID
        arxiv_id = entry.find("atom:id", ns)
        arxiv_id = arxiv_id.text.split("/")[-1] if arxiv_id is not None else ""
        
        results.append({
            "title": title.text.strip() if title is not None else "",
            "authors": ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else ""),
            "arxiv_id": arxiv_id,
            "url": f"https://arxiv.org/abs/{arxiv_id}",
            "pdf_url": pdf_url,
            "abstract": (summary.text.strip()[:300] + "...") if summary is not None else "",
            "source": "arxiv",
        })
    
    return results


def resolve_doi(doi: str) -> dict | None:
    """
    Resolve a DOI to get paper metadata.
    
    Args:
        doi: DOI string (e.g., "10.1234/example")
        
    Returns:
        Paper metadata or None
    """
    url = f"https://doi.org/{doi}"
    headers = {"Accept": "application/json"}
    
    try:
        with httpx.Client(follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
        
        authors = []
        for author in data.get("author", []):
            name = f"{author.get('given', '')} {author.get('family', '')}".strip()
            if name:
                authors.append(name)
        
        return {
            "title": data.get("title", ""),
            "authors": ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else ""),
            "year": data.get("published", {}).get("date-parts", [[None]])[0][0],
            "doi": doi,
            "url": data.get("URL", ""),
            "journal": data.get("container-title", [""])[0] if data.get("container-title") else "",
            "source": "doi",
        }
    except Exception as e:
        console.print(f"[red]DOI resolution failed:[/red] {e}")
        return None


def print_results(results: list[dict], format: str = "table"):
    """Print search results."""
    if not results:
        console.print("[yellow]No results found[/yellow]")
        return
    
    if format == "json":
        print(json.dumps(results, indent=2))
        return
    
    table = Table(show_header=True, header_style="bold")
    table.add_column("#", width=3)
    table.add_column("Title", max_width=50)
    table.add_column("Authors/Source", max_width=30)
    table.add_column("Year", width=6)
    
    for i, r in enumerate(results, 1):
        year = str(r.get("year", "")) if r.get("year") else ""
        authors = r.get("authors", r.get("source", ""))
        table.add_row(str(i), r.get("title", "")[:50], authors[:30], year)
    
    console.print(table)
    console.print()
    
    for i, r in enumerate(results, 1):
        if r.get("pdf_url"):
            console.print(f"  [{i}] PDF: {r['pdf_url']}")
        elif r.get("url"):
            console.print(f"  [{i}] URL: {r['url']}")


def main():
    parser = argparse.ArgumentParser(
        description="Search for academic papers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s brave "transformer attention" --academic
  %(prog)s scholar "attention is all you need"
  %(prog)s arxiv "vision transformer"
  %(prog)s doi "10.48550/arXiv.1706.03762"
        """,
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Brave
    p_brave = subparsers.add_parser("brave", help="Search with Brave")
    p_brave.add_argument("query", help="Search query")
    p_brave.add_argument("-n", "--count", type=int, default=10)
    p_brave.add_argument("--academic", "-a", action="store_true", help="Focus on academic sources")
    p_brave.add_argument("--json", action="store_true")
    
    # Semantic Scholar
    p_scholar = subparsers.add_parser("scholar", help="Search Semantic Scholar")
    p_scholar.add_argument("query", help="Search query")
    p_scholar.add_argument("-n", "--count", type=int, default=10)
    p_scholar.add_argument("--json", action="store_true")
    
    # arXiv
    p_arxiv = subparsers.add_parser("arxiv", help="Search arXiv")
    p_arxiv.add_argument("query", help="Search query")
    p_arxiv.add_argument("-n", "--count", type=int, default=10)
    p_arxiv.add_argument("--json", action="store_true")
    
    # DOI
    p_doi = subparsers.add_parser("doi", help="Resolve DOI")
    p_doi.add_argument("doi", help="DOI to resolve")
    p_doi.add_argument("--json", action="store_true")
    
    args = parser.parse_args()
    
    if args.command == "brave":
        results = brave_search(args.query, args.count, args.academic)
        print_results(results, "json" if args.json else "table")
        
    elif args.command == "scholar":
        results = semantic_scholar_search(args.query, args.count)
        print_results(results, "json" if args.json else "table")
        
    elif args.command == "arxiv":
        results = arxiv_search(args.query, args.count)
        print_results(results, "json" if args.json else "table")
        
    elif args.command == "doi":
        result = resolve_doi(args.doi)
        if result:
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                console.print(f"[bold]{result['title']}[/bold]")
                console.print(f"Authors: {result['authors']}")
                console.print(f"Year: {result.get('year', 'N/A')}")
                console.print(f"Journal: {result.get('journal', 'N/A')}")
                console.print(f"DOI: {result['doi']}")
                console.print(f"URL: {result['url']}")


if __name__ == "__main__":
    main()
