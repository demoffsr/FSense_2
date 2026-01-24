"""
Settings and Configuration - v0.0.1

Environment variables and application configuration.
Loads from .env file using python-dotenv.

IMPORTANT: OPENAI_API_KEY is REQUIRED.
The application will fail to start if it's missing.
"""

from dataclasses import dataclass
from typing import Optional
from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)


def _load_dotenv() -> None:
    """
    Load environment variables from .env file.
    
    Searches for .env in:
    1. Current working directory
    2. Backend root directory
    3. Project root directory
    """
    try:
        from dotenv import load_dotenv
        
        # Try multiple locations for .env file
        possible_paths = [
            Path.cwd() / ".env",
            Path(__file__).parent.parent / ".env",  # backend/.env
            Path(__file__).parent.parent.parent / ".env",  # project root/.env
        ]
        
        for env_path in possible_paths:
            if env_path.exists():
                load_dotenv(env_path)
                logger.debug(f"Loaded .env from: {env_path}")
                return
        
        # No .env found, try loading from environment anyway
        load_dotenv()
        
    except ImportError:
        logger.warning("python-dotenv not installed, using environment variables only")


class SettingsError(Exception):
    """Raised when required settings are missing or invalid."""
    pass


@dataclass(frozen=True)
class Settings:
    """
    Application settings loaded from environment.

    Required:
    - openai_api_key: Must be set, cannot be empty
    - database_url: PostgreSQL connection string (Supabase)

    Optional:
    - All other settings have sensible defaults
    """

    # OpenAI (REQUIRED)
    openai_api_key: str
    openai_model: str = "gpt-4o"  # Complex tasks (FMRA, CRI, SFA)
    openai_model_fast: str = "gpt-4o-mini"  # Simple tasks (~3x faster)
    openai_timeout: int = 60  # seconds
    openai_max_retries: int = 3

    # Database (REQUIRED for production)
    database_url: str = ""  # PostgreSQL connection string

    # Application
    fsense_env: str = "local"
    fsense_version: str = "v0.0.1"

    # Pipeline
    default_region: str = "us"
    max_candidates: int = 5

    # Debug
    debug_mode: bool = False
    log_level: str = "INFO"
    
    @classmethod
    def from_env(cls) -> "Settings":
        """
        Load settings from environment variables.
        
        Raises:
            SettingsError: If OPENAI_API_KEY is missing or empty
        """
        # Load .env file first
        _load_dotenv()
        
        # Get API key (REQUIRED)
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        
        if not api_key:
            raise SettingsError(
                "OPENAI_API_KEY is required but not set.\n"
                "Please create a .env file with your OpenAI API key.\n"
                "See .env.example for the required format."
            )
        
        if api_key == "your-openai-api-key-here":
            raise SettingsError(
                "OPENAI_API_KEY contains the placeholder value.\n"
                "Please replace it with your actual OpenAI API key."
            )
        
        return cls(
            # Required
            openai_api_key=api_key,

            # OpenAI settings
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            openai_model_fast=os.getenv("OPENAI_MODEL_FAST", "gpt-4o-mini"),
            openai_timeout=int(os.getenv("OPENAI_TIMEOUT", "60")),
            openai_max_retries=int(os.getenv("OPENAI_MAX_RETRIES", "3")),

            # Database
            database_url=os.getenv("DATABASE_URL", ""),

            # Application
            fsense_env=os.getenv("FSENSE_ENV", "local"),
            fsense_version=os.getenv("FSENSE_VERSION", "v0.0.1"),

            # Pipeline
            default_region=os.getenv("DEFAULT_REGION", "us"),
            max_candidates=int(os.getenv("MAX_CANDIDATES", "5")),

            # Debug
            debug_mode=os.getenv("DEBUG_MODE", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )
    
    def validate(self) -> None:
        """
        Validate settings after loading.
        
        Raises:
            SettingsError: If validation fails
        """
        if not self.openai_api_key.startswith("sk-"):
            logger.warning(
                "OPENAI_API_KEY doesn't start with 'sk-'. "
                "This might indicate an invalid key format."
            )


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON PATTERN
# ═══════════════════════════════════════════════════════════════════════════════

_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get or create settings singleton.
    
    First call loads settings from environment.
    Subsequent calls return cached instance.
    
    Raises:
        SettingsError: If required settings are missing
    """
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
        _settings.validate()
    return _settings


def reset_settings() -> None:
    """
    Reset settings singleton (for testing).
    
    Next call to get_settings() will reload from environment.
    """
    global _settings
    _settings = None
