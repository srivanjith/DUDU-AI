"""
DODO Browser Security & Domain Access Policy
Enforces URL validation, protocol restrictions, localhost development support,
sensitive action detection, and audit logging.
"""
import datetime
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

logger = logging.getLogger("dodo.browser.security")

# Allowed schemes
ALLOWED_SCHEMES = {"http", "https", "data"}

# Prohibited schemes that escape sandbox or read local filesystem
PROHIBITED_SCHEMES = {"file", "javascript", "vbscript", "about", "chrome", "edge", "view-source"}

# Localhost hosts
LOCALHOST_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}

# Sensitive action keyword patterns in selectors, values, or button text
SENSITIVE_ACTION_PATTERNS = [
    r"\b(delete|remove|destroy|drop|purge|truncate)\b",
    r"\b(checkout|purchase|pay|buy|transfer)\b",
    r"\b(send\s+message|publish|broadcast)\b",
    r"\b(create\s+account|sign\s+up|register)\b",
]


class BrowserAuditRecord:
    def __init__(
        self,
        action: str,
        target: str,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error: Optional[str] = None,
    ):
        self.action = action
        self.target = target
        self.details = details or {}
        self.success = success
        self.error = error
        self.timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "target": self.target,
            "details": self.details,
            "success": self.success,
            "error": self.error,
            "timestamp": self.timestamp,
        }


class BrowserSecurityPolicy:
    """Enforces strict navigation safety and action gating."""

    def __init__(self):
        self._audit_history: List[BrowserAuditRecord] = []
        self._max_audit = 500
        self.allowed_domains: Set[str] = set()  # Empty means all http/https allowed unless denylisted
        self.denied_domains: Set[str] = {
            "malware.com", "phishing.com", "169.254.169.254" # Cloud metadata IP
        }

    def validate_url(self, url: str) -> Tuple[bool, str]:
        """
        Validates URL against security rules:
        - Blocks file:// to prevent reading arbitrary local filesystem files.
        - Blocks javascript:, about:, chrome:.
        - Permits localhost/127.0.0.1 development servers.
        - Permits standard HTTP/HTTPS websites.
        """
        if not url or not url.strip():
            return False, "URL cannot be empty."

        clean_url = url.strip()

        # Handle data: URLs (used for internal offline tests)
        if clean_url.startswith("data:"):
            if clean_url.startswith("data:text/html"):
                return True, ""
            return False, "Only data:text/html data URLs are permitted."

        try:
            parsed = urlparse(clean_url)
            scheme = (parsed.scheme or "").lower()

            if scheme in PROHIBITED_SCHEMES or scheme == "file":
                return False, f"Security Policy Violation: Scheme '{scheme}://' is prohibited. Local file access is blocked."

            if scheme not in ALLOWED_SCHEMES:
                return False, f"Unsupported URL scheme '{scheme}'. Only http:// and https:// are permitted."

            hostname = (parsed.hostname or "").lower()
            if not hostname:
                return False, "Invalid URL: Missing hostname."

            # Check denylist
            if hostname in self.denied_domains:
                return False, f"Access to domain '{hostname}' is denied by security policy."

            # Allow localhost / 127.0.0.1 development testing unconditionally
            if hostname in LOCALHOST_HOSTS:
                return True, ""

            # Check allowlist if configured
            if self.allowed_domains and hostname not in self.allowed_domains:
                return False, f"Domain '{hostname}' is not in the authorized domain allowlist."

            return True, ""
        except Exception as e:
            return False, f"Invalid URL format: {str(e)}"

    def check_sensitive_interaction(
        self,
        action: str,
        selector: str,
        value: str = "",
        approved: bool = False,
    ) -> Tuple[bool, bool, str]:
        """
        Checks if a click, fill, or form submission is potentially sensitive.
        Returns (is_allowed, requires_approval, reason).
        """
        target_str = f"{action} {selector} {value}".lower()

        for pat in SENSITIVE_ACTION_PATTERNS:
            if re.search(pat, target_str):
                reason = f"Action '{action}' on '{selector}' matches sensitive pattern '{pat}'."
                if not approved:
                    return False, True, f"Approval Required: {reason}"
                return True, False, "Approved sensitive action."

        return True, False, ""

    def log_action(
        self,
        action: str,
        target: str,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error: Optional[str] = None,
    ):
        record = BrowserAuditRecord(action, target, details, success, error)
        self._audit_history.append(record)
        if len(self._audit_history) > self._max_audit:
            self._audit_history.pop(0)

    def get_audit_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._audit_history[-limit:]]


browser_security = BrowserSecurityPolicy()

