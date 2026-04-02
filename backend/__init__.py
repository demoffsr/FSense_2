"""
FSense Backend - v0.0.1

AI-powered flower recommendation backend for iOS.

Main Entrypoint:
    from backend import run_flower_chat
    
    result = run_flower_chat("I want to apologize sincerely")
    if result["success"]:
        flower_card = result["data"]
"""

from backend.pipeline.runner import run_flower_chat

__version__ = "0.0.1"
__all__ = ["run_flower_chat", "__version__"]
