"""
SFA Adapter - Symbolic Flower Agent (FINAL ASSEMBLER) - v0.0.1

Purpose:
THE ONLY COMPONENT that assembles the final UI payload.
Reads all context data and produces the FlowerCardPayload
that matches the iOS UI contract.

Input (from ctx):
- ALL preceding agent outputs
- User input and priors

Output (to ctx.ui_payload):
- Complete FlowerCardPayload dictionary

CRITICAL: This is the SINGLE SOURCE OF TRUTH for the iOS payload.
No other agent should modify ui_payload.
"""

from typing import Any

from backend.agents.base import BaseAgent
from backend.pipeline.context import PipelineContext
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


class SFAAdapter(BaseAgent):
    """
    Symbolic Flower Agent Adapter - FINAL ASSEMBLER.
    
    This agent is DIFFERENT from all others:
    - It runs LAST
    - It only READS from context (except ui_payload)
    - It produces the FINAL iOS payload
    
    The payload structure MUST match:
    - FSense/Features/FlowerCard/Models/Flower.swift
    - FSense/Features/FlowerCard/Models/GiftingInfo.swift
    - FSense/Features/FlowerCard/Models/ContextInfo.swift
    
    TODO v0.1.0:
    - Implement full payload assembly from real agent data
    - Add localization support
    - Add image URL resolution
    """
    
    name = "SFA"
    
    def run(self, ctx: PipelineContext) -> None:
        """
        Assemble the final UI payload for iOS.
        
        This method reads ALL context data and produces
        a structured FlowerCardPayload.
        """
        # Get primary flower candidate
        flower = ctx.get_selected_flower()
        
        if flower is None:
            ctx.ui_payload = self._build_error_payload("No flower candidate available")
            return
        
        # Build payload
        payload = self._assemble_payload(ctx, flower)
        
        # Validate and convert to dict
        ctx.ui_payload = payload.model_dump(mode="json")
    
    def _assemble_payload(self, ctx: PipelineContext, flower: Any) -> FlowerCardPayload:
        """
        Assemble complete FlowerCardPayload from context.
        
        TODO: Replace mock data with actual context data
        """
        # Header
        header = FlowerHeader(
            flower_id=flower.flower_id,
            name=flower.name,
            image_url=None,  # TODO: Resolve image URL
            image_asset="RedRose",  # TODO: Map to asset
        )
        
        # Meaning Tab
        meaning_tab = MeaningTab(
            meanings=flower.meanings[:5],  # Max 5 meanings
            symbolism=SymbolismCard(
                title="Symbolism",
                text="The red rose has been a symbol of love and passion for centuries, representing deep emotional connection and romantic devotion.",
            ),
            why_this_flower=WhyThisFlowerCard(
                title="Why This Flower",
                text="Perfect for expressing deep romantic feelings. The red rose speaks the universal language of love.",
                banner_image_asset="WhyFlowerBanner",
            ),
            mood_intensity=MoodIntensity(
                value=ctx.intensity.mood_intensity,
                label=ctx.intensity.intensity_label.replace("_", " ").title(),
            ),
        )
        
        # Gifting Tab
        gifting_tab = self._build_gifting_tab(ctx)
        
        # Context Tab
        context_tab = self._build_context_tab(ctx)
        
        # Ask AI Metadata
        ask_ai = AskAIMetadata(
            enabled=True,
            suggested_questions=[
                "What other flowers express similar emotions?",
                "How should I present this flower?",
                "What colors complement red roses?",
            ],
        )
        
        return FlowerCardPayload(
            header=header,
            meaning=meaning_tab,
            gifting=gifting_tab,
            context=context_tab,
            ask_ai=ask_ai,
            pipeline_version="0.0.1",
            request_id=ctx.request_id,
        )
    
    def _build_gifting_tab(self, ctx: PipelineContext) -> GiftingTab:
        """Build gifting tab from context."""
        # TODO: Use actual risk data from ctx.risks
        
        suitability = GiftSuitabilityCard(
            level="excellent",
            description="Suitable for sincere apologies and calm reconciliation",
        )
        
        risk = EmotionalRiskCard(
            level="low",
            description="Low risk of misinterpretation in delicate situations",
        )
        
        recipients = [
            RecipientFitItem(
                recipient_type="Romantic Partner",
                fit_level="excellent",
                note="Classic choice",
            ),
            RecipientFitItem(
                recipient_type="Spouse",
                fit_level="excellent",
                note=None,
            ),
            RecipientFitItem(
                recipient_type="New Crush",
                fit_level="risky",
                note="Consider lighter options first",
            ),
            RecipientFitItem(
                recipient_type="Friend",
                fit_level="not_recommended",
                note="May send wrong signals",
            ),
            RecipientFitItem(
                recipient_type="Family Member",
                fit_level="not_recommended",
                note="Choose different color",
            ),
        ]
        
        when_to_gift = [
            GiftingOccasionItem(occasion="Reconciliation", suitability="excellent"),
            GiftingOccasionItem(occasion="Apology", suitability="excellent"),
            GiftingOccasionItem(occasion="Anniversary", suitability="excellent"),
        ]
        
        when_to_avoid = [
            GiftingOccasionItem(occasion="First Date", suitability="risky"),
            GiftingOccasionItem(occasion="Business Meeting", suitability="not_recommended"),
            GiftingOccasionItem(occasion="Casual Friendship", suitability="not_recommended"),
        ]
        
        return GiftingTab(
            suitability=suitability,
            emotional_risk=risk,
            recipient_fits=recipients,
            when_to_gift=when_to_gift,
            when_to_avoid=when_to_avoid,
        )
    
    def _build_context_tab(self, ctx: PipelineContext) -> ContextTab:
        """Build context tab from context."""
        # Use cultural insights from CRI
        cultural_items = [
            CulturalInterpretationItem(
                emoji=ci.emoji,
                culture=ci.culture,
                interpretation=ci.interpretation,
                sentiment=ci.sentiment,
            )
            for ci in ctx.cultural_insights.cultural_insights
        ]
        
        # Fallback if empty
        if not cultural_items:
            cultural_items = [
                CulturalInterpretationItem(
                    emoji="🌍",
                    culture="Universal",
                    interpretation="Symbol of love and affection",
                    sentiment="positive",
                ),
            ]
        
        summary = ContextSummary(
            text="Best suited for emotionally sensitive situations where subtlety and restraint are important.",
        )
        
        relationships = [
            RelationshipContextItem(
                relationship_type="New Relationship",
                appropriateness="neutral",
                guidance="May be too intense for early dating stages",
            ),
            RelationshipContextItem(
                relationship_type="Established Relationship",
                appropriateness="highly_appropriate",
                guidance="Perfect expression of ongoing love",
            ),
            RelationshipContextItem(
                relationship_type="Professional",
                appropriateness="inappropriate",
                guidance="Could be misinterpreted; choose neutral flowers",
            ),
        ]
        
        timings = [
            TimingSensitivityItem(
                timing="After an argument",
                sensitivity="high",
                note="May seem like an easy fix rather than genuine apology",
            ),
            TimingSensitivityItem(
                timing="Unexpected moments",
                sensitivity="low",
                note="Spontaneous gifts often have the greatest impact",
            ),
            TimingSensitivityItem(
                timing="Public settings",
                sensitivity="moderate",
                note="Consider if recipient would be comfortable",
            ),
        ]
        
        misinterpretations = [
            CommonMisinterpretationItem(
                misinterpretation="Only for Valentine's Day",
                clarification="Appropriate year-round for romantic partners and special moments",
            ),
            CommonMisinterpretationItem(
                misinterpretation="Any number is fine",
                clarification="Different quantities carry different meanings in some cultures",
            ),
            CommonMisinterpretationItem(
                misinterpretation="Too cliché to gift",
                clarification="Classic choice that remains meaningful when given sincerely",
            ),
        ]
        
        return ContextTab(
            summary=summary,
            cultural_interpretations=cultural_items,
            relationship_contexts=relationships,
            timing_sensitivities=timings,
            common_misinterpretations=misinterpretations,
        )
    
    def _build_error_payload(self, message: str) -> dict[str, Any]:
        """Build error payload when assembly fails."""
        return {
            "error": True,
            "message": message,
            "pipeline_version": "0.0.1",
        }
