import os
import re
from pathlib import Path
from typing import Optional, Tuple
from backend.app.core.config import settings

# Disallowed dangerous shell tokens / commands for autonomous execution without explicit confirmation
PROHIBITED_COMMAND_PATTERNS = [
    r"\brmdir\s+/[sS]\s+[cC]:",
    r"\bformat\s+[cC]:",
    r"\bdel\s+/[fF]\s+/[sS]\s+[cC]:\\windows",
    r"\brm\s+-rf\s+/[^a-zA-Z0-9_]",
    r"\bshutdown\b",
    r"\breboot\b",
    r"\bdrop\s+database\b",
    r":(){ :|:& };:",
    r"\bInvoke-Expression\b.*DownloadString",
]

SECRET_PATTERNS = [
    r"(?i)(api[_-]?key|secret|password|token|bearer|private[_-]?key)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?",
    r"(?i)(mongodb(\+srv)?:\/\/[^:\s]+:)([^@]+)(@)",
]


def redact_secrets(text: str) -> str:
    """Redact sensitive credentials, keys, and tokens from text before logging or storing."""
    if not text:
        return text
    # 1. MongoDB URI credentials: mongodb(+srv)://user:password@host
    redacted = re.sub(r"(?i)(mongodb(?:\+srv)?:\/\/[^:\s]+:)[^@]+(@)", r"\1***REDACTED***\2", text)
    # 2. Key-value secrets: api_key=..., password=...
    redacted = re.sub(r"(?i)(api[_-]?key|secret|password|token|bearer|private[_-]?key)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{4,})['\"]?", r"\1=***REDACTED***", redacted)
    return redacted


def validate_workspace_path(path: str, workspace_root: Optional[str] = None) -> Tuple[bool, Path, str]:
    """
    Enforces strict filesystem jail.
    Path must reside within the authorized workspace directory.
    Returns (is_valid, resolved_path, error_message).
    """
    root = Path(workspace_root or settings.AUTHORIZED_WORKSPACE_DIR).resolve()
    try:
        root.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    try:
        target = Path(path)
        if not target.is_absolute():
            resolved = (root / target).resolve()
        else:
            resolved = target.resolve()

        # Check if resolved path is relative to root
        resolved.relative_to(root)
        return True, resolved, ""
    except ValueError:
        return False, Path(path), f"Security Violation: Path '{path}' escapes authorized workspace '{root}'."
    except Exception as e:
        return False, Path(path), f"Invalid path '{path}': {str(e)}"


def check_command_safety(command: str) -> Tuple[bool, str, str]:
    """
    Validates terminal command against safety policies.
    Returns (is_safe, permission_level, reason).
    Levels: 'automatic', 'requires_approval', 'prohibited'
    """
    cmd = command.strip()
    if not cmd:
        return False, "prohibited", "Command is empty."

    # Prohibited patterns
    for pat in PROHIBITED_COMMAND_PATTERNS:
        if re.search(pat, cmd, re.IGNORECASE):
            return False, "prohibited", f"Command matched prohibited security pattern: {pat}"

    # Safe automated commands
    safe_prefixes = [
        "git status", "git diff", "git log", "git branch",
        "npm list", "pip list", "pytest", "npm test",
        "node -v", "python --version", "npm -v", "echo ",
        "dir", "ls", "cat", "type", "where", "which"
    ]
    for prefix in safe_prefixes:
        if cmd.lower().startswith(prefix):
            return True, "automatic", "Read-only inspection command."

    # Controlled project execution commands
    controlled_prefixes = [
        "npm install", "pnpm install", "pip install",
        "npm run", "npx ", "python ", "node ", "git "
    ]
    for prefix in controlled_prefixes:
        if cmd.lower().startswith(prefix):
            return True, "controlled", "Project build or runtime command."

    return True, "requires_approval", "Unfamiliar command requires user verification."


def verify_local_agent_token(token: Optional[str]) -> bool:
    """Verifies authentication token from DODO Local Agent."""
    if not token:
        return False
    return token == settings.LOCAL_AGENT_SECRET_TOKEN

