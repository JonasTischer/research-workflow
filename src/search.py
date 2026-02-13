#!/usr/bin/env python3
"""
CLI for searching and reading papers.

Usage:
    python search.py find "attention mechanisms"
    python search.py read vaswani2017
    python search.py summary vaswani2017
    python search.py list
    python search.py verify vaswani2017 "Transformers achieved 28.4 BLEU"
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from google_search import GooglePaperSearch
from citation_checker import verify_claim_against_paper, Citation


def get_dirs():
    """Get configured directories from env or defaults."""
    base = Path(os.environ.get("THESIS_DIR", Path(__file__).parent.parent))
    return {
        "papers": Path(os.environ.get("THESIS_PAPERS_DIR", base / "papers")),
        "markdown": Path(os.environ.get("THESIS_MARKDOWN_DIR", base / "markdown")),
        "summaries": Path(os.environ.get("THESIS_SUMMARIES_DIR", base / "summaries")),
    }


def cmd_find(args):
    """Search for relevant papers."""
    try:
        client = GooglePaperSearch()
        results = client.search(args.query, top_k=args.top)
        
        if not results:
            print("No relevant papers found.")
            return
        
        print(f"Found {len(results)} relevant papers:\n")
        for i, r in enumerate(results, 1):
            print(f"{i}. {r.filename} (relevance: {r.score:.2f})")
            if r.snippet:
                print(f"   {r.snippet}")
            print()
        
        print("Use 'search.py read <name>' to read full paper")
        print("Use 'search.py summary <name>' to read summary")
        
    except Exception as e:
        print(f"Search error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_list(args):
    """List all papers in library."""
    dirs = get_dirs()
    
    papers = []
    if dirs["markdown"].exists():
        for md in dirs["markdown"].glob("*.md"):
            if not md.name.endswith(".summary.md"):
                papers.append(md.stem)
    
    summaries = set()
    if dirs["summaries"].exists():
        for s in dirs["summaries"].glob("*.summary.md"):
            summaries.add(s.stem.replace(".summary", ""))
    
    if not papers:
        print("No papers in library yet.")
        print(f"\nAdd PDFs to: {dirs['papers']}")
        print("Then run: python watcher.py --once")
        return
    
    print(f"Papers in library ({len(papers)}):\n")
    for p in sorted(papers):
        has_summary = "✓" if p in summaries else " "
        print(f"  [{has_summary}] {p}")
    
    print("\n[✓] = has AI summary")


def cmd_read(args):
    """Read full paper markdown."""
    dirs = get_dirs()
    
    md_path = dirs["markdown"] / f"{args.name}.md"
    
    if not md_path.exists():
        # Try fuzzy match
        matches = list(dirs["markdown"].glob(f"*{args.name}*.md"))
        matches = [m for m in matches if not m.name.endswith(".summary.md")]
        if matches:
            md_path = matches[0]
            print(f"(matched: {md_path.name})\n", file=sys.stderr)
        else:
            print(f"Paper not found: {args.name}", file=sys.stderr)
            print("\nAvailable papers:", file=sys.stderr)
            cmd_list(args)
            sys.exit(1)
    
    content = md_path.read_text(encoding="utf-8")
    
    if args.section:
        # Extract specific section
        lines = content.split("\n")
        in_section = False
        section_lines = []
        
        for line in lines:
            if line.startswith("#") and args.section.lower() in line.lower():
                in_section = True
            elif in_section and line.startswith("#") and not line.startswith("###"):
                break
            
            if in_section:
                section_lines.append(line)
        
        if section_lines:
            print("\n".join(section_lines))
        else:
            print(f"Section '{args.section}' not found", file=sys.stderr)
            sys.exit(1)
    else:
        print(content)


def cmd_summary(args):
    """Read paper summary."""
    dirs = get_dirs()
    
    summary_path = dirs["summaries"] / f"{args.name}.summary.md"
    
    if not summary_path.exists():
        # Try fuzzy match
        matches = list(dirs["summaries"].glob(f"*{args.name}*.summary.md"))
        if matches:
            summary_path = matches[0]
            print(f"(matched: {summary_path.name})\n", file=sys.stderr)
        else:
            print(f"Summary not found for: {args.name}", file=sys.stderr)
            sys.exit(1)
    
    print(summary_path.read_text(encoding="utf-8"))


def cmd_verify(args):
    """Verify a citation claim against paper."""
    dirs = get_dirs()
    
    # Find paper
    md_path = dirs["markdown"] / f"{args.paper}.md"
    if not md_path.exists():
        matches = list(dirs["markdown"].glob(f"*{args.paper}*.md"))
        matches = [m for m in matches if not m.name.endswith(".summary.md")]
        if matches:
            md_path = matches[0]
        else:
            print(f"❌ Paper not found: {args.paper}", file=sys.stderr)
            sys.exit(1)
    
    paper_content = md_path.read_text(encoding="utf-8")
    
    citation = Citation(
        key=args.paper,
        context=args.claim,
        file=Path("thesis.tex"),
        line=0,
    )
    
    print(f"Verifying claim against: {md_path.name}\n")
    
    verified, confidence, quote, notes = verify_claim_against_paper(
        citation, paper_content
    )
    
    # Output
    if verified is True:
        print("✅ VERIFIED")
    elif verified is False:
        print("❌ NOT VERIFIED")
    else:
        print("⚠️ UNCLEAR")
    
    print(f"Confidence: {confidence:.0%}\n")
    
    print("Claim:")
    print(f"  {args.claim}\n")
    
    print("Supporting quote:")
    print(f"  {quote}\n")
    
    print(f"Notes: {notes}")
    
    if verified is False:
        sys.exit(1)


def cmd_upload(args):
    """Upload papers to Google for search indexing."""
    dirs = get_dirs()
    
    try:
        client = GooglePaperSearch()
        
        if args.name:
            # Upload single paper
            pdf_path = dirs["papers"] / f"{args.name}.pdf"
            if not pdf_path.exists():
                matches = list(dirs["papers"].glob(f"*{args.name}*.pdf"))
                if matches:
                    pdf_path = matches[0]
                else:
                    print(f"PDF not found: {args.name}", file=sys.stderr)
                    sys.exit(1)
            
            client.upload_paper(pdf_path)
        else:
            # Upload all
            results = client.upload_all(dirs["papers"])
            print(f"\nUploaded {len(results)} papers to Google")
            
    except Exception as e:
        print(f"Upload error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Search and read research papers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s find "attention mechanisms in transformers"
  %(prog)s list
  %(prog)s read vaswani2017
  %(prog)s read vaswani2017 --section "Results"
  %(prog)s summary vaswani2017
  %(prog)s verify vaswani2017 "Transformers achieved 28.4 BLEU on WMT 2014"
  %(prog)s upload                    # Upload all papers to Google
  %(prog)s upload vaswani2017        # Upload single paper
        """,
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # find
    p_find = subparsers.add_parser("find", help="Search for relevant papers")
    p_find.add_argument("query", help="Search query")
    p_find.add_argument("--top", "-n", type=int, default=5, help="Number of results")
    p_find.set_defaults(func=cmd_find)
    
    # list
    p_list = subparsers.add_parser("list", help="List all papers")
    p_list.set_defaults(func=cmd_list)
    
    # read
    p_read = subparsers.add_parser("read", help="Read full paper markdown")
    p_read.add_argument("name", help="Paper name")
    p_read.add_argument("--section", "-s", help="Extract specific section")
    p_read.set_defaults(func=cmd_read)
    
    # summary
    p_summary = subparsers.add_parser("summary", help="Read paper summary")
    p_summary.add_argument("name", help="Paper name")
    p_summary.set_defaults(func=cmd_summary)
    
    # verify
    p_verify = subparsers.add_parser("verify", help="Verify citation claim")
    p_verify.add_argument("paper", help="Paper name")
    p_verify.add_argument("claim", help="Claim to verify")
    p_verify.set_defaults(func=cmd_verify)
    
    # upload
    p_upload = subparsers.add_parser("upload", help="Upload papers to Google")
    p_upload.add_argument("name", nargs="?", help="Paper name (or all if omitted)")
    p_upload.set_defaults(func=cmd_upload)
    
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
