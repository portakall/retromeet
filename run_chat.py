import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.chat_interface import launch_chat

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Run the Gradio chat interface')
    parser.add_argument('--port', type=int, default=8081, help='Port to run the Gradio interface on')
    args = parser.parse_args()
    
    # Get configuration from environment variables and arguments
    gradio_host = "localhost"  # Force to localhost for testing
    gradio_port = args.port  # Use the provided port or default to 8081
    
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
