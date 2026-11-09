"""
DODO Local Agent Security & Command Permission Registry
Enforces strict workspace isolation, command categorization, dangerous command prohibition,
path jailing, and secret redaction.
"""
import enum
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from local_agent.config import local_settings

api_key_header = APIKeyHeader(name="X-DODO-Token", auto_error=False)


class CommandCategory(str, enum.Enum):
    READ = "READ"
    TEST = "TEST"
    DEV_SERVER = "DEV_SERVER"
    DEPENDENCY_INSTALL = "DEPENDENCY_INSTALL"
    BUILD = "BUILD"
    UNKNOWN = "UNKNOWN"
    PROHIBITED = "PROHIBITED"


class PermissionRisk(str, enum.Enum):
    AUTOMATIC = "automatic"              # Read-only or safe test commands
    REQUIRES_APPROVAL = "requires_approval"  # Dependency install, file modifications, unfamiliar
    PROHIBITED = "prohibited"            # Dangerous shell commands, disk formatting, escaping


# Regex patterns of strictly prohibited commands
PROHIBITED_COMMAND_PATTERNS = [
    r"\brmdir\s+/[sS]\s+[cC]:",
    r"\bformat\s+[a-zA-Z]:",
    r"\bdel\s+/[fF]\s+/[sS]\s+[cC]:\\windows",
    r"\brm\s+-rf\s+/(etc|boot|sys|usr|bin|sbin|var)?",
    r"\bshutdown(\.exe)?\b",
    r"\breboot(\.exe)?\b",
    r"\bdrop\s+database\b",
    r":\(\)\s*\{\s*:\|:&\s*\};:",         # Fork bomb
    r"\bInvoke-Expression\b.*DownloadString",
    r"\bpowershell(\.exe)?\s+-enc(odedcommand)?",
    r"\b(curl|wget)\b.*\|\s*(bash|sh|powershell|cmd)",
    r"\b(mkfs|dd\s+if=)",
    r"\breg\s+delete\s+HK",
]

# Secret patterns for redaction
SECRET_PATTERNS = [
    r"(?i)(api[_-]?key|secret|password|token|bearer|private[_-]?key|authorization)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?",
    r"(?i)(mongodb(\+srv)?:\/\/[^:\s]+:)([^@]+)(@)",
    r"(?i)(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{82})",
    r"(?i)(dodo_local_agent_[a-zA-Z0-9_]+)",
]


def verify_token(token: Optional[str] = Security(api_key_header)) -> bool:
    """Authenticates API requests against local agent secret token."""
    expected = local_settings.SECRET_TOKEN
    if not token or token != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid or missing DODO Local Agent authentication token."
        )
    return True


def verify_token_string(token: Optional[str]) -> bool:
    """Verifies token string for WebSocket handshake."""
    if not token:
        return False
    return token == local_settings.SECRET_TOKEN


def redact_secrets(text: str) -> str:
    """Masks credentials, tokens, and secrets from output and logs."""
    if not text:
        return text
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = re.sub(
            pattern,
            r"\1***REDACTED***\4" if r"\4" in pattern else r"\1=***REDACTED***",
            redacted
        )
    # Also explicitly redact local secret token if present
    if local_settings.SECRET_TOKEN in redacted:
        redacted = redacted.replace(local_settings.SECRET_TOKEN, "***DODO_SECRET_TOKEN_REDACTED***")
    return redacted


def jail_path(relative_or_absolute: str, workspace_root: Optional[str] = None) -> Tuple[bool, Path, str]:
    """
    Strict filesystem jail.
    Path must reside within the authorized workspace directory.
    Prevents path traversal ('..'), symlink escape, and unrelated disk drive access.
    """
    root_str = workspace_root or local_settings.AUTHORIZED_WORKSPACE
    root = Path(root_str).resolve()
    root.mkdir(parents=True, exist_ok=True)

    if not relative_or_absolute or relative_or_absolute.strip() == "":
        return True, root, ""

    try:
        # Check for obvious traversal attempts before resolving
        clean_input = relative_or_absolute.replace("\\", "/")
        if "/../" in clean_input or clean_input.startswith("../") or clean_input.endswith("/..") or clean_input == "..":
            # Let Path.resolve check if it actually escapes
            pass

        target = Path(relative_or_absolute)
        resolved = (root / target).resolve() if not target.is_absolute() else target.resolve()

        # Check containment
        resolved.relative_to(root)
        return True, resolved, ""
    except ValueError:
        return False, Path(relative_or_absolute), f"Path jail violation: '{relative_or_absolute}' escapes authorized workspace '{root}'."
    except Exception as e:
        return False, Path(relative_or_absolute), str(e)


