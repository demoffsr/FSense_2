"""
ScanContext - v1.0

Lightweight context for the scan pipeline.
Unlike PipelineContext (10 agents), this handles just 3 agents:
FID → FSA → SDA

Design:
- Minimal state for fast execution
- Focused on identification rather than recommendation
"""

from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime
import uuid


@dataclass
class IdentifiedFlower:
    """Single flower identified from image."""
    id: str = ""
    name: str = ""
    scientific_name: Optional[str] = None
    confidence: float = 0.0
    color: Optional[str] = None
    position: Optional[str] = None  # "primary", "secondary"


@dataclass
class IdentificationData:
    """Output from FID (Flower Identification Agent)."""
    primary_flower: Optional[IdentifiedFlower] = None
    additional_flowers: list[IdentifiedFlower] = field(default_factory=list)
    bouquet_description: str = ""
    raw_response: dict[str, Any] = field(default_factory=dict)


@dataclass
class FlowerInfoData:
    """Output from FSA (Flower Search Agent)."""
    # Botanical info
    family: str = ""
    native_regions: list[str] = field(default_factory=list)
    bloom_seasons: list[str] = field(default_factory=list)
    lifespan: str = ""

    # Meanings
    meanings: list[str] = field(default_factory=list)

    # Care info
    care_difficulty: str = "moderate"
    light_requirement: str = "medium"
    water_frequency: str = "moderate"
    temperature_range: str = ""
    humidity: str = ""
    care_tips: list[str] = field(default_factory=list)

    # Similar flowers
    similar_flowers: list[IdentifiedFlower] = field(default_factory=list)

    raw_response: dict[str, Any] = field(default_factory=dict)


@dataclass
class TimingRecord:
    """Timing record for a single agent."""
    agent_name: str = ""
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_ms: int = 0
    status: str = "pending"


@dataclass
class ScanContext:
    """
    Lightweight context for scan pipeline.

    Flow: Image → FID → FSA → SDA → Payloads

    Sections:
    1. Request input (immutable)
    2. Agent outputs (mutable by respective agents)
    3. Final payloads (written by SDA)
    4. Execution metadata
    """

    # ─────────────────────────────────────────────────────────────────────
    # 1. REQUEST INPUT (set at creation)
    # ─────────────────────────────────────────────────────────────────────
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)

    image_base64: str = ""
    scan_mode: str = "single"  # "single" or "bouquet"
    region: str = "US"

    # ─────────────────────────────────────────────────────────────────────
    # 2. AGENT OUTPUTS
    # ─────────────────────────────────────────────────────────────────────

    # FID → Flower Identification Agent
    identification: IdentificationData = field(default_factory=IdentificationData)

    # FSA → Flower Search Agent
    flower_info: FlowerInfoData = field(default_factory=FlowerInfoData)

    # ─────────────────────────────────────────────────────────────────────
    # 3. FINAL PAYLOADS (written by SDA)
    # ─────────────────────────────────────────────────────────────────────
    quick_payload: Optional[dict[str, Any]] = None
    detail_payload: Optional[dict[str, Any]] = None

    # ─────────────────────────────────────────────────────────────────────
    # 4. EXECUTION METADATA
    # ─────────────────────────────────────────────────────────────────────
    timings: list[TimingRecord] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    # ─────────────────────────────────────────────────────────────────────
    # HELPER METHODS
    # ─────────────────────────────────────────────────────────────────────

    def get_primary_flower(self) -> Optional[IdentifiedFlower]:
        """Get the primary identified flower."""
        return self.identification.primary_flower

    def add_error(self, error: str) -> None:
        """Record an error during pipeline execution."""
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

    def has_valid_identification(self) -> bool:
        """Check if we have a valid flower identification."""
        flower = self.get_primary_flower()
        return flower is not None and flower.name and flower.confidence >= 0.5
