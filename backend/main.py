"""
FSense API Server - v0.0.1

FastAPI HTTP server for iOS integration.

Run with:
    uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

Or from project root:
    python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
import asyncio
import json
from pathlib import Path
import logging

from backend.pipeline.runner import run_flower_chat
from backend.database.connection import init_database, get_db
from backend.database.repository import ImageCacheRepository

logger = logging.getLogger(__name__)

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
# STARTUP & BACKGROUND TASKS
# ═══════════════════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_database()
    logger.info("Database initialized")


# Global background tasks list for image generation
_background_tasks_list = []


def add_background_task(func, *args):
    """
    Add background task for execution.

    Note: This is a simple helper for SFA adapter to schedule image generation.
    Tasks are executed immediately in a separate thread.
    """
    import threading
    thread = threading.Thread(target=func, args=args, daemon=True)
    thread.start()
    _background_tasks_list.append(thread)
    logger.info(f"Started background task: {func.__name__}")


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
            # Short timeout for responsive streaming
            return log_queue.get(block=True, timeout=0.5)
        except queue_module.Empty:
            return None

    # Send immediate connection confirmation
    yield f"data: {json.dumps({'type': 'connected'})}\n\n"

    while True:
        try:
            # Use run_in_executor to avoid blocking the async event loop
            log_data = await asyncio.get_event_loop().run_in_executor(None, get_with_timeout)

            if log_data is not None:
                yield f"data: {json.dumps(log_data)}\n\n"
            # No keepalive needed with short timeout - just continue polling
        except Exception as e:
            # Send error
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            await asyncio.sleep(0.5)

@app.get("/api/logs/stream")
async def stream_logs():
    """Server-Sent Events endpoint for real-time logs."""
    return StreamingResponse(
        log_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Access-Control-Allow-Origin": "*",
        }
    )

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
    # Run pipeline in thread pool to NOT block the event loop
    # This allows SSE streaming to work in parallel
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,  # Use default thread pool
        lambda: run_flower_chat(
            prompt=request.prompt,
            region=request.region,
        )
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
    # Run pipeline in thread pool to NOT block the event loop
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: run_flower_chat(prompt=prompt, region=region)
    )

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Failed to generate recommendation")
        )

    return {"success": True, "data": result["data"]}


# ═══════════════════════════════════════════════════════════════════════════════
# IMAGE GENERATION ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/images/status/{cache_key}")
async def get_image_status(cache_key: str):
    """
    Poll image generation status.

    Args:
        cache_key: Cache key from FlowerCardPayload

    Returns:
        {
            "cache_key": str,
            "status": "pending" | "generating" | "completed" | "failed",
            "image_url": str | null,
            "error": str | null,
            "updated_at": str
        }

    Raises:
        404: Cache entry not found
    """
    with get_db() as db:
        repo = ImageCacheRepository(db)
        entry = repo.get_by_cache_key(cache_key)

        if not entry:
            raise HTTPException(status_code=404, detail="Cache entry not found")

        return {
            "cache_key": cache_key,
            "status": entry.status,
            "image_url": entry.image_url,
            "error": entry.error_message,
            "updated_at": entry.updated_at.isoformat(),
        }


@app.get("/static/images/{filename}")
async def serve_image(filename: str):
    """
    Serve generated flower image.

    Args:
        filename: Image filename (e.g., "abc123.png")

    Returns:
        Image file

    Raises:
        404: Image not found
    """
    image_path = Path(__file__).parent / "static" / "images" / filename

    if not image_path.exists() or not image_path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(image_path, media_type="image/png")


@app.get("/api/images/cache-key")
async def get_cache_key_for_debugging(flower_name: str, emotion_context: str):
    """
    Get cache key for debugging.

    Query params:
        - flower_name: string
        - emotion_context: string

    Returns:
        {"cache_key": str}
    """
    from backend.services.image_service import ImageService
    service = ImageService()
    cache_key = service.get_cache_key(flower_name, emotion_context)

    return {"cache_key": cache_key}


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
