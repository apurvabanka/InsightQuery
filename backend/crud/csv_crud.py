from sqlalchemy.orm import Session
from models.csv_model import CSVSession, CSVFile
from typing import List, Optional
import os

class CSVSessionCRUD:
    @staticmethod
    def create_session(db: Session, session_id: str) -> CSVSession:
        db_session = CSVSession(session_id=session_id)
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        return db_session
    
    @staticmethod
    def get_session_by_id(db: Session, session_id: str) -> Optional[CSVSession]:
        return db.query(CSVSession).filter(CSVSession.session_id == session_id).first()
    
    @staticmethod
    def get_all_sessions(db: Session) -> List[CSVSession]:
        return db.query(CSVSession).all()
    
    @staticmethod
    def delete_session(db: Session, session_id: str) -> bool:
        session = db.query(CSVSession).filter(CSVSession.session_id == session_id).first()
        if session:
            db.delete(session)
            db.commit()
            return True
        return False

class CSVFileCRUD:
    @staticmethod
    def create_csv_file(
        db: Session, 
        session_id: str, 
        filename: str, 
        original_filename: str, 
        file_size: int, 
        content_type: str, 
        file_path: str
    ) -> CSVFile:
        csv_file = CSVFile(
            session_id=session_id,
            filename=filename,
            original_filename=original_filename,
            file_size=file_size,
            content_type=content_type,
            file_path=file_path
        )
        db.add(csv_file)
        db.commit()
        db.refresh(csv_file)
        return csv_file
    
    @staticmethod
    def get_files_by_session(db: Session, session_id: str) -> List[CSVFile]:
        return db.query(CSVFile).filter(CSVFile.session_id == session_id).all()
    
    @staticmethod
    def get_file_by_id(db: Session, file_id: str) -> Optional[CSVFile]:
        return db.query(CSVFile).filter(CSVFile.id == file_id).first()
    
    @staticmethod
    def delete_file(db: Session, file_id: str) -> bool:
        csv_file = db.query(CSVFile).filter(CSVFile.id == file_id).first()
        if csv_file:
            # Delete the physical file
            if os.path.exists(csv_file.file_path):
                os.remove(csv_file.file_path)
            
            db.delete(csv_file)
            db.commit()
            return True
        return False 