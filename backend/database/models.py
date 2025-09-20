from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class Participant(Base):
    __tablename__ = "participants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    avatar_path = Column(String(255), nullable=True) # Stores path relative to PROJECT_ROOT
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Many-to-many relationship with projects
    project_associations = relationship("ProjectParticipant", back_populates="participant")
    responses = relationship("Response", back_populates="participant")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Many-to-many relationship with participants
    participant_associations = relationship("ProjectParticipant", back_populates="project")

class ProjectParticipant(Base):
    __tablename__ = "project_participants"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    participant_id = Column(Integer, ForeignKey("participants.id"), nullable=False)
    joined_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="participant_associations")
    participant = relationship("Participant", back_populates="project_associations")

class Response(Base):
    __tablename__ = "responses"
    
    id = Column(Integer, primary_key=True, index=True)
    participant_id = Column(Integer, ForeignKey("participants.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    question = Column(String(255), nullable=False)
    original_response = Column(Text, nullable=False)
    refined_response = Column(Text, nullable=True)
    chat_response_file_path = Column(String(500), nullable=True)  # Path to .md file with full chat response
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    participant = relationship("Participant", back_populates="responses")
    project = relationship("Project")
