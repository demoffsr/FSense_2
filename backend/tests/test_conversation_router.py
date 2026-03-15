"""
Tests for ConversationRouter - v0.7.0

Tests heuristic fast-paths (no AI), AI routing (mocked),
and integration with route_conversation().
"""

import pytest
from unittest.mock import patch, MagicMock

from backend.agents.adapters.conversation_router import ConversationRouter
from backend.schemas.chat_response import RouteAction, ExtractedContext, ClarificationType


# ═══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def router():
    return ConversationRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# HEURISTIC FAST-PATH TESTS (no AI call)
# ═══════════════════════════════════════════════════════════════════════════════

class TestGreetings:
    """Greetings go through AI routing for natural, varied responses."""

    @patch("backend.agents.adapters.conversation_router.get_ai_client_fast")
    @pytest.mark.parametrize("greeting", [
        "Hi", "Hello!", "Hey", "hi!", "hello",
        "Good morning", "Good afternoon",
    ])
    def test_english_greetings_use_ai(self, mock_get_client, router, greeting):
        """Greetings should go to AI, not return hardcoded text."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.complete_json.return_value = {
            "action": "respond",
            "message": f"Hey there! I'm FSense. Looking for flowers today?",
            "language": "en",
        }
        result = router.route(greeting)
        assert result.action == RouteAction.RESPOND
        assert mock_client.complete_json.called

    @patch("backend.agents.adapters.conversation_router.get_ai_client_fast")
    @pytest.mark.parametrize("greeting", [
        "Привет", "Здравствуйте", "Добрый день", "привет!",
    ])
    def test_russian_greetings_use_ai(self, mock_get_client, router, greeting):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.complete_json.return_value = {
            "action": "respond",
            "message": "Привет! Чем могу помочь с цветами?",
            "language": "ru",
        }
        result = router.route(greeting)
        assert result.action == RouteAction.RESPOND
        assert result.detected_language == "ru"


class TestObviousFlowerRequests:
    """Obvious flower requests should return 'recommend' immediately."""

    @pytest.mark.parametrize("request_text", [
        "Flowers for my wife's birthday",
        "Recommend flowers for an apology",
        "Help me choose a bouquet for my mom",
        "I want to apologize to my wife",
    ])
    def test_english_flower_requests(self, router, request_text):
        result = router.route(request_text)
        assert result.action == RouteAction.RECOMMEND
        assert result.message  # Has acknowledgement

    @pytest.mark.parametrize("request_text", [
        "Подбери цветы для мамы",
        "Хочу извиниться перед женой",
        "Какие цветы подарить на день рождения",
    ])
    def test_russian_flower_requests(self, router, request_text):
        result = router.route(request_text)
        assert result.action == RouteAction.RECOMMEND
        assert result.detected_language == "ru"

    def test_extracts_relationship(self, router):
        result = router.route("Flowers for my wife's birthday")
        assert result.extracted_context is not None
        assert result.extracted_context.relationship == "wife"

    def test_extracts_occasion(self, router):
        result = router.route("Flowers for my wife's birthday")
        assert result.extracted_context is not None
        assert result.extracted_context.occasion == "birthday"

    def test_extracts_apology_occasion(self, router):
        result = router.route("I want to apologize to my wife")
        assert result.extracted_context is not None
        assert result.extracted_context.occasion == "apology"

    def test_extracts_mother_relationship(self, router):
        result = router.route("Recommend flowers for my mom")
        assert result.extracted_context is not None
        assert result.extracted_context.relationship == "mother"


class TestOffTopic:
    """Off-topic messages go through AI for natural redirects."""

    @patch("backend.agents.adapters.conversation_router.get_ai_client_fast")
    @pytest.mark.parametrize("message", [
        "What's the weather?",
        "Tell me a joke",
    ])
    def test_off_topic_uses_ai(self, mock_get_client, router, message):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.complete_json.return_value = {
            "action": "respond",
            "message": "I'm all about flowers! Looking for a bouquet?",
            "language": "en",
        }
        result = router.route(message)
        assert result.action == RouteAction.RESPOND
        assert mock_client.complete_json.called


class TestClarifications:
    """Flower knowledge questions should signal clarify_flower."""

    def test_symbolism_question(self, router):
        result = router.route("What do tulips symbolize?")
        assert result.action == RouteAction.CLARIFY_FLOWER
        assert result.clarification_type == ClarificationType.GENERAL_INFO

    def test_suitability_question(self, router):
        result = router.route("Are roses suitable for apology?")
        assert result.action == RouteAction.CLARIFY_FLOWER
        assert result.clarification_type == ClarificationType.CONFIRMATION

    def test_alternatives_question(self, router):
        result = router.route("What else can I give besides roses?")
        assert result.action == RouteAction.CLARIFY_FLOWER
        assert result.clarification_type == ClarificationType.ALTERNATIVES


class TestImageBypass:
    """Image presence should always route to recommend."""

    def test_image_always_recommends(self, router):
        result = router.route("What's this?", image_base64="base64data")
        assert result.action == RouteAction.RECOMMEND

    def test_image_with_empty_message(self, router):
        result = router.route("", image_base64="base64data")
        assert result.action == RouteAction.RECOMMEND

    def test_image_with_greeting(self, router):
        """Even greetings with images should recommend (VIA handles it)."""
        result = router.route("Hello!", image_base64="base64data")
        assert result.action == RouteAction.RECOMMEND


# ═══════════════════════════════════════════════════════════════════════════════
# AI ROUTING TESTS (mocked AI client)
# ═══════════════════════════════════════════════════════════════════════════════

class TestAIRouting:
    """Tests for ambiguous messages that require AI routing."""

    @patch("backend.agents.adapters.conversation_router.get_ai_client_fast")
    def test_ambiguous_message_calls_ai(self, mock_get_client, router):
        """'I need help' is ambiguous and should use AI."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.complete_json.return_value = {
            "action": "respond",
            "message": "I'd love to help! Are you looking for flowers for a specific occasion?",
            "context": None,
            "language": "en",
        }

        result = router.route("I need help")
        assert result.action == RouteAction.RESPOND
        assert mock_client.complete_json.called

    @patch("backend.agents.adapters.conversation_router.get_ai_client_fast")
    def test_ai_recommends_with_context(self, mock_get_client, router):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.complete_json.return_value = {
            "action": "recommend",
            "message": "Great! Let me find perfect flowers for your girlfriend's birthday!",
            "context": {
                "relationship": "girlfriend",
                "occasion": "birthday",
                "emotion": "love",
                "budget_hint": None,
                "synthesized_request": "Birthday flowers for girlfriend",
            },
            "language": "en",
        }

        result = router.route(
            "For my girlfriend",
            conversation_summary="User: I need flowers\nAssistant: For whom?"
        )
        assert result.action == RouteAction.RECOMMEND
        assert result.extracted_context is not None
        assert result.extracted_context.relationship == "girlfriend"
        assert result.extracted_context.occasion == "birthday"

    @patch("backend.agents.adapters.conversation_router.get_ai_client_fast")
    def test_ai_responds_in_russian(self, mock_get_client, router):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.complete_json.return_value = {
            "action": "respond",
            "message": "Кому хотите подарить цветы?",
            "context": None,
            "language": "ru",
        }

        result = router.route("Хочу цветы")
        assert result.action == RouteAction.RESPOND
        assert result.detected_language == "ru"

    @patch("backend.agents.adapters.conversation_router.get_ai_client_fast")
    def test_ai_error_falls_back_to_recommend(self, mock_get_client, router):
        """When AI fails, fallback to recommend (conservative)."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.complete_json.side_effect = Exception("API Error")

        result = router.route("I need something special")
        assert result.action == RouteAction.RECOMMEND

    @patch("backend.agents.adapters.conversation_router.get_ai_client_fast")
    def test_ai_invalid_action_defaults_to_respond(self, mock_get_client, router):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.complete_json.return_value = {
            "action": "invalid_action",
            "message": "Hello!",
            "language": "en",
        }

        result = router.route("Tell me something")
        assert result.action == RouteAction.RESPOND

    @patch("backend.agents.adapters.conversation_router.get_ai_client_fast")
    def test_conversation_summary_passed_to_ai(self, mock_get_client, router):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.complete_json.return_value = {
            "action": "respond",
            "message": "response",
            "language": "en",
        }

        summary = "User: Hi\nAssistant: Hello! How can I help?"
        router.route("I want flowers", conversation_summary=summary)

        # Verify the prompt includes conversation history
        call_args = mock_client.complete_json.call_args
        prompt = call_args[1].get("prompt") or call_args[0][0] if call_args[0] else call_args[1]["prompt"]
        assert "Conversation history" in prompt
        assert summary in prompt


# ═══════════════════════════════════════════════════════════════════════════════
# CONTEXT EXTRACTION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestContextExtraction:
    """Test _extract_context_from_text helper."""

    def test_extracts_wife_relationship(self, router):
        ctx = router._extract_context_from_text("Flowers for my wife")
        assert ctx is not None
        assert ctx.relationship == "wife"

    def test_extracts_friend_relationship(self, router):
        ctx = router._extract_context_from_text("Gift for a friend")
        assert ctx is not None
        assert ctx.relationship == "friend"

    def test_extracts_birthday_occasion(self, router):
        ctx = router._extract_context_from_text("For a birthday party")
        assert ctx is not None
        assert ctx.occasion == "birthday"

    def test_extracts_apology_emotion(self, router):
        ctx = router._extract_context_from_text("I need to apologize")
        assert ctx is not None
        assert ctx.occasion == "apology"

    def test_extracts_love_emotion(self, router):
        ctx = router._extract_context_from_text("I love her so much")
        assert ctx is not None
        assert ctx.emotion == "love"

    def test_builds_synthesized_request(self, router):
        ctx = router._extract_context_from_text("Flowers for my wife's birthday")
        assert ctx is not None
        assert ctx.synthesized_request is not None
        assert "birthday" in ctx.synthesized_request
        assert "wife" in ctx.synthesized_request

    def test_no_context_from_generic_message(self, router):
        ctx = router._extract_context_from_text("I need something nice")
        assert ctx is None

    def test_russian_relationship_extraction(self, router):
        ctx = router._extract_context_from_text("Цветы для жены")
        assert ctx is not None
        assert ctx.relationship == "wife"

    def test_russian_occasion_extraction(self, router):
        ctx = router._extract_context_from_text("Подарок на день рождения")
        assert ctx is not None
        assert ctx.occasion == "birthday"


# ═══════════════════════════════════════════════════════════════════════════════
# LANGUAGE DETECTION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestLanguageDetection:
    """Test language detection helper."""

    def test_english_detected(self, router):
        assert router._detect_language("Hello world") == "en"

    def test_russian_detected(self, router):
        assert router._detect_language("Привет мир") == "ru"

    def test_chinese_detected(self, router):
        assert router._detect_language("你好世界") == "zh"

    def test_japanese_detected(self, router):
        assert router._detect_language("こんにちは") == "ja"

    def test_mixed_defaults_to_dominant(self, router):
        # Mostly Cyrillic
        assert router._detect_language("Привет world") == "ru"


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS (route_conversation function)
# ═══════════════════════════════════════════════════════════════════════════════

class TestRouteConversationIntegration:
    """Integration tests for route_conversation() runner function."""

    @patch("backend.pipeline.runner.CHAT_CONVERSATIONAL_ROUTER", True)
    def test_route_with_image_returns_recommend(self):
        from backend.pipeline.runner import route_conversation
        result = route_conversation(
            prompt="What is this?",
            image_base64="base64data",
        )
        assert result["action"] == "recommend"

    @patch("backend.pipeline.runner.CHAT_CONVERSATIONAL_ROUTER", True)
    @patch("backend.agents.adapters.conversation_router.get_ai_client_fast")
    def test_route_greeting_returns_respond(self, mock_get_client):
        from backend.pipeline.runner import route_conversation
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.complete_json.return_value = {
            "action": "respond",
            "message": "Hello! I'm FSense. Need help with flowers?",
            "language": "en",
        }
        result = route_conversation(prompt="Hello!")
        assert result["action"] == "respond"

    @patch("backend.pipeline.runner.CHAT_CONVERSATIONAL_ROUTER", True)
    def test_route_obvious_flower_returns_recommend_with_context(self):
        from backend.pipeline.runner import route_conversation
        result = route_conversation(prompt="Flowers for my wife's birthday")
        assert result["action"] == "recommend"
        assert result.get("context") is not None
        assert result["context"]["relationship"] == "wife"
        assert result["context"]["occasion"] == "birthday"

    @patch("backend.pipeline.runner.CHAT_CONVERSATIONAL_ROUTER", False)
    @patch("backend.agents.adapters.intent_classifier_agent.IntentClassifierAgent.classify")
    def test_route_fallback_uses_old_classifier(self, mock_classify):
        """When feature flag is off, falls back to IntentClassifierAgent."""
        from backend.pipeline.runner import route_conversation
        from backend.schemas.chat_response import ClassifierOutput, IntentType

        mock_classify.return_value = ClassifierOutput(
            intent=IntentType.FLOWER_REQUEST,
            confidence=0.9,
            detected_language="en",
        )

        result = route_conversation(prompt="I want roses")
        assert result["action"] == "recommend"
        mock_classify.assert_called_once()

    @patch("backend.pipeline.runner.CHAT_CONVERSATIONAL_ROUTER", True)
    @patch("backend.agents.adapters.conversation_router.get_ai_client_fast")
    def test_route_empty_history(self, mock_get_client):
        """First message with no conversation history."""
        from backend.pipeline.runner import route_conversation
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.complete_json.return_value = {
            "action": "respond",
            "message": "Привет! Чем помочь?",
            "language": "ru",
        }
        result = route_conversation(
            prompt="Привет",
            conversation_history=[],
        )
        assert result["action"] == "respond"

    @patch("backend.pipeline.runner.CHAT_CONVERSATIONAL_ROUTER", True)
    @patch("backend.agents.adapters.conversation_router.get_ai_client_fast")
    def test_route_with_history(self, mock_get_client):
        """Multi-turn conversation with history."""
        from backend.pipeline.runner import route_conversation

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.complete_json.return_value = {
            "action": "recommend",
            "message": "Отлично! Подберу цветы для извинения перед женой.",
            "context": {
                "relationship": "wife",
                "occasion": "apology",
                "emotion": "regret",
                "budget_hint": None,
                "synthesized_request": "Apology flowers for wife",
            },
            "language": "ru",
        }

        history = [
            {"role": "user", "content": "Привет"},
            {"role": "assistant", "content": "Привет! Чем могу помочь?"},
            {"role": "user", "content": "Хочу подарить цветы"},
            {"role": "assistant", "content": "Кому хотите подарить?"},
        ]

        result = route_conversation(
            prompt="Жене, хочу извиниться",
            conversation_history=history,
        )
        assert result["action"] == "recommend"
        assert result.get("context") is not None
        assert result["context"]["relationship"] == "wife"

    @patch("backend.pipeline.runner.CHAT_CONVERSATIONAL_ROUTER", True)
    @patch("backend.agents.adapters.conversation_router.get_ai_client_fast")
    def test_clarify_flower_delegates_to_quick_reply(self, mock_get_client):
        """clarify_flower action delegates to QuickReplyAgent."""
        from backend.pipeline.runner import route_conversation

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # First call: router returns clarify_flower
        # Second call: IntentClassifier (used for QuickReplyAgent)
        # Third call: QuickReplyAgent generates response
        mock_client.complete_json.side_effect = [
            {
                "action": "clarify_flower",
                "message": "",
                "language": "en",
                "clarification_type": "general_info",
            },
            {
                "intent": "clarification",
                "confidence": 0.9,
                "flower_name": "tulip",
                "emotion": None,
                "language": "en",
                "clarification_type": "general_info",
            },
        ]
        mock_client.complete.return_value = "Tulips symbolize perfect love and spring."

        result = route_conversation(
            prompt="What do tulips symbolize?",
        )
        assert result["action"] == "respond"
        # The message should come from QuickReplyAgent


# ═══════════════════════════════════════════════════════════════════════════════
# EDGE CASE TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_empty_message_with_image(self, router):
        result = router.route("", image_base64="data")
        assert result.action == RouteAction.RECOMMEND

    def test_whitespace_only_message(self, router):
        """Whitespace-only should go through AI routing (no heuristic match)."""
        # This might hit AI or error handling
        result = router.route("   ")
        # Should not crash, action should be valid
        assert result.action in (RouteAction.RESPOND, RouteAction.RECOMMEND)

    def test_very_long_message(self, router):
        """Very long messages shouldn't crash."""
        long_msg = "I want flowers " * 100
        result = router.route(long_msg)
        assert result.action in (RouteAction.RESPOND, RouteAction.RECOMMEND)

    @patch("backend.agents.adapters.conversation_router.get_ai_client_fast")
    def test_special_characters(self, mock_get_client, router):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.complete_json.return_value = {
            "action": "respond", "message": "Hi!", "language": "en",
        }
        result = router.route("Hello! @#$%^&*()")
        assert result.action == RouteAction.RESPOND

    @patch("backend.agents.adapters.conversation_router.get_ai_client_fast")
    def test_case_insensitive_greeting(self, mock_get_client, router):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.complete_json.return_value = {
            "action": "respond", "message": "Hello!", "language": "en",
        }
        result = router.route("HELLO")
        assert result.action == RouteAction.RESPOND

    @patch("backend.agents.adapters.conversation_router.get_ai_client_fast")
    def test_greeting_with_punctuation(self, mock_get_client, router):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.complete_json.return_value = {
            "action": "respond", "message": "Hey!", "language": "en",
        }
        result = router.route("Hello!")
        assert result.action == RouteAction.RESPOND

    @patch("backend.agents.adapters.conversation_router.get_ai_client_fast")
    def test_greeting_with_trailing_spaces(self, mock_get_client, router):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.complete_json.return_value = {
            "action": "respond", "message": "Hi!", "language": "en",
        }
        result = router.route("  Hello  ")
        assert result.action == RouteAction.RESPOND
