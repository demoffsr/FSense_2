"""
SFA Adapter - Symbolic Flower Agent (FINAL ASSEMBLER) - v4 (Multi-Candidate)

Purpose:
THE ONLY COMPONENT that assembles the final UI payload.
Uses comprehensive AI prompt with full pipeline context from all 10 agents:
FIA, EIA, RIL, FMRA, CIA, AITB, RFFA, CRI, SRFL → SFA

Now supports alternative flower recommendations from FMRA.

Based on: symbolic_flower_agent_v3.py
"""

import logging
from typing import Any, Tuple, Optional

from backend.agents.base import BaseAgent
from backend.pipeline.context import PipelineContext
from backend.core.ai_client import get_ai_client_fast, AIClientError
from backend.core.console_logger import get_console_logger
from backend.services.image_service import ImageService
from backend.schemas.flower_card_payload import (
    FlowerCardPayload,
    FlowerHeader,
    AlternativeFlower,
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
    PricingInfo,
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

Integration Guidelines (IMPORTANT - incorporate these signals):
- If risk_level = "high" → suitability_status MUST be "Caution" or "Not recommended", explain risk
- If cultural_warnings present → include them in "when_to_avoid" and cultural interpretations
- If is_making_amends = true → emphasize reconciliation, sincerity, healing in tone
- If relationship_type = "professional" → keep formal, avoid romantic language
- If adaptive_tone = "apologetic" → use softer, more sincere language throughout
- If intensity_label = "very_low" or "low" → keep descriptions gentle and understated
- If intensity_label = "high" or "very_high" → allow more expressive, passionate language

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

    def __init__(self):
        super().__init__()
        self.image_service = ImageService()

    def run(self, ctx: PipelineContext) -> None:
        """Assemble the final UI payload."""
        flower = ctx.get_selected_flower()

        if flower is None:
            ctx.ui_payload = self._build_error_payload("No flower selected")
            return

        payload = self._assemble_payload(ctx, flower)
        ctx.ui_payload = payload.model_dump(mode="json", by_alias=True)

        # Debug: log actual JSON keys
        header_keys = list(ctx.ui_payload.get("header", {}).keys())
        header_data = ctx.ui_payload.get("header", {})
        logger.debug(f"JSON header keys: {header_keys}")
        logger.debug(f"JSON imageUrl: {header_data.get('imageUrl')}")
        logger.debug(f"JSON imageCacheKey: {header_data.get('imageCacheKey')}")

        # Console output
        console = get_console_logger()
        pricing_info = f"{payload.pricing.price_tier_label} ({payload.pricing.estimated_range})" if payload.pricing else "N/A"
        console.agent_result("SFA", {
            "Final Flower": payload.header.name,
            "Meanings": payload.meaning.meanings[:4],
            "Mood Intensity": f"{payload.meaning.mood_intensity.value:.2f} ({payload.meaning.mood_intensity.label})",
            "Price Tier": pricing_info,
            "Suitability": payload.gifting.suitability.level,
            "Risk Level": payload.gifting.emotional_risk.level,
            "Alternatives": [f"{a.name} ({a.confidence:.0%})" for a in payload.alternatives],
            "Pipeline Version": payload.pipeline_version,
        })

    def _assemble_payload(self, ctx: PipelineContext, flower: Any) -> FlowerCardPayload:
        """Assemble complete payload using AI."""
        # Generate AI content
        ai_content = self._generate_ai_content(ctx, flower)

        # Get or initiate image generation
        image_url, cache_key = self._get_or_generate_image(flower.name, ctx)

        logger.debug(f"Returning to payload - imageUrl: {image_url}, imageCacheKey: {cache_key}")

        # Build header
        header = FlowerHeader(
            flower_id=flower.flower_id,
            name=flower.name,
            image_url=image_url,  # May be None if generating
            image_asset=flower.name.replace(" ", ""),
            image_cache_key=cache_key,
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

        # Build pricing info
        pricing = self._build_pricing_info(ctx, flower)
        price_tier = getattr(flower, "price_tier", None) or "mid"

        # Ask AI metadata with budget question for premium flowers
        suggested_questions = ai_content.get("suggested_questions", [
            f"What other flowers are similar to {flower.name}?",
            "How should I present this flower?",
            "What message should I include?",
        ])[:3]

        # Add budget question for premium flowers if user hasn't specified budget
        if price_tier == "premium" and not ctx.priors.budget_range:
            suggested_questions = ["What's your budget for this gift?"] + suggested_questions[:2]

        ask_ai = AskAIMetadata(
            enabled=True,
            suggested_questions=suggested_questions,
        )

        # Build alternatives from remaining candidates (skip primary)
        alternatives = self._build_alternatives(ctx, flower.flower_id)

        return FlowerCardPayload(
            header=header,
            meaning=meaning_tab,
            gifting=gifting_tab,
            context=context_tab,
            pricing=pricing,
            alternatives=alternatives,
            ask_ai=ask_ai,
            pipeline_version="0.5.0",
            request_id=ctx.request_id,
        )

    def _normalize_intensity(self, value: int) -> float:
        """Convert 15-40 scale to 0.0-1.0."""
        # 15-40 range → 0.0-1.0
        clamped = max(15, min(40, value))
        return (clamped - 15) / 25.0

    def _build_alternatives(self, ctx: PipelineContext, primary_flower_id: str) -> list[AlternativeFlower]:
        """
        Build list of alternative flower recommendations.

        Takes remaining candidates from FMRA (after primary) and converts
        them to AlternativeFlower objects for the UI.

        Args:
            ctx: Pipeline context with candidates
            primary_flower_id: ID of primary flower to exclude

        Returns:
            List of 0-4 AlternativeFlower objects
        """
        alternatives = []

        # No candidates at all
        if not ctx.candidates or not ctx.candidates.candidates:
            logger.debug("No candidates at all")
            return alternatives

        # Only 1 candidate - generate fallback alternatives from database
        if len(ctx.candidates.candidates) == 1:
            logger.debug("Only 1 candidate - generating fallback alternatives")
            return self._generate_fallback_alternatives(ctx, primary_flower_id)

        # Skip the primary flower, take up to 4 alternatives
        for candidate in ctx.candidates.candidates[1:5]:
            if candidate.flower_id == primary_flower_id:
                continue

            # Skip low-quality alternatives
            if candidate.match_score < 0.4:
                logger.debug(f"Skipping low-score alternative: {candidate.name} ({candidate.match_score:.2f})")
                continue

            # Get brief reason (first reason or default)
            brief_reason = "Good alternative"
            if candidate.match_reasons:
                # Filter out diversity penalty notes
                reasons = [r for r in candidate.match_reasons if not r.startswith("diversity_adjusted")]
                if reasons:
                    brief_reason = reasons[0]

            alternatives.append(AlternativeFlower(
                flower_id=candidate.flower_id,
                name=candidate.name,
                image_asset=candidate.name.replace(" ", ""),
                image_url=None,  # iOS will use local asset
                confidence=candidate.match_score,
                brief_reason=brief_reason,
            ))

            logger.debug(f"Added alternative: {candidate.name} ({candidate.match_score:.2f})")

        logger.info(f"Built {len(alternatives)} alternative flowers")
        return alternatives

    def _generate_fallback_alternatives(self, ctx: PipelineContext, primary_id: str) -> list[AlternativeFlower]:
        """
        Generate alternatives when FMRA provided only 1 candidate.

        Queries the flower database for flowers matching the detected emotion.

        Args:
            ctx: Pipeline context
            primary_id: ID of primary flower to exclude

        Returns:
            List of 0-4 AlternativeFlower objects
        """
        from backend.database.flower_database import get_flowers_by_emotion

        alternatives = []
        emotion = ctx.emotions.primary_emotion.lower() if ctx.emotions and ctx.emotions.primary_emotion else "love"

        try:
            # Get 6 flowers for this emotion (to have buffer after excluding primary)
            flowers = get_flowers_by_emotion(emotion, top_n=6)

            for flower in flowers:
                if flower["flower_id"] == primary_id:
                    continue
                if len(alternatives) >= 4:
                    break

                flower_name = flower.get("name", flower["flower_id"].replace("_", " ").title())

                alternatives.append(AlternativeFlower(
                    flower_id=flower["flower_id"],
                    name=flower_name,
                    image_asset=flower_name.replace(" ", ""),
                    image_url=None,
                    confidence=flower.get("match_score", 0.8),
                    brief_reason=f"Also expresses {emotion}",
                ))

            logger.info(f"Generated {len(alternatives)} fallback alternatives for emotion '{emotion}'")

        except Exception as e:
            logger.warning(f"Failed to generate fallback alternatives: {e}")

        return alternatives

    def _extract_emotion_context(self, ctx: PipelineContext) -> str:
        """
        Extract emotion context from pipeline for cache key.

        Strategy: Use primary emotion + intent
        Examples: "love", "apology", "celebration", "sympathy"

        Args:
            ctx: Pipeline context with all agent data

        Returns:
            Normalized emotion context string
        """
        parts = []

        if ctx.emotions and ctx.emotions.primary_emotion:
            parts.append(ctx.emotions.primary_emotion.lower())

        if ctx.intent and ctx.intent.primary_intent:
            parts.append(ctx.intent.primary_intent.lower())

        # Fallback
        if not parts:
            return "general"

        # Join with underscore (max 2 components)
        return "_".join(parts[:2])

    def _get_or_generate_image(
        self,
        flower_name: str,
        ctx: PipelineContext,
    ) -> Tuple[Optional[str], str]:
        """
        Get cached image or initiate background generation.

        Args:
            flower_name: Name of the flower
            ctx: Pipeline context

        Returns:
            (image_url, cache_key) tuple
            - image_url: Optional[str] - URL if completed, None if generating
            - cache_key: str - for polling
        """
        logger.debug(f"_get_or_generate_image called for: {flower_name}")

        # Extract emotion context from pipeline
        emotion_context = self._extract_emotion_context(ctx)

        # If request came with a user image, force new generation
        # (don't use user's photo in card - generate clean studio image)
        if ctx.image_base64:
            emotion_context = f"vision_{emotion_context}"
            logger.info(f"Image request detected - forcing generation with context: {emotion_context}")

        logger.debug(f"Extracted emotion_context: {emotion_context}")

        # Check cache or create entry
        cache_key, image_url, status = self.image_service.get_or_create_entry(
            flower_name=flower_name,
            emotion_context=emotion_context,
        )

        logger.debug(f"Generated cache_key for {flower_name} ({emotion_context}): {cache_key}")

        if status == "completed":
            # Cache hit - return immediately
            logger.info(f"Image cache hit: {flower_name} ({emotion_context})")
            return (image_url, cache_key)

        elif status == "pending":
            # Cache miss - initiate background generation
            logger.info(f"Image cache miss: {flower_name} ({emotion_context}) - initiating generation")

            # Add to background tasks queue
            # Import here to avoid circular dependency
            try:
                from backend.main import add_background_task
                add_background_task(
                    self.image_service.generate_image_sync,
                    flower_name,
                    emotion_context,
                    cache_key,
                )
            except Exception as e:
                logger.error(f"Failed to initiate background image generation: {e}")

        # Return None - iOS will use local asset and poll for updates
        return (None, cache_key)

    def _generate_ai_content(self, ctx: PipelineContext, flower: Any) -> dict:
        """Generate all content sections using AI with full pipeline context."""
        try:
            client = get_ai_client_fast()

            # Build comprehensive context from all agents
            context_parts = []

            # === FIA + EIA ===
            if ctx.intent:
                intent_data = ctx.intent.raw_output
                context_parts.append(f"Intent: {ctx.intent.primary_intent}")
                context_parts.append(f"- Occasion: {intent_data.get('occasion', 'general')}")
                context_parts.append(f"- Recipient: {intent_data.get('recipient', 'unspecified')}")
                context_parts.append(f"- Tone: {intent_data.get('tone', 'neutral')}")

            if ctx.emotions:
                context_parts.append(f"\nEmotions: {ctx.emotions.primary_emotion} (intensity: {ctx.emotions.emotion_intensity:.2f})")
                context_parts.append(f"- Emotional tone: {ctx.emotions.emotional_tone}")
                if ctx.emotions.secondary_emotions:
                    context_parts.append(f"- Secondary: {', '.join(ctx.emotions.secondary_emotions)}")

            # === RIL ===
            if ctx.relationship:
                rel_data = ctx.relationship.raw_output
                context_parts.append(f"\nRelationship: {ctx.relationship.relationship_type}")
                context_parts.append(f"- Stage: {rel_data.get('relationship_stage', 'unknown')}")
                context_parts.append(f"- Tone: {rel_data.get('relationship_tone', 'neutral')}")
                context_parts.append(f"- Intimacy: {ctx.relationship.intimacy_level:.2f}")

            # === CIA ===
            if ctx.intensity:
                context_parts.append(f"\nCalculated intensity: {ctx.intensity.mood_intensity:.2f} ({ctx.intensity.intensity_label})")
                if ctx.intensity.intensity_factors:
                    context_parts.append(f"- Factors: {', '.join(ctx.intensity.intensity_factors)}")

            # === AITB ===
            if ctx.adaptive:
                context_parts.append(f"\nAdaptive tone: {ctx.adaptive.tone}")
                context_parts.append(f"- Voice style: {ctx.adaptive.voice_style}")
                context_parts.append(f"- Formality: {ctx.adaptive.formality}")
                if ctx.adaptive.personalization_hints:
                    context_parts.append(f"- Hints: {', '.join(ctx.adaptive.personalization_hints)}")

            # === RFFA ===
            if ctx.risks:
                context_parts.append(f"\nRisk assessment: {ctx.risks.overall_risk_level}")
                context_parts.append(f"- Fit: {ctx.risks.fit_assessment}")
                if ctx.risks.risks:
                    context_parts.append(f"- Identified risks: {len(ctx.risks.risks)}")
                    for risk in ctx.risks.risks[:2]:
                        context_parts.append(f"  * {risk.risk_type} ({risk.severity}): {risk.description}")

            # === CRI ===
            if ctx.cultural_insights:
                if ctx.cultural_insights.warnings:
                    context_parts.append(f"\nCultural warnings: {', '.join(ctx.cultural_insights.warnings)}")
                cultural_raw = ctx.cultural_insights.raw_output
                if cultural_raw.get("traditional_symbolism"):
                    context_parts.append(f"- Traditional: {cultural_raw['traditional_symbolism']}")
                if cultural_raw.get("modern_symbolism"):
                    context_parts.append(f"- Modern: {cultural_raw['modern_symbolism']}")

            # === SRFL ===
            if ctx.reflection:
                context_parts.append(f"\nReflection: confidence={ctx.reflection.confidence_score:.2f}, consistent={ctx.reflection.consistency_check}")
                if ctx.reflection.suggestions:
                    context_parts.append(f"- Suggestion: {ctx.reflection.suggestions[0]}")

            context_summary = "\n".join(context_parts)

            # Build user prompt with comprehensive context
            user_prompt = f"""Flower: {flower.name}
Region: {ctx.region.upper()}

Pipeline Analysis:
{context_summary}

User's original message: "{ctx.user_input}"

Generate UI content that reflects this rich analysis. Use the calculated intensity value ({ctx.intensity.mood_intensity if ctx.intensity else 0.5}) to determine the mood intensity (convert 0.0-1.0 to 15-40 scale). Incorporate the emotional tone ({ctx.adaptive.tone if ctx.adaptive else 'warm'}), relationship context, and cultural insights into your descriptions."""

            response = client.complete_json(
                prompt=user_prompt,
                system_prompt=CONTENT_GENERATION_PROMPT,
                temperature=0.4,  # Lower for consistency
                max_tokens=1500,
            )

            # Apply calculated intensity from CIA if available
            if ctx.intensity and "meaning" in response:
                # Convert 0.0-1.0 to 15-40 scale
                calculated_value = int(15 + (ctx.intensity.mood_intensity * 25))
                response["meaning"]["mood_intensity"] = calculated_value
                response["meaning"]["mood_label"] = self._get_intensity_label(calculated_value)
                logger.info(f"SFA applied calculated intensity: {calculated_value} from CIA value {ctx.intensity.mood_intensity:.2f}")

            # Debug logging
            meaning_data = response.get("meaning", {})
            logger.debug(f"SFA AI returned meanings: {meaning_data.get('meanings')}")
            logger.debug(f"SFA AI returned mood: {meaning_data.get('mood_intensity')} ({meaning_data.get('mood_label')})")

            return response

        except AIClientError as e:
            logger.error(f"SFA AI content generation failed: {e}")
            return self._get_fallback_content(flower.name, flower, ctx)

        except Exception as e:
            logger.error(f"SFA error: {e}", exc_info=True)
            return self._get_fallback_content(flower.name, flower, ctx)

    def _get_intensity_label(self, value: int) -> str:
        """Get intensity label for 15-40 scale."""
        if value <= 20:
            return "Very Low"
        elif value <= 26:
            return "Low"
        elif value <= 32:
            return "Balanced"
        elif value <= 37:
            return "High"
        else:
            return "Very High"

    def _get_fallback_content(self, flower_name: str, flower: Any = None, ctx: PipelineContext = None) -> dict:
        """Context-aware fallback content when AI fails."""
        # Use flower's database meanings if available
        meanings = ["Beauty", "Emotion", "Care", "Thoughtfulness"]
        if flower and hasattr(flower, 'meanings') and flower.meanings:
            meanings = flower.meanings[:4]

        # Contextual why_this_flower
        why_text = f"{flower_name} is a thoughtful choice for this occasion."
        if ctx and ctx.intent and ctx.intent.raw_output:
            occasion = ctx.intent.raw_output.get("occasion", "")
            if occasion == "apology":
                why_text = f"{flower_name} symbolizes sincerity and the desire for reconciliation."
            elif occasion == "anniversary":
                why_text = f"{flower_name} celebrates your special bond and lasting love."
            elif occasion == "sympathy":
                why_text = f"{flower_name} offers comfort and expresses heartfelt condolences."
            elif occasion == "birthday":
                why_text = f"{flower_name} adds joy and warmth to birthday celebrations."
            elif occasion == "thank you":
                why_text = f"{flower_name} beautifully conveys gratitude and appreciation."

        # Calculate mood intensity from CIA if available
        mood_intensity = 25
        mood_label = "Balanced"
        if ctx and ctx.intensity:
            mood_intensity = int(15 + (ctx.intensity.mood_intensity * 25))
            mood_label = self._get_intensity_label(mood_intensity)

        # Adjust suitability based on RFFA
        suitability_status = "Safe choice"
        risk_level = "Low"
        risk_explanation = "Generally well-received."
        if ctx and ctx.risks:
            if ctx.risks.overall_risk_level == "high":
                suitability_status = "Caution"
                risk_level = "High"
                risk_explanation = ctx.risks.fit_assessment or "Review context before gifting."
            elif ctx.risks.overall_risk_level == "medium":
                suitability_status = "Safe choice"
                risk_level = "Medium"
                risk_explanation = ctx.risks.fit_assessment or "Generally appropriate with some considerations."

        return {
            "meaning": {
                "why_this_flower": why_text,
                "symbolism": f"{flower_name} carries meaningful symbolism and emotional depth.",
                "meanings": meanings,
                "mood_intensity": mood_intensity,
                "mood_label": mood_label,
            },
            "gifting": {
                "suitability": f"{flower_name} is appropriate for this context.",
                "suitability_status": suitability_status,
                "risk_level": risk_level,
                "risk_explanation": risk_explanation,
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
            "pipeline_version": "0.4.0",
        }

    # ─────────────────────────────────────────────────────────────────────
    # PRICING HELPERS
    # ─────────────────────────────────────────────────────────────────────

    def _build_pricing_info(self, ctx: PipelineContext, flower: Any) -> PricingInfo:
        """Build pricing information for the recommended flower."""
        price_tier = getattr(flower, "price_tier", None) or "mid"

        return PricingInfo(
            price_tier=price_tier,
            price_tier_label=self._get_tier_label(price_tier),
            estimated_range=self._get_price_range(price_tier, ctx.region),
            budget_warning=self._get_budget_warning(price_tier, ctx.priors.budget_range),
        )

    def _get_tier_label(self, tier: str) -> str:
        """Get human-readable price tier label."""
        labels = {
            "budget": "Budget-friendly",
            "mid": "Mid-range",
            "premium": "Premium",
        }
        return labels.get(tier, "Mid-range")

    def _get_price_range(self, tier: str, region: str) -> str:
        """Get estimated price range for tier and region."""
        ranges = {
            "US": {"budget": "$20-40", "mid": "$40-80", "premium": "$80-150+"},
            "CA": {"budget": "CA$25-50", "mid": "CA$50-100", "premium": "CA$100-200+"},
            "RU": {"budget": "1500-3000 ₽", "mid": "3000-6000 ₽", "premium": "6000-15000 ₽"},
        }
        region_upper = region.upper()
        region_ranges = ranges.get(region_upper, ranges["US"])
        return region_ranges.get(tier, region_ranges["mid"])

    def _get_budget_warning(self, tier: str, user_budget: Optional[str]) -> Optional[str]:
        """Get budget warning if flower price doesn't match user's budget."""
        if tier == "premium":
            if user_budget in ["modest", "budget", "low", "cheap"]:
                return "This flower tends to be expensive. Consider the alternatives below for budget-friendly options."
            return "Premium flower - typically higher priced"
        elif tier == "budget" and user_budget in ["premium", "high", "expensive", "luxury"]:
            return "Budget-friendly option - premium alternatives available"
        return None
