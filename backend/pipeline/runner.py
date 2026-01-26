"""
Pipeline Runner - v0.0.1

Main entrypoint for the FSense flower recommendation pipeline.
This module provides the primary API for iOS integration.

iOS Integration:
- Call run_flower_chat() for each user message
- Each call is independent (no conversation state)
- Returns deterministic JSON response

Response Format:
- Success: {"success": true, "data": FlowerCardPayload}
- Failure: {"success": false, "error": "Human-readable message"}
"""

from typing import Any, Dict, Optional, Union
import logging
import traceback

from backend.pipeline.context import PipelineContext, UserPriors
from backend.pipeline.orchestrator import PipelineOrchestrator
from backend.core.settings import get_settings, SettingsError
from backend.core.input_validator import validate_input, validate_region

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# RESPONSE TYPE (Python 3.9 compatible)
# ═══════════════════════════════════════════════════════════════════════════════

# Response is either:
# - Success: {"success": True, "data": FlowerCardPayload}
# - Error: {"success": False, "error": "message"}
PipelineResponse = Dict[str, Any]


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRYPOINT FOR iOS
# ═══════════════════════════════════════════════════════════════════════════════

def run_flower_chat(
    prompt: str,
    region: str = "US",
    image_base64: Optional[str] = None,
) -> PipelineResponse:
    """
    Run the flower recommendation pipeline for a chat message.

    THIS IS THE MAIN ENTRYPOINT FOR iOS.

    Semantics:
    - Every message is treated as: "Find the best flower for this message"
    - If image_base64 provided, analyzes the bouquet image to identify flowers
    - No conversation history (v0.0.1)
    - Each call is independent and deterministic

    Args:
        prompt: User's chat message (e.g., "I want to apologize to my wife")
        region: Geographic region for cultural context (default: "US")
        image_base64: Optional base64-encoded bouquet image for flower identification

    Returns:
        On success: {"success": True, "data": FlowerCardPayload}
        On failure: {"success": False, "error": "Human-readable error"}
        
    Example:
        >>> result = run_flower_chat("I want to apologize sincerely")
        >>> if result["success"]:
        ...     flower_card = result["data"]
        ...     print(flower_card["header"]["name"])
        ... else:
        ...     print(f"Error: {result['error']}")
    """
    # Validate and sanitize input
    validation = validate_input(prompt)
    if not validation.is_valid:
        return {
            "success": False,
            "error": validation.error_message,
        }

    # Use sanitized input
    prompt = validation.sanitized_input

    # Log warnings if any suspicious patterns detected
    if validation.warnings:
        logger.warning(f"Input validation warnings for prompt: {validation.warnings}")

    # Validate and normalize region
    region = validate_region(region)
    
    try:
        # Validate settings (will raise if API key missing)
        settings = get_settings()
        
        has_image = image_base64 is not None
        logger.info(f"Starting flower chat: region={region}, prompt_len={len(prompt)}, has_image={has_image}")

        # Build context
        ctx = PipelineContext(
            user_input=prompt,  # Already sanitized
            region=region.lower(),  # Context expects lowercase
            priors=UserPriors(),
            image_base64=image_base64,  # Pass image for vision analysis
        )
        
        # Run pipeline
        orchestrator = PipelineOrchestrator()
        ctx = orchestrator.run(ctx)
        
        # Check for UI payload
        if ctx.ui_payload is None:
            logger.error(f"Pipeline completed but no UI payload: request_id={ctx.request_id}")
            return {
                "success": False,
                "error": "Failed to generate flower recommendation. Please try again.",
            }
        
        # Check for critical errors
        if ctx.errors:
            logger.warning(f"Pipeline completed with errors: {ctx.errors}")
            # Still return payload if available (graceful degradation)
        
        logger.info(f"Flower chat completed: request_id={ctx.request_id}")
        
        return {
            "success": True,
            "data": ctx.ui_payload,
        }
        
    except SettingsError as e:
        logger.error(f"Settings error: {e}")
        return {
            "success": False,
            "error": "Backend configuration error. Please contact support.",
        }
        
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"An unexpected error occurred: {str(e)}",
        }


# ═══════════════════════════════════════════════════════════════════════════════
# ADVANCED API (For internal use)
# ═══════════════════════════════════════════════════════════════════════════════

def run_pipeline(
    user_input: str,
    region: str = "us",
    relationship_type: Optional[str] = None,
    occasion: Optional[str] = None,
    recipient_info: Optional[str] = None,
    debug: bool = False,
) -> dict[str, Any]:
    """
    Run the complete flower recommendation pipeline with all options.
    
    This is the advanced API for cases where you need more control.
    For iOS integration, use run_flower_chat() instead.
    
    Args:
        user_input: The user's flower query/request
        region: Geographic region for cultural context
        relationship_type: Optional relationship context
        occasion: Optional occasion context
        recipient_info: Optional recipient description
        debug: Enable debug mode
        
    Returns:
        FlowerCardPayload as dictionary (raw, no success wrapper)
    """
    # Build context with priors
    priors = UserPriors(
        relationship_type=relationship_type,
        occasion=occasion,
        recipient_info=recipient_info,
    )
    
    ctx = PipelineContext(
        user_input=user_input,
        region=region,
        priors=priors,
    )
    ctx.flags.is_debug = debug
    
    # Run pipeline
    orchestrator = PipelineOrchestrator()
    ctx = orchestrator.run(ctx)
    
    # Return UI payload
    if ctx.ui_payload is not None:
        return ctx.ui_payload
    
    # Fallback: return error payload
    return {
        "error": True,
        "message": "Pipeline completed but no UI payload was generated",
        "errors": ctx.errors,
    }


def run_pipeline_raw(ctx: PipelineContext) -> PipelineContext:
    """
    Run pipeline with full context access.
    
    For advanced use cases where you need access to all intermediate data.
    
    Args:
        ctx: Pre-configured pipeline context
        
    Returns:
        Mutated context with all agent outputs
    """
    orchestrator = PipelineOrchestrator()
    return orchestrator.run(ctx)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE (For testing only)
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    """CLI entrypoint for testing the pipeline."""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(
        description="FSense Flower Recommendation Pipeline v0.0.1"
    )
    parser.add_argument(
        "query",
        type=str,
        help="The flower query/request to process"
    )
    parser.add_argument(
        "--region",
        type=str,
        default="US",
        help="Geographic region (default: US)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty print JSON output"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    
    # Run pipeline using iOS API
    result = run_flower_chat(
        prompt=args.query,
        region=args.region,
    )
    
    # Output
    indent = 2 if args.pretty else None
    print(json.dumps(result, indent=indent, ensure_ascii=False))


if __name__ == "__main__":
    main()
