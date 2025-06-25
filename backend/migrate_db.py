#!/usr/bin/env python3
"""
Database migration script to add chat_response_file_path column to responses table
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add the project root and backend directory to the path
backend_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(backend_dir)
sys.path.append(project_root)
sys.path.append(backend_dir)

# Load environment variables
load_dotenv(os.path.join(project_root, '.env'))

# Import database models
from backend.database.models import Base
from backend.database.database import engine, DATABASE_URL

def migrate_database():
    """Add the new chat_response_file_path column to the responses table"""
    print(f"Connecting to database: {DATABASE_URL}")
    
    try:
        # Check if the column already exists
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(responses)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'chat_response_file_path' in columns:
                print("Column 'chat_response_file_path' already exists in responses table.")
                return
            
            # Add the new column
            print("Adding 'chat_response_file_path' column to responses table...")
            conn.execute(text("ALTER TABLE responses ADD COLUMN chat_response_file_path VARCHAR(500)"))
            conn.commit()
            print("Migration completed successfully!")
            
    except Exception as e:
        print(f"Error during migration: {e}")
        return False
    
    return True

def create_tables():
    """Create all tables if they don't exist"""
    print("Creating tables if they don't exist...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

if __name__ == "__main__":
    print("Starting database migration...")
    
    # Create tables first
    create_tables()
    
    # Run migration
    if migrate_database():
        print("Database migration completed successfully!")
    else:
        print("Database migration failed!")
        sys.exit(1)
