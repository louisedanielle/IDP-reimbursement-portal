from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import os
import shutil
from datetime import datetime

from ..config import settings
from ..database import get_db
from ..models import Document
from ..schemas import DocumentUploadResponse
from ..workers.processor import process_document

router = APIRouter()

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a receipt/document for processing"""
    
    # Validate file type
    allowed_types = ['image/jpeg', 'image/png', 'image/tiff', 'application/pdf']
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file.content_type} not allowed. Allowed: {allowed_types}"
        )
    
    # Validate file size (max 20MB)
    file_content = await file.read()
    if len(file_content) > 20 * 1024 * 1024:  # 20MB
        raise HTTPException(
            status_code=400,
            detail="File size exceeds 20MB limit"
        )
    
    # Save file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)
    
    with open(filepath, "wb") as f:
        f.write(file_content)
    
    # Create document record
    document = Document(
        filename=file.filename,
        file_path=filepath,
        file_size=len(file_content),
        mime_type=file.content_type,
        status="pending"
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Start async processing
    process_document.delay(document.id)
    
    return DocumentUploadResponse(
        document_id=document.id,
        filename=file.filename,
        status="processing",
        message="Document uploaded and processing started"
    )

@router.get("/{document_id}/status")
async def get_document_status(
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """Get document processing status"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "document_id": document.id,
        "filename": document.filename,
        "status": document.status,
        "error_message": document.error_message,
        "upload_date": document.upload_date
    }

@router.get("/{document_id}/extracted")
async def get_extracted_data(
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """Get extracted data from document"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    extracted = db.query(ExtractedData).filter(
        ExtractedData.document_id == document_id
    ).first()
    
    if not extracted:
        return {
            "document_id": document_id,
            "status": "pending",
            "message": "Document is still being processed"
        }
    
    return {
        "document_id": document_id,
        "filename": document.filename,
        "raw_text": extracted.raw_text,
        "items": extracted.structured_data.get("items", []),
        "confidence_score": extracted.confidence_score,
        "is_verified": extracted.is_verified
    }

@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """Download the uploaded document"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        document.file_path,
        media_type=document.mime_type,
        filename=document.filename
    )