"""
Agent Adapters - v0.0.1

Standardized adapters that wrap legacy agents or implement new logic.
All adapters conform to the BaseAgent interface.

Execution Order:
1. FIA  - Flower Intent Agent
2. EIA  - Emotion Intelligence Agent
3. RIL  - Relationship Intelligence Layer
4. FMRA - Flower Matching & Ranking Agent
5. CIA  - Context Intensity Agent
6. AITB - Adaptive Intelligence & Tone Builder
7. RFFA - Risk & Fit Assessment Agent
8. CRI  - Cultural & Regional Intelligence
9. SRFL - Self-Reflection Layer
10. SFA - Symbolic Flower Agent (FINAL ASSEMBLER)
"""

from backend.agents.adapters.fia_adapter import FIAAdapter
from backend.agents.adapters.eia_adapter import EIAAdapter
from backend.agents.adapters.ril_adapter import RILAdapter
from backend.agents.adapters.fmra_adapter import FMRAAdapter
from backend.agents.adapters.cia_adapter import CIAAdapter
from backend.agents.adapters.aitb_adapter import AITBAdapter
from backend.agents.adapters.rffa_adapter import RFFAAdapter
from backend.agents.adapters.cri_adapter import CRIAdapter
from backend.agents.adapters.srfl_adapter import SRFLAdapter
from backend.agents.adapters.sfa_adapter import SFAAdapter

__all__ = [
    "FIAAdapter",
    "EIAAdapter",
    "RILAdapter",
    "FMRAAdapter",
    "CIAAdapter",
    "AITBAdapter",
    "RFFAAdapter",
    "CRIAdapter",
    "SRFLAdapter",
    "SFAAdapter",
]
