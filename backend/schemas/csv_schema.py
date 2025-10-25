from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class CSVFileResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size: int
    content_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class CSVSessionResponse(BaseModel):
    id: str
    session_id: str
    created_at: datetime
    updated_at: Optional[datetime]
    csv_files: List[CSVFileResponse] = []
    
    class Config:
        from_attributes = True

class CSVUploadResponse(BaseModel):
    message: str
    session_id: str
    file: CSVFileResponse

class CreateSessionRequest(BaseModel):
    session_id: str

class CreateSessionResponse(BaseModel):
    message: str
    session_id: str 