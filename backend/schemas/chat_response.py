"""
Chat Response Schemas - v0.1.0

Schemas for the clarification chat feature.
Supports two response types: recommendation (FlowerCardPayload) and text.
"""

from enum import Enum
from typing import Optional, Literal, Union, Any, List
from pydantic import BaseModel, Field, ConfigDict


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class IntentType(str, Enum):
    """
    Classification of user message intent.
    """
    FLOWER_REQUEST = "flower_request"      # Full pipeline needed
    CLARIFICATION = "clarification"        # Quick text response
    OFF_TOPIC = "off_topic"                # Not about flowers


class ClarificationType(str, Enum):
    """
    Type of clarification question.
    """
    CONFIRMATION = "confirmation"          # "А точно подходит?"
    ALTERNATIVES = "alternatives"          # "Что ещё можно?"
    CULTURAL = "cultural"                  # "Можно ли в Японии?"
    QUANTITY = "quantity"                  # "Сколько дарить?"
    GENERAL_INFO = "general_info"          # "Что символизирует?"


class ResponseType(str, Enum):
    """
    Type of chat response.
    """
    RECOMMENDATION = "recommendation"
    TEXT = "text"


class RouteAction(str, Enum):
    """
    Action determined by ConversationRouter.
    """
    RESPOND = "respond"                # Conversational text response
    RECOMMEND = "recommend"            # Signal pipeline trigger
    CLARIFY_FLOWER = "clarify_flower"  # Delegate to QuickReplyAgent


class ExtractedContext(BaseModel):
    """Context extracted from multi-turn conversation for pipeline enrichment."""
    relationship: Optional[str] = None      # "wife", "friend", "colleague"
    occasion: Optional[str] = None          # "birthday", "apology"
    emotion: Optional[str] = None           # "love", "gratitude", "regret"
    budget_hint: Optional[str] = None       # "budget", "mid", "premium"
    synthesized_request: Optional[str] = None  # Natural language summary


class RouteResult(BaseModel):
    """Output from ConversationRouter."""
    action: RouteAction
    message: str
    extracted_context: Optional[ExtractedContext] = None
    detected_language: str = "en"
    clarification_type: Optional[ClarificationType] = None  # For clarify_flower


# ═══════════════════════════════════════════════════════════════════════════════
# INPUT MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class ChatContext(BaseModel):
    """
    Optional context from iOS for fallback when intent cannot be extracted from text.

    Maps to Swift: ChatContext
    """
    model_config = ConfigDict(populate_by_name=True)

    last_flower_name: Optional[str] = Field(
        None,
        description="Last recommended flower ID",
        serialization_alias="lastFlowerName"
    )
    last_emotion: Optional[str] = Field(
        None,
        description="Last detected emotion/occasion",
        serialization_alias="lastEmotion"
    )
    region: str = Field(
        default="US",
        description="User's region for cultural context"
    )


class ConversationMessage(BaseModel):
    """
    A single message in the conversation history.

    Maps to Swift: ConversationMessage
    """
    model_config = ConfigDict(populate_by_name=True)

    role: Literal["user", "assistant"] = Field(
        ...,
        description="Message sender role"
    )
    content: str = Field(
        ...,
        description="Message text content"
    )
    message_type: Optional[str] = Field(
        None,
        description="Type of message: 'text' or 'recommendation'",
        serialization_alias="messageType"
    )
    flower_name: Optional[str] = Field(
        None,
        description="Flower name if this was a recommendation",
        serialization_alias="flowerName"
    )


class ChatContextV2(BaseModel):
    """
    Extended context with full conversation history.

    Maps to Swift: ChatContextV2
    """
    model_config = ConfigDict(populate_by_name=True)

    conversation_history: List[ConversationMessage] = Field(
        default_factory=list,
        description="Full conversation history",
        serialization_alias="conversationHistory"
    )
    last_flower_name: Optional[str] = Field(
        None,
        description="Last recommended flower ID",
        serialization_alias="lastFlowerName"
    )
    last_emotion: Optional[str] = Field(
        None,
        description="Last detected emotion/occasion",
        serialization_alias="lastEmotion"
    )
    region: str = Field(
        default="US",
        description="User's region for cultural context"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSIFIER OUTPUT
# ═══════════════════════════════════════════════════════════════════════════════

class ClassifierOutput(BaseModel):
    """
    Output from IntentClassifierAgent.
    """
    intent: IntentType = Field(..., description="Classified intent")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Classification confidence"
    )
    extracted_flower: Optional[str] = Field(
        None,
        description="Flower ID extracted from message text"
    )
    extracted_emotion: Optional[str] = Field(
        None,
        description="Emotion/occasion extracted from message text"
    )
    detected_language: Literal["en", "ru"] = Field(
        default="en",
        description="Detected language of the message"
    )
    clarification_type: Optional[ClarificationType] = Field(
        None,
        description="Type of clarification (if intent is clarification)"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class TextResponseData(BaseModel):
    """
    Text response payload.

    Maps to Swift: TextMessage
    """
    message: str = Field(..., description="Text response message")


class ChatResponse(BaseModel):
    """
    Unified chat response that can contain either recommendation or text.

    Maps to Swift: ChatResponse
    """
    model_config = ConfigDict(populate_by_name=True)

    success: bool = Field(..., description="Whether the request succeeded")
    type: ResponseType = Field(..., description="Response type")
    data: Any = Field(..., description="Response data (FlowerCardPayload or TextResponseData)")
    error: Optional[str] = Field(None, description="Error message if success is False")
