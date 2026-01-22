"""
SFA Adapter - Symbolic Flower Agent (FINAL ASSEMBLER) - v0.0.3

Purpose:
THE ONLY COMPONENT that assembles the final UI payload.
Uses comprehensive AI prompt to generate all UI sections.
"""

import logging
from typing import Any

from backend.agents.base import BaseAgent
from backend.pipeline.context import PipelineContext
from backend.core.ai_client import get_ai_client, AIClientError
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

# Comprehensive content generation prompt
CONTENT_GENERATION_PROMPT = """You are generating structured content for a flower detail card in a mobile app.

Your task is to fully populate ALL UI sections for the selected flower.
Do not skip any section.
Do not leave fields empty.
Follow the exact structure and number of items.

Generate content for the following sections:

1. Meaning tab
- "Why this flower?" → exactly 1 short paragraph (1–2 sentences)
- "Symbolism" → exactly 1 short paragraph (2–3 sentences)
- "Meanings" → 4 to 6 single-word or two-word tags (adapt to the specific flower and situation)
- "Mood intensity" → numeric value (15–40) + label. Scale guide:
  * 15-20 = "Very Low" (subtle, gentle emotions like sympathy, condolences)
  * 21-26 = "Low" (calm, thoughtful gestures like gratitude, friendship)
  * 27-32 = "Balanced" (moderate emotions like appreciation, congratulations)
  * 33-37 = "High" (strong emotions like joy, excitement, deep thanks)
  * 38-40 = "Very High" (intense emotions like passionate love, profound celebration)

2. Gifting tab
- "Gift suitability" → short description + status (Safe choice / Caution / Not recommended)
- "Emotional risk level" → Low / Medium / High + 1 sentence explanation
- "When to gift" → exactly 3 short items
- "When to avoid" → exactly 3 short items
- "Recipient fit" → 2–4 recipient types (e.g. Partner, Friend, Family) with brief justification

3. Context tab
- "Context summary" → exactly 1 paragraph
- "Cultural interpretation" → exactly 3 regions with 1 sentence each
- "Relationship context" → exactly 3 relationship types with explanations
- "Timing sensitivity" → exactly 3 short items
- "Common misinterpretations" → exactly 3 short items

Rules:
- Match a calm, emotionally intelligent tone
- Avoid generic filler text
- Content must feel appropriate for a flower recommendation app
- Output must be deterministic and UI-ready

Return JSON with this exact structure:
{
    "meaning": {
        "why_this_flower": "1-2 sentences",
        "symbolism": "2-3 sentences",
        "meanings": ["tag1", "tag2", "tag3", "tag4"],
        "mood_intensity": 25,
        "mood_label": "Balanced"
    },
    "gifting": {
        "suitability": "description",
        "suitability_status": "Safe choice|Caution|Not recommended",
        "risk_level": "Low|Medium|High",
        "risk_explanation": "explanation",
        "when_to_gift": ["item1", "item2", "item3"],
        "when_to_avoid": ["item1", "item2", "item3"],
        "recipient_fit": [
            {"type": "Partner", "justification": "why"}
        ]
    },
    "context": {
        "summary": "paragraph",
        "cultural": [
            {"emoji": "🇺🇸", "region": "Western", "interpretation": "meaning"}
        ],
        "relationships": [
            {"type": "Romantic", "guidance": "advice"}
        ],
        "timing": ["item1", "item2", "item3"],
        "misinterpretations": [
            {"myth": "misconception", "truth": "reality"}
        ]
    },
    "suggested_questions": ["question1?", "question2?", "question3?"]
}"""


