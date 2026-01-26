"""
AI Client - v0.0.1

Unified OpenAI client for all LLM interactions.
All agent adapters MUST use this client for AI calls.

Features:
- Single initialization point
- Automatic retry with exponential backoff
- Consistent error handling
- JSON mode support
"""

from typing import Any, Optional
import json
import logging

from openai import OpenAI
from openai import APIError, APIConnectionError, RateLimitError, APITimeoutError

from backend.core.settings import get_settings, SettingsError

logger = logging.getLogger(__name__)


class AIClientError(Exception):
    """Base exception for AI client errors."""
    pass


class AIClient:
    """
    Unified AI client for all LLM interactions.
    
    Usage:
        client = AIClient()
        response = client.complete("What flower represents love?")
        
        # Or with JSON response:
        data = client.complete_json("Return flower data as JSON")
    
    Thread Safety:
        This class is thread-safe. The underlying OpenAI client
        handles connection pooling automatically.
    """
    
    def __init__(
        self,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ) -> None:
        """
        Initialize AI client.
        
        Args:
            model: Override default model from settings
            timeout: Override default timeout from settings
            max_retries: Override default max_retries from settings
            
        Raises:
            SettingsError: If OPENAI_API_KEY is not configured
        """
        settings = get_settings()
        
        self.model = model or settings.openai_model
        self.timeout = timeout or settings.openai_timeout
        self.max_retries = max_retries or settings.openai_max_retries
        
        # Initialize OpenAI client
        self._client = OpenAI(
            api_key=settings.openai_api_key,
            timeout=self.timeout,
            max_retries=self.max_retries,
        )
        
        logger.debug(f"AIClient initialized: model={self.model}")
    
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """
        Send a completion request to the LLM.
        
        Args:
            prompt: User message/prompt
            system_prompt: Optional system message
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated text response
            
        Raises:
            AIClientError: If the API call fails
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            content = response.choices[0].message.content
            
            if content is None:
                raise AIClientError("Empty response from API")
            
            logger.debug(f"Completion successful: {len(content)} chars")
            return content
            
        except RateLimitError as e:
            logger.error(f"Rate limit exceeded: {e}")
            raise AIClientError(f"Rate limit exceeded. Please try again later.") from e
            
        except APITimeoutError as e:
            logger.error(f"API timeout: {e}")
            raise AIClientError(f"Request timed out after {self.timeout}s") from e
            
        except APIConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise AIClientError("Failed to connect to OpenAI API") from e
            
        except APIError as e:
            logger.error(f"API error: {e}")
            raise AIClientError(f"OpenAI API error: {e.message}") from e
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            raise AIClientError(f"Unexpected error: {str(e)}") from e
    
    def analyze_image(
        self,
        image_base64: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 500,
    ) -> dict[str, Any]:
        """
        Analyze an image using GPT-4 Vision API.

        Args:
            image_base64: Base64 encoded image data
            prompt: Text prompt describing what to analyze
            system_prompt: Optional system message
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            Parsed JSON response from the model

        Raises:
            AIClientError: If the API call fails or JSON is invalid
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Build vision message with image and text
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}",
                        "detail": "low"  # Use low detail for faster processing
                    }
                }
            ]
        })

        try:
            response = self._client.chat.completions.create(
                model=self.model,  # gpt-4o supports vision
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content

            if content is None:
                raise AIClientError("Empty response from Vision API")

            # Parse JSON
            try:
                data = json.loads(content)
                logger.debug(f"Vision analysis successful: {len(content)} chars")
                return data
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON from Vision API: {content[:200]}...")
                raise AIClientError(f"Invalid JSON in response: {e}") from e

        except RateLimitError as e:
            logger.error(f"Rate limit exceeded: {e}")
            raise AIClientError(f"Rate limit exceeded. Please try again later.") from e

        except APITimeoutError as e:
            logger.error(f"API timeout: {e}")
            raise AIClientError(f"Request timed out after {self.timeout}s") from e

        except APIConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise AIClientError("Failed to connect to OpenAI API") from e

        except APIError as e:
            logger.error(f"API error: {e}")
            raise AIClientError(f"OpenAI API error: {e.message}") from e

        except AIClientError:
            raise

        except Exception as e:
            logger.error(f"Unexpected error in Vision API: {e}", exc_info=True)
            raise AIClientError(f"Unexpected error: {str(e)}") from e

    def complete_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> dict[str, Any]:
        """
        Send a completion request expecting JSON response.
        
        Uses OpenAI's JSON mode for guaranteed valid JSON output.
        
        Args:
            prompt: User message/prompt (should ask for JSON)
            system_prompt: Optional system message
            temperature: Sampling temperature (lower = more deterministic)
            max_tokens: Maximum tokens in response
            
        Returns:
            Parsed JSON as dictionary
            
        Raises:
            AIClientError: If the API call fails or JSON is invalid
        """
        # Enhance system prompt for JSON mode
        json_system = system_prompt or ""
        if json_system:
            json_system += "\n\n"
        json_system += "You must respond with valid JSON only. No markdown, no explanations."
        
        messages = [
            {"role": "system", "content": json_system},
            {"role": "user", "content": prompt},
        ]
        
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
            
            content = response.choices[0].message.content
            
            if content is None:
                raise AIClientError("Empty response from API")
            
            # Parse JSON
            try:
                data = json.loads(content)
                logger.debug(f"JSON completion successful: {len(content)} chars")
                return data
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON response: {content[:200]}...")
                raise AIClientError(f"Invalid JSON in response: {e}") from e
            
        except RateLimitError as e:
            logger.error(f"Rate limit exceeded: {e}")
            raise AIClientError(f"Rate limit exceeded. Please try again later.") from e
            
        except APITimeoutError as e:
            logger.error(f"API timeout: {e}")
            raise AIClientError(f"Request timed out after {self.timeout}s") from e
            
        except APIConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise AIClientError("Failed to connect to OpenAI API") from e
            
        except APIError as e:
            logger.error(f"API error: {e}")
            raise AIClientError(f"OpenAI API error: {e.message}") from e
            
        except AIClientError:
            raise
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            raise AIClientError(f"Unexpected error: {str(e)}") from e


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON PATTERN
# ═══════════════════════════════════════════════════════════════════════════════

_default_client: Optional[AIClient] = None
_fast_client: Optional[AIClient] = None


def get_ai_client() -> AIClient:
    """
    Get default AI client (gpt-4o) for complex tasks.

    Use for: FMRA, CRI, SFA - tasks requiring deep reasoning.
    """
    global _default_client
    if _default_client is None:
        _default_client = AIClient()
    return _default_client


def get_ai_client_fast() -> AIClient:
    """
    Get fast AI client (gpt-4o-mini) for simple tasks.

    Use for: FIA, EIA, RIL, CIA, AITB, RFFA, SRFL - simpler analysis tasks.
    ~3x faster than gpt-4o with good quality for these tasks.
    """
    global _fast_client
    if _fast_client is None:
        settings = get_settings()
        _fast_client = AIClient(model=settings.openai_model_fast)
    return _fast_client


def reset_ai_client() -> None:
    """Reset AI client singletons (for testing)."""
    global _default_client, _fast_client
    _default_client = None
    _fast_client = None