def classify_command(command: str) -> Tuple[CommandCategory, PermissionRisk, str]:
    """
    Classifies a command into categories and risk levels:
    - READ: Low risk, automatic.
    - TEST: Low/medium risk, automatic in authorized workspace.
    - DEV_SERVER: Medium risk, tracks PID, prevents duplicates.
    - DEPENDENCY_INSTALL: High risk, REQUIRES USER APPROVAL.
    - BUILD: Medium risk, controlled.
    - PROHIBITED: Blocked unconditionally.
    """
    cmd = command.strip()
    if not cmd:
        return CommandCategory.PROHIBITED, PermissionRisk.PROHIBITED, "Command string is empty."

    # 1. Prohibited pattern scan
    for pattern in PROHIBITED_COMMAND_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return (
                CommandCategory.PROHIBITED,
                PermissionRisk.PROHIBITED,
                f"Command matched prohibited security pattern: {pattern}"
            )

    cmd_lower = cmd.lower()

    # 2. Dependency Installation -> ALWAYS REQUIRES APPROVAL
    dep_install_patterns = [
        r"^(python\s+-m\s+)?pip\s+install\b",
        r"^(python\s+-m\s+)?pip3\s+install\b",
        r"^npm\s+(install|i|add)\b",
        r"^pnpm\s+(install|i|add)\b",
        r"^yarn\s+add\b",
        r"^poetry\s+add\b",
        r"^conda\s+install\b",
    ]
    for pat in dep_install_patterns:
        if re.search(pat, cmd_lower):
            return (
                CommandCategory.DEPENDENCY_INSTALL,
                PermissionRisk.REQUIRES_APPROVAL,
                "Package installation modifies system/environment dependencies and requires explicit user approval."
            )

    # 3. Development Server Commands
    dev_server_patterns = [
        r"^npm\s+run\s+dev\b",
        r"^npm\s+start\b",
        r"^pnpm\s+run\s+dev\b",
        r"^yarn\s+dev\b",
        r"^(python\s+-m\s+)?uvicorn\b",
        r"^python\s+(main|app|server)\.py\b",
    ]
    for pat in dev_server_patterns:
        if re.search(pat, cmd_lower):
            return (
                CommandCategory.DEV_SERVER,
                PermissionRisk.AUTOMATIC,
                "Development server command (managed as background process with duplicate prevention)."
            )

    # 4. Test Commands
    test_patterns = [
        r"^(python\s+-m\s+)?pytest\b",
        r"^(python\s+-m\s+)?unittest\b",
        r"^npm\s+test\b",
        r"^pnpm\s+test\b",
        r"^yarn\s+test\b",
        r"^vitest\b",
        r"^jest\b",
    ]
    for pat in test_patterns:
        if re.search(pat, cmd_lower):
            return (
                CommandCategory.TEST,
                PermissionRisk.AUTOMATIC,
                "Test suite command executed within authorized workspace."
            )

    # 5. Build Commands
    build_patterns = [
        r"^npm\s+run\s+build\b",
        r"^pnpm\s+run\s+build\b",
        r"^yarn\s+build\b",
        r"^python\s+setup\.py\s+build\b",
        r"^cargo\s+build\b",
    ]
    for pat in build_patterns:
        if re.search(pat, cmd_lower):
            return (
                CommandCategory.BUILD,
                PermissionRisk.AUTOMATIC,
                "Project build command."
            )

    # 6. Read-only Inspection Commands
    read_prefixes = [
        "git status", "git diff", "git log", "git branch", "git show",
        "dir", "ls", "type", "cat", "echo ", "where ", "which ",
        "python --version", "python -v", "node -v", "npm -v", "pnpm -v",
        "pip list", "npm list", "pnpm list",
    ]
    for prefix in read_prefixes:
        if cmd_lower.startswith(prefix):
            return (
                CommandCategory.READ,
                PermissionRisk.AUTOMATIC,
                "Read-only workspace inspection command."
            )

    # 7. Unfamiliar / Potentially modifying commands -> Requires approval
    return (
        CommandCategory.UNKNOWN,
        PermissionRisk.REQUIRES_APPROVAL,
        "Unrecognized command requires explicit user verification before execution."
    )
