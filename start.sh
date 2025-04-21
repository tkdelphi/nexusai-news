#!/bin/bash

echo "Starting NexusAI News Hub..."
echo "-------------------------------------"
echo "API Server running on http://localhost:5001"
echo "To view the website, open http://localhost:5001 in your browser"
echo "Press Ctrl+C to stop the server"
echo "-------------------------------------"

# Start the API server on port 5001
cd "$(dirname "$0")"
source .venv/bin/activate
nohup python3 api.py &
echo "API server started on http://localhost:5001"
