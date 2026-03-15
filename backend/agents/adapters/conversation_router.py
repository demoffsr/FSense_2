"""
Conversation Router - v0.7.0

Routes user messages to either conversational response or pipeline trigger.
Replaces the IntentClassifierAgent + QuickReplyAgent two-step pattern for
General chat mode.

NOT a BaseAgent — runs before the pipeline, like IntentClassifierAgent.

Key design:
- Heuristic fast-paths (no AI call, instant): greetings, obvious flower requests
- AI routing (GPT-4o-mini, ~1-2s): for ambiguous messages
- Image bypass: if image present, always route to recommend
"""

import logging
import re
import json
from typing import Optional, List, Dict, Any

from backend.core.ai_client import get_ai_client_fast, AIClientError
from backend.schemas.chat_response import (
    RouteAction,
    RouteResult,
    ExtractedContext,
    ClarificationType,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# GREETING PATTERNS (instant, no AI call)
# ═══════════════════════════════════════════════════════════════════════════════

_GREETING_PATTERNS = [
    r"^(hi|hello|hey|good\s*(morning|afternoon|evening))[\s!.,]*$",
    r"^(привет|здравствуй(те)?|добрый\s*(день|вечер|утро)|хай|хелло)[\s!.,]*$",
    r"^(hola|bonjour|hallo|guten\s*(tag|morgen|abend))[\s!.,]*$",
    r"^(こんにちは|こんばんは|おはよう)[\s!.,]*$",
    r"^(你好|嗨)[\s!.,]*$",
    r"^(yo|sup|whats\s*up|what'?s\s*up)[\s!.,]*$",
    r"^(how are you|как дела|что нового)[\s?!.,]*$",
]

_GREETING_RESPONSES = {
    "en": "Hi! I'm FSense — your flower recommendation assistant. How can I help you today?",
    "ru": "Привет! Я FSense — ваш помощник по подбору цветов. Чем могу помочь?",
    "es": "¡Hola! Soy FSense, tu asistente de recomendación de flores. ¿En qué puedo ayudarte?",
    "de": "Hallo! Ich bin FSense — Ihr Blumenberater. Wie kann ich Ihnen helfen?",
    "fr": "Bonjour ! Je suis FSense, votre assistant floral. Comment puis-je vous aider ?",
    "ja": "こんにちは！FSenseです。お花選びをお手伝いします。どうされましたか？",
    "zh": "你好！我是FSense——你的花卉推荐助手。有什么可以帮你的吗？",
}

# ═══════════════════════════════════════════════════════════════════════════════
# OBVIOUS FLOWER REQUEST PATTERNS (instant, no AI call)
# ═══════════════════════════════════════════════════════════════════════════════

_FLOWER_REQUEST_PATTERNS_EN = [
    r"(recommend|suggest|find|choose|pick|help me).*(flower|bouquet|roses?|tulips?|lilies?)",
    r"(flower|bouquet|roses?|tulips?).*(for my|for a|for the|to give)",
    r"(want to|need to|going to).*(apologize|thank|congratulate|celebrate)",
    r"what flower.*(should|can|would)",
    r"flowers?\s+for\s+(my\s+)?(mom|mother|wife|husband|girlfriend|boyfriend|friend|boss|colleague|sister|brother|dad|father)",
    r"(birthday|anniversary|wedding|funeral|graduation|valentine|apology)\s+(flower|gift|bouquet|present)",
]

_FLOWER_REQUEST_PATTERNS_RU = [
    r"(подбери|посоветуй|найди|выбери|порекомендуй).*(цвет|букет|роз|тюльпан|лили)",
    r"(хочу|нужно|собираюсь).*(извинить|поблагодарить|поздравить|подарить)",
    r"какие цветы.*(подарить|выбрать|купить)",
    r"цветы\s+(для|маме?|жене?|подруге?|другу|коллеге?|сестре?|брату|папе?)",
    r"(день рождения|годовщин|свадьб|похорон|выпускн).*(цвет|букет|подар)",
]

# ═══════════════════════════════════════════════════════════════════════════════
# CLARIFICATION PATTERNS (flower knowledge questions)
# ═══════════════════════════════════════════════════════════════════════════════

_CLARIFICATION_PATTERNS = [
    (r"(is|are|будут|подходят|подойд).*(suitable|good|appropriate|для)", ClarificationType.CONFIRMATION),
    (r"(what else|что ещё|что еще|другие варианты|alternatives)", ClarificationType.ALTERNATIVES),
    (r"(can i give|можно ли дарить|можно дарить).*(in|в)\s+\w+", ClarificationType.CULTURAL),
    (r"(how many|сколько).*(flower|цвет|штук)", ClarificationType.QUANTITY),
    (r"(what do|что означа|символизир|meaning of|what does.*mean)", ClarificationType.GENERAL_INFO),
]

# ═══════════════════════════════════════════════════════════════════════════════
# OFF-TOPIC / NON-FLOWER PATTERNS
# ═══════════════════════════════════════════════════════════════════════════════

_OFF_TOPIC_PATTERNS = [
    r"(weather|погода|temperature|температура)",
    r"(tell me a joke|расскажи анекдот|joke|шутк)",
    r"(what time|который час|сколько времени)",
    r"(who are you|кто ты|what can you do|что ты умеешь)",
]

_OFF_TOPIC_RESPONSES = {
    "en": "I specialize in flowers and bouquets! I can help you find the perfect flowers for any occasion. Who are you looking to give flowers to?",
    "ru": "Я специализируюсь на цветах и букетах! Могу помочь подобрать идеальные цветы для любого повода. Кому хотите подарить цветы?",
}


# ═══════════════════════════════════════════════════════════════════════════════
# AI ROUTING PROMPT
# ═══════════════════════════════════════════════════════════════════════════════

ROUTER_SYSTEM_PROMPT = """You are FSense, a warm and friendly flower expert assistant.

Your job is to have a natural conversation and determine when you have enough context to recommend flowers.

RULES:
1. Respond in the user's language (detect from their message)
2. Ask ONE question at a time — don't interrogate
3. Signal "recommend" when you have at minimum: a sense of WHO the flowers are for OR WHY (occasion/emotion)
4. "I want flowers for my wife's birthday" = enough → recommend immediately
5. "I want flowers" alone = not enough → ask for whom or what occasion
6. NEVER recommend specific flowers yourself — only gather context and signal readiness
7. For flower knowledge questions (what does X symbolize, is X suitable for Y) → signal "clarify_flower"
8. Be warm, concise (1-2 sentences), and natural
9. When signaling "recommend", write an acknowledgement message (e.g., "Great choice! Let me find the perfect flowers...")

Return STRICT JSON:
{
  "action": "respond" | "recommend" | "clarify_flower",
  "message": "Your response text to show the user",
  "context": {
    "relationship": "wife" | "friend" | null,
    "occasion": "birthday" | "apology" | null,
    "emotion": "love" | "gratitude" | null,
    "budget_hint": "budget" | "mid" | "premium" | null,
    "synthesized_request": "Natural language summary of what user wants" | null
  },
  "language": "en" | "ru" | "es" | "de" | "fr" | "ja" | "zh",
  "clarification_type": "confirmation" | "alternatives" | "cultural" | "quantity" | "general_info" | null
}"""


# ═══════════════════════════════════════════════════════════════════════════════
# CONVERSATION ROUTER
# ═══════════════════════════════════════════════════════════════════════════════

class ConversationRouter:
    """
    Routes user messages to conversational response or pipeline trigger.

    Not a BaseAgent — runs before the pipeline, like IntentClassifierAgent.
    """

    def route(
        self,
        message: str,
        conversation_summary: Optional[str] = None,
        image_base64: Optional[str] = None,
    ) -> RouteResult:
        """
        Route a user message.

        Args:
            message: User's message text
            conversation_summary: Formatted conversation history
            image_base64: If present, always route to recommend

        Returns:
            RouteResult with action, message, and optional extracted context
        """
        # Image bypass: GPT-4o-mini has no vision, VIA handles images
        if image_base64:
            lang = self._detect_language(message)
            ack = self._image_acknowledgement(message, lang)
            return RouteResult(
                action=RouteAction.RECOMMEND,
                message=ack,
                detected_language=lang,
            )

        try:
            # Heuristic fast-paths (no AI call)
            quick_result = self._quick_route(message)
            if quick_result is not None:
                return quick_result

            # AI routing for ambiguous messages
            return self._ai_route(message, conversation_summary)

        except Exception as e:
            logger.error(f"ConversationRouter error: {e}", exc_info=True)
            # Fallback: treat as recommend (conservative, same as old behavior)
            lang = self._detect_language(message)
            return RouteResult(
                action=RouteAction.RECOMMEND,
                message=self._fallback_acknowledgement(lang),
                detected_language=lang,
            )

    def _quick_route(self, message: str) -> Optional[RouteResult]:
        """
        Heuristic fast-paths. Returns None if AI routing is needed.

        Only intercepts messages where AI adds no value:
        - Obvious flower requests (saves ~1-2s AI call, context extractable by regex)
        - Clarification questions (need QuickReplyAgent delegation)

        Everything else (greetings, small talk, off-topic, ambiguous) goes to AI
        for natural, varied responses.
        """
        normalized = message.lower().strip()
        lang = self._detect_language(message)

        # 1. Clarification questions → delegate to QuickReplyAgent
        #    (checked BEFORE flower requests to avoid "roses suitable for apology"
        #     matching flower request pattern via "roses...for a")
        for pattern, ctype in _CLARIFICATION_PATTERNS:
            if re.search(pattern, normalized):
                return RouteResult(
                    action=RouteAction.CLARIFY_FLOWER,
                    message="",  # Will be filled by QuickReplyAgent
                    detected_language=lang,
                    clarification_type=ctype,
                )

        # 2. Obvious flower request with context → recommend immediately
        all_request_patterns = _FLOWER_REQUEST_PATTERNS_EN + _FLOWER_REQUEST_PATTERNS_RU
        for pattern in all_request_patterns:
            if re.search(pattern, normalized):
                context = self._extract_context_from_text(message)
                ack = self._generate_quick_acknowledgement(message, context, lang)
                return RouteResult(
                    action=RouteAction.RECOMMEND,
                    message=ack,
                    extracted_context=context,
                    detected_language=lang,
                )

        # Everything else → AI routing for natural conversation
        return None

    def _ai_route(
        self,
        message: str,
        conversation_summary: Optional[str] = None,
    ) -> RouteResult:
        """Use AI for complex/ambiguous routing."""
        try:
            client = get_ai_client_fast()

            # Build prompt with conversation context
            history_context = ""
            if conversation_summary:
                history_context = f"\n\nConversation history:\n{conversation_summary}\n"

            prompt = f"""User message: "{message}"{history_context}

Route this message."""

            response = client.complete_json(
                prompt=prompt,
                system_prompt=ROUTER_SYSTEM_PROMPT,
                temperature=0.3,
                max_tokens=500,
            )

            # Parse action
            action_str = response.get("action", "respond")
            try:
                action = RouteAction(action_str)
            except ValueError:
                action = RouteAction.RESPOND

            # Parse extracted context
            extracted_context = None
            ctx_data = response.get("context")
            if ctx_data and isinstance(ctx_data, dict):
                # Only create context if at least one field is non-null
                has_data = any(
                    ctx_data.get(k)
                    for k in ["relationship", "occasion", "emotion", "budget_hint", "synthesized_request"]
                )
                if has_data:
                    extracted_context = ExtractedContext(
                        relationship=ctx_data.get("relationship"),
                        occasion=ctx_data.get("occasion"),
                        emotion=ctx_data.get("emotion"),
                        budget_hint=ctx_data.get("budget_hint"),
                        synthesized_request=ctx_data.get("synthesized_request"),
                    )

            # Parse language
            detected_language = response.get("language", "en")

            # Parse clarification type
            clarification_type = None
            if action == RouteAction.CLARIFY_FLOWER and response.get("clarification_type"):
                try:
                    clarification_type = ClarificationType(response["clarification_type"])
                except ValueError:
                    clarification_type = ClarificationType.GENERAL_INFO

            # Get message
            ai_message = response.get("message", "")
            if not ai_message:
                ai_message = self._fallback_acknowledgement(detected_language)

            return RouteResult(
                action=action,
                message=ai_message,
                extracted_context=extracted_context,
                detected_language=detected_language,
                clarification_type=clarification_type,
            )

        except AIClientError as e:
            logger.error(f"AI routing error: {e}")
            # Fallback: treat as recommend
            lang = self._detect_language(message)
            return RouteResult(
                action=RouteAction.RECOMMEND,
                message=self._fallback_acknowledgement(lang),
                detected_language=lang,
            )

    # ═══════════════════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════════════════

    def _detect_language(self, text: str) -> str:
        """Detect language from text character set."""
        cyrillic_count = sum(1 for c in text if '\u0400' <= c <= '\u04FF')
        if cyrillic_count > len(text) * 0.3:
            return "ru"

        # Check for CJK characters
        cjk_count = sum(1 for c in text if '\u4E00' <= c <= '\u9FFF')
        if cjk_count > len(text) * 0.2:
            return "zh"

        hiragana_katakana = sum(1 for c in text if '\u3040' <= c <= '\u30FF')
        if hiragana_katakana > len(text) * 0.2:
            return "ja"

        return "en"

    def _extract_context_from_text(self, message: str) -> Optional[ExtractedContext]:
        """Extract relationship, occasion, emotion from message text."""
        msg_lower = message.lower()

        relationship = None
        occasion = None
        emotion = None

        # Relationship extraction
        rel_patterns = {
            r"\b(wife|жен[еуаы])\b": "wife",
            r"\b(husband|муж[уа]?)\b": "husband",
            r"\b(mom|mother|мам[еуа]?)\b": "mother",
            r"\b(dad|father|пап[еуа]?)\b": "father",
            r"\b(girlfriend|девушк[еуи]?)\b": "girlfriend",
            r"\b(boyfriend|парн[юяе])\b": "boyfriend",
            r"\b(friend|друг[уа]?|подруг[еуи]?)\b": "friend",
            r"\b(sister|сестр[еуы]?)\b": "sister",
            r"\b(brother|брат[уа]?)\b": "brother",
            r"\b(boss|начальник[уа]?|руководител[юя])\b": "boss",
            r"\b(colleague|коллег[еуи]?)\b": "colleague",
            r"\b(teacher|учител[юя]|преподавател[юя])\b": "teacher",
        }
        for pattern, rel in rel_patterns.items():
            if re.search(pattern, msg_lower):
                relationship = rel
                break

        # Occasion extraction (use word-start boundary, no trailing \b for prefix matching)
        occ_patterns = {
            r"\b(birthday|день рождения|днюх)": "birthday",
            r"\b(anniversary|годовщин)": "anniversary",
            r"\b(wedding|свадьб)": "wedding",
            r"\b(funeral|похорон|траур)": "funeral",
            r"\b(graduation|выпускн)": "graduation",
            r"\b(valentine|валентин)": "valentine",
            r"\b(apolog|извин|прости)": "apology",
            r"\b(thank|благодар|спасибо)": "thank_you",
            r"\b(congrat|поздрав)": "congratulations",
            r"\b(get well|выздоравлив)": "get_well",
        }
        for pattern, occ in occ_patterns.items():
            if re.search(pattern, msg_lower):
                occasion = occ
                break

        # Emotion extraction
        emo_patterns = {
            r"\b(love|люб)\b": "love",
            r"\b(sorry|сожале|виноват)\b": "regret",
            r"\b(gratitude|благодарн)\b": "gratitude",
            r"\b(joy|радост|счаст)\b": "joy",
            r"\b(sympathy|сочувств|соболезн)\b": "sympathy",
        }
        for pattern, emo in emo_patterns.items():
            if re.search(pattern, msg_lower):
                emotion = emo
                break

        if relationship or occasion or emotion:
            # Build synthesized request
            parts = []
            if occasion:
                parts.append(f"for {occasion}")
            if relationship:
                parts.append(f"for {relationship}")
            if emotion:
                parts.append(f"expressing {emotion}")
            synthesized = f"Flower recommendation {' '.join(parts)}" if parts else None

            return ExtractedContext(
                relationship=relationship,
                occasion=occasion,
                emotion=emotion,
                synthesized_request=synthesized,
            )

        return None

    def _generate_quick_acknowledgement(
        self,
        message: str,
        context: Optional[ExtractedContext],
        lang: str,
    ) -> str:
        """Generate a context-aware acknowledgement for quick-path recommend."""
        if lang == "ru":
            if context and context.occasion == "apology":
                return "Понял! Сейчас подберу идеальные цветы для извинения..."
            if context and context.occasion == "birthday":
                return "День рождения! Сейчас подберу что-то особенное..."
            if context and context.relationship:
                return f"Отлично! Сейчас подберу идеальные цветы..."
            return "Понял! Дайте мне подумать о лучшем выборе для вас..."

        if context and context.occasion == "apology":
            return "I understand. Let me find the perfect flowers to express your feelings..."
        if context and context.occasion == "birthday":
            return "A birthday! Let me find something special..."
        if context and context.relationship:
            return "Great! Let me find the perfect flowers..."
        return "Got it! Let me think about the best choice for you..."

    def _image_acknowledgement(self, message: str, lang: str) -> str:
        """Acknowledgement for image-based requests."""
        if lang == "ru":
            return "Вижу изображение! Дайте мне определить цветы..." if not message.strip() else "Отлично! Анализирую изображение..."
        return "I see an image! Let me identify the flowers..." if not message.strip() else "Great! Analyzing the image..."

    def _fallback_acknowledgement(self, lang: str) -> str:
        """Fallback acknowledgement when AI routing fails."""
        if lang == "ru":
            return "Понял! Дайте мне подобрать лучший вариант для вас..."
        return "Got it! Let me find the best option for you..."
