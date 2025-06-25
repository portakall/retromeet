from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from backend.database.database import get_db
from backend.services.response_service import ResponseService
from backend.database.models import Response, Participant
from datetime import datetime

router = APIRouter(prefix="/responses", tags=["responses"])

class ResponseCreate(BaseModel):
    participant_name: str
    project_id: int
    question: str
    response_text: str

class ChatResponseCreate(BaseModel):
    participant_name: str
    project_id: int
    chat_content: str
    question: str = "Chat Response"

class ResponseData(BaseModel):
    id: int
    participant_id: int
    project_id: int
    question: str
    original_response: str
    refined_response: str
    chat_response_file_path: Optional[str] = None
    participant_name: str
    participant_avatar_path: Optional[str] = None # Added avatar path
    created_at: datetime

@router.post("/", response_model=ResponseData)
def create_response(response: ResponseCreate, db: Session = Depends(get_db)):
    """Create a new response for a participant in a project"""
    service = ResponseService(db)
    processed_response = service.process_response_pipeline(
        participant_name=response.participant_name,
        project_id=response.project_id,
        question=response.question,
        response_text=response.response_text
    )
    
    # Fetch participant to get avatar_path for new responses
    participant_obj = db.query(Participant).filter(Participant.id == processed_response['participant_id']).first()
    avatar_path = participant_obj.avatar_path if participant_obj else None

    # The pipeline returns a dictionary, so we access its items by key.
    return ResponseData(
        id=processed_response['response_id'],
        participant_id=processed_response['participant_id'],
        project_id=response.project_id,  # from the original request
        question=processed_response['question'],
        original_response=processed_response['original_response'],
        refined_response=processed_response['refined_response'] or "", # Use empty string as fallback
        chat_response_file_path=None, # This pipeline doesn't handle file paths
        participant_name=response.participant_name, # from the original request
        participant_avatar_path=avatar_path,
        created_at=datetime.utcnow() # Use current time for the response
    )

@router.post("/chat", response_model=ResponseData)
def create_chat_response(response: ChatResponseCreate, db: Session = Depends(get_db)):
    """Create a new chat response for a participant in a project"""
    service = ResponseService(db)
    processed_response = service.process_chat_response(
        participant_name=response.participant_name,
        project_id=response.project_id,
        chat_content=response.chat_content,
        question=response.question
    )
    
    return ResponseData(
        id=processed_response.id,
        participant_id=processed_response.participant_id,
        project_id=processed_response.project_id,
        question=processed_response.question,
        original_response=processed_response.original_response,
        refined_response=processed_response.refined_response or "",
        chat_response_file_path=processed_response.chat_response_file_path,
        participant_name=processed_response.participant.name if processed_response.participant else response.participant_name,
        participant_avatar_path=processed_response.participant.avatar_path if processed_response.participant else None,
        created_at=processed_response.created_at
    )

@router.get("/project/{project_id}", response_model=List[ResponseData])
def get_project_responses(project_id: int, db: Session = Depends(get_db)):
    """Get all responses for a specific project"""
    responses = db.query(Response).join(Participant).filter(Response.project_id == project_id).all()
    
    return [
        ResponseData(
            id=r.id,
            participant_id=r.participant_id,
            project_id=r.project_id,
            question=r.question,
            original_response=r.original_response,
            refined_response=r.refined_response or "",
            chat_response_file_path=r.chat_response_file_path,
            participant_name=r.participant.name if r.participant else f"Participant {r.participant_id}",
            participant_avatar_path=r.participant.avatar_path if r.participant else None,
            created_at=r.created_at
        )
        for r in responses
    ]

@router.get("/{response_id}", response_model=ResponseData)
def get_response(response_id: int, db: Session = Depends(get_db)):
    """Get a specific response by ID"""
    response = db.query(Response).join(Participant).filter(Response.id == response_id).first()
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    
    return ResponseData(
        id=response.id,
        participant_id=response.participant_id,
        project_id=response.project_id,
        question=response.question,
        original_response=response.original_response,
        refined_response=response.refined_response or "",
        chat_response_file_path=response.chat_response_file_path,
        participant_name=response.participant.name if response.participant else f"Participant {response.participant_id}",
        participant_avatar_path=response.participant.avatar_path if response.participant else None,
        created_at=response.created_at
    )
