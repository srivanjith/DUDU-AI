# DODO Security & Isolation Architecture

## 1. Zero Trust Model Execution

Large Language Models (LLMs) are never granted direct operating-system shell access. All actions are routed through the `ToolRegistry` and vetted by permission managers.

### Security Boundaries:
1. **Workspace Path Jail**: All filesystem operations (`read_file`, `write_file`, `edit_file`) resolve relative to `AUTHORIZED_WORKSPACE_DIR` (`D:\DODO\workspace`). Path traversal attacks (such as `../../windows/system32`) trigger immediate security violations.
2. **Command Sanitization**: Terminal commands are inspected for dangerous patterns (`rmdir /s /q c:`, `format`, `del /s /q c:\windows`, etc.). Destructive commands are strictly prohibited.
3. **Secret Redaction**: Regex scanners scrub API keys, bearer tokens, passwords, and MongoDB authentication strings from execution logs and API responses.
4. **Local Agent Authentication**: The separate `local_agent` service enforces header token verification (`X-DODO-Token`). Unauthenticated requests are rejected with HTTP 401.

---

## 2. Command Permission Matrix

| Operation Category | Automatic Execution | Requires Confirmation | Prohibited |
|---|:---:|:---:|:---:|
| Project Inspection (`git status`, `dir`, `read_file`) | ✅ | — | — |
| Workspace File Creation (`write_file`) | ✅ (Controlled) | — | — |
| File Modification (`edit_file`) | ✅ (Generates Diff) | — | — |
| Build / Test Execution (`pytest`, `npm test`) | ✅ | — | — |
| Package Installation (`npm install`, `pip install`) | ✅ (Controlled) | — | — |
| Destructive File Deletion (`delete_file`) | — | ✅ | — |
| System Modification (`format`, `shutdown`) | — | — | ❌ |

