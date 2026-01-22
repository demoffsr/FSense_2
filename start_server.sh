#!/bin/bash
echo "🚀 Starting FSense API Server..."
echo "================================"
echo "Server will run on: http://localhost:8000"
echo "Health check: http://localhost:8000/health"
echo "API endpoint: http://localhost:8000/api/recommend"
echo ""
echo "Press Ctrl+C to stop"
echo "================================"
echo ""

PYTHONPATH=. python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
