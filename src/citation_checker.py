#!/usr/bin/env python3
"""
Citation verification system.

Checks that:
1. Every \\cite{key} has a matching entry in .bib

For semantic verification (checking if claims match papers),
use the verifier subagent instead:
  "Verify this claim against [paper]"
"""

import re
import sys
from pathlib import Path
from dataclasses import dataclass

from rich.console import Console
from rich.table import Table

console = Console()


@dataclass
class Citation:
    """A citation found in the LaTeX source."""
    key: str
    context: str  # Surrounding text
    file: Path
    line: int


@dataclass 
class VerificationResult:
    """Result of verifying a citation."""
    citation: Citation
    bib_exists: bool
    notes: str


def extract_citations(tex_path: Path) -> list[Citation]:
    """
    Extract all citations from a LaTeX file.
    
    Returns list of Citation objects with surrounding context.
    """
    content = tex_path.read_text(encoding="utf-8")
    lines = content.split("\n")
    
    citations = []
    
    # Match \cite{key}, \citep{key}, \citet{key}, etc.
    cite_pattern = re.compile(r'\\cite[pt]?\{([^}]+)\}')
    
    for line_num, line in enumerate(lines, 1):
        for match in cite_pattern.finditer(line):
            keys = match.group(1).split(",")
            
            # Get context (surrounding sentences)
            start = max(0, line_num - 3)
            end = min(len(lines), line_num + 2)
            context = "\n".join(lines[start:end])
            
            for key in keys:
                key = key.strip()
                citations.append(Citation(
                    key=key,
                    context=context,
                    file=tex_path,
                    line=line_num,
                ))
    
    return citations


def parse_bib_keys(bib_path: Path) -> set[str]:
    """Extract all citation keys from a .bib file."""
    content = bib_path.read_text(encoding="utf-8")
    
    # Match @article{key, @book{key, etc.
    pattern = re.compile(r'@\w+\{([^,]+),')
    
    return {match.group(1).strip() for match in pattern.finditer(content)}


def check_citations(
    tex_dir: Path,
    bib_path: Path,
) -> list[VerificationResult]:
    """
    Check all citations in LaTeX files have matching .bib entries.
    
    Args:
        tex_dir: Directory containing .tex files
        bib_path: Path to .bib file
        
    Returns:
        List of verification results
    """
    results = []
    
    # Get valid bib keys
    bib_keys = parse_bib_keys(bib_path) if bib_path.exists() else set()
    console.print(f"Found {len(bib_keys)} entries in bibliography\n")
    
    # Find all tex files
    tex_files = list(tex_dir.glob("**/*.tex"))
    
    for tex_file in tex_files:
        citations = extract_citations(tex_file)
        console.print(f"[blue]{tex_file.name}:[/blue] {len(citations)} citations")
        
        for citation in citations:
            bib_exists = citation.key in bib_keys
            notes = "" if bib_exists else "Citation key not found in .bib file!"
            
            results.append(VerificationResult(
                citation=citation,
                bib_exists=bib_exists,
                notes=notes,
            ))
    
    return results


def print_report(results: list[VerificationResult]):
    """Print a formatted verification report."""
    
    # Summary
    total = len(results)
    missing_bib = sum(1 for r in results if not r.bib_exists)
    
    console.print("\n" + "=" * 60)
    console.print("[bold]CITATION CHECK REPORT[/bold]")
    console.print("=" * 60)
    
    console.print(f"\nTotal citations: {total}")
    console.print(f"  ✓ Found in .bib: {total - missing_bib}")
    console.print(f"  ⚠ Missing from .bib: {missing_bib}")
    
    # Issues table
    issues = [r for r in results if not r.bib_exists]
    
    if issues:
        console.print("\n[bold red]MISSING CITATIONS:[/bold red]\n")
        
        table = Table(show_header=True, header_style="bold")
        table.add_column("Key")
        table.add_column("File:Line")
        table.add_column("Context")
        
        for r in issues:
            context_preview = r.citation.context[:50].replace("\n", " ") + "..."
            table.add_row(
                r.citation.key,
                f"{r.citation.file.name}:{r.citation.line}",
                context_preview,
            )
        
        console.print(table)
        console.print("\n[dim]Add these entries to your .bib file before committing.[/dim]")
        console.print("[dim]For semantic verification, use the verifier subagent.[/dim]")
    else:
        console.print("\n[bold green]All citations found in .bib file![/bold green]")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Check LaTeX citations against .bib file",
        epilog="""
For semantic verification (checking if claims match papers),
use the verifier subagent instead:
  "Verify this claim against [paper]"
        """,
    )
    parser.add_argument("tex_dir", type=Path, help="Directory with .tex files")
    parser.add_argument("bib_file", type=Path, help="Path to .bib file")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    results = check_citations(
        tex_dir=args.tex_dir,
        bib_path=args.bib_file,
    )
    
    if args.json:
        import json
        output = [
            {
                "key": r.citation.key,
                "file": str(r.citation.file),
                "line": r.citation.line,
                "bib_exists": r.bib_exists,
                "notes": r.notes,
            }
            for r in results
        ]
        print(json.dumps(output, indent=2))
    else:
        print_report(results)
    
    # Exit with error if issues found
    issues = [r for r in results if not r.bib_exists]
    sys.exit(1 if issues else 0)


if __name__ == "__main__":
    main()
