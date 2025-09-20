from sqlalchemy.orm import Session
from backend.database.models import Participant
import os
import shutil
from typing import Optional, List
import uuid

class AvatarService:
    def __init__(self, db: Session):
        self.db = db
        # Define project root and construct absolute path for avatar_dir
        # Assumes avatar_service.py is in backend/services/
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.avatar_dir = os.path.join(project_root, "frontend", "static", "avatars")
        
        # Ensure avatar directory exists
        os.makedirs(self.avatar_dir, exist_ok=True)
    
    def get_available_avatars(self) -> List[str]:
        """Get a list of all available avatar files"""
        if not os.path.exists(self.avatar_dir):
            return []
        
        avatars = []
        for file in os.listdir(self.avatar_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                avatars.append(file)
        
        return avatars
    
    def assign_avatar_to_participant(self, participant_id: int, avatar_filename: str) -> Optional[Participant]:
        """Assign an avatar to a participant"""
        participant = self.db.query(Participant).filter(Participant.id == participant_id).first()
        if not participant:
            return None
        
        avatar_file_path = os.path.join(self.avatar_dir, avatar_filename)
        if not os.path.exists(avatar_file_path):
            return None
        
        # Store path that works with FastAPI static file serving (/static mount)
        participant.avatar_path = f"/static/avatars/{avatar_filename}"
        self.db.commit()
        self.db.refresh(participant)
        
        return participant
    
    def upload_avatar(self, file_content: bytes, filename: str) -> str:
        """Upload a new avatar file"""
        # Generate a unique filename to avoid conflicts
        file_ext = os.path.splitext(filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        
        # Save the file
        avatar_path = os.path.join(self.avatar_dir, unique_filename)
        with open(avatar_path, "wb") as f:
            f.write(file_content)
        
        return unique_filename
