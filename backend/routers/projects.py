from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from backend.database.database import get_db
from backend.database.models import Project, ProjectParticipant, Participant
import datetime

router = APIRouter(prefix="/projects", tags=["projects"])

class ProjectCreate(BaseModel):
    name: str

class ProjectResponse(BaseModel):
    id: int
    name: str
    created_at: datetime.datetime
    participants_count: Optional[int] = 0

class ProjectParticipantResponse(BaseModel):
    id: int
    name: str
    avatar_path: Optional[str] = None
    joined_at: datetime.datetime

class AddParticipantRequest(BaseModel):
    participant_id: int

@router.get("/", response_model=List[ProjectResponse])
def get_projects(db: Session = Depends(get_db)):
    """Get all projects with participant counts"""
    projects = db.query(Project).all()
    
    result = []
    for project in projects:
        participant_count = db.query(ProjectParticipant).filter(
            ProjectParticipant.project_id == project.id
        ).count()
        
        result.append(ProjectResponse(
            id=project.id,
            name=project.name,
            created_at=project.created_at,
            participants_count=participant_count
        ))
    
    return result

@router.post("/", response_model=ProjectResponse)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project"""
    db_project = Project(name=project.name)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    return ProjectResponse(
        id=db_project.id,
        name=db_project.name,
        created_at=db_project.created_at,
        participants_count=0
    )

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """Get a specific project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    participant_count = db.query(ProjectParticipant).filter(
        ProjectParticipant.project_id == project_id
    ).count()
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        created_at=project.created_at,
        participants_count=participant_count
    )

@router.get("/{project_id}/participants", response_model=List[ProjectParticipantResponse])
def get_project_participants(project_id: int, db: Session = Depends(get_db)):
    """Get all participants for a specific project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get participants through the junction table
    participants = db.query(Participant, ProjectParticipant.joined_at).join(
        ProjectParticipant, Participant.id == ProjectParticipant.participant_id
    ).filter(ProjectParticipant.project_id == project_id).all()
    
    return [
        ProjectParticipantResponse(
            id=participant.id,
            name=participant.name,
            avatar_path=participant.avatar_path,
            joined_at=joined_at
        )
        for participant, joined_at in participants
    ]

@router.post("/{project_id}/participants", response_model=dict)
def add_participant_to_project(
    project_id: int, 
    request: AddParticipantRequest, 
    db: Session = Depends(get_db)
):
    """Add an existing participant to a project"""
    # Check if project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if participant exists
    participant = db.query(Participant).filter(Participant.id == request.participant_id).first()
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    
    # Check if already associated
    existing = db.query(ProjectParticipant).filter(
        ProjectParticipant.project_id == project_id,
        ProjectParticipant.participant_id == request.participant_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=409, detail="Participant already in this project")
    
    # Create association
    association = ProjectParticipant(
        project_id=project_id,
        participant_id=request.participant_id
    )
    db.add(association)
    db.commit()
    
    return {"message": f"Participant {participant.name} added to project {project.name}"}

@router.delete("/{project_id}/participants/{participant_id}")
def remove_participant_from_project(
    project_id: int, 
    participant_id: int, 
    db: Session = Depends(get_db)
):
    """Remove a participant from a project"""
    association = db.query(ProjectParticipant).filter(
        ProjectParticipant.project_id == project_id,
        ProjectParticipant.participant_id == participant_id
    ).first()
    
    if not association:
        raise HTTPException(status_code=404, detail="Participant not found in this project")
    
    db.delete(association)
    db.commit()
    
    return {"message": "Participant removed from project"}

@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """Delete a project and all its associations"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Delete all project-participant associations
    db.query(ProjectParticipant).filter(ProjectParticipant.project_id == project_id).delete()
    
    # Delete the project
    db.delete(project)
    db.commit()
    
    return {"message": "Project deleted successfully"}
