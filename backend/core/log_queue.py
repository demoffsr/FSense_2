"""
Global log queue for broadcasting logs to web interface.
Uses thread-safe queue to bridge sync agents with async SSE streaming.
"""

import asyncio
import queue
from typing import Optional

# Global log queue - thread-safe for sync->async communication
_log_queue: Optional[queue.Queue] = None


def get_log_queue() -> queue.Queue:
    """Get or create the global log queue."""
    global _log_queue
    if _log_queue is None:
        _log_queue = queue.Queue(maxsize=1000)
    return _log_queue


def broadcast_log(log_data: dict) -> None:
    """Broadcast log entry to all connected clients (thread-safe)."""
    try:
        q = get_log_queue()
        # Try to put without blocking
        try:
            q.put_nowait(log_data)
        except queue.Full:
            # Queue full, skip this log
            pass
    except Exception:
        # Silently ignore broadcast errors
        pass
