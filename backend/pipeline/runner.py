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

from typing import Any, Dict, Optional, Union, List
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
# CONVERSATION HISTORY HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def build_conversation_summary(history: List[Dict[str, Any]], max_messages: int = 10) -> str:
    """
    Convert conversation history into a text summary for AI prompts.

    Args:
        history: List of conversation messages with 'role' and 'content' keys
        max_messages: Maximum number of recent messages to include (default: 10)

    Returns:
        Formatted string with conversation history
    """
    if not history:
        return ""

    # Take last N messages for context
    recent = history[-max_messages:]

    lines = []
    for msg in recent:
        role = "User" if msg.get("role") == "user" else "Assistant"
        content = msg.get("content", "")

        # Truncate very long messages
        if len(content) > 200:
            content = content[:200] + "..."

        # Add flower context if present
        flower_name = msg.get("flower_name") or msg.get("flowerName")
        if flower_name and msg.get("message_type") == "recommendation":
            lines.append(f"{role}: [Recommended: {flower_name}]")
        else:
            lines.append(f"{role}: {content}")

    return "\n".join(lines)


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

    # Defense-in-depth: Block if any suspicious patterns detected
    # (Primary blocking is in validate_input, this is secondary safety)
    if validation.warnings:
        logger.warning(f"Prompt injection attempt blocked: {validation.warnings}")
        return {
            "success": False,
            "error": "Your message contains disallowed content. Please rephrase your request.",
        }

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

        logger.info(f"Flower chat completed: request_id={ctx.request_id}")

        # Build response
        response: PipelineResponse = {
            "success": True,
            "data": ctx.ui_payload,
        }

        # Include warnings if any non-critical errors occurred
        if ctx.errors:
            logger.warning(f"Pipeline completed with warnings: {ctx.errors}")
            response["warnings"] = ctx.errors

        return response
        
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
# V2 API WITH CLARIFICATION SUPPORT
# ═══════════════════════════════════════════════════════════════════════════════

def run_flower_chat_v2(
    prompt: str,
    region: str = "US",
    image_base64: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    conversation_summary: Optional[str] = None,
) -> PipelineResponse:
    """
    Run the flower chat with clarification support (v2 API).

    NEW ENTRYPOINT FOR iOS - supports both recommendations and text responses.

    This version classifies the user's intent first:
    - flower_request: Runs full 10-agent pipeline, returns FlowerCardPayload
    - clarification: Returns quick text response about flowers
    - off_topic: Returns polite redirect message

    Args:
        prompt: User's chat message
        region: Geographic region for cultural context (default: "US")
        image_base64: Optional base64-encoded image
        context: Optional context from previous interaction:
            - lastFlowerName: Previous flower ID
            - lastEmotion: Previous emotion/occasion
            - region: User's region

    Returns:
        On recommendation: {"success": True, "type": "recommendation", "data": FlowerCardPayload}
        On text response: {"success": True, "type": "text", "data": {"message": "..."}}
        On failure: {"success": False, "type": "text", "error": "..."}

    Example:
        >>> # Flower request
        >>> result = run_flower_chat_v2("I want to apologize to my wife")
        >>> result["type"]  # "recommendation"

        >>> # Clarification question
        >>> result = run_flower_chat_v2("Are roses suitable for apology?")
        >>> result["type"]  # "text"
        >>> result["data"]["message"]  # "Yes, roses are excellent for..."
    """
    from backend.agents.adapters.intent_classifier_agent import IntentClassifierAgent
    from backend.agents.adapters.quick_reply_agent import QuickReplyAgent
    from backend.schemas.chat_response import ChatContext, IntentType, ResponseType

    # Validate input
    validation = validate_input(prompt)
    if not validation.is_valid:
        return {
            "success": False,
            "type": ResponseType.TEXT.value,
            "error": validation.error_message,
        }

    prompt = validation.sanitized_input
    region = validate_region(region)

    # Parse context from iOS
    chat_context = None
    if context:
        chat_context = ChatContext(
            last_flower_name=context.get("lastFlowerName"),
            last_emotion=context.get("lastEmotion"),
            region=context.get("region", region),
        )

    try:
        # Step 1: Classify intent
        classifier = IntentClassifierAgent()
        classification = classifier.classify(prompt, chat_context, conversation_summary)

        logger.info(
            f"Intent classified: {classification.intent.value} "
            f"(confidence={classification.confidence:.2f}, "
            f"flower={classification.extracted_flower}, "
            f"type={classification.clarification_type})"
        )

        # Step 2: Route based on intent
        if classification.intent == IntentType.FLOWER_REQUEST:
            # Full pipeline
            result = run_flower_chat(prompt, region, image_base64)

            # Wrap in v2 format
            if result["success"]:
                response = {
                    "success": True,
                    "type": ResponseType.RECOMMENDATION.value,
                    "data": result["data"],
                }
                # Pass through warnings if present
                if "warnings" in result:
                    response["warnings"] = result["warnings"]
                return response
            else:
                return {
                    "success": False,
                    "type": ResponseType.TEXT.value,
                    "error": result.get("error", "Unknown error"),
                }

        elif classification.intent == IntentType.CLARIFICATION:
            # Quick text response
            quick_agent = QuickReplyAgent()
            response = quick_agent.generate_response(
                message=prompt,
                classifier_output=classification,
                context=chat_context,
                conversation_summary=conversation_summary,
            )

            return {
                "success": True,
                "type": ResponseType.TEXT.value,
                "data": {"message": response.message},
            }

        else:  # OFF_TOPIC
            quick_agent = QuickReplyAgent()
            response = quick_agent.generate_response(
                message=prompt,
                classifier_output=classification,
                context=chat_context,
                conversation_summary=conversation_summary,
            )

            return {
                "success": True,
                "type": ResponseType.TEXT.value,
                "data": {"message": response.message},
            }

    except SettingsError as e:
        logger.error(f"Settings error in v2: {e}")
        return {
            "success": False,
            "type": ResponseType.TEXT.value,
            "error": "Backend configuration error. Please contact support.",
        }

    except Exception as e:
        logger.error(f"Pipeline v2 error: {e}", exc_info=True)
        return {
            "success": False,
            "type": ResponseType.TEXT.value,
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
