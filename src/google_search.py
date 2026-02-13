"""Google File Search integration for paper retrieval."""

import os
from pathlib import Path
from dataclasses import dataclass
import google.generativeai as genai
from rich.console import Console

console = Console()


@dataclass
class SearchResult:
    """A search result with relevance score."""
    filename: str
    score: float
    snippet: str
    

class GooglePaperSearch:
    """
    Search papers using Google's Gemini File API.
    
    Papers are uploaded to Gemini and can be searched semantically.
    """
    
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-1.5-flash",
    ):
        """
        Initialize the search client.
        
        Args:
            api_key: Google API key (or uses GOOGLE_API_KEY env)
            model: Gemini model for search/retrieval
        """
        api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Google API key required (GOOGLE_API_KEY env or api_key param)")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self.uploaded_files: dict[str, genai.File] = {}
    
    def upload_paper(self, pdf_path: Path) -> str | None:
        """
        Upload a PDF to Gemini for indexing.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            File ID if successful, None otherwise
        """
        try:
            console.print(f"[blue]Uploading to Google:[/blue] {pdf_path.name}")
            
            # Upload the file
            uploaded = genai.upload_file(
                path=str(pdf_path),
                display_name=pdf_path.stem,
            )
            
            # Wait for processing
            import time
            while uploaded.state.name == "PROCESSING":
                time.sleep(2)
                uploaded = genai.get_file(uploaded.name)
            
            if uploaded.state.name == "FAILED":
                console.print(f"[red]Upload failed:[/red] {pdf_path.name}")
                return None
            
            self.uploaded_files[pdf_path.stem] = uploaded
            console.print(f"[green]✓ Uploaded:[/green] {pdf_path.name}")
            return uploaded.name
            
        except Exception as e:
            console.print(f"[red]Upload error:[/red] {e}")
            return None
    
    def upload_all(self, pdf_dir: Path) -> dict[str, str]:
        """
        Upload all PDFs in a directory.
        
        Args:
            pdf_dir: Directory containing PDFs
            
        Returns:
            Dict mapping filenames to file IDs
        """
        results = {}
        for pdf_path in sorted(pdf_dir.glob("*.pdf")):
            file_id = self.upload_paper(pdf_path)
            if file_id:
                results[pdf_path.stem] = file_id
        return results
    
    def list_uploaded(self) -> list[str]:
        """List all uploaded files."""
        files = list(genai.list_files())
        return [f.display_name for f in files]
    
    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[SearchResult]:
        """
        Search uploaded papers for relevant content.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of SearchResult objects
        """
        # Get all uploaded files
        files = list(genai.list_files())
        if not files:
            return []
        
        # Ask Gemini to rank papers by relevance
        prompt = f"""Given these uploaded papers, rank them by relevance to this query:

Query: {query}

Papers available:
{chr(10).join(f'- {f.display_name}' for f in files)}

Return a JSON array of the top {top_k} most relevant papers with format:
[{{"filename": "paper-name", "score": 0.95, "reason": "brief explanation"}}]

Only include papers that are actually relevant. Score from 0.0 to 1.0.
Return ONLY the JSON array, no other text."""

        try:
            response = self.model.generate_content(prompt)
            
            import json
            # Extract JSON from response
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            
            results_data = json.loads(text)
            
            return [
                SearchResult(
                    filename=r["filename"],
                    score=r.get("score", 0.5),
                    snippet=r.get("reason", ""),
                )
                for r in results_data[:top_k]
            ]
            
        except Exception as e:
            console.print(f"[red]Search error:[/red] {e}")
            return []
    
    def search_with_context(
        self,
        query: str,
        paper_name: str,
        max_chunks: int = 3,
    ) -> list[str]:
        """
        Search within a specific paper for relevant passages.
        
        Args:
            query: What to search for
            paper_name: Name of the paper (without extension)
            max_chunks: Maximum number of passages to return
            
        Returns:
            List of relevant text passages
        """
        # Find the file
        files = list(genai.list_files())
        target_file = None
        for f in files:
            if f.display_name == paper_name:
                target_file = f
                break
        
        if not target_file:
            return []
        
        prompt = f"""From this paper, extract the {max_chunks} most relevant passages for:

Query: {query}

Return each passage as a separate paragraph. Include page/section references if visible.
Focus on exact quotes and specific details, not summaries."""

        try:
            response = self.model.generate_content([target_file, prompt])
            
            # Split into passages
            passages = [p.strip() for p in response.text.split("\n\n") if p.strip()]
            return passages[:max_chunks]
            
        except Exception as e:
            console.print(f"[red]Context search error:[/red] {e}")
            return []


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python google_search.py upload <pdf_dir>")
        print("  python google_search.py search <query>")
        print("  python google_search.py list")
        sys.exit(1)
    
    cmd = sys.argv[1]
    client = GooglePaperSearch()
    
    if cmd == "upload" and len(sys.argv) > 2:
        pdf_dir = Path(sys.argv[2])
        results = client.upload_all(pdf_dir)
        print(f"Uploaded {len(results)} files")
        
    elif cmd == "search" and len(sys.argv) > 2:
        query = " ".join(sys.argv[2:])
        results = client.search(query)
        for r in results:
            print(f"{r.score:.2f} | {r.filename} | {r.snippet}")
            
    elif cmd == "list":
        files = client.list_uploaded()
        for f in files:
            print(f)
    else:
        print("Unknown command")
        sys.exit(1)
