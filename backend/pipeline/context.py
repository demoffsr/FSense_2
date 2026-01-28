"""
PipelineContext - v0.0.1

The SINGLE SOURCE OF TRUTH for all pipeline data.
This object flows through the entire pipeline and is mutated by agents.

Design Principles:
1. All intermediate and final data lives here
2. Agents read from and write to context
3. No agent-to-agent direct communication
4. Final assembler (SFA) reads everything to build UI payload
"""

from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime
import uuid


@dataclass
class UserPriors:
    """User-provided context and preferences."""
    relationship_type: Optional[str] = None
    occasion: Optional[str] = None
    recipient_info: Optional[str] = None
    budget_range: Optional[str] = None
    color_preferences: list[str] = field(default_factory=list)
    cultural_context: Optional[str] = None


@dataclass
class IntentData:
    """Output from FIA (Flower Intent Agent)."""
    primary_intent: str = ""
    confidence: float = 0.0
    sub_intents: list[str] = field(default_factory=list)
    raw_output: dict[str, Any] = field(default_factory=dict)


@dataclass
class EmotionData:
    """Output from EIA (Emotion Intelligence Agent)."""
    primary_emotion: str = ""
    emotion_intensity: float = 0.0
    secondary_emotions: list[str] = field(default_factory=list)
    emotional_tone: str = ""
    raw_output: dict[str, Any] = field(default_factory=dict)


@dataclass
class RelationshipData:
    """Output from RIL (Relationship Intelligence Layer)."""
    relationship_type: str = ""
    intimacy_level: float = 0.0
    formality_level: float = 0.0
    power_dynamic: str = ""
    raw_output: dict[str, Any] = field(default_factory=dict)


@dataclass
class FlowerCandidate:
    """Single flower candidate from FMRA."""
    flower_id: str = ""
    name: str = ""
    match_score: float = 0.0
    match_reasons: list[str] = field(default_factory=list)
    meanings: list[str] = field(default_factory=list)


@dataclass
class CandidatesData:
    """Output from FMRA (Flower Matching & Ranking Agent)."""
    candidates: list[FlowerCandidate] = field(default_factory=list)
    total_considered: int = 0
    ranking_criteria: list[str] = field(default_factory=list)
    raw_output: dict[str, Any] = field(default_factory=dict)


@dataclass
class IntensityData:
    """Output from CIA (Context Intensity Agent)."""
    mood_intensity: float = 0.5
    intensity_label: str = "balanced"
    intensity_factors: list[str] = field(default_factory=list)
    raw_output: dict[str, Any] = field(default_factory=dict)


@dataclass
class AdaptiveData:
    """Output from AITB (Adaptive Intelligence & Tone Builder)."""
    tone: str = ""
    voice_style: str = ""
    formality: str = ""
    personalization_hints: list[str] = field(default_factory=list)
    raw_output: dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskItem:
    """Single risk identified by RFFA."""
    risk_type: str = ""
    severity: str = ""
    description: str = ""
    mitigation: str = ""


@dataclass
class RisksData:
    """Output from RFFA (Risk & Fit Assessment Agent)."""
    overall_risk_level: str = "low"
    risks: list[RiskItem] = field(default_factory=list)
    fit_assessment: str = ""
    raw_output: dict[str, Any] = field(default_factory=dict)


@dataclass
class CulturalInsight:
    """Single cultural interpretation."""
    culture: str = ""
    emoji: str = ""
    interpretation: str = ""
    sentiment: str = "neutral"


@dataclass
class CulturalData:
    """Output from CRI (Cultural & Regional Intelligence)."""
    detected_region: str = ""
    cultural_insights: list[CulturalInsight] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    raw_output: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReflectionData:
    """Output from SRFL (Self-Reflection Layer)."""
    confidence_score: float = 0.0
    consistency_check: bool = True
    gaps_identified: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    raw_output: dict[str, Any] = field(default_factory=dict)


@dataclass
class TimingRecord:
    """Timing record for a single agent."""
    agent_name: str = ""
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_ms: int = 0
    status: str = "pending"  # pending, running, completed, failed