class SFAAdapter(BaseAgent):
    """Final assembler - generates complete UI payload."""

    name = "SFA"

    def run(self, ctx: PipelineContext) -> None:
        """Assemble the final UI payload."""
        flower = ctx.get_selected_flower()

        if flower is None:
            ctx.ui_payload = self._build_error_payload("No flower selected")
            return

        payload = self._assemble_payload(ctx, flower)
        ctx.ui_payload = payload.model_dump(mode="json")

    def _assemble_payload(self, ctx: PipelineContext, flower: Any) -> FlowerCardPayload:
        """Assemble complete payload using AI."""
        # Generate AI content
        ai_content = self._generate_ai_content(ctx, flower)

        # Build header
        header = FlowerHeader(
            flower_id=flower.flower_id,
            name=flower.name,
            image_url=None,
            image_asset=flower.name.replace(" ", ""),
        )

        # Build meaning tab from AI
        meaning_data = ai_content.get("meaning", {})
        meaning_tab = MeaningTab(
            meanings=meaning_data.get("meanings", flower.meanings)[:6],
            symbolism=SymbolismCard(
                title="Symbolism",
                text=meaning_data.get("symbolism", f"{flower.name} carries deep symbolic meaning."),
            ),
            why_this_flower=WhyThisFlowerCard(
                title="Why This Flower",
                text=meaning_data.get("why_this_flower", f"{flower.name} is perfect for this occasion."),
                banner_image_asset=header.image_asset,
            ),
            mood_intensity=MoodIntensity(
                value=self._normalize_intensity(meaning_data.get("mood_intensity", 25)),
                label=meaning_data.get("mood_label", "Balanced"),
            ),
        )

        # Build gifting tab from AI
        gifting_tab = self._build_gifting_tab(ai_content.get("gifting", {}))

        # Build context tab from AI
        context_tab = self._build_context_tab(ai_content.get("context", {}))

        # Ask AI metadata
        ask_ai = AskAIMetadata(
            enabled=True,
            suggested_questions=ai_content.get("suggested_questions", [
                f"What other flowers are similar to {flower.name}?",
                "How should I present this flower?",
                "What message should I include?",
            ])[:3],
        )

        return FlowerCardPayload(
            header=header,
            meaning=meaning_tab,
            gifting=gifting_tab,
            context=context_tab,
            ask_ai=ask_ai,
            pipeline_version="0.0.3",
            request_id=ctx.request_id,
        )

    def _normalize_intensity(self, value: int) -> float:
        """Convert 15-40 scale to 0.0-1.0."""
        # 15-40 range → 0.0-1.0
        clamped = max(15, min(40, value))
        return (clamped - 15) / 25.0

    def _generate_ai_content(self, ctx: PipelineContext, flower: Any) -> dict:
        """Generate all content sections using AI."""
        try:
            client = get_ai_client()

            # Build context for prompt
            user_intent = ctx.intent.primary_intent if ctx.intent else "General gifting"
            emotion_summary = ctx.emotions.primary_emotion if ctx.emotions else "Neutral"
            relationship_type = ctx.relationship.relationship_type if ctx.relationship else "General"
            region = ctx.region.upper()

            # Build user prompt with context
            user_prompt = f"""Flower: {flower.name}
User intent: {user_intent}
Emotional context: {emotion_summary}
Relationship context: {relationship_type}
Region: {region}

User's original message: "{ctx.user_input}"
"""

            response = client.complete_json(
                prompt=user_prompt,
                system_prompt=CONTENT_GENERATION_PROMPT,
                temperature=0.6,
                max_tokens=3000,
            )

            # Debug logging
            meaning_data = response.get("meaning", {})
            print(f"[SFA DEBUG] AI returned meanings: {meaning_data.get('meanings')}")
            print(f"[SFA DEBUG] AI returned mood: {meaning_data.get('mood_intensity')} ({meaning_data.get('mood_label')})")
            print(f"[SFA DEBUG] Flower meanings from FMRA: {flower.meanings}")

            return response

        except AIClientError as e:
            logger.error(f"SFA AI content generation failed: {e}")
            return self._get_fallback_content(flower.name)

        except Exception as e:
            logger.error(f"SFA error: {e}", exc_info=True)
            return self._get_fallback_content(flower.name)

    def _get_fallback_content(self, flower_name: str) -> dict:
        """Fallback content when AI fails."""
        return {
            "meaning": {
                "why_this_flower": f"{flower_name} is a thoughtful choice for this occasion.",
                "symbolism": f"{flower_name} carries meaningful symbolism and emotional depth.",
                "meanings": ["Beauty", "Emotion", "Care", "Thoughtfulness"],
                "mood_intensity": 25,
                "mood_label": "Balanced",
            },
            "gifting": {
                "suitability": f"{flower_name} is appropriate for most occasions.",
                "suitability_status": "Safe choice",
                "risk_level": "Low",
                "risk_explanation": "Generally well-received.",
                "when_to_gift": ["Special occasions", "Celebrations", "Appreciation gestures"],
                "when_to_avoid": ["Formal business", "Very casual settings", "Unknown preferences"],
                "recipient_fit": [
                    {"type": "Partner", "justification": "Romantic and meaningful"},
                    {"type": "Friend", "justification": "Appropriate gesture"},
                ],
            },
            "context": {
                "summary": f"{flower_name} is versatile and carries positive symbolism.",
                "cultural": [
                    {"emoji": "🌍", "region": "Universal", "interpretation": "Symbol of beauty and emotion"}
                ],
                "relationships": [
                    {"type": "Close relationship", "guidance": "A meaningful gesture"}
                ],
                "timing": ["Spontaneous moments", "Planned celebrations", "After difficult times"],
                "misinterpretations": [
                    {"myth": "One flower fits all", "truth": "Context matters"}
                ],
            },
            "suggested_questions": [
                f"What pairs well with {flower_name}?",
                "How do I care for this flower?",
                "What message should I include?",
            ],
        }

    def _build_gifting_tab(self, gifting_data: dict) -> GiftingTab:
        """Build gifting tab from AI data."""
        # Map status to API enum
        status = gifting_data.get("suitability_status", "Safe choice")
        status_map = {
            "Safe choice": "excellent",
            "Caution": "moderate",
            "Not recommended": "not_recommended",
        }
        suitability_level = status_map.get(status, "good")

        suitability = GiftSuitabilityCard(
            level=suitability_level,
            description=gifting_data.get("suitability", "A thoughtful choice."),
        )

        # Map risk level
        risk_level_map = {
            "Low": "low",
            "Medium": "moderate",
            "High": "high",
        }
        risk_level = risk_level_map.get(gifting_data.get("risk_level", "Low"), "low")

        risk = EmotionalRiskCard(
            level=risk_level,
            description=gifting_data.get("risk_explanation", "Low risk."),
        )

        # Recipient fits
        recipients = []
        for r in gifting_data.get("recipient_fit", [])[:4]:
            recipients.append(RecipientFitItem(
                recipient_type=r.get("type", "General"),
                fit_level="excellent",
                note=r.get("justification"),
            ))

        if not recipients:
            recipients = [RecipientFitItem(recipient_type="General", fit_level="good", note=None)]

        # When to gift
        when_to_gift = []
        for w in gifting_data.get("when_to_gift", [])[:3]:
            when_to_gift.append(GiftingOccasionItem(
                occasion=w,
                suitability="excellent",
            ))

        if not when_to_gift:
            when_to_gift = [GiftingOccasionItem(occasion="Special occasions", suitability="good")]

        # When to avoid
        when_to_avoid = []
        for w in gifting_data.get("when_to_avoid", [])[:3]:
            when_to_avoid.append(GiftingOccasionItem(
                occasion=w,
                suitability="risky",
            ))

        if not when_to_avoid:
            when_to_avoid = [GiftingOccasionItem(occasion="Inappropriate settings", suitability="not_recommended")]

        return GiftingTab(
            suitability=suitability,
            emotional_risk=risk,
            recipient_fits=recipients,
            when_to_gift=when_to_gift,
            when_to_avoid=when_to_avoid,
        )

    def _build_context_tab(self, context_data: dict) -> ContextTab:
        """Build context tab from AI data."""
        summary = ContextSummary(
            text=context_data.get("summary", "A meaningful flower choice."),
        )

        # Cultural interpretations
        cultural_items = []
        for c in context_data.get("cultural", [])[:3]:
            cultural_items.append(CulturalInterpretationItem(
                emoji=c.get("emoji", "🌍"),
                culture=c.get("region", "Universal"),
                interpretation=c.get("interpretation", "Symbol of beauty"),
                sentiment="positive",
            ))

        if not cultural_items:
            cultural_items = [CulturalInterpretationItem(
                emoji="🌍", culture="Universal", interpretation="Symbol of beauty", sentiment="positive"
            )]

        # Relationships
        relationships = []
        for r in context_data.get("relationships", [])[:3]:
            relationships.append(RelationshipContextItem(
                relationship_type=r.get("type", "General"),
                appropriateness="appropriate",
                guidance=r.get("guidance", "A thoughtful gesture."),
            ))

        if not relationships:
            relationships = [RelationshipContextItem(
                relationship_type="General", appropriateness="appropriate", guidance="A thoughtful gesture."
            )]

        # Timing
        timings = []
        for t in context_data.get("timing", [])[:3]:
            timings.append(TimingSensitivityItem(
                timing=t,
                sensitivity="low",
                note="Consider the context.",
            ))

        if not timings:
            timings = [TimingSensitivityItem(
                timing="Any occasion", sensitivity="low", note="Generally appropriate."
            )]

        # Misinterpretations
        misinterpretations = []
        for m in context_data.get("misinterpretations", [])[:3]:
            misinterpretations.append(CommonMisinterpretationItem(
                misinterpretation=m.get("myth", "Common misconception"),
                clarification=m.get("truth", "The reality."),
            ))

        if not misinterpretations:
            misinterpretations = [CommonMisinterpretationItem(
                misinterpretation="One size fits all", clarification="Context matters."
            )]

        return ContextTab(
            summary=summary,
            cultural_interpretations=cultural_items,
            relationship_contexts=relationships,
            timing_sensitivities=timings,
            common_misinterpretations=misinterpretations,
        )

    def _build_error_payload(self, message: str) -> dict[str, Any]:
        """Build error payload."""
        return {
            "error": True,
            "message": message,
            "pipeline_version": "0.0.3",
        }
