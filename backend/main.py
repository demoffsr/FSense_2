"""
FSense API Server - v0.0.1

FastAPI HTTP server for iOS integration.

Run with:
    uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

Or from project root:
    python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
import asyncio
import json
from pathlib import Path

from backend.pipeline.runner import run_flower_chat

# ═══════════════════════════════════════════════════════════════════════════════
# APP CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="FSense API",
    description="AI-powered flower recommendation API",
    version="0.0.1",
)

# CORS for iOS simulator and local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════════
# REQUEST/RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class RecommendRequest(BaseModel):
    """Request body for flower recommendation."""
    prompt: str = Field(..., min_length=1, description="User's message/query")
    region: str = Field(default="US", description="Geographic region for cultural context")


class RecommendResponse(BaseModel):
    """Wrapper for successful recommendation response."""
    success: bool = True
    data: Dict[str, Any]


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: str


# ═══════════════════════════════════════════════════════════════════════════════
# LOG STREAMING
# ═══════════════════════════════════════════════════════════════════════════════

from backend.core.log_queue import get_log_queue
import queue as queue_module

async def log_stream():
    """Stream logs to connected clients via Server-Sent Events."""
    log_queue = get_log_queue()

    def get_with_timeout():
        try:
            return log_queue.get(block=True, timeout=30.0)
        except queue_module.Empty:
            return None

    while True:
        try:
            # Use run_in_executor to avoid blocking the async event loop
            log_data = await asyncio.get_event_loop().run_in_executor(None, get_with_timeout)

            if log_data is not None:
                yield f"data: {json.dumps(log_data)}\n\n"
            else:
                # Timeout - send keepalive
                yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"
        except Exception as e:
            # Send error and keepalive
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            await asyncio.sleep(1)

@app.get("/api/logs/stream")
async def stream_logs():
    """Server-Sent Events endpoint for real-time logs."""
    return StreamingResponse(log_stream(), media_type="text/event-stream")

@app.get("/logs", response_class=HTMLResponse)
async def logs_page():
    """Serve the logs viewer page."""
    html_path = Path(__file__).parent / "static" / "logs.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text())
    return HTMLResponse("<h1>Logs page not found</h1>")


# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "0.0.1"}


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN RECOMMENDATION ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/recommend", response_model=RecommendResponse)
async def recommend(request: RecommendRequest):
    """
    Generate a flower recommendation based on user prompt.

    This is the main endpoint for iOS integration.

    Args:
        request: Contains prompt (user message) and optional region

    Returns:
        FlowerCardPayload with header, meaning, gifting, and context tabs

    Raises:
        HTTPException 400: If prompt is invalid or pipeline fails
    """
    result = run_flower_chat(
        prompt=request.prompt,
        region=request.region,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Failed to generate recommendation")
        )

    return RecommendResponse(success=True, data=result["data"])


# ═══════════════════════════════════════════════════════════════════════════════
# SIMPLE GET ENDPOINT (for testing)
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/recommend")
async def recommend_get(prompt: str, region: str = "US"):
    """
    GET version of recommend endpoint for easy testing.

    Example:
        GET /api/recommend?prompt=I%20want%20to%20apologize&region=US
    """
    result = run_flower_chat(prompt=prompt, region=region)

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Failed to generate recommendation")
        )

    return {"success": True, "data": result["data"]}


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
