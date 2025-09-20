from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Any
import threading
import time
import logging

# Assuming create_chat_interface is correctly defined in backend.chat_interface
from backend.chat_interface import create_chat_interface

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)

class Participant(BaseModel):
    id: int
    name: str
    avatar_path: Optional[str] = None
    responses_count: Optional[int] = 0

class ChatLinkRequest(BaseModel):
    project_id: int
    participants: List[Participant]

class ChatLinkResponse(BaseModel):
    link: str
    message: str

# --- Global State for Gradio Interface ---
chat_thread: Optional[threading.Thread] = None
gradio_app_instance: Optional[Any] = None  # To store the Gradio app object
current_gradio_public_url: Optional[str] = None
gradio_project_id_active: Optional[int] = None
gradio_thread_exception: Optional[Exception] = None

GRADIO_SERVER_PORT = 8081
GRADIO_SERVER_NAME = "0.0.0.0" # Use 0.0.0.0 for better share=True behavior
# --- End Global State ---

def stop_current_gradio_instance():
    """Safely stops the current Gradio instance and cleans up state."""
    global chat_thread, gradio_app_instance, current_gradio_public_url, gradio_project_id_active, gradio_thread_exception

    logger.info("Attempting to stop current Gradio instance.")
    if gradio_app_instance:
        try:
            logger.info(f"Closing Gradio app instance for project {gradio_project_id_active}.")
            gradio_app_instance.close() # Gracefully close Gradio
            logger.info("Gradio app instance closed.")
        except Exception as e:
            logger.error(f"Error closing Gradio app instance: {e}")
    
    gradio_app_instance = None
    current_gradio_public_url = None
    gradio_project_id_active = None
    gradio_thread_exception = None
    # chat_thread is managed by its caller, typically joined after this func.
    logger.info("Gradio global state reset.")

def launch_chat_interface_thread_target(project_id: int, participants_details: list):
    """Target function for the Gradio interface thread."""
    global gradio_app_instance, current_gradio_public_url, gradio_project_id_active, gradio_thread_exception

    logger.info(f"Gradio thread started for project_id: {project_id}")
    gradio_thread_exception = None # Reset exception at start of new thread
    local_share_url = None
    local_app_ref = None

    try:
        demo = create_chat_interface(
            project_id=project_id,
            project_participants_details=participants_details
        )
        
        logger.info(f"Launching Gradio for project {project_id} on {GRADIO_SERVER_NAME}:{GRADIO_SERVER_PORT}")
        
        # Launch Gradio. `block=False` and `prevent_thread_lock=True` are crucial for non-blocking launch.
        # `launch` returns (app, local_url, share_url) but share_url might be None initially.
        app_ref, local_url, initial_share_url = demo.launch(
            server_name=GRADIO_SERVER_NAME,
            server_port=GRADIO_SERVER_PORT,
            share=True, 
            quiet=False, # Set to False for more Gradio logs if needed
            prevent_thread_lock=True
        )
        local_app_ref = app_ref # Store for finally block
        gradio_app_instance = app_ref # Store globally
        gradio_project_id_active = project_id

        logger.info(f"Gradio launched. App: {app_ref}, Local URL: {local_url}, Initial Share URL: {initial_share_url}")

        # Poll for the share_url as it might take time for the tunnel to establish
        # The `share_url` attribute is on the app instance itself if `share=True`
        if app_ref:
            poll_attempts = 10
            for attempt in range(poll_attempts):
                if hasattr(app_ref, 'share_url') and app_ref.share_url:
                    local_share_url = app_ref.share_url
                    logger.info(f"Gradio share URL obtained after {attempt+1} attempts: {local_share_url}")
                    break
                logger.info(f"Polling for Gradio share URL (attempt {attempt+1}/{poll_attempts})...")
                time.sleep(1) # Wait 1 second between polls
            
            if not local_share_url:
                logger.warning("Gradio share URL not available after polling. Using local URL as fallback.")
                local_share_url = local_url # Fallback to local URL
        else:
            logger.error("Gradio app_ref is None after launch. Cannot obtain share URL.")
            local_share_url = local_url # Fallback

        current_gradio_public_url = local_share_url
        logger.info(f"Gradio public URL set to: {current_gradio_public_url}")

        if gradio_app_instance:
            logger.info("Blocking Gradio thread to keep server alive...")
            gradio_app_instance.block_thread() # Keep the server running in this thread
            logger.info("Gradio thread unblocked (server likely stopped).")

    except Exception as e:
        logger.error(f"Exception in Gradio thread for project {project_id}: {e}", exc_info=True)
        gradio_thread_exception = e
    finally:
        logger.info(f"Gradio thread for project {project_id} is ending. Cleaning up.")
        # Ensure cleanup, even if block_thread was interrupted or launch failed
        if local_app_ref and local_app_ref != gradio_app_instance: # If instance changed or cleared by stop_current
             try:
                logger.info(f"Closing local_app_ref from thread target for project {project_id}")
                local_app_ref.close()
             except Exception as e_close:
                logger.error(f"Error closing local_app_ref in finally: {e_close}")
        # Global cleanup will be handled by stop_current_gradio_instance if called by /stop-chat or new start
        # If thread exits on its own, this signals it's no longer 'live' for status checks.
        if gradio_project_id_active == project_id: # Only clear if this thread was the active one
            stop_current_gradio_instance() # Reset global state if this thread dies

