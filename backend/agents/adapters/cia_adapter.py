"""
CIA Adapter - Context Intensity Agent - v0.0.1

Purpose:
Determines the emotional intensity level appropriate for
the selected flower(s) based on context.

Input (from ctx):
- emotions
- relationship
- candidates

Output (to ctx.intensity):
- mood_intensity (0.0 - 1.0)
- intensity_label
- intensity_factors
- raw_output

NOT IMPLEMENTED IN v0.0.1 - Placeholder only.
"""

from backend.agents.base import BaseAgent
from backend.pipeline.context import PipelineContext, IntensityData


class CIAAdapter(BaseAgent):
    """
    Context Intensity Agent Adapter.
    
    Calibrates emotional intensity:
    - Very Low (0.0-0.2): Subtle, understated
    - Low (0.2-0.4): Gentle, friendly
    - Balanced (0.4-0.6): Appropriate, neutral
    - High (0.6-0.8): Strong, passionate
    - Very High (0.8-1.0): Intense, overwhelming
    
    TODO v0.1.0:
    - Implement intensity calculation
    - Add relationship-based adjustment
    - Add occasion-based calibration
    """
    
    name = "CIA"
    
    def run(self, ctx: PipelineContext) -> None:
        """
        Calculate appropriate mood intensity.
        
        TODO: Implement actual intensity analysis
        """
        # Placeholder implementation for v0.0.1
        # Default to emotion intensity if available
        intensity = ctx.emotions.emotion_intensity if ctx.emotions else 0.5
        
        # Determine label
        if intensity < 0.2:
            label = "very_low"
        elif intensity < 0.4:
            label = "low"
        elif intensity < 0.6:
            label = "balanced"
        elif intensity < 0.8:
            label = "high"
        else:
            label = "very_high"
        
        ctx.intensity = IntensityData(
            mood_intensity=intensity,
            intensity_label=label,
            intensity_factors=["emotion_level"],
            raw_output={"status": "not_implemented", "version": "0.0.1"},
        )
