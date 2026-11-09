import asyncio
import json
import logging
import time
from typing import Any, AsyncGenerator, Dict, List, Optional
import httpx
from backend.app.core.config import settings

logger = logging.getLogger("dodo.intelligence.ollama")


class OllamaServiceError(Exception):
    """Raised when Ollama server cannot be reached."""
    pass


class ModelNotFoundError(Exception):
    """Raised when the requested model is not installed locally in Ollama."""
    pass


class OllamaClient:
    """
    Client for interacting with local Ollama inference server.
    Provides strict health checks, dynamic model discovery, capability inspection,
    streaming completions, and graceful error handling.
    Does NOT fabricate model responses.
    """

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.timeout = settings.OLLAMA_TIMEOUT_SECONDS

    async def check_health(self) -> Dict[str, Any]:
        """Checks if Ollama daemon is running, responsive, and measures latency."""
        start_time = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{self.base_url}/api/version")
                latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
                if res.status_code == 200:
                    version_info = res.json()
                    models = await self.list_models()
                    return {
                        "status": "online",
                        "version": version_info.get("version", "unknown"),
                        "base_url": self.base_url,
                        "latency_ms": latency_ms,
                        "model_count": len(models),
                        "models": [m.get("name", "") for m in models],
                    }
        except Exception as e:
            logger.debug(f"Ollama health check failed: {e}")

        return {
            "status": "offline",
            "base_url": self.base_url,
            "latency_ms": None,
            "error": f"Ollama service is not reachable at {self.base_url}. Start it with 'ollama serve'.",
            "model_count": 0,
            "models": [],
        }

    async def list_models(self) -> List[Dict[str, Any]]:
        """Discovers locally installed models in Ollama with sizes and metadata."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    raw_models = data.get("models", [])
                    parsed = []
                    for m in raw_models:
                        details = m.get("details", {})
                        parsed.append({
                            "name": m.get("name", ""),
                            "model": m.get("model", ""),
                            "size": m.get("size", 0),
                            "size_gb": round(m.get("size", 0) / (1024 ** 3), 2),
                            "digest": m.get("digest", "")[:12],
                            "modified_at": m.get("modified_at", ""),
                            "family": details.get("family", ""),
                            "parameter_size": details.get("parameter_size", ""),
                            "quantization_level": details.get("quantization_level", ""),
                        })
                    return parsed
        except Exception as e:
            logger.debug(f"Could not reach Ollama at {self.base_url}: {e}")
        return []

    async def show_model(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves detailed architecture and template information for a specific model."""
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.post(f"{self.base_url}/api/show", json={"name": model_name})
                if res.status_code == 200:
                    return res.json()
        except Exception as e:
            logger.debug(f"Could not inspect model '{model_name}': {e}")
        return None

    async def is_model_available(self, model_name: str) -> bool:
        """Verifies if the specific model is currently downloaded in local Ollama."""
        models = await self.list_models()
        target = model_name.strip()
        for m in models:
            name = m.get("name", "")
            if name == target or name.startswith(f"{target}:") or target.startswith(f"{name}:"):
                return True
        return False

    async def chat_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        options: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Streams chat tokens from Ollama.
        Does NOT fake AI responses. If Ollama is offline or model is missing,
        yields clear structured error events.
        """
        health = await self.check_health()
        if health["status"] != "online":
            err_msg = (
                f"Ollama inference daemon is offline at {self.base_url}.\n\n"
                "To start Ollama locally, run in your terminal:\n"
                "```powershell\n"
                "ollama serve\n"
                "```"
            )
            yield {
                "error": err_msg,
                "error_code": "OLLAMA_OFFLINE",
                "done": True,
                "model": model,
            }
            return

        # Check if the requested model is actually installed
        available = await self.is_model_available(model)
        if not available:
            installed = await self.list_models()
            installed_names = [m["name"] for m in installed]
            err_msg = (
                f"Model `{model}` is not installed in local Ollama.\n\n"
                f"Currently installed models: {installed_names if installed_names else 'None'}\n\n"
                "To download this model, run with approval in your terminal:\n"
                f"```powershell\nollama pull {model}\n```"
            )
            yield {
                "error": err_msg,
                "error_code": "MODEL_NOT_FOUND",
                "done": True,
                "model": model,
            }
            return

        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": options or {"temperature": 0.3, "num_ctx": 4096},
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json=payload,
                ) as response:
                    if response.status_code != 200:
                        err_text = await response.aread()
                        yield {
                            "error": f"Ollama HTTP {response.status_code}: {err_text.decode('utf-8', errors='replace')}",
                            "error_code": "OLLAMA_HTTP_ERROR",
                            "done": True,
                            "model": model,
                        }
                        return

                    async for line in response.aiter_lines():
                        if line:
                            try:
                                chunk = json.loads(line)
                                content = chunk.get("message", {}).get("content", "")
                                done = chunk.get("done", False)
                                yield {
                                    "content": content,
                                    "done": done,
                                    "model": model,
                                    "total_duration": chunk.get("total_duration"),
                                    "eval_count": chunk.get("eval_count"),
                                    "eval_duration": chunk.get("eval_duration"),
                                }
                            except Exception:
                                continue
        except httpx.TimeoutException:
            yield {
                "error": f"Inference timed out after {self.timeout} seconds.",
                "error_code": "INFERENCE_TIMEOUT",
                "done": True,
                "model": model,
            }
        except Exception as e:
            yield {
                "error": f"Ollama connection error during inference: {str(e)}",
                "error_code": "CONNECTION_ERROR",
                "done": True,
                "model": model,
            }


ollama_client = OllamaClient()