def start_chat_interface(project_id: int, participants: List[Participant]):
    """Manages the lifecycle of the Gradio chat interface thread."""
    global chat_thread, gradio_project_id_active

    logger.info(f"Request to start chat interface for project_id: {project_id}")

    if chat_thread and chat_thread.is_alive():
        if gradio_project_id_active == project_id:
            logger.info(f"Chat interface for project {project_id} is already running.")
            # Optionally, could check if current_gradio_public_url is set and re-verify
            return
        else:
            logger.info(f"Chat interface is running for a different project ({gradio_project_id_active}). Stopping it first.")
            stop_current_gradio_instance() # Stops app, clears globals
            try:
                chat_thread.join(timeout=5) # Wait for the old thread to finish
                if chat_thread.is_alive():
                    logger.warning("Old chat thread did not terminate in time.")
            except Exception as e:
                logger.error(f"Error joining old chat thread: {e}")
            chat_thread = None # Ensure it's reset
    
    # Prepare participant details for Gradio
    participant_list = [{"id": p.id, "name": p.name, "avatar_path": p.avatar_path} for p in participants]
    
    # Reset relevant global state before starting new thread
    global current_gradio_public_url, gradio_thread_exception
    current_gradio_public_url = None
    gradio_thread_exception = None
    
    logger.info(f"Starting new chat interface thread for project {project_id}.")
    chat_thread = threading.Thread(
        target=launch_chat_interface_thread_target,
        args=(project_id, participant_list),
        daemon=True
    )
    chat_thread.start()

@router.post("/generate-link", response_model=ChatLinkResponse)
async def generate_chat_link(request: ChatLinkRequest):
    """Initializes the chat interface for a project and participants."""
    logger.info(f"Received /generate-link request for project_id: {request.project_id}")
    try:
        start_chat_interface(request.project_id, request.participants)
        return ChatLinkResponse(
            link="",  # Link will be available via /status endpoint
            message=f"Chat interface for project {request.project_id} is initializing. Poll /chat/status for the link."
        )
    except Exception as e:
        logger.error(f"Error in /generate-link for project {request.project_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start chat interface: {str(e)}")

@router.get("/status", response_model=ChatLinkResponse)
async def get_chat_status(project_id_query: Optional[int] = Query(None, alias="projectId")):
    """Gets the status of the chat interface, optionally for a specific project_id."""
    global chat_thread, current_gradio_public_url, gradio_project_id_active, gradio_thread_exception

    logger.debug(f"Received /status request. Query projectId: {project_id_query}, Active projectId: {gradio_project_id_active}")

    if gradio_thread_exception:
        logger.error(f"Reporting Gradio thread exception: {gradio_thread_exception}")
        return ChatLinkResponse(
            link="",
            message=f"Chat interface encountered an error: {str(gradio_thread_exception)}"
        )

    if not (chat_thread and chat_thread.is_alive()):
        logger.info("Chat interface is not running (thread not alive).")
        return ChatLinkResponse(link="", message="Chat interface is not running.")

    # Thread is alive
    if gradio_project_id_active is None:
        logger.info("Chat interface thread is alive, but project ID not yet active (initializing).")
        return ChatLinkResponse(link="", message="Chat interface is initializing...")

    if project_id_query is not None and gradio_project_id_active != project_id_query:
        msg = f"Chat interface is running, but for a different project (ID: {gradio_project_id_active}). Requested project ID: {project_id_query}."
        logger.info(msg)
        return ChatLinkResponse(link="", message=msg)
    
    # Project ID matches or no specific project_id_query was made, and it's for the active one
    if current_gradio_public_url:
        logger.info(f"Chat interface is running for project {gradio_project_id_active} with URL: {current_gradio_public_url}")
        return ChatLinkResponse(
            link=current_gradio_public_url,
            message=f"Chat interface is running for project {gradio_project_id_active}."
        )
    else:
        logger.info(f"Chat interface for project {gradio_project_id_active} is running, but shareable link not yet available.")
        return ChatLinkResponse(
            link="",
            message=f"Chat interface for project {gradio_project_id_active} is running, but shareable link is not yet available. Please try again shortly."
        )

@router.post("/stop-chat", status_code=200)
async def stop_chat_endpoint():
    """Stops the currently running Gradio chat interface."""
    global chat_thread
    logger.info("Received /stop-chat request.")
    
    stop_current_gradio_instance() # Stops app, clears globals
    
    if chat_thread and chat_thread.is_alive():
        logger.info("Waiting for chat thread to join...")
        try:
            chat_thread.join(timeout=10) # Wait for the thread to finish
            if chat_thread.is_alive():
                logger.warning("Chat thread did not terminate in the allocated time after stop request.")
            else:
                logger.info("Chat thread successfully joined.")
        except Exception as e:
            logger.error(f"Error joining chat thread during stop: {e}")
    chat_thread = None # Ensure it's reset
    
    return {"message": "Chat interface stopping process initiated."}
