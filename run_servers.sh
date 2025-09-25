#!/bin/bash

# Activate the virtual environment
source venv/bin/activate

# Start the backend server in the background
echo "Starting backend server on http://localhost:8000..."
python backend/main.py &
BACKEND_PID=$!

# Wait a moment for the backend to initialize
sleep 3

# Start the Gradio interface
echo "Starting Gradio interface on http://localhost:8081..."
python run_chat.py --port 8081

# If the Gradio interface exits, also kill the backend
kill $BACKEND_PID
