import os
import sys
import time
import traceback
from dotenv import load_dotenv

# Add the project root to the Python path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# Load environment variables
load_dotenv()

try:
    print("Importing FastAPI and Uvicorn...", flush=True)
    from fastapi import FastAPI, Request
    from fastapi.staticfiles import StaticFiles
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    
    print("Importing database modules...", flush=True)
    from backend.database.database import engine
    from backend.database.models import Base
    
    print("Importing routers...", flush=True)
    from backend.routers import participants, responses
    
    # Create the database tables
    print("Creating database tables...", flush=True)
    Base.metadata.create_all(bind=engine)
    
    # Create the FastAPI app
    print("Creating FastAPI app...", flush=True)
    app = FastAPI(title="RetroMeet API")
    
    # Add CORS middleware
    print("Adding CORS middleware...", flush=True)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins
        allow_credentials=True,
        allow_methods=["*"],  # Allow all methods
        allow_headers=["*"],  # Allow all headers
    )
    
    # Mount static files
    print("Mounting static files...", flush=True)
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
    
    # Include routers
    print("Including routers...", flush=True)
    app.include_router(participants.router)
    app.include_router(responses.router)
    
    @app.get("/")
    async def root(request: Request):
        return {"message": "RetroMeet API is running"}
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}
    
    # Create necessary directories
    print("Creating necessary directories...", flush=True)
    os.makedirs("frontend/static/avatars", exist_ok=True)
    os.makedirs("frontend/static/videos", exist_ok=True)
    os.makedirs("frontend/static/audio", exist_ok=True)
    
    # Start the FastAPI server
    print("Starting Uvicorn server...", flush=True)
    sys.stdout.flush()
    
    # Use this instead of uvicorn.run() to keep the process alive
    config = uvicorn.Config(app, host="localhost", port=8080, log_level="info")
    server = uvicorn.Server(config)
    server.run()
    
except Exception as e:
    print(f"ERROR: {str(e)}", flush=True)
    print("Traceback:", flush=True)
    traceback.print_exc()
    sys.stdout.flush()
    
    # Keep the script running so we can see the error
    print("Keeping script alive for 60 seconds to view error...", flush=True)
    time.sleep(60)