@dataclass
class PipelineFlags:
    """Pipeline execution flags and metadata."""
    is_debug: bool = False
    skip_cultural: bool = False
    force_single_candidate: bool = False
    include_raw_outputs: bool = False


@dataclass
class PipelineContext:
    """
    SINGLE SOURCE OF TRUTH for the entire pipeline.
    
    This object is created at pipeline start and flows through every agent.
    Each agent reads what it needs and writes its output section.
    
    Sections:
    1. Request metadata (immutable after creation)
    2. User input (immutable after creation)
    3. Agent outputs (mutable by respective agents)
    4. Final payload (written only by SFA)
    5. Execution metadata (timings, flags)
    """
    
    # ─────────────────────────────────────────────────────────────────────
    # 1. REQUEST METADATA (set at creation, never modified)
    # ─────────────────────────────────────────────────────────────────────
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # ─────────────────────────────────────────────────────────────────────
    # 2. USER INPUT (set at creation, never modified)
    # ─────────────────────────────────────────────────────────────────────
    user_input: str = ""
    region: str = "us"
    priors: UserPriors = field(default_factory=UserPriors)
    
    # ─────────────────────────────────────────────────────────────────────
    # 3. AGENT OUTPUTS (each agent writes to its section)
    # ─────────────────────────────────────────────────────────────────────
    
    # FIA → Flower Intent Agent
    intent: IntentData = field(default_factory=IntentData)
    
    # EIA → Emotion Intelligence Agent
    emotions: EmotionData = field(default_factory=EmotionData)
    
    # RIL → Relationship Intelligence Layer
    relationship: RelationshipData = field(default_factory=RelationshipData)
    
    # FMRA → Flower Matching & Ranking Agent
    candidates: CandidatesData = field(default_factory=CandidatesData)
    
    # CIA → Context Intensity Agent
    intensity: IntensityData = field(default_factory=IntensityData)
    
    # AITB → Adaptive Intelligence & Tone Builder
    adaptive: AdaptiveData = field(default_factory=AdaptiveData)
    
    # RFFA → Risk & Fit Assessment Agent
    risks: RisksData = field(default_factory=RisksData)
    
    # CRI → Cultural & Regional Intelligence
    cultural_insights: CulturalData = field(default_factory=CulturalData)
    
    # SRFL → Self-Reflection Layer
    reflection: ReflectionData = field(default_factory=ReflectionData)
    
    # ─────────────────────────────────────────────────────────────────────
    # 4. FINAL UI PAYLOAD (written ONLY by SFA)
    # ─────────────────────────────────────────────────────────────────────
    ui_payload: Optional[dict[str, Any]] = None
    
    # ─────────────────────────────────────────────────────────────────────
    # 5. EXECUTION METADATA
    # ─────────────────────────────────────────────────────────────────────
    timings: list[TimingRecord] = field(default_factory=list)
    flags: PipelineFlags = field(default_factory=PipelineFlags)
    errors: list[str] = field(default_factory=list)
    
    # ─────────────────────────────────────────────────────────────────────
    # HELPER METHODS
    # ─────────────────────────────────────────────────────────────────────
    
    def get_selected_flower(self) -> Optional[FlowerCandidate]:
        """Get the top-ranked flower candidate."""
        if self.candidates.candidates:
            return self.candidates.candidates[0]
        return None
    
    def add_error(self, error: str) -> None:
        """Record an error that occurred during pipeline execution."""
        self.errors.append(f"[{datetime.utcnow().isoformat()}] {error}")
    
    def start_timing(self, agent_name: str) -> None:
        """Record agent execution start."""
        self.timings.append(TimingRecord(
            agent_name=agent_name,
            started_at=datetime.utcnow(),
            status="running"
        ))
    
    def end_timing(self, agent_name: str, status: str = "completed") -> None:
        """Record agent execution end."""
        for record in self.timings:
            if record.agent_name == agent_name and record.status == "running":
                record.finished_at = datetime.utcnow()
                record.status = status
                if record.started_at:
                    delta = record.finished_at - record.started_at
                    record.duration_ms = int(delta.total_seconds() * 1000)
                break
