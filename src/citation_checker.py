#!/usr/bin/env python3
"""
Citation verification system.

Checks that:
1. Every \cite{key} has a matching entry in .bib
2. The citation context matches what the paper actually says
3. No hallucinated claims are attributed to papers
"""

import re
import os
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from anthropic import Anthropic
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
    claim_verified: Optional[bool]  # None if couldn't check
    paper_quote: Optional[str]  # Supporting quote from paper
    confidence: float
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


def verify_claim_against_paper(
    citation: Citation,
    paper_markdown: str,
    model: str = "claude-sonnet-4-20250514",
    api_key: str | None = None,
) -> tuple[bool, float, str, str]:
    """
    Verify that the claim in context is supported by the paper.
    
    Returns:
        (is_verified, confidence, supporting_quote, notes)
    """
    client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
    
    prompt = f"""You are a citation verification assistant. Your job is to check if a claim made in a thesis is actually supported by the cited paper.

CLAIM CONTEXT (from thesis):
```
{citation.context}
```

The citation key is: {citation.key}

PAPER CONTENT:
```
{paper_markdown[:50000]}  # Truncate for context limits
```

TASK:
1. Identify what specific claim is being attributed to this paper
2. Search the paper for evidence supporting or contradicting this claim
3. Return your assessment

Respond in this exact format:
CLAIM: [what the thesis claims the paper says]
VERIFIED: [YES/NO/PARTIAL/UNCLEAR]
CONFIDENCE: [0.0-1.0]
QUOTE: [exact quote from paper that supports/contradicts, or "N/A"]
NOTES: [brief explanation]
"""

    try:
        response = client.messages.create(
            model=model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        
        text = response.content[0].text
        
        # Parse response
        verified = "YES" in text.split("VERIFIED:")[1].split("\n")[0].upper() if "VERIFIED:" in text else None
        
        confidence = 0.5
        if "CONFIDENCE:" in text:
            try:
                conf_str = text.split("CONFIDENCE:")[1].split("\n")[0].strip()
                confidence = float(conf_str)
            except:
                pass
        
        quote = "N/A"
        if "QUOTE:" in text:
            quote = text.split("QUOTE:")[1].split("NOTES:")[0].strip()
        
        notes = ""
        if "NOTES:" in text:
            notes = text.split("NOTES:")[1].strip()
        
        return (verified, confidence, quote, notes)
        
    except Exception as e:
        return (None, 0.0, "N/A", f"Error: {e}")


def check_citations(
    tex_dir: Path,
    bib_path: Path,
    markdown_dir: Path,
    verify_claims: bool = True,
) -> list[VerificationResult]:
    """
    Check all citations in LaTeX files.
    
    Args:
        tex_dir: Directory containing .tex files
        bib_path: Path to .bib file
        markdown_dir: Directory with paper markdown files
        verify_claims: Whether to verify claims against papers (slower)
        
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
            # Check if key exists in bib
            bib_exists = citation.key in bib_keys
            
            claim_verified = None
            paper_quote = None
            confidence = 0.0
            notes = ""
            
            if not bib_exists:
                notes = "Citation key not found in .bib file!"
            elif verify_claims:
                # Try to find the paper markdown
                paper_md = markdown_dir / f"{citation.key}.md"
                
                # Also try matching by partial name
                if not paper_md.exists():
                    matches = list(markdown_dir.glob(f"*{citation.key.split('_')[0]}*.md"))
                    if matches:
                        paper_md = matches[0]
                
                if paper_md.exists():
                    paper_content = paper_md.read_text(encoding="utf-8")
                    claim_verified, confidence, paper_quote, notes = \
                        verify_claim_against_paper(citation, paper_content)
                else:
                    notes = f"Paper markdown not found for verification"
            
            results.append(VerificationResult(
                citation=citation,
                bib_exists=bib_exists,
                claim_verified=claim_verified,
                paper_quote=paper_quote,
                confidence=confidence,
                notes=notes,
            ))
    
    return results


def print_report(results: list[VerificationResult]):
    """Print a formatted verification report."""
    
    # Summary
    total = len(results)
    missing_bib = sum(1 for r in results if not r.bib_exists)
    verified = sum(1 for r in results if r.claim_verified is True)
    unverified = sum(1 for r in results if r.claim_verified is False)
    unchecked = sum(1 for r in results if r.claim_verified is None and r.bib_exists)
    
    console.print("\n" + "=" * 60)
    console.print("[bold]CITATION VERIFICATION REPORT[/bold]")
    console.print("=" * 60)
    
    console.print(f"\nTotal citations: {total}")
    console.print(f"  ✓ Verified: {verified}")
    console.print(f"  ✗ Unverified: {unverified}")
    console.print(f"  ? Unchecked: {unchecked}")
    console.print(f"  ⚠ Missing from .bib: {missing_bib}")
    
    # Issues table
    issues = [r for r in results if not r.bib_exists or r.claim_verified is False]
    
    if issues:
        console.print("\n[bold red]ISSUES FOUND:[/bold red]\n")
        
        table = Table(show_header=True, header_style="bold")
        table.add_column("Key")
        table.add_column("File:Line")
        table.add_column("Issue")
        table.add_column("Notes")
        
        for r in issues:
            issue_type = "Missing .bib" if not r.bib_exists else "Claim not verified"
            table.add_row(
                r.citation.key,
                f"{r.citation.file.name}:{r.citation.line}",
                issue_type,
                r.notes[:50] + "..." if len(r.notes) > 50 else r.notes,
            )
        
        console.print(table)
    else:
        console.print("\n[bold green]No issues found![/bold green]")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify LaTeX citations")
    parser.add_argument("tex_dir", type=Path, help="Directory with .tex files")
    parser.add_argument("bib_file", type=Path, help="Path to .bib file")
    parser.add_argument("--markdown-dir", type=Path, help="Directory with paper markdowns")
    parser.add_argument("--no-verify", action="store_true", help="Skip claim verification")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    markdown_dir = args.markdown_dir or args.tex_dir.parent / "markdown"
    
    results = check_citations(
        tex_dir=args.tex_dir,
        bib_path=args.bib_file,
        markdown_dir=markdown_dir,
        verify_claims=not args.no_verify,
    )
    
    if args.json:
        import json
        output = [
            {
                "key": r.citation.key,
                "file": str(r.citation.file),
                "line": r.citation.line,
                "bib_exists": r.bib_exists,
                "claim_verified": r.claim_verified,
                "confidence": r.confidence,
                "notes": r.notes,
            }
            for r in results
        ]
        print(json.dumps(output, indent=2))
    else:
        print_report(results)
    
    # Exit with error if issues found
    issues = [r for r in results if not r.bib_exists or r.claim_verified is False]
    sys.exit(1 if issues else 0)


if __name__ == "__main__":
    main()
