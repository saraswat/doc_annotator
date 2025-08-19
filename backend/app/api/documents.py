from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, distinct
from typing import List, Optional, Dict, Any
import os
import hashlib
import aiofiles
import zipfile
import tarfile
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from app.core.database import get_async_session
from app.core.security import get_current_user
from app.models import User, Document, DocumentType
from app.schemas import (
    DocumentCreate, 
    DocumentUpdate, 
    DocumentResponse, 
    DocumentListResponse,
    UserResponse
)
from app.services.document_processor import DocumentProcessor
from app.core.config import settings

router = APIRouter()

@router.post("/upload", response_model=DocumentResponse)
@router.post("/upload/", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    is_public: bool = Form(False),
    allow_comments: bool = Form(True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Upload and process a document"""
    
    # Validate file type
    allowed_extensions = {'.html', '.htm', '.md', '.markdown', '.pdf', '.txt'}
    file_extension = Path(file.filename).suffix.lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Determine document type
    if file_extension in {'.html', '.htm'}:
        document_type = DocumentType.HTML
    elif file_extension in {'.md', '.markdown'}:
        document_type = DocumentType.MARKDOWN
    elif file_extension == '.pdf':
        document_type = DocumentType.PDF
    else:
        document_type = DocumentType.TEXT
    
    # Create uploads directory if it doesn't exist
    upload_dir = Path(settings.UPLOAD_PATH)
    upload_dir.mkdir(exist_ok=True)
    
    # Generate unique filename
    file_hash = hashlib.md5(file.filename.encode()).hexdigest()[:8]
    filename = f"{file_hash}_{file.filename}"
    file_path = upload_dir / filename
    
    # Save file
    content = await file.read()
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    
    # Process document content with error handling
    processor = DocumentProcessor()
    try:
        processed_content = await processor.process_document(file_path, document_type)
    except Exception as process_error:
        # Fallback processing for malformed documents
        print(f"Warning: Failed to process document {filename}: {str(process_error)}")
        
        # Create fallback content
        if document_type == DocumentType.HTML:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    raw_content = f.read()
                processed_content = {
                    "content": raw_content,
                    "text_content": raw_content[:1000] + "..." if len(raw_content) > 1000 else raw_content,
                    "word_count": len(raw_content.split()),
                    "metadata": {"processing_error": str(process_error), "fallback": True}
                }
            except Exception:
                processed_content = {
                    "content": f"<p>Document could not be processed: {str(process_error)}</p>",
                    "text_content": f"Document could not be processed: {str(process_error)}",
                    "word_count": 0,
                    "metadata": {"processing_error": str(process_error), "fallback": True}
                }
        else:
            processed_content = {
                "content": f"Document processing failed: {str(process_error)}",
                "text_content": f"Document processing failed: {str(process_error)}",
                "word_count": 0,
                "metadata": {"processing_error": str(process_error), "fallback": True}
            }
    
    # Create document record
    document = Document(
        title=title,
        filename=filename,
        file_path=str(file_path),
        file_size=len(content),
        document_type=document_type,
        content=processed_content.get('content'),
        content_hash=hashlib.md5(content).hexdigest(),
        description=description,
        tags=tags,
        owner_id=current_user.id,
        is_public=is_public,
        allow_comments=allow_comments,
        processing_status="completed"
    )
    
    db.add(document)
    await db.commit()
    await db.refresh(document)
    
    return DocumentResponse.from_orm(document)

@router.post("/upload-single", response_model=DocumentResponse)
@router.post("/upload-single/", response_model=DocumentResponse)
async def upload_single_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    document_key: str = Form(...),
    document_date: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Upload a single document with key and date"""
    
    # Validate file type
    allowed_extensions = {'.html', '.htm', '.md', '.markdown', '.pdf', '.txt'}
    file_extension = Path(file.filename or '').suffix.lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Determine document type
    if file_extension in {'.html', '.htm'}:
        document_type = DocumentType.HTML
    elif file_extension in {'.md', '.markdown'}:
        document_type = DocumentType.MARKDOWN
    elif file_extension == '.pdf':
        document_type = DocumentType.PDF
    else:
        document_type = DocumentType.TEXT
    
    # Create directory structure for uploads
    upload_base = Path(settings.UPLOAD_PATH)
    key_dir = upload_base / document_key
    date_dir = key_dir / document_date
    date_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename with timestamp
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    file_stem = Path(file.filename or 'document').stem
    unique_filename = f"{timestamp}_{file_stem}{file_extension}"
    final_file_path = date_dir / unique_filename
    
    # Save file
    content = await file.read()
    async with aiofiles.open(final_file_path, 'wb') as f:
        await f.write(content)
    
    # Process document content with error handling
    processor = DocumentProcessor()
    try:
        processed_content = await processor.process_document(final_file_path, document_type)
    except Exception as process_error:
        # Fallback processing for malformed documents
        print(f"Warning: Failed to process document {file.filename}: {str(process_error)}")
        
        # Create fallback content
        if document_type == DocumentType.HTML:
            try:
                with open(final_file_path, 'r', encoding='utf-8', errors='replace') as f:
                    raw_content = f.read()
                processed_content = {
                    "content": raw_content,
                    "text_content": raw_content[:1000] + "..." if len(raw_content) > 1000 else raw_content,
                    "word_count": len(raw_content.split()),
                    "metadata": {"processing_error": str(process_error), "fallback": True}
                }
            except Exception:
                processed_content = {
                    "content": f"<p>Document could not be processed: {str(process_error)}</p>",
                    "text_content": f"Document could not be processed: {str(process_error)}",
                    "word_count": 0,
                    "metadata": {"processing_error": str(process_error), "fallback": True}
                }
        else:
            processed_content = {
                "content": f"Document processing failed: {str(process_error)}",
                "text_content": f"Document processing failed: {str(process_error)}",
                "word_count": 0,
                "metadata": {"processing_error": str(process_error), "fallback": True}
            }
    
    # Create document record
    document = Document(
        title=title,
        filename=unique_filename,
        file_path=str(final_file_path),
        file_size=len(content),
        document_type=document_type,
        content=processed_content.get('content'),
        content_hash=hashlib.md5(content).hexdigest(),
        description=description,
        document_key=document_key,
        document_date=document_date,
        owner_id=current_user.id,
        is_public=False,
        allow_comments=True,
        processing_status="completed"
    )
    
    db.add(document)
    await db.commit()
    await db.refresh(document)
    
    return DocumentResponse.from_orm(document)

@router.post("/bulk-upload")
@router.post("/bulk-upload/")
async def bulk_upload_documents(
    file: UploadFile = File(...),
    make_public: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Bulk upload documents from ZIP or TAR archive"""
    
    # Validate file type
    file_extension = Path(file.filename or '').suffix.lower()
    if file_extension not in {'.zip', '.tar', '.gz', '.tgz'}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only ZIP and TAR files are supported for bulk upload"
        )
    
    # Create temporary directory for extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        archive_path = temp_path / file.filename
        
        # Save uploaded file
        content = await file.read()
        with open(archive_path, 'wb') as f:
            f.write(content)
        
        # Extract archive
        extract_path = temp_path / 'extracted'
        extract_path.mkdir()
        
        try:
            if file_extension == '.zip':
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
            elif file_extension in {'.tar', '.gz', '.tgz'}:
                mode = 'r:gz' if file_extension in {'.gz', '.tgz'} else 'r'
                with tarfile.open(archive_path, mode) as tar_ref:
                    tar_ref.extractall(extract_path)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to extract archive: {str(e)}"
            )
        
        # Process extracted files
        results = []
        errors = []
        
        # Walk through the directory structure
        for root, dirs, files in os.walk(extract_path):
            root_path = Path(root)
            
            # Skip if we're in the root extraction directory
            if root_path == extract_path:
                continue
            
            # Calculate relative path from extraction root
            rel_path = root_path.relative_to(extract_path)
            path_parts = rel_path.parts
            
            # Expect structure: key/date/files
            if len(path_parts) >= 2:
                document_key = path_parts[0]
                document_date = path_parts[1]
                
                # Process files in this directory
                for filename in files:
                    file_path = root_path / filename
                    
                    # Skip hidden files and directories
                    if filename.startswith('.'):
                        continue
                    
                    # Check file extension
                    file_ext = Path(filename).suffix.lower()
                    allowed_extensions = {'.html', '.htm', '.md', '.markdown', '.pdf', '.txt'}
                    
                    if file_ext not in allowed_extensions:
                        results.append({
                            'file': str(rel_path / filename),
                            'status': 'error',
                            'message': f'Unsupported file type: {file_ext}',
                            'key': document_key,
                            'date': document_date
                        })
                        continue
                    
                    try:
                        # Determine document type
                        if file_ext in {'.html', '.htm'}:
                            document_type = DocumentType.HTML
                        elif file_ext in {'.md', '.markdown'}:
                            document_type = DocumentType.MARKDOWN
                        elif file_ext == '.pdf':
                            document_type = DocumentType.PDF
                        else:
                            document_type = DocumentType.TEXT
                        
                        # Read file content
                        with open(file_path, 'rb') as f:
                            file_content = f.read()
                        
                        # Process document content
                        processor = DocumentProcessor()
                        
                        # Save file to uploads directory
                        upload_dir = Path(settings.UPLOAD_PATH)
                        upload_dir.mkdir(exist_ok=True)
                        
                        # Generate unique filename
                        file_hash = hashlib.md5(filename.encode()).hexdigest()[:8]
                        unique_filename = f"{file_hash}_{filename}"
                        final_file_path = upload_dir / unique_filename
                        
                        with open(final_file_path, 'wb') as f:
                            f.write(file_content)
                        
                        # Process content with error handling
                        try:
                            processed_content = await processor.process_document(final_file_path, document_type)
                        except Exception as process_error:
                            # Fallback processing for malformed documents
                            print(f"Warning: Failed to process document {filename}: {str(process_error)}")
                            
                            # Create fallback content based on document type
                            if document_type == DocumentType.HTML:
                                # Read raw content and provide minimal HTML processing
                                try:
                                    with open(final_file_path, 'r', encoding='utf-8', errors='replace') as f:
                                        raw_content = f.read()
                                    processed_content = {
                                        "content": raw_content,
                                        "text_content": raw_content[:1000] + "..." if len(raw_content) > 1000 else raw_content,
                                        "word_count": len(raw_content.split()),
                                        "metadata": {"processing_error": str(process_error), "fallback": True}
                                    }
                                except Exception:
                                    processed_content = {
                                        "content": f"<p>Document could not be processed: {str(process_error)}</p>",
                                        "text_content": f"Document could not be processed: {str(process_error)}",
                                        "word_count": 0,
                                        "metadata": {"processing_error": str(process_error), "fallback": True}
                                    }
                            else:
                                # Generic fallback for other document types
                                processed_content = {
                                    "content": f"Document processing failed: {str(process_error)}",
                                    "text_content": f"Document processing failed: {str(process_error)}",
                                    "word_count": 0,
                                    "metadata": {"processing_error": str(process_error), "fallback": True}
                                }
                        
                        # Generate title from filename
                        title = Path(filename).stem.replace('_', ' ').replace('-', ' ').title()
                        
                        # Create document record
                        document = Document(
                            title=title,
                            filename=unique_filename,
                            file_path=str(final_file_path),
                            file_size=len(file_content),
                            document_type=document_type,
                            content=processed_content.get('content'),
                            content_hash=hashlib.md5(file_content).hexdigest(),
                            description=f"Auto-uploaded from bulk import: {document_key}/{document_date}",
                            document_key=document_key,
                            document_date=document_date,
                            owner_id=current_user.id,
                            is_public=make_public,
                            allow_comments=True,
                            processing_status="completed"
                        )
                        
                        db.add(document)
                        await db.commit()
                        await db.refresh(document)
                        
                        results.append({
                            'file': str(rel_path / filename),
                            'status': 'success',
                            'message': f'Successfully uploaded as "{title}"',
                            'key': document_key,
                            'date': document_date,
                            'document_id': document.id
                        })
                        
                    except Exception as e:
                        # Clean up file if it was created
                        if 'final_file_path' in locals() and final_file_path.exists():
                            final_file_path.unlink()
                        
                        results.append({
                            'file': str(rel_path / filename),
                            'status': 'error',
                            'message': f'Failed to process: {str(e)}',
                            'key': document_key,
                            'date': document_date
                        })
                        errors.append(str(e))
            else:
                # Files not in the expected structure
                for filename in files:
                    if not filename.startswith('.'):
                        results.append({
                            'file': str(rel_path / filename),
                            'status': 'error',
                            'message': 'File not in expected key/date/file structure',
                            'key': None,
                            'date': None
                        })
    
    return {
        'message': f'Bulk upload completed. Processed {len(results)} files.',
        'results': results,
        'errors': errors[:10],  # Limit error messages
        'total_files': len(results),
        'successful_uploads': len([r for r in results if r['status'] == 'success']),
        'failed_uploads': len([r for r in results if r['status'] == 'error'])
    }

@router.post("/bulk-upload-directory")
@router.post("/bulk-upload-directory/")
async def bulk_upload_directory(
    files: List[UploadFile] = File(...),
    paths: List[str] = Form(...),
    make_public: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Bulk upload documents from directory selection"""
    
    if len(files) != len(paths):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mismatch between files and paths"
        )
    
    results = []
    errors = []
    
    # Process each file with its relative path
    for file, relative_path in zip(files, paths):
        try:
            # Parse the relative path to extract key and date
            path_parts = Path(relative_path).parts
            
            # Skip files not in the expected structure
            if len(path_parts) < 3:  # Should be at least key/date/filename
                results.append({
                    'file': relative_path,
                    'status': 'error',
                    'message': 'File not in expected key/date/file structure',
                    'key': None,
                    'date': None
                })
                continue
            
            document_key = path_parts[0]
            document_date = path_parts[1]
            filename = path_parts[-1]
            
            # Skip hidden files
            if filename.startswith('.'):
                continue
            
            # Check file extension
            file_ext = Path(filename).suffix.lower()
            allowed_extensions = {'.html', '.htm', '.md', '.markdown', '.pdf', '.txt'}
            
            if file_ext not in allowed_extensions:
                results.append({
                    'file': relative_path,
                    'status': 'error',
                    'message': f'Unsupported file type: {file_ext}',
                    'key': document_key,
                    'date': document_date
                })
                continue
            
            # Determine document type
            if file_ext in {'.html', '.htm'}:
                document_type = DocumentType.HTML
            elif file_ext in {'.md', '.markdown'}:
                document_type = DocumentType.MARKDOWN
            elif file_ext == '.pdf':
                document_type = DocumentType.PDF
            else:  # .txt
                document_type = DocumentType.TEXT
            
            # Generate unique filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            file_stem = Path(filename).stem
            unique_filename = f"{timestamp}_{file_stem}{file_ext}"
            
            # Create document directory
            upload_base = Path(settings.UPLOAD_PATH)
            key_dir = upload_base / document_key
            date_dir = key_dir / document_date
            date_dir.mkdir(parents=True, exist_ok=True)
            
            # Save file
            final_file_path = date_dir / unique_filename
            content = await file.read()
            with open(final_file_path, 'wb') as f:
                f.write(content)
            
            # Generate title from filename
            title = file_stem.replace('_', ' ').replace('-', ' ').title()
            
            # Store relative path from uploads directory
            relative_storage_path = final_file_path.relative_to(upload_base)
            
            # Create document record
            document_data = DocumentCreate(
                title=title,
                content="",  # Will be processed later
                document_type=document_type,
                file_path=str(relative_storage_path),
                document_key=document_key,
                document_date=document_date,
                is_public=make_public
            )
            
            # Save to database
            document = Document(**document_data.dict(), user_id=current_user.id)
            db.add(document)
            await db.commit()
            await db.refresh(document)
            
            results.append({
                'file': relative_path,
                'status': 'success',
                'message': f'Successfully uploaded as "{title}"',
                'key': document_key,
                'date': document_date,
                'document_id': document.id
            })
            
        except Exception as e:
            results.append({
                'file': relative_path,
                'status': 'error',
                'message': f'Failed to process: {str(e)}',
                'key': document_key if 'document_key' in locals() else None,
                'date': document_date if 'document_date' in locals() else None
            })
            errors.append(str(e))
    
    return {
        'message': f'Directory upload completed. Processed {len(results)} files.',
        'results': results,
        'errors': errors[:10],
        'total_files': len(results),
        'successful_uploads': len([r for r in results if r['status'] == 'success']),
        'failed_uploads': len([r for r in results if r['status'] == 'error'])
    }

@router.get("/", response_model=List[DocumentListResponse])
@router.get("", response_model=List[DocumentListResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    document_type: Optional[DocumentType] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """List documents accessible to the current user"""
    
    # Build query
    query = select(Document).where(
        or_(
            Document.owner_id == current_user.id,
            Document.is_public == True
        )
    )
    
    # Add filters
    if search:
        query = query.where(
            or_(
                Document.title.ilike(f"%{search}%"),
                Document.description.ilike(f"%{search}%")
            )
        )
    
    if document_type:
        query = query.where(Document.document_type == document_type)
    
    # Add pagination
    query = query.offset(skip).limit(limit).order_by(Document.created_at.desc())
    
    result = await db.execute(query)
    documents = result.scalars().all()
    
    return [DocumentListResponse.from_orm(doc) for doc in documents]

@router.get("/keys", response_model=List[str])
@router.get("/keys/", response_model=List[str])
async def get_document_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get all unique document keys for dropdown selection"""
    
    query = select(distinct(Document.document_key)).where(
        and_(
            Document.document_key.is_not(None),
            Document.document_key != "",
            or_(
                Document.owner_id == current_user.id,
                Document.is_public == True
            )
        )
    ).order_by(Document.document_key)
    
    result = await db.execute(query)
    keys = result.scalars().all()
    
    return [key for key in keys if key]

@router.get("/dates", response_model=List[str])
@router.get("/dates/", response_model=List[str])
async def get_document_dates(
    key: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get all unique document dates for a specific key or all dates"""
    
    query = select(distinct(Document.document_date)).where(
        and_(
            Document.document_date.is_not(None),
            Document.document_date != "",
            or_(
                Document.owner_id == current_user.id,
                Document.is_public == True
            )
        )
    )
    
    # Filter by key if provided
    if key:
        query = query.where(Document.document_key == key)
    
    query = query.order_by(Document.document_date.desc())
    
    result = await db.execute(query)
    dates = result.scalars().all()
    
    return [date for date in dates if date]

@router.get("/by-key-date", response_model=List[DocumentListResponse])
@router.get("/by-key-date/", response_model=List[DocumentListResponse])
async def get_documents_by_key_date(
    key: str,
    date: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get documents filtered by specific key and date combination"""
    
    query = select(Document).where(
        and_(
            Document.document_key == key,
            Document.document_date == date,
            or_(
                Document.owner_id == current_user.id,
                Document.is_public == True
            )
        )
    ).order_by(Document.created_at.desc())
    
    result = await db.execute(query)
    documents = result.scalars().all()
    
    return [DocumentListResponse.from_orm(doc) for doc in documents]

@router.get("/{document_id}", response_model=DocumentResponse)
@router.get("/{document_id}/", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get a specific document"""
    
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check access permissions
    if document.owner_id != current_user.id and not document.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this document"
        )
    
    return DocumentResponse.from_orm(document)

@router.patch("/{document_id}", response_model=DocumentResponse)
@router.patch("/{document_id}/", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    update_data: DocumentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Update a document"""
    
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check permissions
    if document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this document"
        )
    
    # Update fields
    update_data_dict = update_data.dict(exclude_unset=True)
    for field, value in update_data_dict.items():
        setattr(document, field, value)
    
    await db.commit()
    await db.refresh(document)
    
    return DocumentResponse.from_orm(document)

@router.delete("/{document_id}")
@router.delete("/{document_id}/")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Delete a document"""
    
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check permissions
    if document.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this document"
        )
    
    # Delete file from disk
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    # Delete from database
    await db.delete(document)
    await db.commit()
    
    return {"status": "deleted"}

@router.get("/{document_id}/content")
@router.get("/{document_id}/content/")
async def get_document_content(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get document content for viewing"""
    
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check access permissions
    if document.owner_id != current_user.id and not document.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this document"
        )
    
    # Return content based on document type
    if document.document_type == DocumentType.PDF:
        # For PDF, return file path for PDF.js to load
        return {
            "type": "pdf",
            "url": f"/uploads/{document.filename}",
            "title": document.title
        }
    else:
        # For HTML/Markdown/Text, return processed content
        return {
            "type": document.document_type.value,
            "content": document.content,
            "title": document.title
        }

@router.get("/{document_id}/pdf")
@router.get("/{document_id}/pdf/")
async def serve_pdf_file(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Serve PDF file directly"""
    
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check access permissions
    if document.owner_id != current_user.id and not document.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this document"
        )
    
    # Ensure it's a PDF
    if document.document_type != DocumentType.PDF:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document is not a PDF"
        )
    
    # Check if file exists
    if not os.path.exists(document.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF file not found on disk"
        )
    
    return FileResponse(
        path=document.file_path,
        media_type='application/pdf',
        filename=document.filename
    )

@router.get("/{document_id}/pdf-test")
@router.get("/{document_id}/pdf-test/")
async def serve_pdf_file_test(
    document_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """TEST: Serve PDF file without authentication"""
    
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document or document.document_type != DocumentType.PDF:
        raise HTTPException(status_code=404, detail="PDF document not found")
    
    if not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="PDF file not found on disk")
    
    return FileResponse(
        path=document.file_path,
        media_type='application/pdf',
        filename=document.filename
    )