"""
Quick Reply Agent - v0.1.0

Generates text responses for clarification questions.
Uses FlowerKnowledgeBase to provide accurate, fact-based answers.
"""

import logging
from typing import Optional

from backend.core.ai_client import get_ai_client_fast, AIClientError
from backend.schemas.chat_response import (
    ClassifierOutput,
    ClarificationType,
    ChatContext,
    TextResponseData,
)
from backend.services.flower_knowledge_base import FlowerKnowledgeBase

logger = logging.getLogger(__name__)


RESPONSE_PROMPT_EN = """You are a helpful flower expert assistant.
Generate a friendly, informative response based on the provided flower knowledge.

Guidelines:
- Be concise (2-4 sentences max)
- Use the facts provided, don't make up information
- Be warm and helpful in tone
- If the flower/situation isn't suitable, suggest alternatives
- Never be judgmental about the user's choices

Respond in English."""

RESPONSE_PROMPT_RU = """Ты — дружелюбный эксперт по цветам.
Сгенерируй полезный ответ на основе предоставленных данных о цветах.

Правила:
- Будь кратким (2-4 предложения максимум)
- Используй только предоставленные факты, не выдумывай
- Будь тёплым и дружелюбным
- Если цветок/ситуация не подходит, предложи альтернативы
- Не осуждай выбор пользователя

Отвечай на русском языке."""


OFF_TOPIC_RESPONSES = {
    "en": "I'm a flower recommendation assistant. I can help you choose flowers, explain their meanings, or answer questions about gifting flowers. How can I help you with flowers today?",
    "ru": "Я помощник по выбору цветов. Могу помочь подобрать цветы, объяснить их значения или ответить на вопросы о дарении цветов. Чем могу помочь с цветами?",
}


