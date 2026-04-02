"""
Intent Classifier Agent - v0.1.0

Classifies user messages into:
- flower_request: Full pipeline needed (10 agents)
- clarification: Quick text response about flowers
- off_topic: Not related to flowers

Runs BEFORE the main pipeline to determine routing.
"""

import logging
import re
from typing import Optional

from backend.core.ai_client import get_ai_client_fast, AIClientError
from backend.core.safe_parse import safe_parse_float
from backend.schemas.chat_response import (
    ClassifierOutput,
    IntentType,
    ClarificationType,
    ChatContext,
)
from backend.services.flower_knowledge_base import FlowerKnowledgeBase

logger = logging.getLogger(__name__)


CLASSIFIER_PROMPT = """You are an intent classifier for a flower recommendation chatbot.

Classify the user message into ONE of these categories:

1. "flower_request" - User wants flower recommendations
   Examples:
   - "I want to apologize to my wife"
   - "What flowers for a birthday?"
   - "Подбери цветы для мамы"
   - "Help me choose flowers"

2. "clarification" - User is asking a question about flowers (not requesting recommendations)
   Examples:
   - "Are roses suitable for apology?" (confirmation)
   - "What else can I give besides roses?" (alternatives)
   - "Can I give white flowers in Japan?" (cultural)
   - "How many flowers to give in Russia?" (quantity)
   - "What do tulips symbolize?" (general_info)

3. "off_topic" - Not related to flowers at all
   Examples:
   - "What's the weather?"
   - "Tell me a joke"
   - "Hello"

Also extract:
- flower_name: If a specific flower is mentioned (e.g., "rose", "tulip", "роза")
- emotion: If an emotion/occasion is mentioned (e.g., "apology", "love", "birthday")
- language: "en" for English, "ru" for Russian/Cyrillic text
- clarification_type: If clarification, specify type:
  - "confirmation" - asking if something is suitable
  - "alternatives" - asking for other options
  - "cultural" - asking about cultural rules
  - "quantity" - asking about how many flowers
  - "general_info" - asking about flower meanings/symbolism

Return STRICT JSON:
{
  "intent": "flower_request" | "clarification" | "off_topic",
  "confidence": 0.0-1.0,
  "flower_name": "rose" | null,
  "emotion": "apology" | null,
  "language": "en" | "ru",
  "clarification_type": "confirmation" | "alternatives" | "cultural" | "quantity" | "general_info" | null
}

Be CONSERVATIVE: When in doubt between flower_request and clarification, choose flower_request."""


