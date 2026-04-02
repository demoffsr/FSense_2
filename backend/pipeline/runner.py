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
import os

from pydantic import ValidationError

from backend.pipeline.context import PipelineContext, UserPriors
from backend.pipeline.orchestrator import PipelineOrchestrator
from backend.core.settings import get_settings, SettingsError
from backend.core.input_validator import validate_input, validate_region
from backend.core.budget_normalizer import normalize_budget
from backend.schemas.flower_card_payload import (
    FlowerCardPayload,
    FlowerHeader,
    MeaningTab,
    SymbolismCard,
    WhyThisFlowerCard,
    MoodIntensity,
    GiftingTab,
    GiftSuitabilityCard,
    EmotionalRiskCard,
    RecipientFitItem,
    GiftingOccasionItem,
    ContextTab,
    ContextSummary,
    CulturalInterpretationItem,
    RelationshipContextItem,
    TimingSensitivityItem,
    CommonMisinterpretationItem,
    AskAIMetadata,
)

logger = logging.getLogger(__name__)

# Feature flag for rollback capability
FALLBACK_PAYLOAD_ENABLED = os.getenv("FALLBACK_PAYLOAD_ENABLED", "true").lower() == "true"


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
# FALLBACK PAYLOAD BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

def _build_fallback_payload(ctx: PipelineContext) -> Optional[FlowerCardPayload]:
    """
    Build minimal FlowerCardPayload from available context when SFA fails.

    Returns None if:
    - Feature flag disabled
    - No candidates from FMRA
    - Invalid flower data (missing id/name)
    - Pydantic validation fails
    """
    if not FALLBACK_PAYLOAD_ENABLED:
        logger.debug("Fallback payload disabled by FALLBACK_PAYLOAD_ENABLED=false")
        return None

    # Need at least one flower candidate from FMRA
    if not ctx.candidates or not ctx.candidates.candidates:
        logger.warning("Cannot build fallback: no candidates from FMRA")
        return None

    top_flower = ctx.candidates.candidates[0]

    # Validate required flower fields
    flower_id = top_flower.flower_id or "unknown"
    flower_name = top_flower.name or "Flower"

    if not top_flower.flower_id or not top_flower.name:
        logger.warning(
            f"Fallback: using placeholder for missing flower data: "
            f"id={top_flower.flower_id}, name={top_flower.name}"
        )

    # Use flower meanings from FMRA, ensure non-empty
    meanings = top_flower.meanings[:4] if top_flower.meanings else []
    if not meanings:
        meanings = ["Beauty", "Emotion", "Care"]

    # Simple why_this_flower text (avoid duplicating SFA's occasion logic)
    why_text = f"{flower_name} is a thoughtful choice that carries meaningful symbolism."

    # Risk assessment from RFFA if available
    risk_level = "low"
    risk_description = "Generally well-received."
    suitability_level = "good"
    suitability_description = f"{flower_name} is appropriate for this context."

    if ctx.risks:
        if ctx.risks.overall_risk_level == "high":
            risk_level = "high"
            risk_description = ctx.risks.fit_assessment or "Review context before gifting."
            suitability_level = "moderate"
            suitability_description = f"{flower_name} requires careful consideration."
        elif ctx.risks.overall_risk_level == "medium":
            risk_level = "moderate"
            risk_description = ctx.risks.fit_assessment or "Generally appropriate with some considerations."

    try:
        payload = FlowerCardPayload(
            header=FlowerHeader(
                flower_id=flower_id,
                name=flower_name,
                image_url=None,
                image_asset=None,
            ),
            meaning=MeaningTab(
                meanings=meanings,
                symbolism=SymbolismCard(
                    text=f"{flower_name} carries meaningful symbolism and emotional depth.",
                ),
                why_this_flower=WhyThisFlowerCard(
                    text=why_text,
                ),
                mood_intensity=MoodIntensity(
                    value=0.4,  # Project default (raw 0.0-1.0 scale)
                    label="Balanced",
                ),
            ),
            gifting=GiftingTab(
                suitability=GiftSuitabilityCard(
                    level=suitability_level,
                    description=suitability_description,
                ),
                emotional_risk=EmotionalRiskCard(
                    level=risk_level,
                    description=risk_description,
                ),
                recipient_fits=[
                    RecipientFitItem(recipient_type="General", fit_level="good", note=None)
                ],
                when_to_gift=[
                    GiftingOccasionItem(
                        occasion="Special occasions", suitability="good", description=None
                    )
                ],
                when_to_avoid=[
                    GiftingOccasionItem(
                        occasion="Uncertain contexts", suitability="risky", description=None
                    )
                ],
            ),
            context=ContextTab(
                summary=ContextSummary(
                    text=f"{flower_name} is versatile and carries positive symbolism."
                ),
                cultural_interpretations=[
                    CulturalInterpretationItem(
                        emoji="🌍",
                        culture="Universal",
                        interpretation="Symbol of beauty and emotion",
                        sentiment="positive",
                    )
                ],
                relationship_contexts=[
                    RelationshipContextItem(
                        relationship_type="Close relationship",
                        appropriateness="appropriate",
                        guidance="A meaningful gesture",
                    )
                ],
                timing_sensitivities=[
                    TimingSensitivityItem(
                        timing="Any occasion",
                        sensitivity="low",
                        note="Generally appropriate",
                    )
                ],
                common_misinterpretations=[
                    CommonMisinterpretationItem(
                        misinterpretation="One flower fits all",
                        clarification="Context always matters for best results",
                    )
                ],
            ),
            ask_ai=AskAIMetadata(
                enabled=True,
                suggested_questions=[
                    f"What pairs well with {flower_name}?",
                    "What message should I include?",
                ],
            ),
            pipeline_version="0.5.7",
            request_id=ctx.request_id,
        )
        return payload
    except ValidationError as e:
        logger.error(
            f"Fallback payload validation failed: request_id={ctx.request_id}, error={e}"
        )
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRYPOINT FOR iOS
# ═══════════════════════════════════════════════════════════════════════════════

