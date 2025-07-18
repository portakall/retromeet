import os
import sys
import shutil
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the database components
from backend.database.database import engine, SessionLocal
from backend.database.models import Base, Participant, Response

def init_database():
    """Initialize the database by creating all tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")

def create_directories():
    """Create necessary directories for the application"""
    directories = [
        "frontend/static/avatars",
        "frontend/static/videos",
        "frontend/static/audio"
    ]
    
    print("Creating directories...")
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")

def add_sample_avatars():
    """Add sample avatars to the avatars directory"""
    # This is a placeholder. In a real implementation, you would copy actual avatar files.
    # For now, we'll just create placeholder files.
    avatar_dir = "frontend/static/avatars"
    
    print("Adding sample avatars...")
    
    # Create sample avatar files (these would normally be image files)
    sample_avatars = [
        "avatar1.png",
        "avatar2.png",
        "avatar3.png"
    ]
    
    for avatar in sample_avatars:
        avatar_path = os.path.join(avatar_dir, avatar)
        with open(avatar_path, "w") as f:
            f.write("This is a placeholder for an avatar image file.")
        print(f"Created sample avatar: {avatar}")

def add_sample_participants():
    """Add sample participants to the database"""
    db = SessionLocal()
    
    try:
        print("Adding sample participants...")
        
        # Create sample participants
        participants = [
            Participant(name="John Doe", avatar_path="/static/avatars/avatar1.png"),
            Participant(name="Jane Smith", avatar_path="/static/avatars/avatar2.png"),
            Participant(name="Bob Johnson", avatar_path="/static/avatars/avatar3.png"),
            Participant(name="Alice Brown", avatar_path="/static/avatars/avatar4.png"),
            Participant(name="Charlie Davis", avatar_path="/static/avatars/avatar5.png")
        ]
        
        # Add participants to the database
        for participant in participants:
            db.add(participant)
        
        db.commit()
        print("Sample participants added successfully.")
    
    except Exception as e:
        db.rollback()
        print(f"Error adding sample participants: {e}")
    
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
    create_directories()
    add_sample_avatars()
    add_sample_participants()
    print("Initialization complete!")