class IntentClassifierAgent:
    """
    Classifies user messages to determine routing.

    Not a BaseAgent - runs before the pipeline, not as part of it.
    """

    # Confidence threshold - below this, default to flower_request
    CONFIDENCE_THRESHOLD = 0.7

    def classify(
        self,
        message: str,
        context: Optional[ChatContext] = None,
        conversation_summary: Optional[str] = None
    ) -> ClassifierOutput:
        """
        Classify user message intent.

        Args:
            message: User's message text
            context: Optional context from previous interaction
            conversation_summary: Optional formatted conversation history for context

        Returns:
            ClassifierOutput with intent classification
        """
        try:
            # Quick heuristics first
            quick_result = self._quick_classify(message)
            if quick_result is not None:
                return quick_result

            # Use AI for complex cases
            return self._ai_classify(message, context, conversation_summary)

        except Exception as e:
            logger.error(f"Classification error: {e}", exc_info=True)
            # Default to flower_request on error (conservative)
            return ClassifierOutput(
                intent=IntentType.FLOWER_REQUEST,
                confidence=0.5,
                detected_language=self._detect_language(message),
            )

    def _quick_classify(self, message: str) -> Optional[ClassifierOutput]:
        """
        Quick heuristic classification for obvious cases.

        Returns None if AI classification is needed.
        """
        normalized = message.lower().strip()
        lang = self._detect_language(message)

        # Off-topic patterns
        off_topic_patterns = [
            r"^(hi|hello|hey|привет|здравствуй)[\s!.]*$",
            r"^(how are you|как дела|что нового)[\s?]*$",
            r"weather|погода",
            r"^(thanks|спасибо)[\s!.]*$",
        ]
        for pattern in off_topic_patterns:
            if re.search(pattern, normalized):
                return ClassifierOutput(
                    intent=IntentType.OFF_TOPIC,
                    confidence=0.95,
                    detected_language=lang,
                )

        # Clear flower request patterns
        request_patterns_en = [
            r"(recommend|suggest|find|choose|pick|help me).*(flower|bouquet)",
            r"(flower|bouquet).*(for my|for a|to give)",
            r"(want to|need to|going to).*(apologize|thank|congratulate|celebrate)",
            r"what flower.*(should|can|would)",
        ]
        request_patterns_ru = [
            r"(подбери|посоветуй|найди|выбери).*(цвет|букет)",
            r"(хочу|нужно|собираюсь).*(извинить|поблагодарить|поздравить)",
            r"какие цветы.*(подарить|выбрать|купить)",
        ]

        all_request_patterns = request_patterns_en + request_patterns_ru
        for pattern in all_request_patterns:
            if re.search(pattern, normalized):
                return ClassifierOutput(
                    intent=IntentType.FLOWER_REQUEST,
                    confidence=0.9,
                    detected_language=lang,
                )

        # Clear clarification patterns
        clarification_indicators = [
            (r"(is|are|будут|подходят|подойд).*(suitable|good|appropriate|для)", "confirmation"),
            (r"(what else|что ещё|что еще|другие варианты|alternatives)", "alternatives"),
            (r"(can i give|можно ли дарить|можно дарить).*(in|в)\s+\w+", "cultural"),
            (r"(how many|сколько).*(flower|цвет|штук)", "quantity"),
            (r"(what do|что означа|символизир|meaning of)", "general_info"),
        ]

        for pattern, ctype in clarification_indicators:
            if re.search(pattern, normalized):
                # Try to extract flower name
                flower_id = self._extract_flower_from_text(message)

                return ClassifierOutput(
                    intent=IntentType.CLARIFICATION,
                    confidence=0.85,
                    extracted_flower=flower_id,
                    detected_language=lang,
                    clarification_type=ClarificationType(ctype),
                )

        # No clear pattern - need AI classification
        return None

    def _ai_classify(
        self,
        message: str,
        context: Optional[ChatContext] = None,
        conversation_summary: Optional[str] = None
    ) -> ClassifierOutput:
        """Use AI for complex classification."""
        try:
            client = get_ai_client_fast()

            # Add context info if available
            context_info = ""
            if context:
                if context.last_flower_name:
                    context_info += f"\nPrevious flower discussed: {context.last_flower_name}"
                if context.last_emotion:
                    context_info += f"\nPrevious emotion/occasion: {context.last_emotion}"

            # Add conversation history if available
            history_context = ""
            if conversation_summary:
                history_context = f"\n\nConversation history:\n{conversation_summary}"

            prompt = f"""User message: "{message}"{context_info}{history_context}

Classify this message."""

            response = client.complete_json(
                prompt=prompt,
                system_prompt=CLASSIFIER_PROMPT,
                temperature=0.1,  # Low temperature for consistency
            )

            # Parse response
            intent_str = response.get("intent", "flower_request")
            confidence = safe_parse_float(
                response.get("confidence"),
                default=0.7,
                context="FIA.confidence"
            )

            # Conservative: if low confidence, default to flower_request
            if confidence < self.CONFIDENCE_THRESHOLD:
                intent_str = "flower_request"

            # Map to enums
            try:
                intent = IntentType(intent_str)
            except ValueError:
                intent = IntentType.FLOWER_REQUEST

            clarification_type = None
            if intent == IntentType.CLARIFICATION and response.get("clarification_type"):
                try:
                    clarification_type = ClarificationType(response["clarification_type"])
                except ValueError:
                    clarification_type = ClarificationType.GENERAL_INFO

            # Try to resolve flower name to ID
            flower_id = None
            if response.get("flower_name"):
                flower_id = FlowerKnowledgeBase.resolve_flower_id(response["flower_name"])

            return ClassifierOutput(
                intent=intent,
                confidence=confidence,
                extracted_flower=flower_id,
                extracted_emotion=response.get("emotion"),
                detected_language=response.get("language", "en"),
                clarification_type=clarification_type,
            )

        except AIClientError as e:
            logger.error(f"AI classification error: {e}")
            # Fallback to flower_request
            return ClassifierOutput(
                intent=IntentType.FLOWER_REQUEST,
                confidence=0.5,
                detected_language=self._detect_language(message),
            )

    def _detect_language(self, text: str) -> str:
        """Simple language detection based on character set."""
        # Check for Cyrillic characters
        cyrillic_count = sum(1 for c in text if '\u0400' <= c <= '\u04FF')
        if cyrillic_count > len(text) * 0.3:
            return "ru"
        return "en"

    def _extract_flower_from_text(self, text: str) -> Optional[str]:
        """Try to extract flower ID from text using FlowerKnowledgeBase."""
        # Common flower names to look for
        flower_patterns = [
            r"(rose|roses|роз[аыу]?)",
            r"(tulip|tulips|тюльпан[ыа]?)",
            r"(lily|lilies|лили[яию]?)",
            r"(orchid|orchids|орхиде[яию]?)",
            r"(chrysanthemum|хризантем[аыу]?)",
            r"(carnation|гвоздик[аиу]?)",
            r"(peony|peonies|пион[ыа]?)",
            r"(sunflower|подсолнух|подсолнечник)",
        ]

        text_lower = text.lower()
        for pattern in flower_patterns:
            match = re.search(pattern, text_lower)
            if match:
                flower_text = match.group(1)
                return FlowerKnowledgeBase.resolve_flower_id(flower_text)

        return None
