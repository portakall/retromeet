#!/usr/bin/env python3
import os
import sys
import shutil
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database.database import SessionLocal, engine
from backend.database.models import Participant, Response, Base

# Load environment variables
load_dotenv()

def main():
    # Create a database session
    db = SessionLocal()
    
    try:
        print("Deleting all existing participants and their responses...")
        # Delete all responses first (due to foreign key constraints)
        db.query(Response).delete()
        # Delete all participants
        db.query(Participant).delete()
        db.commit()
        print("All participants and responses deleted successfully.")
        
        # Create new participants
        print("Creating new participants...")
        
        # Ensure the avatars directory exists
        avatars_dir = "frontend/static/avatars"
        os.makedirs(avatars_dir, exist_ok=True)
        
        # Create Andre participant
        andre = Participant(
            name="Andre",
            avatar_path="frontend/static/avatars/andre.png"
        )
        db.add(andre)
        
        # Create Arif participant
        arif = Participant(
            name="Arif",
            avatar_path="frontend/static/avatars/arif.png"
        )
        db.add(arif)
        
        # Commit the changes
        db.commit()
        print("New participants created successfully.")
        
        # Print the participants
        participants = db.query(Participant).all()
        print("\nCurrent participants:")
        for p in participants:
            print(f"ID: {p.id}, Name: {p.name}, Avatar: {p.avatar_path}")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
