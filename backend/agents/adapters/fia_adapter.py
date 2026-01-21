"""
FIA Adapter - Flower Intent Agent - v0.0.1

Purpose:
Analyzes user input to determine the primary intent behind
the flower query/request.

Input (from ctx):
- user_input
- priors (optional context)

Output (to ctx.intent):
- primary_intent
- confidence
- sub_intents
- raw_output

NOT IMPLEMENTED IN v0.0.1 - Placeholder only.
"""

from backend.agents.base import BaseAgent
from backend.pipeline.context import PipelineContext, IntentData


class FIAAdapter(BaseAgent):
    """
    Flower Intent Agent Adapter.
    
    Determines what the user wants to achieve with flowers:
    - Express love/romance
    - Apologize
    - Celebrate
    - Comfort
    - Thank
    - etc.
    
    TODO v0.1.0:
    - Implement LLM-based intent classification
    - Add multi-intent detection
    - Add confidence calibration
    """
    
    name = "FIA"
    
    def run(self, ctx: PipelineContext) -> None:
        """
        Analyze user input and extract intent.
        
        TODO: Implement actual intent analysis
        """
        # Placeholder implementation for v0.0.1
        ctx.intent = IntentData(
            primary_intent="express_love",  # TODO: Detect from input
            confidence=0.0,
            sub_intents=[],
            raw_output={"status": "not_implemented", "version": "0.0.1"},
        )
