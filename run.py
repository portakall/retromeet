#!/usr/bin/env python3
"""
RetroMeet Application Runner

This script provides instructions on how to run the RetroMeet application.
The application consists of two main components:
1. FastAPI backend server - Handles data storage, processing, and video generation
2. Gradio chat interface - Collects responses from participants

Both components should be run separately for stability.
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def print_instructions():
    """Print instructions on how to run the RetroMeet application"""
    print("\n" + "=" * 80)
    print("RetroMeet Application")
    print("=" * 80)
    print("\nThis application consists of two main components that should be run separately:")
    print("\n1. FastAPI Backend Server")
    print("   - Handles data storage, processing, and video generation")
    print("   - Run with: python -m backend.main")
    print("   - Access at: http://localhost:8000")
    print("\n2. Gradio Chat Interface")
    print("   - Collects responses from participants")
    print("   - Run with: python run_chat.py")
    print("   - Access at: http://localhost:7860")
    print("   - Will generate a shareable link for external participants")
    print("\nTo run both components, open two terminal windows and run each command separately.")
    print("\nMake sure to activate the virtual environment first:")
    print("source venv/bin/activate")
    print("\n" + "=" * 80)

def check_environment():
    """Check if the virtual environment is activated"""
    if not os.environ.get("VIRTUAL_ENV"):
        print("\nWARNING: Virtual environment is not activated!")
        print("Please activate the virtual environment first:")
        print("source venv/bin/activate\n")
        return False
    return True

if __name__ == "__main__":
    # Check if virtual environment is activated
    check_environment()
    
    # Print instructions
    print_instructions()
    
    # Ask the user what they want to run
    print("\nWhat would you like to run?")
    print("1. FastAPI Backend Server")
    print("2. Gradio Chat Interface")
    print("3. Both (in separate processes)")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ")
    
    if choice == "1":
        # Run FastAPI backend server
        print("\nStarting FastAPI Backend Server...")
        subprocess.run([sys.executable, "-m", "backend.main"])
    elif choice == "2":
        # Run Gradio chat interface
        print("\nStarting Gradio Chat Interface...")
        subprocess.run([sys.executable, "run_chat.py"])
    elif choice == "3":
        # Run both components in separate processes
        print("\nStarting both components in separate processes...")
        print("Press Ctrl+C to stop all processes")
        
        # Start FastAPI backend server in a separate process
        backend_process = subprocess.Popen([sys.executable, "-m", "backend.main"])
        
        # Start Gradio chat interface in a separate process
        chat_process = subprocess.Popen([sys.executable, "run_chat.py"])
        
        try:
            # Wait for both processes to complete (or be interrupted)
            backend_process.wait()
            chat_process.wait()
        except KeyboardInterrupt:
            print("\nStopping all processes...")
            backend_process.terminate()
            chat_process.terminate()
    else:
        print("\nExiting...")
        sys.exit(0)
