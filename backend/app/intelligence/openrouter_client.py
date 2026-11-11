"""
DODO OpenRouter Cloud AI Provider
Integrates NVIDIA Nemotron 3 Ultra (nvidia/nemotron-3-ultra-550b-a55b:free) via OpenRouter.
Provides:
- Non-streaming and Server-Sent Event (SSE) streaming chat completions
- Robust error handling (401, 403, 429, timeouts, malformed responses)
- Tool calling integration with DODO's secure tool registry
- Strict privacy controls & secret redaction (never transmit .env, private keys, or credentials)
- Text-only enforcement (blocks image/video payloads)
- Graceful fallback guidance to local Qwen2.5-Coder
"""
import asyncio
import json
import logging
import re
import time
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, Tuple
import httpx

from backend.app.core.config import settings
from backend.app.core.security import redact_secrets
from backend.app.tools.registry import tool_registry

logger = logging.getLogger("dodo.intelligence.openrouter")

NEMOTRON_MODEL_ID = "nvidia/nemotron-3-ultra-550b-a55b:free"


class OpenRouterError(Exception):
    """Base exception for OpenRouter operations."""
    def __init__(self, message: str, status_code: Optional[int] = None, error_code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or "OPENROUTER_ERROR"


class PrivacyViolationError(Exception):
    """Raised when private environment or credential data is detected in outgoing cloud payload."""
    pass


class OpenRouterClient:
    """
    OpenAI-compatible client for OpenRouter cloud inference.
    Pinned model: nvidia/nemotron-3-ultra-550b-a55b:free
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_id: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self._api_key = api_key if api_key is not None else settings.OPENROUTER_API_KEY
        self.base_url = (base_url or settings.OPENROUTER_BASE_URL).rstrip("/")
        self.model_id = model_id or settings.OPENROUTER_MODEL or NEMOTRON_MODEL_ID
        self.timeout = timeout or settings.OPENROUTER_TIMEOUT_SECONDS

    @property
    def api_key(self) -> Optional[str]:
        if self._api_key is not None:
            return self._api_key
        return settings.OPENROUTER_API_KEY or os.environ.get("OPENROUTER_API_KEY")

    def is_configured(self) -> bool:
        """Returns True if a valid non-empty API key is present."""
        key = self.api_key
        return bool(key and len(key.strip()) > 5)

    def get_headers(self) -> Dict[str, str]:
        """Constructs secure request headers. Never logs the API key."""
        key = self.api_key or ""
        return {
            "Authorization": f"Bearer {key.strip()}",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "DODO Autonomous AI IDE",
            "Content-Type": "application/json",
        }

    # -------------------------------------------------------------------------
    # PRIVACY CONTROLS & SANITIZATION (Critical Safety Rule)
    # -------------------------------------------------------------------------
    def sanitize_messages_for_cloud(
        self,
        messages: List[Dict[str, Any]],
        cloud_consent: bool = True
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Applies privacy guard before cloud transmission:
        1. Redacts secrets (passwords, tokens, database URIs, API keys).
        2. Blocks/redacts any '.env' or credential blocks.
        3. Strips image and video inputs (Nemotron 3 Ultra is text-only).
        4. Returns sanitized messages and a list of redaction notices.
        """
        sanitized = []
        notices = []

        # Prohibited patterns that must never reach a third-party cloud endpoint
        prohibited_indicators = [
            r"BEGIN\s+(RSA|OPENSSH|EC|DSA|PRIVATE)\s+KEY",
            r"MONGODB_URI\s*=\s*[^\r\n]+",
            r"mongodb(?:\+srv)?:\/\/[^\s\"']+",
            r"OPENROUTER_API_KEY\s*=\s*[a-zA-Z0-9_\-]+",
            r"SECRET_KEY\s*=\s*[a-zA-Z0-9_\-]+",
        ]

        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")

            # If content is a list of blocks (multimodal format), enforce text-only
            if isinstance(content, list):
                text_parts = []
                for part in content:
                    if isinstance(part, dict):
                        if part.get("type") == "text":
                            text_parts.append(part.get("text", ""))
                        elif part.get("type") in ["image_url", "image", "video"]:
                            notices.append(f"Omitted non-text {part.get('type')} block (Nemotron 3 Ultra is text-only).")
                            text_parts.append("[Non-text media omitted: Model is text-only]")
                    elif isinstance(part, str):
                        text_parts.append(part)
                content = "\n".join(text_parts)

            if not isinstance(content, str):
                content = str(content)

            # Check for critical secrets
            for pattern in prohibited_indicators:
                if re.search(pattern, content, re.IGNORECASE):
                    notices.append("Redacted sensitive environment/private key configuration from outgoing cloud prompt.")
                    content = re.sub(pattern, "[SENSITIVE CREDENTIAL REDACTED BY DODO PRIVACY GUARD]", content, flags=re.IGNORECASE)

            # Apply general secret redaction
            redacted_content = redact_secrets(content)
            if redacted_content != content:
                notices.append("Redacted potential secrets/tokens using DODO Security Policy.")

            sanitized.append({
                "role": role,
                "content": redacted_content,
            })

        return sanitized, notices

    # -------------------------------------------------------------------------
    # FORMAT DODO TOOLS FOR OPENAI SCHEMA
    # -------------------------------------------------------------------------
    def format_dodo_tools(self, tool_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Converts registered DODO tools into OpenAI-compatible tool specifications."""
        definitions = tool_registry.list_definitions()
        openai_tools = []

        type_map = {
            "string": "string",
            "str": "string",
            "integer": "integer",
            "int": "integer",
            "boolean": "boolean",
            "bool": "boolean",
            "number": "number",
            "float": "number",
            "array": "array",
            "list": "array",
            "object": "object",
            "dict": "object",
        }

        for d in definitions:
            name = d.get("name")
            if tool_names and name not in tool_names:
                continue

            properties = {}
            required = []

            for p in d.get("parameters", []):
                p_name = p.get("name")
                p_type = type_map.get(str(p.get("type", "string")).lower(), "string")
                properties[p_name] = {
                    "type": p_type,
                    "description": p.get("description", ""),
                }
                if p.get("required", False):
                    required.append(p_name)

            openai_tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": d.get("description", ""),
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                    },
                },
            })

        return openai_tools

    # -------------------------------------------------------------------------
    # NON-STREAMING CHAT COMPLETION
    # -------------------------------------------------------------------------
    async def chat_complete(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Executes non-streaming chat completion with OpenRouter."""
        if not self.is_configured():
            raise OpenRouterError(
                "OPENROUTER_API_KEY is not configured in backend/.env. "
                "Please configure an OpenRouter API key to use NVIDIA Nemotron 3 Ultra, or switch to local Qwen.",
                status_code=401,
                error_code="OPENROUTER_API_KEY_MISSING",
            )

        target_model = model or self.model_id
        sanitized_messages, notices = self.sanitize_messages_for_cloud(messages)

        payload: Dict[str, Any] = {
            "model": target_model,
            "messages": sanitized_messages,
            "temperature": temperature,
            "stream": False,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice or "auto"

        url = f"{self.base_url}/chat/completions"
        start_time = time.perf_counter()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(url, headers=self.get_headers(), json=payload)
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

                if res.status_code == 200:
                    data = res.json()
                    choice = data.get("choices", [{}])[0]
                    message = choice.get("message", {})
                    usage = data.get("usage", {})

                    return {
                        "content": message.get("content") or "",
                        "tool_calls": message.get("tool_calls", []) or [],
                        "model": data.get("model", target_model),
                        "finish_reason": choice.get("finish_reason", "stop"),
                        "usage": usage,
                        "duration_ms": duration_ms,
                        "privacy_notices": notices,
                    }
                else:
                    self._handle_http_error(res)

        except httpx.TimeoutException:
            raise OpenRouterError(
                f"OpenRouter request timed out after {self.timeout} seconds.",
                error_code="TIMEOUT_ERROR",
            )
        except httpx.RequestError as e:
            raise OpenRouterError(
                f"Network error connecting to OpenRouter at {self.base_url}: {e}",
                error_code="NETWORK_ERROR",
            )

    # -------------------------------------------------------------------------
    # STREAMING CHAT COMPLETION (SSE)
    # -------------------------------------------------------------------------
    async def chat_stream(
        self,
        model: Optional[str],
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Streams chat completion tokens from OpenRouter.
        Yields structured events matching DODO SSE schema:
        - {"content": str, "done": False, "model": str}
        - {"tool_calls": list, "done": False, "model": str}
        - {"done": True, "eval_count": int, "usage": dict}
        - {"error": str, "error_code": str, "done": True, "can_fallback_to_qwen": True}
        """
        target_model = model or self.model_id

        if not self.is_configured():
            err_msg = (
                "⚠️ **OpenRouter API Key Missing**\n\n"
                "`OPENROUTER_API_KEY` is not set in `D:\\DODO\\.env`.\n\n"
                "To use **NVIDIA Nemotron 3 Ultra (Cloud)**, add your API key:\n"
                "```env\n"
                "OPENROUTER_API_KEY=sk-or-v1-...\n"
                "```\n"
                "💡 Alternatively, select **qwen2.5-coder:1.5b (Local Ollama)** from the model selector."
            )
            yield {
                "error": err_msg,
                "error_code": "OPENROUTER_API_KEY_MISSING",
                "done": True,
                "model": target_model,
                "can_fallback_to_qwen": True,
            }
            return

        sanitized_messages, notices = self.sanitize_messages_for_cloud(messages)

        opts = options or {}
        payload: Dict[str, Any] = {
            "model": target_model,
            "messages": sanitized_messages,
            "stream": True,
            "temperature": opts.get("temperature", 0.3),
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice or "auto"

        url = f"{self.base_url}/chat/completions"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    url,
                    headers=self.get_headers(),
                    json=payload,
                ) as response:
                    if response.status_code != 200:
                        err_bytes = await response.aread()
                        err_text = err_bytes.decode("utf-8", errors="replace")
                        err_obj = self._format_error_message(response.status_code, err_text)
                        yield {
                            "error": err_obj["message"],
                            "error_code": err_obj["code"],
                            "done": True,
                            "model": target_model,
                            "can_fallback_to_qwen": True,
                        }
                        return

                    accumulated_content = []
                    accumulated_tool_calls: Dict[int, Dict[str, Any]] = {}
                    usage_meta = {}

                    async for line in response.aiter_lines():
                        line = line.strip()
                        if not line:
                            continue
                        if line == "data: [DONE]":
                            break
                        if line.startswith("data: "):
                            raw_json = line[6:]
                            try:
                                chunk = json.loads(raw_json)
                                choice = chunk.get("choices", [{}])[0]
                                delta = choice.get("delta", {})
                                finish_reason = choice.get("finish_reason")

                                # Check text delta
                                text = delta.get("content")
                                if text:
                                    accumulated_content.append(text)
                                    yield {
                                        "content": text,
                                        "done": False,
                                        "model": target_model,
                                    }

                                # Check tool calls delta
                                delta_tools = delta.get("tool_calls")
                                if delta_tools:
                                    for t_chunk in delta_tools:
                                        idx = t_chunk.get("index", 0)
                                        if idx not in accumulated_tool_calls:
                                            accumulated_tool_calls[idx] = {
                                                "id": t_chunk.get("id", f"call_{idx}_{int(time.time())}"),
                                                "type": "function",
                                                "function": {"name": "", "arguments": ""},
                                            }
                                        fn = t_chunk.get("function", {})
                                        if fn.get("name"):
                                            accumulated_tool_calls[idx]["function"]["name"] += fn["name"]
                                        if fn.get("arguments"):
                                            accumulated_tool_calls[idx]["function"]["arguments"] += fn["arguments"]

                                if chunk.get("usage"):
                                    usage_meta = chunk["usage"]

                            except Exception as parse_err:
                                logger.debug(f"Error parsing SSE chunk: {parse_err}")
                                continue

                    # If tool calls were accumulated, emit them before completion
                    if accumulated_tool_calls:
                        parsed_calls = list(accumulated_tool_calls.values())
                        yield {
                            "tool_calls": parsed_calls,
                            "done": False,
                            "model": target_model,
                        }

                    yield {
                        "done": True,
                        "model": target_model,
                        "eval_count": len(accumulated_content),
                        "usage": usage_meta,
                    }

        except httpx.TimeoutException:
            yield {
                "error": f"OpenRouter inference timed out after {self.timeout}s. Switch to local Qwen or retry.",
                "error_code": "TIMEOUT_ERROR",
                "done": True,
                "model": target_model,
                "can_fallback_to_qwen": True,
            }
        except Exception as e:
            yield {
                "error": f"OpenRouter communication failure: {str(e)}",
                "error_code": "CONNECTION_ERROR",
                "done": True,
                "model": target_model,
                "can_fallback_to_qwen": True,
            }

    # -------------------------------------------------------------------------
    # MULTI-ROUND SECURE TOOL CALLING ORCHESTRATOR
    # -------------------------------------------------------------------------
    async def run_tool_calling_loop(
        self,
        prompt: str,
        workspace_path: str,
        system_prompt: Optional[str] = None,
        max_iterations: int = 5,
        approved: bool = False,
        cancellation_token: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Executes a secure multi-round tool calling cycle with Nemotron 3 Ultra:
        1. Formats registered DODO tools.
        2. Calls model with tools.
        3. Parses model-generated function calls (safely handles non-JSON / malformed syntax).
        4. Enforces DODO backend permissions via tool_registry.
        5. Feeds tool execution results back into next iteration.
        6. Respects iteration limits and cancellation tokens.
        """
        dodo_tools = self.format_dodo_tools()
        messages: List[Dict[str, Any]] = []

        sys_msg = system_prompt or (
            "You are DODO, an autonomous AI software development assistant powered by NVIDIA Nemotron 3 Ultra. "
            "You have access to tools for filesystem operations and code synthesis. "
            "Call the appropriate tools with valid JSON arguments to fulfill the user request."
        )
        messages.append({"role": "system", "content": sys_msg})
        messages.append({"role": "user", "content": prompt})

        iterations = 0
        executed_tool_records = []

        while iterations < max_iterations:
            iterations += 1

            # Check cancellation token
            if cancellation_token and getattr(cancellation_token, "is_cancelled", False):
                return {
                    "success": False,
                    "cancelled": True,
                    "message": "Task cancelled by user.",
                    "tool_history": executed_tool_records,
                }

            # Call Nemotron
            res = await self.chat_complete(
                messages=messages,
                tools=dodo_tools,
                tool_choice="auto",
            )

            tool_calls = res.get("tool_calls", [])
            content = res.get("content", "")

            # If no tools were invoked, model reached final answer
            if not tool_calls:
                return {
                    "success": True,
                    "final_response": content,
                    "iterations": iterations,
                    "tool_history": executed_tool_records,
                }

            # Append assistant message with tool calls
            messages.append({
                "role": "assistant",
                "content": content or "",
                "tool_calls": tool_calls,
            })

            # Execute each proposed tool securely
            for tc in tool_calls:
                call_id = tc.get("id", f"call_{iterations}")
                fn = tc.get("function", {})
                tool_name = fn.get("name", "")
                raw_args = fn.get("arguments", "{}")

                # Robust JSON argument parsing (free endpoint doesn't enforce response_format)
                parsed_args = {}
                try:
                    if isinstance(raw_args, str):
                        parsed_args = json.loads(raw_args)
                    elif isinstance(raw_args, dict):
                        parsed_args = raw_args
                except Exception as json_err:
                    err_resp = f"Error: Tool arguments were not valid JSON: {json_err}. Raw: {raw_args}"
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "name": tool_name,
                        "content": json_resp(err_resp),
                    })
                    executed_tool_records.append({
                        "tool": tool_name,
                        "success": False,
                        "error": err_resp,
                    })
                    continue

                # Ensure workspace root is bound
                if "workspace_root" not in parsed_args and "workspace_path" not in parsed_args:
                    parsed_args["workspace_root"] = workspace_path

                # Execute through existing DODO Tool Registry with permission enforcement
                exec_result = await tool_registry.execute(
                    tool_name=tool_name,
                    parameters=parsed_args,
                    enforce_permissions=True,
                    approved=approved,
                )

                executed_tool_records.append({
                    "tool": tool_name,
                    "args": parsed_args,
                    "result": exec_result,
                })

                # If execution blocked due to permissions, return early with notice
                if exec_result.get("permission_denied"):
                    return {
                        "success": False,
                        "needs_approval": True,
                        "blocked_tool": tool_name,
                        "permission_required": exec_result.get("permission_required"),
                        "message": exec_result.get("error"),
                        "tool_history": executed_tool_records,
                    }

                # Feed execution result back into conversation
                tool_output_str = json.dumps(exec_result)
                messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": tool_name,
                    "content": tool_output_str,
                })

        return {
            "success": True,
            "final_response": "Reached maximum tool iteration limit.",
            "iterations": iterations,
            "tool_history": executed_tool_records,
        }

    # -------------------------------------------------------------------------
    # ERROR CLASSIFICATION & USER GUIDANCE
    # -------------------------------------------------------------------------
    def _format_error_message(self, status_code: int, err_text: str) -> Dict[str, str]:
        """Provides human-readable diagnostic messages with actionable remediation."""
        if status_code == 401:
            return {
                "code": "AUTH_FAILED",
                "message": (
                    "🔑 **OpenRouter Authentication Failed (HTTP 401)**\n\n"
                    "Your `OPENROUTER_API_KEY` is invalid or unauthorized.\n\n"
                    "**Actions:**\n"
                    "1. Check your API key at [openrouter.ai/keys](https://openrouter.ai/keys)\n"
                    "2. Update `OPENROUTER_API_KEY` in `D:\\DODO\\.env`\n"
                    "3. Or switch back to **qwen2.5-coder:1.5b (Local)**."
                ),
            }
        elif status_code == 403:
            return {
                "code": "ACCESS_FORBIDDEN",
                "message": (
                    "⛔ **Access Forbidden (HTTP 403)**\n\n"
                    f"Model `{self.model_id}` is restricted or unavailable on this account.\n"
                    f"Details: {err_text}"
                ),
            }
        elif status_code == 429:
            return {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": (
                    "⏳ **OpenRouter Rate Limit Exceeded (HTTP 429)**\n\n"
                    "Free tier rate limit reached for `nvidia/nemotron-3-ultra-550b-a55b:free`.\n\n"
                    "**Recommendation:**\n"
                    "Switch to **qwen2.5-coder:1.5b (Local Ollama)** to continue coding without rate limits."
                ),
            }
        elif status_code in [500, 502, 503, 504]:
            return {
                "code": "PROVIDER_UNAVAILABLE",
                "message": (
                    f"🌐 **OpenRouter Cloud Service Unavailable (HTTP {status_code})**\n\n"
                    "The upstream provider is experiencing temporary downtime.\n"
                    "Select local Qwen from the model selector to work offline."
                ),
            }
        else:
            return {
                "code": f"HTTP_{status_code}",
                "message": f"OpenRouter Error ({status_code}): {err_text}",
            }

    def _handle_http_error(self, res: httpx.Response):
        err_text = res.text
        fmt = self._format_error_message(res.status_code, err_text)
        raise OpenRouterError(fmt["message"], status_code=res.status_code, error_code=fmt["code"])


def json_resp(text: str) -> str:
    return json.dumps({"message": text})


openrouter_client = OpenRouterClient()
