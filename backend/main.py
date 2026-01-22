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
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional

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
