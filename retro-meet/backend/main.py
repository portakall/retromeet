import os
import sys

# Add the project root to the Python path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from backend.database.database import engine
from backend.database.models import Base
from backend.routers import participants, responses, chat, projects, topics, summary
import gradio as gr
from backend.chat_interface import create_chat_interface

# Create the database tables
Base.metadata.create_all(bind=engine)

# Create the FastAPI app
app = FastAPI(title="RetroMeet API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Mount static files
import pathlib
STATIC_DIR = pathlib.Path(__file__).parent.parent / "frontend" / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Set up templates
templates = Jinja2Templates(directory="../frontend/templates")

# Include routers
app.include_router(projects.router)
app.include_router(participants.router)
app.include_router(responses.router)
app.include_router(chat.router)
app.include_router(topics.router)
app.include_router(summary.router)

# Create and mount the Gradio chat interface
# You might need to pass initial parameters to create_chat_interface
# For example, if project_id or participants are known at startup or via another mechanism.
# If they are determined dynamically per session, the Gradio app itself needs to handle that (e.g., via URL params it parses).
gradio_chat_app_instance = create_chat_interface(api_url="http://localhost:8000") # Adjust api_url if needed
app = gr.mount_gradio_app(app, gradio_chat_app_instance, path="/retrospective_chat")

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    # Create necessary directories
    os.makedirs("frontend/static/avatars", exist_ok=True)
    
    # Start the FastAPI server
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
