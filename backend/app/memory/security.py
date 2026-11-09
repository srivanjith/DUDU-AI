"""
DODO Memory Security & Privacy Engine
Detects secrets, credentials, tokens, private keys, and strips hidden chain-of-thought
to ensure safe long-term persistence without data leakage.
"""
import re
from typing import List, Tuple

# Patterns that detect sensitive credentials, API keys, tokens, and private keys
SENSITIVE_PATTERNS = [
    # API Keys & Secrets
    r"(?i)\b(?:api[_-]?key|access[_-]?key|secret[_-]?key|private[_-]?key)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{12,})['\"]?",
    # Bearer tokens & JWTs
    r"(?i)\b(?:bearer\s+)?(ey[a-zA-Z0-9_-]{15,}\.ey[a-zA-Z0-9_-]{15,}\.[a-zA-Z0-9_-]+)",
    # Passwords in assignment or JSON format
    r"(?i)\b(?:password|passwd|pwd)\s*[:=]\s*['\"]?([^'\"\s\r\n]{6,})['\"]?",
    # MongoDB connection strings with credentials
    r"(?i)mongodb(?:\+srv)?:\/\/[^:]+:([^@]+)@",
    # AWS Access / Secret Key ID patterns
    r"\b(AKIA[0-9A-Z]{16})\b",
    # Generic Private Key blocks
    r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----[\s\S]+?-----END (?:RSA |EC )?PRIVATE KEY-----",
]

# Hidden chain-of-thought or reasoning tags to strip
CHAIN_OF_THOUGHT_PATTERNS = [
    r"<think>[\s\S]*?<\/think>",
    r"\[thinking\][\s\S]*?\[\/thinking\]",
    r"BEGIN_THOUGHTS[\s\S]*?END_THOUGHTS",
]

# Suspicious prompt injection vectors inside stored memories
PROMPT_INJECTION_PATTERNS = [
    r"(?i)ignore (?:all )?previous instructions",
    r"(?i)system: you are now",
    r"(?i)disregard the system prompt",
    r"(?i)you must override your rules",
]


class MemorySecurityPolicy:
    """Enforces privacy, secret sanitization, and prompt-injection barriers for stored memories."""

    @staticmethod
    def contains_secret(text: str) -> Tuple[bool, str]:
        """Checks if text contains potential secrets, tokens, or credentials."""
        if not text:
            return False, ""
        for pat in SENSITIVE_PATTERNS:
            match = re.search(pat, text)
            if match:
                return True, f"Detected sensitive pattern matching security policy."
        return False, ""

    @staticmethod
    def sanitize_content(text: str) -> str:
        """
        Removes secrets, hidden reasoning traces, and malicious injection attempts
        from content before storage.
        """
        if not text:
            return ""

        cleaned = text

        # 1. Strip hidden chain-of-thought / reasoning
        for pat in CHAIN_OF_THOUGHT_PATTERNS:
            cleaned = re.sub(pat, "", cleaned, flags=re.DOTALL)

        # 2. Redact sensitive credentials and tokens
        for pat in SENSITIVE_PATTERNS:
            cleaned = re.sub(pat, "[REDACTED_SECRET]", cleaned)

        # 3. Defang prompt injection attempts
        for pat in PROMPT_INJECTION_PATTERNS:
            cleaned = re.sub(pat, "[FILTERED_INSTRUCTION]", cleaned)

        return cleaned.strip()

    @staticmethod
    def validate_for_storage(text: str) -> Tuple[bool, str]:
        """
        Validates content suitability for memory persistence.
        Returns (is_valid, reason).
        """
        if not text or len(text.strip()) < 3:
            return False, "Memory content is too short or empty."

        if len(text) > 8000:
            return False, "Memory content exceeds maximum limit of 8000 characters."

        # Verify not pure chain of thought
        stripped = text
        for pat in CHAIN_OF_THOUGHT_PATTERNS:
            stripped = re.sub(pat, "", stripped)
        if len(stripped.strip()) < 2:
            return False, "Content contained only internal reasoning / chain-of-thought."

        return True, ""


memory_security = MemorySecurityPolicy()

