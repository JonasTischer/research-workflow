#!/usr/bin/env python3
"""
Watch for new PDFs and process them through the pipeline.

Pipeline:
1. PDF arrives in papers/
2. Convert to markdown (Marker)
3. Generate summary (Claude)
4. Upload to Google (optional, for search indexing)
"""

import os
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime

import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from rich.console import Console
from rich.panel import Panel

from converter import convert_pdf_to_markdown
from summarizer import summarize_paper

console = Console()


def load_config(config_path: Path) -> dict:
    """Load configuration from YAML file."""
    if not config_path.exists():
        console.print(f"[red]Config not found:[/red] {config_path}")
        console.print("Copy config.example.yaml to config.yaml and edit it.")
        sys.exit(1)
    
    with open(config_path) as f:
        return yaml.safe_load(f)


class PaperHandler(FileSystemEventHandler):
    """Handle new PDF files."""
    
    def __init__(
        self,
        markdown_dir: Path,
        summary_dir: Path,
        converter_config: dict,
        summarizer_config: dict,
        upload_to_google: bool = False,
    ):
        self.markdown_dir = markdown_dir
        self.summary_dir = summary_dir
        self.converter_config = converter_config
        self.summarizer_config = summarizer_config
        self.upload_to_google = upload_to_google
        self.processed: set[str] = set()
        
        # Track recently modified files to avoid duplicates
        self.recent_events: dict[str, float] = {}
        self.debounce_seconds = 2.0
    
    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
        self._process_if_pdf(event.src_path)
    
    def on_modified(self, event):
        """Handle file modification events (some apps create then write)."""
        if event.is_directory:
            return
        self._process_if_pdf(event.src_path)
    
    def _process_if_pdf(self, path: str):
        """Process file if it's a PDF and not recently processed."""
        path = Path(path)
        
        if path.suffix.lower() != ".pdf":
            return
        
        # Debounce: skip if processed very recently
        now = time.time()
        if path.name in self.recent_events:
            if now - self.recent_events[path.name] < self.debounce_seconds:
                return
        
        self.recent_events[path.name] = now
        
        # Skip if already fully processed
        if path.name in self.processed:
            return
        
        # Wait a moment for file to be fully written
        time.sleep(1)
        
        console.print(Panel(
            f"[bold]New paper detected:[/bold] {path.name}",
            style="blue",
        ))
        
        self.process_paper(path)
    
    def process_paper(self, pdf_path: Path):
        """Run the full processing pipeline on a paper."""
        
        # Step 1: Convert to markdown
        md_path = self.markdown_dir / f"{pdf_path.stem}.md"
        
        if not md_path.exists():
            md_path = convert_pdf_to_markdown(
                pdf_path,
                self.markdown_dir,
                **self.converter_config,
            )
            
            if not md_path:
                console.print(f"[red]✗ Conversion failed, skipping[/red]")
                return
        else:
            console.print(f"[dim]Markdown exists:[/dim] {md_path.name}")
        
        # Step 2: Generate summary
        summary_path = self.summary_dir / f"{pdf_path.stem}.summary.md"
        
        if not summary_path.exists():
            summary_path = summarize_paper(
                md_path,
                self.summary_dir,
                **self.summarizer_config,
            )
            
            if not summary_path:
                console.print(f"[yellow]⚠ Summary failed, continuing[/yellow]")
        else:
            console.print(f"[dim]Summary exists:[/dim] {summary_path.name}")
        
        # Step 3: Upload to Google (optional)
        if self.upload_to_google:
            try:
                from google_search import GooglePaperSearch
                client = GooglePaperSearch()
                client.upload_paper(pdf_path)
            except Exception as e:
                console.print(f"[yellow]⚠ Google upload failed:[/yellow] {e}")
        
        # Mark as processed
        self.processed.add(pdf_path.name)
        
        console.print(Panel(
            f"[bold green]✓ Processed:[/bold green] {pdf_path.name}",
            style="green",
        ))


