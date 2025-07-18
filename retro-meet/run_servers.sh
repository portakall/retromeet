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
echo "Starting Gradio interface on http://localhost:8080..."
python run_chat.py

# If the Gradio interface exits, also kill the backend
kill $BACKEND_PID
