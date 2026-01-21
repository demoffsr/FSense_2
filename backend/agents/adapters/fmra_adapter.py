"""
FMRA Adapter - Flower Matching & Ranking Agent - v0.0.1

Purpose:
Selects and ranks flower candidates based on all preceding
agent analyses (intent, emotion, relationship).

Input (from ctx):
- intent
- emotions
- relationship
- priors

Output (to ctx.candidates):
- candidates (list of FlowerCandidate)
- total_considered
- ranking_criteria
- raw_output

NOT IMPLEMENTED IN v0.0.1 - Placeholder only.
"""

from backend.agents.base import BaseAgent
from backend.pipeline.context import (
    PipelineContext,
    CandidatesData,
    FlowerCandidate,
)


class FMRAAdapter(BaseAgent):
    """
    Flower Matching & Ranking Agent Adapter.
    
    Core recommendation engine:
    - Matches flowers to emotional context
    - Ranks by relevance and appropriateness
    - Considers cultural factors
    - Applies user preferences
    
    TODO v0.1.0:
    - Implement flower database integration
    - Add semantic matching
    - Add personalization layer
    """
    
    name = "FMRA"
    
    def run(self, ctx: PipelineContext) -> None:
        """
        Select and rank flower candidates.
        
        TODO: Implement actual flower matching
        """
        # Placeholder implementation for v0.0.1
        # Returns a single mock candidate
        mock_candidate = FlowerCandidate(
            flower_id="red_rose_001",
            name="Red Rose",
            match_score=0.95,
            match_reasons=["Classic symbol of love", "High emotional impact"],
            meanings=["Love", "Passion", "Romance", "Desire", "Beauty"],
        )
        
        ctx.candidates = CandidatesData(
            candidates=[mock_candidate],
            total_considered=1,
            ranking_criteria=["emotional_match", "cultural_fit", "availability"],
            raw_output={"status": "not_implemented", "version": "0.0.1"},
        )