def process_existing(
    papers_dir: Path,
    markdown_dir: Path,
    summary_dir: Path,
    converter_config: dict,
    summarizer_config: dict,
):
    """Process all existing PDFs in the papers directory."""
    console.print("[bold]Processing existing papers...[/bold]\n")
    
    handler = PaperHandler(
        markdown_dir=markdown_dir,
        summary_dir=summary_dir,
        converter_config=converter_config,
        summarizer_config=summarizer_config,
    )
    
    pdfs = list(papers_dir.glob("*.pdf"))
    console.print(f"Found {len(pdfs)} PDFs\n")
    
    for pdf_path in sorted(pdfs):
        handler.process_paper(pdf_path)
    
    console.print(f"\n[bold green]Done processing {len(pdfs)} papers[/bold green]")


def watch(
    papers_dir: Path,
    markdown_dir: Path,
    summary_dir: Path,
    converter_config: dict,
    summarizer_config: dict,
    upload_to_google: bool = False,
):
    """Start watching for new PDFs."""
    console.print(Panel(
        f"[bold]Watching for new papers[/bold]\n\n"
        f"Papers dir: {papers_dir}\n"
        f"Markdown dir: {markdown_dir}\n"
        f"Summary dir: {summary_dir}",
        title="Thesis Workflow",
        style="blue",
    ))
    
    handler = PaperHandler(
        markdown_dir=markdown_dir,
        summary_dir=summary_dir,
        converter_config=converter_config,
        summarizer_config=summarizer_config,
        upload_to_google=upload_to_google,
    )
    
    observer = Observer()
    observer.schedule(handler, str(papers_dir), recursive=False)
    observer.start()
    
    console.print("\n[dim]Press Ctrl+C to stop[/dim]\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        console.print("\n[yellow]Stopping watcher...[/yellow]")
    
    observer.join()


def main():
    parser = argparse.ArgumentParser(description="Watch for new papers and process them")
    parser.add_argument(
        "--config", "-c",
        type=Path,
        default=Path(__file__).parent.parent / "config.yaml",
        help="Path to config file",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process existing files once and exit (don't watch)",
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Upload PDFs to Google for search indexing",
    )
    
    args = parser.parse_args()
    
    # Load config
    config = load_config(args.config)
    
    # Resolve paths relative to config file
    config_dir = args.config.parent
    paths = config.get("paths", {})
    
    papers_dir = Path(paths.get("papers", "./papers"))
    markdown_dir = Path(paths.get("markdown", "./markdown"))
    summary_dir = Path(paths.get("summaries", "./summaries"))
    
    if not papers_dir.is_absolute():
        papers_dir = config_dir / papers_dir
    if not markdown_dir.is_absolute():
        markdown_dir = config_dir / markdown_dir
    if not summary_dir.is_absolute():
        summary_dir = config_dir / summary_dir
    
    # Create directories
    papers_dir.mkdir(parents=True, exist_ok=True)
    markdown_dir.mkdir(parents=True, exist_ok=True)
    summary_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract configs
    converter_config = config.get("converter", {})
    summarizer_config = config.get("summarizer", {})
    
    if args.once:
        process_existing(
            papers_dir=papers_dir,
            markdown_dir=markdown_dir,
            summary_dir=summary_dir,
            converter_config=converter_config,
            summarizer_config=summarizer_config,
        )
    else:
        # Process existing first if configured
        if config.get("watcher", {}).get("process_existing", True):
            process_existing(
                papers_dir=papers_dir,
                markdown_dir=markdown_dir,
                summary_dir=summary_dir,
                converter_config=converter_config,
                summarizer_config=summarizer_config,
            )
        
        watch(
            papers_dir=papers_dir,
            markdown_dir=markdown_dir,
            summary_dir=summary_dir,
            converter_config=converter_config,
            summarizer_config=summarizer_config,
            upload_to_google=args.upload,
        )


if __name__ == "__main__":
    main()
