# 🛡️ DODO Security & Sandbox Boundaries

## Security Principles

DODO is designed to operate on your local development machine with complete autonomy under strict, auditable user-controlled boundaries:

1. **Path Jailing**: All filesystem operations are strictly jailed inside the authorized workspace directory (`D:\DODO\workspace`). Path traversal attempts (`../..`) are blocked.
2. **Local Agent Authentication**: The Python Local Agent (port 8001) requires a pre-shared cryptographic bearer token (`LOCAL_AGENT_SECRET_TOKEN`) to accept command execution requests.
3. **Command Permission Registry**:
   - **Automatic (READ)**: Read-only inspection (`git status`, `git diff`, `dir`, `ls`, `cat`, `node -v`).
   - **Controlled**: Known project build commands (`npm install`, `pip install`, `pytest`).
   - **Requires Approval**: Unfamiliar commands, delete operations, or long-running development servers.
   - **Prohibited**: Destructive shell patterns (`format C:`, `del /f /s C:\Windows`, `rm -rf /`, `shutdown`, `drop database`).
4. **Browser Automation Security (`BrowserSecurityPolicy`)**:
   - Blocks dangerous protocols: `file://`, `javascript:`.
   - Allows safe development environments: `http://localhost:*`, `http://127.0.0.1:*`, `data:text/html`.
   - Sensitive Action Gating: Clicks on buttons containing "delete", "remove", "drop", "purge", "checkout", or "pay" mandate explicit user approval.
5. **Secret Filtering & Memory Privacy**:
   - API keys, JWT bearer tokens, AWS credentials, and passwords are automatically redacted before logging or persistence (`[REDACTED_SECRET]`).
   - Hidden chain-of-thought traces (`<think>...</think>`) are filtered from memory storage.
   - Prompt injection attempts inside stored memories are neutralized.
6. **Zero Unauthorized External Transmission**:
   - DODO never sends code, private files, or persistent memory data to external cloud AI APIs.
