"""
Input Validation and Sanitization - v1.0.0

Protects against:
- Prompt injection attempts
- Excessively long inputs
- Malformed unicode
- Control characters
"""

import re
import unicodedata
import logging
from typing import Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

MAX_PROMPT_LENGTH = 2000  # Characters
MIN_PROMPT_LENGTH = 2     # Characters
MAX_PROMPT_TOKENS_ESTIMATE = 500  # ~4 chars per token

# Patterns that might indicate prompt injection
SUSPICIOUS_PATTERNS = [
    r"ignore\s+(previous|all|above)\s+(instructions?|prompts?)",
    r"disregard\s+(previous|all|above)",
    r"you\s+are\s+now\s+(?:a|an)\s+",
    r"new\s+instruction[s]?:",
    r"system\s*:\s*",
    r"<\s*system\s*>",
    r"\[\s*SYSTEM\s*\]",
    r"```\s*(system|instruction)",
]

# Compiled patterns for efficiency
_SUSPICIOUS_RE = [re.compile(p, re.IGNORECASE) for p in SUSPICIOUS_PATTERNS]


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATION RESULT
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ValidationResult:
    """Result of input validation."""
    is_valid: bool
    sanitized_input: str
    error_message: Optional[str] = None
    warnings: list[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


# ═══════════════════════════════════════════════════════════════════════════════
# SANITIZATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def normalize_unicode(text: str) -> str:
    """
    Normalize unicode to NFC form and remove problematic characters.

    - NFC: Canonical Decomposition, followed by Canonical Composition
    - Removes control characters except newlines and tabs
    """
    # Normalize to NFC
    text = unicodedata.normalize("NFC", text)

    # Remove control characters (keep newlines \n and tabs \t)
    cleaned = []
    for char in text:
        category = unicodedata.category(char)
        # Keep: Letters, Numbers, Punctuation, Symbols, Separators, Marks
        # Remove: Control characters (Cc) except \n, \t, \r
        if category == "Cc":
            if char in ("\n", "\t", "\r"):
                cleaned.append(char)
            # else: skip control character
        else:
            cleaned.append(char)

    return "".join(cleaned)


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace:
    - Convert multiple spaces to single space
    - Convert multiple newlines to double newline
    - Strip leading/trailing whitespace
    """
    # Replace multiple spaces with single space
    text = re.sub(r"[ \t]+", " ", text)

    # Replace 3+ newlines with double newline
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip
    return text.strip()


def check_suspicious_patterns(text: str) -> list[str]:
    """
    Check for patterns that might indicate prompt injection.

    Returns list of detected patterns (empty if clean).
    """
    warnings = []

    for pattern in _SUSPICIOUS_RE:
        if pattern.search(text):
            warnings.append(f"Suspicious pattern detected: {pattern.pattern}")

    return warnings


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN VALIDATION FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def validate_input(prompt: str) -> ValidationResult:
    """
    Validate and sanitize user input.

    Performs:
    1. Null/empty check
    2. Length validation
    3. Unicode normalization
    4. Whitespace normalization
    5. Suspicious pattern detection (BLOCKS prompt injection attempts)

    Args:
        prompt: Raw user input

    Returns:
        ValidationResult with sanitized input or error
    """
    # Null check
    if prompt is None:
        return ValidationResult(
            is_valid=False,
            sanitized_input="",
            error_message="Message cannot be empty",
        )

    # Initial strip
    prompt = prompt.strip()

    # Empty check
    if not prompt:
        return ValidationResult(
            is_valid=False,
            sanitized_input="",
            error_message="Message cannot be empty",
        )

    # Min length check
    if len(prompt) < MIN_PROMPT_LENGTH:
        return ValidationResult(
            is_valid=False,
            sanitized_input=prompt,
            error_message=f"Message too short (minimum {MIN_PROMPT_LENGTH} characters)",
        )

    # Max length check (before sanitization to catch obviously bad input)
    if len(prompt) > MAX_PROMPT_LENGTH * 2:
        return ValidationResult(
            is_valid=False,
            sanitized_input="",
            error_message=f"Message too long (maximum {MAX_PROMPT_LENGTH} characters)",
        )

    # Sanitize
    sanitized = normalize_unicode(prompt)
    sanitized = normalize_whitespace(sanitized)

    # Length check after sanitization
    if len(sanitized) > MAX_PROMPT_LENGTH:
        return ValidationResult(
            is_valid=False,
            sanitized_input="",
            error_message=f"Message too long (maximum {MAX_PROMPT_LENGTH} characters)",
        )

    # Check for suspicious patterns - BLOCK if detected
    warnings = check_suspicious_patterns(sanitized)
    if warnings:
        logger.warning(f"Prompt injection attempt blocked: {warnings}")
        return ValidationResult(
            is_valid=False,
            sanitized_input="",
            error_message="Your message contains disallowed content. Please rephrase your request.",
            warnings=warnings,
        )

    return ValidationResult(
        is_valid=True,
        sanitized_input=sanitized,
        warnings=[],
    )


def validate_region(region: str) -> str:
    """
    Validate and normalize region code.

    Args:
        region: Raw region input

    Returns:
        Normalized region code (uppercase, 2-3 chars)
    """
    if not region:
        return "US"

    # Normalize
    region = region.strip().upper()

    # Validate format (2-3 letter code)
    if not re.match(r"^[A-Z]{2,3}$", region):
        logger.warning(f"Invalid region format: {region}, defaulting to US")
        return "US"

    return region
