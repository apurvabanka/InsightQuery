from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
from datetime import datetime

from db.session import get_db
from crud.csv_crud import CSVSessionCRUD, CSVFileCRUD
from schemas.csv_schema import (
    CSVUploadResponse, 
    CSVFileResponse, 
    CSVSessionResponse,
    CreateSessionRequest,
    CreateSessionResponse
)

router = APIRouter()

# Create uploads directory if it doesn't exist
UPLOADS_DIR = "uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)

@router.post("/sessions", response_model=CreateSessionResponse)
def create_session(
    request: CreateSessionRequest,
    db: Session = Depends(get_db)
):
    """Create a new CSV session"""
    # Check if session already exists
    existing_session = CSVSessionCRUD.get_session_by_id(db, request.session_id)
    if existing_session:
        raise HTTPException(status_code=400, detail="Session already exists")
    
    # Create new session
    session = CSVSessionCRUD.create_session(db, request.session_id)
    
    return CreateSessionResponse(
        message="Session created successfully",
        session_id=session.session_id
    )

@router.post("/upload", response_model=CSVUploadResponse)
async def upload_csv(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    db: Session = Depends(get_db)
):
    """Upload a CSV file to a specific session"""
    
    # Validate file type
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    # Check if session exists
    session = CSVSessionCRUD.get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOADS_DIR, unique_filename)
    
    try:
        # Save file to disk
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Get file size
        file_size = len(content)
        
        # Create database record
        csv_file = CSVFileCRUD.create_csv_file(
            db=db,
            session_id=session_id,
            filename=unique_filename,
            original_filename=file.filename,
            file_size=file_size,
            content_type=file.content_type or "text/csv",
            file_path=file_path
        )
        
        return CSVUploadResponse(
            message="File uploaded successfully",
            session_id=session_id,
            file=CSVFileResponse(
                id=csv_file.id,
                filename=csv_file.filename,
                original_filename=csv_file.original_filename,
                file_size=csv_file.file_size,
                content_type=csv_file.content_type,
                created_at=csv_file.created_at
            )
        )
        
    except Exception as e:
        # Clean up file if database operation fails
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/sessions/{session_id}", response_model=CSVSessionResponse)
def get_session_files(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get all CSV files for a specific session"""
    session = CSVSessionCRUD.get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    csv_files = CSVFileCRUD.get_files_by_session(db, session_id)
    
    return CSVSessionResponse(
        id=session.id,
        session_id=session.session_id,
        created_at=session.created_at,
        updated_at=session.updated_at,
        csv_files=[
            CSVFileResponse(
                id=file.id,
                filename=file.filename,
                original_filename=file.original_filename,
                file_size=file.file_size,
                content_type=file.content_type,
                created_at=file.created_at
            ) for file in csv_files
        ]
    )

@router.get("/sessions", response_model=List[CSVSessionResponse])
def get_all_sessions(db: Session = Depends(get_db)):
    """Get all CSV sessions"""
    sessions = CSVSessionCRUD.get_all_sessions(db)
    
    return [
        CSVSessionResponse(
            id=session.id,
            session_id=session.session_id,
            created_at=session.created_at,
            updated_at=session.updated_at,
            csv_files=[
                CSVFileResponse(
                    id=file.id,
                    filename=file.filename,
                    original_filename=file.original_filename,
                    file_size=file.file_size,
                    content_type=file.content_type,
                    created_at=file.created_at
                ) for file in session.csv_files
            ]
        ) for session in sessions
    ]

@router.delete("/sessions/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db)):
    """Delete a session and all its CSV files"""
    success = CSVSessionCRUD.delete_session(db, session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session deleted successfully"}

@router.delete("/files/{file_id}")
def delete_file(file_id: str, db: Session = Depends(get_db)):
    """Delete a specific CSV file"""
    success = CSVFileCRUD.delete_file(db, file_id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {"message": "File deleted successfully"} 