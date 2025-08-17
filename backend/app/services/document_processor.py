import asyncio
from pathlib import Path
from typing import Dict, Any
import markdown
import pdfplumber
from bs4 import BeautifulSoup
import aiofiles

from app.models.document import DocumentType

class DocumentProcessor:
    """Process different document types for annotation"""
    
    async def process_document(self, file_path: Path, document_type: DocumentType) -> Dict[str, Any]:
        """Process a document and extract content for annotation"""
        
        if document_type == DocumentType.HTML:
            return await self._process_html(file_path)
        elif document_type == DocumentType.MARKDOWN:
            return await self._process_markdown(file_path)
        elif document_type == DocumentType.PDF:
            return await self._process_pdf(file_path)
        elif document_type == DocumentType.TEXT:
            return await self._process_text(file_path)
        else:
            raise ValueError(f"Unsupported document type: {document_type}")
    
    async def _process_html(self, file_path: Path) -> Dict[str, Any]:
        """Process HTML document"""
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
        
        # Parse HTML and clean it
        soup = BeautifulSoup(content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get clean HTML content
        clean_html = str(soup)
        
        # Extract text for search indexing
        text_content = soup.get_text(separator=' ', strip=True)
        
        return {
            "content": clean_html,
            "text_content": text_content,
            "word_count": len(text_content.split()),
            "metadata": {
                "title": soup.title.string if soup.title else None,
                "meta_description": soup.find("meta", attrs={"name": "description"}),
            }
        }
    
    async def _process_markdown(self, file_path: Path) -> Dict[str, Any]:
        """Process Markdown document"""
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            markdown_content = await f.read()
        
        # Convert Markdown to HTML
        md = markdown.Markdown(extensions=['extra', 'codehilite', 'toc'])
        html_content = md.convert(markdown_content)
        
        # Extract metadata if present
        metadata = getattr(md, 'Meta', {})
        
        # Extract plain text for indexing
        soup = BeautifulSoup(html_content, 'html.parser')
        text_content = soup.get_text(separator=' ', strip=True)
        
        return {
            "content": html_content,
            "text_content": text_content,
            "word_count": len(text_content.split()),
            "metadata": metadata,
            "original_markdown": markdown_content
        }
    
    async def _process_pdf(self, file_path: Path) -> Dict[str, Any]:
        """Process PDF document"""
        # Run PDF processing in thread pool to avoid blocking
        return await asyncio.get_event_loop().run_in_executor(
            None, self._extract_pdf_content, file_path
        )
    
    def _extract_pdf_content(self, file_path: Path) -> Dict[str, Any]:
        """Extract content from PDF file"""
        pages_content = []
        full_text = ""
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text() or ""
                    
                    # Extract page-level information
                    page_info = {
                        "page_number": page_num,
                        "text": text,
                        "bbox": page.bbox,
                        "width": page.width,
                        "height": page.height
                    }
                    
                    pages_content.append(page_info)
                    full_text += f"\\n\\n--- Page {page_num} ---\\n\\n{text}"
        
        except Exception as e:
            # Fallback for corrupted PDFs
            return {
                "content": None,
                "text_content": f"Error processing PDF: {str(e)}",
                "word_count": 0,
                "pages": [],
                "metadata": {"error": str(e)}
            }
        
        return {
            "content": None,  # PDF content is not stored as HTML
            "text_content": full_text,
            "word_count": len(full_text.split()),
            "pages": pages_content,
            "metadata": {
                "total_pages": len(pages_content),
                "file_path": str(file_path)
            }
        }
    
    async def _process_text(self, file_path: Path) -> Dict[str, Any]:
        """Process plain text document"""
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
        
        # Convert text to HTML with preserved formatting
        html_content = f"<pre>{content}</pre>"
        
        return {
            "content": html_content,
            "text_content": content,
            "word_count": len(content.split()),
            "metadata": {
                "encoding": "utf-8",
                "line_count": len(content.splitlines())
            }
        }