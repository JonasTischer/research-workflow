"""PDF to Markdown conversion using Marker.

Supports LLM-enhanced mode with Gemini Flash for higher accuracy on:
- Tables spanning multiple pages
- Inline math formatting
- Form value extraction
- Complex table structures
"""

import os
import subprocess
from pathlib import Path
from rich.console import Console

console = Console()


def convert_pdf_to_markdown(
    pdf_path: Path,
    output_dir: Path,
    batch_multiplier: int = 2,
    max_pages: int | None = None,
    languages: list[str] | None = None,
    use_llm: bool = True,
    force_ocr: bool = False,
    redo_inline_math: bool = False,
) -> Path | None:
    """
    Convert a PDF to markdown using Marker.
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save the markdown
        batch_multiplier: Parallel processing factor
        max_pages: Maximum pages to process (None = all)
        languages: List of OCR languages
        use_llm: Use Gemini Flash for higher accuracy (recommended)
        force_ocr: Force OCR on all pages (use for scanned docs or inline math)
        redo_inline_math: Highest quality inline math (requires use_llm)
        
    Returns:
        Path to the generated markdown file, or None if failed
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Build marker command
    cmd = [
        "marker_single",
        str(pdf_path),
        "--output_dir", str(output_dir),
        "--batch_multiplier", str(batch_multiplier),
    ]
    
    # LLM mode for higher accuracy (uses Gemini Flash by default)
    if use_llm:
        # Check for API key
        if os.environ.get("GOOGLE_API_KEY"):
            cmd.append("--use_llm")
            console.print("[dim]Using Gemini Flash for enhanced accuracy[/dim]")
        else:
            console.print("[yellow]GOOGLE_API_KEY not set, skipping LLM enhancement[/yellow]")
    
    if force_ocr:
        cmd.append("--force_ocr")
    
    if redo_inline_math and use_llm:
        cmd.append("--redo_inline_math")
    
    if max_pages:
        cmd.extend(["--max_pages", str(max_pages)])
    
    if languages:
        cmd.extend(["--languages", ",".join(languages)])
    
    console.print(f"[blue]Converting:[/blue] {pdf_path.name}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 min timeout
        )
        
        if result.returncode != 0:
            console.print(f"[red]Marker error:[/red] {result.stderr}")
            return None
        
        # Marker creates a subfolder with the PDF name
        pdf_stem = pdf_path.stem
        output_subdir = output_dir / pdf_stem
        md_file = output_subdir / f"{pdf_stem}.md"
        
        # Move markdown to output_dir root with clean name
        if md_file.exists():
            final_path = output_dir / f"{pdf_stem}.md"
            md_file.rename(final_path)
            
            # Clean up the subfolder if empty (Marker creates extra files)
            try:
                # Keep any images that were extracted
                for img in output_subdir.glob("*.png"):
                    img.rename(output_dir / img.name)
                output_subdir.rmdir()
            except:
                pass
            
            console.print(f"[green]✓ Converted:[/green] {final_path.name}")
            return final_path
        else:
            console.print(f"[red]Output not found:[/red] {md_file}")
            return None
            
    except subprocess.TimeoutExpired:
        console.print(f"[red]Timeout converting:[/red] {pdf_path.name}")
        return None
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        return None


def convert_all_pdfs(
    pdf_dir: Path,
    output_dir: Path,
    skip_existing: bool = True,
    **kwargs,
) -> list[Path]:
    """
    Convert all PDFs in a directory.
    
    Args:
        pdf_dir: Directory containing PDFs
        output_dir: Directory for markdown output
        skip_existing: Skip if markdown already exists
        **kwargs: Passed to convert_pdf_to_markdown
        
    Returns:
        List of successfully converted markdown paths
    """
    converted = []
    
    for pdf_path in sorted(pdf_dir.glob("*.pdf")):
        md_path = output_dir / f"{pdf_path.stem}.md"
        
        if skip_existing and md_path.exists():
            console.print(f"[dim]Skipping (exists):[/dim] {pdf_path.name}")
            continue
        
        result = convert_pdf_to_markdown(pdf_path, output_dir, **kwargs)
        if result:
            converted.append(result)
    
    return converted


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python converter.py <pdf_path> <output_dir>")
        sys.exit(1)
    
    pdf_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    
    result = convert_pdf_to_markdown(pdf_path, output_dir)
    if result:
        print(f"Success: {result}")
    else:
        sys.exit(1)
