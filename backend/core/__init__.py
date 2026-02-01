"""
Backend Core Module - v0.0.1

Contains:
- AIClient: Unified OpenAI client
- Settings: Environment configuration
"""

from backend.core.settings import get_settings, reset_settings, Settings, SettingsError
from backend.core.ai_client import AIClient, get_ai_client, reset_ai_client, AIClientError

__all__ = [
    # Settings
    "Settings",
    "SettingsError",
    "get_settings",
    "reset_settings",
    # AI Client
    "AIClient",
    "AIClientError",
    "get_ai_client",
    "reset_ai_client",
]

__version__ = "0.0.1"
