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
        """Process HTML document with graceful handling of malformed HTML"""
        try:
            # Try different encodings to handle various file formats
            content = None
            for encoding in ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']:
                try:
                    async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
                        content = await f.read()
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue
            
            if content is None:
                # Fallback: read as binary and decode with error handling
                async with aiofiles.open(file_path, 'rb') as f:
                    raw_content = await f.read()
                content = raw_content.decode('utf-8', errors='replace')
            
            # Use lxml parser if available for better malformed HTML handling, fallback to html.parser
            try:
                soup = BeautifulSoup(content, 'lxml')
            except:
                soup = BeautifulSoup(content, 'html.parser')
            
            # Remove script and style elements safely
            try:
                for script in soup(["script", "style"]):
                    script.decompose()
            except Exception:
                # If decompose fails, try extract
                try:
                    for script in soup(["script", "style"]):
                        script.extract()
                except Exception:
                    # If all else fails, continue without removing scripts/styles
                    pass
            
            # Get clean HTML content with error handling
            try:
                clean_html = str(soup)
            except Exception:
                # Fallback to original content if soup conversion fails
                clean_html = content
            
            # Extract text for search indexing with error handling
            try:
                text_content = soup.get_text(separator=' ', strip=True)
            except Exception:
                # Fallback: use regex to strip HTML tags
                import re
                text_content = re.sub(r'<[^>]+>', ' ', content)
                text_content = ' '.join(text_content.split())  # Normalize whitespace
            
            # Safe metadata extraction
            metadata = {}
            try:
                if soup.title and soup.title.string:
                    metadata["title"] = soup.title.string.strip()
            except Exception:
                pass
            
            try:
                meta_desc = soup.find("meta", attrs={"name": "description"})
                if meta_desc and meta_desc.get("content"):
                    metadata["meta_description"] = meta_desc.get("content").strip()
            except Exception:
                pass
            
            return {
                "content": clean_html,
                "text_content": text_content,
                "word_count": len(text_content.split()) if text_content else 0,
                "metadata": metadata
            }
            
        except Exception as e:
            # Ultimate fallback: return minimal processing
            try:
                async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    raw_content = await f.read()
                
                # Basic text extraction without HTML parsing
                import re
                text_content = re.sub(r'<[^>]+>', ' ', raw_content)
                text_content = ' '.join(text_content.split())
                
                return {
                    "content": raw_content,  # Store original content
                    "text_content": text_content,
                    "word_count": len(text_content.split()) if text_content else 0,
                    "metadata": {"processing_error": str(e), "fallback_processing": True}
                }
            except Exception as fallback_error:
                # Absolute fallback
                return {
                    "content": f"<p>Error processing HTML file: {str(e)}</p>",
                    "text_content": f"Error processing HTML file: {str(e)}",
                    "word_count": 0,
                    "metadata": {"processing_error": str(e), "fallback_error": str(fallback_error)}
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