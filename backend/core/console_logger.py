"""
Console Logger - Beautiful console output for pipeline execution

Provides structured, emoji-enriched logging for tracking agent execution.
Also broadcasts to web interface via log queue.
"""

import time
from typing import Optional, Dict, Any, Callable


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
        self.broadcast_callback: Optional[Callable] = None

    def set_broadcast_callback(self, callback: Callable):
        """Set callback for broadcasting logs to web interface."""
        self.broadcast_callback = callback

    def _broadcast(self, log_data: dict):
        """Broadcast log to web interface."""
        try:
            from backend.core.log_queue import broadcast_log
            broadcast_log(log_data)
        except Exception:
            pass  # Ignore broadcast errors

    def pipeline_start(self, request_id: str, user_input: str, region: str) -> None:
        """Log pipeline start."""
        msg = f"PIPELINE STARTED | Request: {request_id[:8]} | Region: {region.upper()} | Input: \"{user_input}\""
        print("\n" + "=" * 80)
        print("🚀 FSENSE PIPELINE STARTED")
        print("=" * 80)
        print(f"📝 Request ID: {request_id}")
        print(f"🌍 Region: {region.upper()}")
        print(f"💬 User Input: \"{user_input}\"")
        print("=" * 80 + "\n")

        self._broadcast({
            "type": "pipeline_start",
            "message": msg,
            "request_id": request_id,
            "region": region,
            "user_input": user_input
        })

    def pipeline_end(self, request_id: str, success: bool, total_time: Optional[float] = None) -> None:
        """Log pipeline completion."""
        status = "SUCCESS" if success else "FAILED"
        msg = f"PIPELINE {status} | Request: {request_id[:8]}"
        if total_time:
            msg += f" | Time: {total_time:.2f}s"

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

        self._broadcast({
            "type": "pipeline_end",
            "message": msg,
            "success": success,
            "total_time": total_time
        })
        self._broadcast({"type": "separator"})

    def agent_start(self, agent_name: str, step: int, total: int) -> None:
        """Log agent execution start."""
        emoji = self.AGENT_EMOJIS.get(agent_name, "🔧")
        msg = f"[{step}/{total}] {agent_name} — Starting..."
        print(f"\n{emoji} {msg}")
        print("─" * 80)
        self.start_times[agent_name] = time.time()

        self._broadcast({
            "type": "agent_start",
            "message": msg,
            "agent": agent_name,
            "emoji": emoji,
            "step": step,
            "total": total
        })

    def agent_result(self, agent_name: str, data: Dict[str, Any]) -> None:
        """Log agent results."""
        for key, value in data.items():
            formatted = self._format_complex(value) if isinstance(value, (list, dict)) else str(value)
            print(f"  • {key}: {formatted}")

            self._broadcast({
                "type": "agent_result",
                "message": f"{key}: {formatted}",
                "agent": agent_name,
                "key": key,
                "value": formatted
            })

    def agent_end(self, agent_name: str, status: str = "completed") -> None:
        """Log agent execution end."""
        duration = time.time() - self.start_times.get(agent_name, time.time())
        status_emoji = "✅" if status == "completed" else "❌"
        msg = f"{agent_name} {status} ({duration:.2f}s)"
        print(f"{status_emoji} {msg}")
        print("─" * 80)

        self._broadcast({
            "type": "agent_end",
            "message": msg,
            "agent": agent_name,
            "duration": duration,
            "status": status
        })

    def agent_error(self, agent_name: str, error: str) -> None:
        """Log agent error."""
        msg = f"{agent_name} ERROR: {error}"
        print(f"❌ {msg}")
        print("─" * 80)

        self._broadcast({
            "type": "error",
            "message": msg,
            "agent": agent_name,
            "error": error
        })

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
