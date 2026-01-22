"""
Console Logger - Beautiful console output for pipeline execution

Provides structured, emoji-enriched logging for tracking agent execution.
"""

import time
from typing import Optional, Dict, Any


class ConsoleLogger:
    """Beautiful console logger for pipeline visualization."""

    # Agent emojis
    AGENT_EMOJIS = {
        "FIA": "🎯",   # Flower Intent Agent
        "EIA": "💞",   # Emotion Intelligence Agent
        "RIL": "👥",   # Relationship Intelligence Layer
        "FMRA": "🌸",  # Flower Matching & Ranking Agent
        "CIA": "🎛️",   # Context Intensity Agent
        "AITB": "🎨",  # Adaptive Intelligence & Tone Builder
        "RFFA": "⚠️",  # Risk & Fit Assessment Agent
        "CRI": "🌍",   # Cultural & Regional Intelligence
        "SRFL": "🪞",  # Self-Reflection Layer
        "SFA": "✨",   # Symbolic Flower Agent (Final Assembler)
    }

    def __init__(self):
        self.start_times: Dict[str, float] = {}

    def pipeline_start(self, request_id: str, user_input: str, region: str) -> None:
        """Log pipeline start."""
        print("\n" + "=" * 80)
        print("🚀 FSENSE PIPELINE STARTED")
        print("=" * 80)
        print(f"📝 Request ID: {request_id}")
        print(f"🌍 Region: {region.upper()}")
        print(f"💬 User Input: \"{user_input}\"")
        print("=" * 80 + "\n")

    def pipeline_end(self, request_id: str, success: bool, total_time: Optional[float] = None) -> None:
        """Log pipeline completion."""
        print("\n" + "=" * 80)
        if success:
            print("✅ PIPELINE COMPLETED SUCCESSFULLY")
        else:
            print("❌ PIPELINE COMPLETED WITH ERRORS")
        print("=" * 80)
        print(f"📝 Request ID: {request_id}")
        if total_time:
            print(f"⏱️  Total Time: {total_time:.2f}s")
        print("=" * 80 + "\n")

    def agent_start(self, agent_name: str, step: int, total: int) -> None:
        """Log agent execution start."""
        emoji = self.AGENT_EMOJIS.get(agent_name, "🔧")
        print(f"\n{emoji} [{step}/{total}] {agent_name} — Starting...")
        print("─" * 80)
        self.start_times[agent_name] = time.time()

    def agent_result(self, agent_name: str, data: Dict[str, Any]) -> None:
        """Log agent results."""
        for key, value in data.items():
            if isinstance(value, (list, dict)):
                print(f"  • {key}: {self._format_complex(value)}")
            else:
                print(f"  • {key}: {value}")

    def agent_end(self, agent_name: str, status: str = "completed") -> None:
        """Log agent execution end."""
        duration = time.time() - self.start_times.get(agent_name, time.time())
        status_emoji = "✅" if status == "completed" else "❌"
        print(f"{status_emoji} {agent_name} {status} ({duration:.2f}s)")
        print("─" * 80)

    def agent_error(self, agent_name: str, error: str) -> None:
        """Log agent error."""
        print(f"❌ {agent_name} ERROR: {error}")
        print("─" * 80)

    def _format_complex(self, value: Any, max_items: int = 3) -> str:
        """Format complex types for display."""
        if isinstance(value, list):
            if len(value) <= max_items:
                return str(value)
            return f"[{', '.join(str(v) for v in value[:max_items])}, ... ({len(value)} total)]"
        elif isinstance(value, dict):
            items = list(value.items())[:max_items]
            formatted = ", ".join(f"{k}={v}" for k, v in items)
            if len(value) > max_items:
                formatted += f", ... ({len(value)} total)"
            return f"{{{formatted}}}"
        return str(value)


# Global instance
_console_logger = ConsoleLogger()


def get_console_logger() -> ConsoleLogger:
    """Get the global console logger instance."""
    return _console_logger
