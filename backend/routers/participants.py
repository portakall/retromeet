from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from backend.database.database import get_db
from backend.services.response_service import ResponseService
from backend.services.avatar_service import AvatarService
import io

router = APIRouter(prefix="/participants", tags=["participants"])

class ParticipantCreate(BaseModel):
    name: str
    avatar_filename: Optional[str] = None

class ParticipantResponse(BaseModel):
    id: int
    name: str
    avatar_path: Optional[str] = None

class AvatarResponse(BaseModel):
    filename: str

@router.get("/", response_model=List[ParticipantResponse])
def get_participants(db: Session = Depends(get_db)):
    """Get all participants in the system"""
    from backend.database.models import Participant
    participants = db.query(Participant).all()
    return [
        ParticipantResponse(
            id=p.id,
            name=p.name,
            avatar_path=p.avatar_path
        )
        for p in participants
    ]

@router.post("/", response_model=ParticipantResponse)
def create_participant(participant: ParticipantCreate, db: Session = Depends(get_db)):
    """Create a new participant (not associated with any project yet)"""
    from backend.database.models import Participant
    
    avatar_path = None
    if participant.avatar_filename:
        avatar_path = f"/static/avatars/{participant.avatar_filename}"
    
    db_participant = Participant(
        name=participant.name,
        avatar_path=avatar_path
    )
    db.add(db_participant)
    db.commit()
    db.refresh(db_participant)
    
    return ParticipantResponse(
        id=db_participant.id,
        name=db_participant.name,
        avatar_path=db_participant.avatar_path
    )

@router.get("/avatars", response_model=List[str])
def get_avatars(db: Session = Depends(get_db)):
    """Get list of available avatar filenames"""
    avatar_service = AvatarService(db)
    return avatar_service.get_available_avatars()

@router.post("/avatars", response_model=AvatarResponse)
def upload_avatar(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a new avatar image"""
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    avatar_service = AvatarService(db)
    filename = avatar_service.upload_avatar(file.file.read(), file.filename)
    
    return AvatarResponse(filename=filename)

@router.put("/{participant_id}/avatar", response_model=ParticipantResponse)
def assign_avatar(participant_id: int, avatar: AvatarResponse, db: Session = Depends(get_db)):
    avatar_service = AvatarService(db)
    participant = avatar_service.assign_avatar_to_participant(participant_id, avatar.filename)
    
    if not participant:
        raise HTTPException(status_code=404, detail="Participant or avatar not found")
    
    return participant

@router.get("/{participant_id}", response_model=ParticipantResponse)
def get_participant(participant_id: int, db: Session = Depends(get_db)):
    """Get a specific participant"""
    from backend.database.models import Participant
    
    participant = db.query(Participant).filter(Participant.id == participant_id).first()
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    
    return ParticipantResponse(
        id=participant.id,
        name=participant.name,
        avatar_path=participant.avatar_path
    )

@router.put("/{participant_id}", response_model=ParticipantResponse)
def update_participant(participant_id: int, participant_data: ParticipantCreate, db: Session = Depends(get_db)):
    """Update a participant"""
    from backend.database.models import Participant
    
    participant = db.query(Participant).filter(Participant.id == participant_id).first()
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    
    participant.name = participant_data.name
    if participant_data.avatar_filename:
        participant.avatar_path = f"/static/avatars/{participant_data.avatar_filename}"
    
    db.commit()
    db.refresh(participant)
    
    return ParticipantResponse(
        id=participant.id,
        name=participant.name,
        avatar_path=participant.avatar_path
    )

@router.delete("/{participant_id}")
def delete_participant(participant_id: int, db: Session = Depends(get_db)):
    """Delete a participant (this will remove them from all projects)"""
    from backend.database.models import Participant, ProjectParticipant
    
    participant = db.query(Participant).filter(Participant.id == participant_id).first()
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    
    # Remove from all projects first
    db.query(ProjectParticipant).filter(ProjectParticipant.participant_id == participant_id).delete()
    
    # Delete the participant
    db.delete(participant)
    db.commit()
    
    return {"message": "Participant deleted successfully"}
