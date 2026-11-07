from pathlib import Path
from typing import Optional, Tuple
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from local_agent.config import local_settings

api_key_header = APIKeyHeader(name="X-DODO-Token", auto_error=False)


def verify_token(token: Optional[str] = Security(api_key_header)) -> bool:
    if not token or token != local_settings.SECRET_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid or missing DODO Local Agent authentication token."
        )
    return True


def jail_path(relative_or_absolute: str) -> Tuple[bool, Path, str]:
    root = Path(local_settings.AUTHORIZED_WORKSPACE).resolve()
    root.mkdir(parents=True, exist_ok=True)
    try:
        target = Path(relative_or_absolute)
        resolved = (root / target).resolve() if not target.is_absolute() else target.resolve()
        resolved.relative_to(root)
        return True, resolved, ""
    except ValueError:
        return False, Path(relative_or_absolute), f"Path jail violation: '{relative_or_absolute}' escapes authorized workspace '{root}'."
    except Exception as e:
        return False, Path(relative_or_absolute), str(e)

