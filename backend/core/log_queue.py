"""
Global log queue for broadcasting logs to web interface.
"""

import asyncio
from typing import Optional

# Global log queue - initialized on first access
_log_queue: Optional[asyncio.Queue] = None


def get_log_queue() -> asyncio.Queue:
    """Get or create the global log queue."""
    global _log_queue
    if _log_queue is None:
        try:
            _log_queue = asyncio.Queue(maxsize=1000)
        except RuntimeError:
            # No event loop, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            _log_queue = asyncio.Queue(maxsize=1000)
    return _log_queue


def broadcast_log(log_data: dict) -> None:
    """Broadcast log entry to all connected clients."""
    try:
        queue = get_log_queue()
        # Try to put without blocking
        try:
            queue.put_nowait(log_data)
        except asyncio.QueueFull:
            # Queue full, skip this log
            pass
    except Exception as e:
        # Silently ignore broadcast errors
        pass
