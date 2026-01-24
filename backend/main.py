"""
FSense API Server - v0.0.1

FastAPI HTTP server for iOS integration.

Run with:
    uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

Or from project root:
    python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
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
from backend.database.repository import ImageCacheRepository, SessionRepository, ConversationHistoryRepository
from backend.core.rate_limiter import RateLimitMiddleware, configure_rate_limiter, get_client_ip

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

# Rate limiting middleware (30 requests/min per IP + 10 burst)
app.add_middleware(RateLimitMiddleware)
configure_rate_limiter(requests_per_minute=30, burst_size=10, enabled=True)


# ═══════════════════════════════════════════════════════════════════════════════
# STARTUP & BACKGROUND TASKS
# ═══════════════════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_database()
    logger.info("Database initialized")

    # Cleanup stale image generation entries from previous runs
    try:
        from backend.services.image_service import ImageService
        service = ImageService()
        cleaned = service.cleanup_stale_entries()
        if cleaned:
            logger.info(f"Cleaned up {cleaned} stale image entries on startup")
    except Exception as e:
        logger.warning(f"Failed to cleanup stale entries: {e}")


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
    session_id: Optional[str] = Field(default=None, description="Session ID for conversation continuity")
    device_id: Optional[str] = Field(default=None, description="iOS device identifier")


class RecommendResponse(BaseModel):
    """Wrapper for successful recommendation response."""
    success: bool = True
    data: Dict[str, Any]
    session_id: Optional[str] = None  # Return session ID for continuity


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
    from backend.database.connection import get_db_info
    db_info = get_db_info()
    return {
        "status": "ok" if db_info["connected"] else "degraded",
        "version": "0.0.1",
        "database": db_info,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN RECOMMENDATION ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/recommend", response_model=RecommendResponse)
async def recommend(request: RecommendRequest, http_request: Request):
    """
    Generate a flower recommendation based on user prompt.

    This is the main endpoint for iOS integration.

    Args:
        request: Contains prompt (user message), optional region, and optional session_id

    Returns:
        FlowerCardPayload with header, meaning, gifting, and context tabs
        Includes session_id for conversation continuity

    Raises:
        HTTPException 400: If prompt is invalid or pipeline fails
    """
    # Get or create session
    session_id = request.session_id
    client_ip = get_client_ip(http_request)
    user_agent = http_request.headers.get("User-Agent")

    with get_db() as db:
        session_repo = SessionRepository(db)

        if session_id:
            # Try to find existing session
            session = session_repo.get_by_session_id(session_id)
            if not session:
                # Session not found, create new one
                logger.warning(f"Session not found: {session_id}, creating new")
                session = session_repo.create(
                    device_id=request.device_id,
                    client_ip=client_ip,
                    region=request.region,
                    user_agent=user_agent,
                )
            else:
                # Update last active
                session_repo.update_last_active(session_id)
        else:
            # No session ID provided, create new session
            session = session_repo.create(
                device_id=request.device_id,
                client_ip=client_ip,
                region=request.region,
                user_agent=user_agent,
            )

        session_id = session.session_id

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

    # Store conversation history
    with get_db() as db:
        session_repo = SessionRepository(db)
        history_repo = ConversationHistoryRepository(db)

        # Increment message count
        session_repo.increment_message_count(session_id)

        # Extract flower info from response
        flower_name = None
        flower_id = None
        if result["success"] and result.get("data"):
            header = result["data"].get("header", {})
            flower_name = header.get("name")
            flower_id = header.get("flowerId")

        # Add to history
        history_repo.add_message(
            session_id=session_id,
            request_id=result.get("data", {}).get("requestId", "unknown"),
            user_message=request.prompt,
            region=request.region,
            flower_name=flower_name,
            flower_id=flower_id,
            response_payload=result.get("data") if result["success"] else None,
            success=result["success"],
            error_message=result.get("error") if not result["success"] else None,
        )

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Failed to generate recommendation")
        )

    return RecommendResponse(
        success=True,
        data=result["data"],
        session_id=session_id,
    )


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

# ═══════════════════════════════════════════════════════════════════════════════
# SESSION ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/sessions")
async def create_session(http_request: Request, device_id: Optional[str] = None, region: str = "US"):
    """
    Create a new session explicitly.

    Returns:
        {
            "session_id": str,
            "region": str,
            "created_at": str
        }
    """
    client_ip = get_client_ip(http_request)
    user_agent = http_request.headers.get("User-Agent")

    with get_db() as db:
        repo = SessionRepository(db)
        session = repo.create(
            device_id=device_id,
            client_ip=client_ip,
            region=region,
            user_agent=user_agent,
        )
        return {
            "session_id": session.session_id,
            "region": session.region,
            "created_at": session.created_at.isoformat(),
        }


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """
    Get session information.

    Returns:
        {
            "session_id": str,
            "region": str,
            "message_count": int,
            "created_at": str,
            "last_active_at": str
        }

    Raises:
        404: Session not found
    """
    with get_db() as db:
        repo = SessionRepository(db)
        session = repo.get_by_session_id(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "session_id": session.session_id,
            "region": session.region,
            "message_count": session.message_count,
            "created_at": session.created_at.isoformat(),
            "last_active_at": session.last_active_at.isoformat(),
        }


@app.get("/api/sessions/{session_id}/history")
async def get_session_history(session_id: str, limit: int = 20, offset: int = 0):
    """
    Get conversation history for a session.

    Args:
        session_id: Session identifier
        limit: Maximum number of entries (default 20, max 100)
        offset: Pagination offset

    Returns:
        {
            "session_id": str,
            "total": int,
            "messages": [
                {
                    "request_id": str,
                    "user_message": str,
                    "flower_name": str | null,
                    "success": bool,
                    "created_at": str
                }
            ]
        }

    Raises:
        404: Session not found
    """
    # Limit max to 100
    limit = min(limit, 100)

    with get_db() as db:
        session_repo = SessionRepository(db)
        session = session_repo.get_by_session_id(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        history_repo = ConversationHistoryRepository(db)
        entries = history_repo.get_session_history(session_id, limit=limit, offset=offset)
        total = history_repo.count_session_messages(session_id)

        messages = [
            {
                "request_id": entry.request_id,
                "user_message": entry.user_message,
                "flower_name": entry.flower_name,
                "flower_id": entry.flower_id,
                "success": entry.success == 1,
                "created_at": entry.created_at.isoformat(),
            }
            for entry in entries
        ]

        return {
            "session_id": session_id,
            "total": total,
            "messages": messages,
        }


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session and its history.

    Returns:
        {"deleted": bool}

    Raises:
        404: Session not found
    """
    with get_db() as db:
        repo = SessionRepository(db)
        deleted = repo.delete_session(session_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"deleted": True}


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


@app.get("/api/images/stats")
async def get_image_generation_stats():
    """
    Get image generation statistics.

    Returns:
        {
            "active_generations": int,
            "max_concurrent": int,
            "available_slots": int
        }
    """
    from backend.services.image_service import ImageService
    return ImageService.get_generation_stats()


@app.post("/api/images/cleanup")
async def cleanup_stale_images():
    """
    Manually trigger cleanup of stale image generation entries.

    Returns:
        {"cleaned": int}
    """
    from backend.services.image_service import ImageService
    service = ImageService()
    cleaned = service.cleanup_stale_entries()
    return {"cleaned": cleaned}


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
