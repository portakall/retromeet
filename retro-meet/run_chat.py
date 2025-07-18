import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.chat_interface import launch_chat

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Get configuration from environment variables
    gradio_host = "localhost"  # Force to localhost for testing
    
    # Use port 8080 to avoid any potential conflicts
    gradio_port = 8080
    
    print(f"Starting RetroMeet Chat Interface at http://{gradio_host}:{gradio_port}", flush=True)
    print("This will create a shareable link for collecting responses from participants", flush=True)
    print("Press Ctrl+C to stop the chat interface", flush=True)
    sys.stdout.flush()
    
    try:
        # Launch the Gradio chat interface
        print("Attempting to launch chat interface...", flush=True)
        sys.stdout.flush()
        launch_chat(share=False, server_name=gradio_host, server_port=gradio_port)
    except Exception as e:
        print(f"Error launching chat interface: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