class QuickReplyAgent:
    """
    Generates text responses for clarification questions.

    Uses FlowerKnowledgeBase for accurate information.
    """

    def generate_response(
        self,
        message: str,
        classifier_output: ClassifierOutput,
        context: Optional[ChatContext] = None,
        conversation_summary: Optional[str] = None
    ) -> TextResponseData:
        """
        Generate a text response for a clarification question.

        Args:
            message: User's original message
            classifier_output: Classification result with extracted entities
            context: Optional context from iOS
            conversation_summary: Optional formatted conversation history for context

        Returns:
            TextResponseData with the response message
        """
        # Store conversation summary for use in AI generation
        self._conversation_summary = conversation_summary

        lang = classifier_output.detected_language

        # Handle off-topic
        if classifier_output.intent.value == "off_topic":
            return TextResponseData(message=OFF_TOPIC_RESPONSES.get(lang, OFF_TOPIC_RESPONSES["en"]))

        # Get clarification type
        ctype = classifier_output.clarification_type
        if ctype is None:
            ctype = ClarificationType.GENERAL_INFO

        # Resolve flower and emotion
        flower_id = classifier_output.extracted_flower
        emotion = classifier_output.extracted_emotion

        # Use context as fallback
        if context:
            if not flower_id and context.last_flower_name:
                flower_id = context.last_flower_name
            if not emotion and context.last_emotion:
                emotion = context.last_emotion

        # Generate response based on type
        try:
            if ctype == ClarificationType.CONFIRMATION:
                return self._handle_confirmation(message, flower_id, emotion, lang)
            elif ctype == ClarificationType.ALTERNATIVES:
                return self._handle_alternatives(message, flower_id, emotion, lang, context)
            elif ctype == ClarificationType.CULTURAL:
                return self._handle_cultural(message, flower_id, lang, context)
            elif ctype == ClarificationType.QUANTITY:
                return self._handle_quantity(message, lang, context)
            elif ctype == ClarificationType.GENERAL_INFO:
                return self._handle_general_info(message, flower_id, lang)
            else:
                return self._handle_general_info(message, flower_id, lang)

        except Exception as e:
            logger.error(f"QuickReplyAgent error: {e}", exc_info=True)
            return self._fallback_response(lang)

    def _handle_confirmation(
        self,
        message: str,
        flower_id: Optional[str],
        emotion: Optional[str],
        lang: str
    ) -> TextResponseData:
        """Handle confirmation questions like 'Are roses suitable for apology?'"""
        if not flower_id:
            return self._ask_to_clarify("flower", lang)

        if not emotion:
            return self._ask_to_clarify("occasion", lang)

        # Check suitability
        is_suitable, score, explanation = FlowerKnowledgeBase.is_flower_suitable(flower_id, emotion)

        # Get flower info for name
        flower_info = FlowerKnowledgeBase.get_flower_info(flower_id)
        flower_name = flower_info.name if flower_info else flower_id

        # Build context for AI
        knowledge = f"""
Flower: {flower_name}
Occasion/Emotion: {emotion}
Suitability score: {score:.0%}
Is suitable: {"Yes" if is_suitable else "No"}
Explanation: {explanation}
"""

        return self._generate_ai_response(message, knowledge, lang)

    def _handle_alternatives(
        self,
        message: str,
        flower_id: Optional[str],
        emotion: Optional[str],
        lang: str,
        context: Optional[ChatContext] = None
    ) -> TextResponseData:
        """Handle alternative questions like 'What else can I give?'"""
        if not emotion:
            # Try to infer from context
            if context and context.last_emotion:
                emotion = context.last_emotion
            else:
                return self._ask_to_clarify("occasion", lang)

        # Get alternatives
        alternatives = FlowerKnowledgeBase.get_alternatives(
            emotion=emotion,
            exclude_flower_id=flower_id,
            top_n=3
        )

        if not alternatives:
            if lang == "ru":
                return TextResponseData(message=f"К сожалению, у меня нет альтернатив для '{emotion}'. Попробуйте описать ситуацию подробнее.")
            return TextResponseData(message=f"I don't have alternatives for '{emotion}'. Try describing your situation in more detail.")

        # Build knowledge
        alt_list = []
        for alt in alternatives:
            name = alt.name_ru if lang == "ru" and alt.name_ru else alt.name
            meaning = alt.meaning_ru if lang == "ru" and alt.meaning_ru else alt.meaning_en
            alt_list.append(f"- {name}: {meaning}")

        knowledge = f"""
Occasion/Emotion: {emotion}
Excluding: {flower_id or 'none'}
Alternative flowers:
{chr(10).join(alt_list)}
"""

        return self._generate_ai_response(message, knowledge, lang)

    def _handle_cultural(
        self,
        message: str,
        flower_id: Optional[str],
        lang: str,
        context: Optional[ChatContext] = None
    ) -> TextResponseData:
        """Handle cultural questions like 'Can I give white flowers in Japan?'"""
        # Try to extract region from message
        region = self._extract_region(message)
        if not region and context:
            region = context.region

        if not region:
            return self._ask_to_clarify("region", lang)

        if not flower_id:
            return self._ask_to_clarify("flower", lang)

        # Get cultural rules
        rules = FlowerKnowledgeBase.get_cultural_rules(flower_id, region)
        flower_info = FlowerKnowledgeBase.get_flower_info(flower_id)
        flower_name = flower_info.name if flower_info else flower_id

        if rules is None:
            if lang == "ru":
                return TextResponseData(message=f"У меня нет специфических культурных правил для {flower_name} в регионе {region}. В целом, этот цветок можно дарить.")
            return TextResponseData(message=f"I don't have specific cultural rules for {flower_name} in {region}. Generally, this flower should be fine to give.")

        knowledge = f"""
Flower: {flower_name}
Region: {region}
Is taboo: {"Yes" if rules.is_taboo else "No"}
Reason: {rules.taboo_reason or 'N/A'}
Occasions to avoid: {', '.join(rules.taboo_occasions) if rules.taboo_occasions else 'None'}
Recommended occasions: {', '.join(rules.recommended_occasions) if rules.recommended_occasions else 'N/A'}
"""

        return self._generate_ai_response(message, knowledge, lang)

    def _handle_quantity(
        self,
        message: str,
        lang: str,
        context: Optional[ChatContext] = None
    ) -> TextResponseData:
        """Handle quantity questions like 'How many flowers to give in Russia?'"""
        # Try to extract region from message
        region = self._extract_region(message)
        if not region and context:
            region = context.region

        if not region:
            return self._ask_to_clarify("region", lang)

        # Get quantity rules
        rules = FlowerKnowledgeBase.get_quantity_rules(region)

        if rules is None:
            if lang == "ru":
                return TextResponseData(message=f"У меня нет специфических правил по количеству для региона {region}. Обычно безопасно дарить нечётное количество цветов.")
            return TextResponseData(message=f"I don't have specific quantity rules for {region}. Generally, odd numbers are a safe choice in most cultures.")

        knowledge = f"""
Region: {region}
Preferred numbers: {', '.join(map(str, rules.preferred_numbers)) if rules.preferred_numbers else 'N/A'}
Numbers to avoid: {', '.join(map(str, rules.taboo_numbers)) if rules.taboo_numbers else 'None'}
Rule explanation: {rules.rule_description}
"""

        return self._generate_ai_response(message, knowledge, lang)

    def _handle_general_info(
        self,
        message: str,
        flower_id: Optional[str],
        lang: str
    ) -> TextResponseData:
        """Handle general info questions like 'What do tulips symbolize?'"""
        if not flower_id:
            return self._ask_to_clarify("flower", lang)

        flower_info = FlowerKnowledgeBase.get_flower_info(flower_id)

        if flower_info is None:
            if lang == "ru":
                return TextResponseData(message="Извините, я не нашёл информацию об этом цветке в моей базе данных.")
            return TextResponseData(message="Sorry, I couldn't find information about this flower in my database.")

        name = flower_info.name_ru if lang == "ru" and flower_info.name_ru else flower_info.name
        meanings = ", ".join(flower_info.primary_meanings) if flower_info.primary_meanings else "N/A"

        knowledge = f"""
Flower: {name}
Color: {flower_info.color or 'Various'}
Primary meanings: {meanings}
Availability: {flower_info.availability}
Price tier: {flower_info.price_tier}
"""

        return self._generate_ai_response(message, knowledge, lang)

    def _generate_ai_response(
        self,
        user_message: str,
        knowledge: str,
        lang: str
    ) -> TextResponseData:
        """Generate AI response using provided knowledge."""
        try:
            client = get_ai_client_fast()

            system_prompt = RESPONSE_PROMPT_RU if lang == "ru" else RESPONSE_PROMPT_EN

            # Add conversation history if available
            history_context = ""
            if hasattr(self, '_conversation_summary') and self._conversation_summary:
                history_context = f"\n\nConversation history:\n{self._conversation_summary}\n"

            prompt = f"""User question: "{user_message}"{history_context}

Knowledge from database:
{knowledge}

Generate a helpful response based on this knowledge."""

            response = client.complete(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=200,
            )

            return TextResponseData(message=response.strip())

        except AIClientError as e:
            logger.error(f"AI response generation error: {e}")
            return self._fallback_response(lang)

    def _ask_to_clarify(self, missing: str, lang: str) -> TextResponseData:
        """Ask user to clarify missing information."""
        messages = {
            "flower": {
                "en": "Which flower are you asking about? Please mention the flower name.",
                "ru": "О каком цветке вы спрашиваете? Пожалуйста, уточните название цветка.",
            },
            "occasion": {
                "en": "What's the occasion? (e.g., birthday, apology, thank you)",
                "ru": "Какой повод? (например, день рождения, извинение, благодарность)",
            },
            "region": {
                "en": "Which country or region are you asking about?",
                "ru": "О какой стране или регионе вы спрашиваете?",
            },
        }
        return TextResponseData(message=messages.get(missing, {}).get(lang, messages[missing]["en"]))

    def _fallback_response(self, lang: str) -> TextResponseData:
        """Fallback response when something goes wrong."""
        if lang == "ru":
            return TextResponseData(message="Извините, у меня возникла проблема. Попробуйте переформулировать вопрос.")
        return TextResponseData(message="Sorry, I had trouble processing that. Please try rephrasing your question.")

    def _extract_region(self, message: str) -> Optional[str]:
        """Extract region from message text."""
        message_lower = message.lower()

        # Region patterns
        region_patterns = {
            "russia": "RU", "россия": "RU", "россию": "RU", "россии": "RU", "рф": "RU",
            "japan": "JP", "японии": "JP", "япония": "JP", "японию": "JP",
            "china": "CN", "китай": "CN", "китае": "CN", "китая": "CN",
            "france": "FR", "франция": "FR", "франции": "FR", "францию": "FR",
            "germany": "DE", "германия": "DE", "германии": "DE", "германию": "DE",
            "usa": "US", "us": "US", "america": "US", "сша": "US", "америк": "US",
            "korea": "KR", "корея": "KR", "корее": "KR", "корею": "KR",
            "brazil": "BR", "бразилия": "BR", "бразилии": "BR", "бразилию": "BR",
            "mexico": "MX", "мексика": "MX", "мексике": "MX", "мексику": "MX",
            "india": "IN", "индия": "IN", "индии": "IN", "индию": "IN",
        }

        for pattern, code in region_patterns.items():
            if pattern in message_lower:
                return code

        return None