def run_flower_chat(
    prompt: str,
    region: str = "US",
    image_base64: Optional[str] = None,
    budget_range: Optional[str] = None,
    relationship_hint: Optional[str] = None,
    occasion_hint: Optional[str] = None,
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

        # Normalize budget terminology early (iOS → canonical)
        normalized_budget = normalize_budget(budget_range)
        if budget_range and normalized_budget and budget_range.lower() != normalized_budget:
            logger.debug(f"Budget normalized: '{budget_range}' -> '{normalized_budget}'")

        # Build context with budget priors and optional router hints
        priors = UserPriors(budget_range=normalized_budget)
        if relationship_hint:
            priors.relationship_type = relationship_hint
        if occasion_hint:
            priors.occasion = occasion_hint

        ctx = PipelineContext(
            user_input=prompt,  # Already sanitized
            region=region.lower(),  # Context expects lowercase
            priors=priors,
            image_base64=image_base64,  # Pass image for vision analysis
        )
        
        # Run pipeline
        orchestrator = PipelineOrchestrator()
        ctx = orchestrator.run(ctx)
        
        # Check for UI payload
        if ctx.ui_payload is None:
            logger.error(f"Pipeline completed but no UI payload: request_id={ctx.request_id}")

            # Attempt to build minimal payload from available context
            fallback_payload = _build_fallback_payload(ctx)
            if fallback_payload:
                logger.warning(f"SFA fallback activated: request_id={ctx.request_id}")
                # Convert to dict with camelCase keys for iOS (by_alias=True)
                # Schema uses serialization_alias for flowerId, imageUrl, etc.
                payload_dict = fallback_payload.model_dump(by_alias=True)
                payload_dict["_fallback"] = True
                return {
                    "success": True,
                    "data": payload_dict,
                }

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
    budget_range: Optional[str] = None,
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
            # Full pipeline with budget
            result = run_flower_chat(prompt, region, image_base64, budget_range)

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
# CONVERSATIONAL ROUTER (v0.7.0)
# ═══════════════════════════════════════════════════════════════════════════════

# Feature flag for rollback
CHAT_CONVERSATIONAL_ROUTER = os.getenv("CHAT_CONVERSATIONAL_ROUTER", "true").lower() == "true"


def route_conversation(
    prompt: str,
    region: str = "US",
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    image_base64: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Route a user message to either conversational response or pipeline trigger.

    Args:
        prompt: User's message
        region: Geographic region
        conversation_history: List of conversation messages
        image_base64: Optional base64-encoded image

    Returns:
        {
            "action": "respond" | "recommend",
            "message": "Text to show user",
            "context": {"relationship": ..., "occasion": ..., ...} | None
        }
    """
    from backend.agents.adapters.conversation_router import ConversationRouter
    from backend.agents.adapters.intent_classifier_agent import IntentClassifierAgent
    from backend.agents.adapters.quick_reply_agent import QuickReplyAgent
    from backend.schemas.chat_response import (
        RouteAction,
        IntentType,
    )

    # Validate input
    validation = validate_input(prompt)
    if not validation.is_valid:
        return {
            "action": "respond",
            "message": validation.error_message or "Invalid input.",
        }

    prompt = validation.sanitized_input
    region = validate_region(region)

    # Build conversation summary
    conversation_summary = build_conversation_summary(conversation_history or [])

    if CHAT_CONVERSATIONAL_ROUTER:
        # New conversational router
        router = ConversationRouter()
        result = router.route(
            message=prompt,
            conversation_summary=conversation_summary or None,
            image_base64=image_base64,
        )

        logger.info(
            f"ConversationRouter: action={result.action.value}, "
            f"lang={result.detected_language}, "
            f"has_context={result.extracted_context is not None}"
        )

        # Handle clarify_flower by delegating to QuickReplyAgent
        if result.action == RouteAction.CLARIFY_FLOWER:
            try:
                from backend.schemas.chat_response import ClassifierOutput, ClarificationType

                # Build ClassifierOutput from router's result to avoid redundant AI call
                classification = ClassifierOutput(
                    intent=IntentType("clarification"),
                    confidence=0.9,
                    detected_language=result.detected_language,
                    clarification_type=result.clarification_type or ClarificationType.GENERAL_INFO,
                )

                quick_agent = QuickReplyAgent()
                text_response = quick_agent.generate_response(
                    message=prompt,
                    classifier_output=classification,
                    conversation_summary=conversation_summary or None,
                )
                return {
                    "action": "respond",
                    "message": text_response.message,
                }
            except Exception as e:
                logger.error(f"QuickReplyAgent fallback error: {e}")
                return {
                    "action": "respond",
                    "message": result.message or "I can help with that!",
                }

        # Build response dict
        response: Dict[str, Any] = {
            "action": result.action.value,
            "message": result.message,
        }

        if result.extracted_context:
            response["context"] = {
                "relationship": result.extracted_context.relationship,
                "occasion": result.extracted_context.occasion,
                "emotion": result.extracted_context.emotion,
                "budgetHint": result.extracted_context.budget_hint,
                "synthesizedRequest": result.extracted_context.synthesized_request,
            }

        return response

    else:
        # Fallback: use old IntentClassifier + QuickReplyAgent, map to route format
        try:
            classifier = IntentClassifierAgent()
            classification = classifier.classify(prompt, None, conversation_summary or None)

            if classification.intent == IntentType.FLOWER_REQUEST:
                return {
                    "action": "recommend",
                    "message": "Let me find the perfect flowers for you...",
                }
            else:
                quick_agent = QuickReplyAgent()
                text_response = quick_agent.generate_response(
                    message=prompt,
                    classifier_output=classification,
                    conversation_summary=conversation_summary or None,
                )
                return {
                    "action": "respond",
                    "message": text_response.message,
                }
        except Exception as e:
            logger.error(f"Fallback router error: {e}")
            return {
                "action": "recommend",
                "message": "Let me find the perfect flowers for you...",
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

    # Attempt fallback
    fallback_payload = _build_fallback_payload(ctx)
    if fallback_payload:
        logger.warning(f"SFA fallback activated (raw API): request_id={ctx.request_id}")
        payload_dict = fallback_payload.model_dump(by_alias=True)
        payload_dict["_fallback"] = True
        return payload_dict

    # Final fallback: return error payload
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
