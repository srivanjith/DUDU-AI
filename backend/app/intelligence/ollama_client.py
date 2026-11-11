import asyncio
import json
import logging
import os
import platform
import shutil
import subprocess
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


def find_ollama_executable() -> Optional[str]:
    """Finds the local Ollama binary across PATH and standard platform locations."""
    # 1. System PATH
    p = shutil.which("ollama")
    if p and os.path.isfile(p):
        return p

    # 2. Windows standard installation locations
    if platform.system() == "Windows":
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if local_app_data:
            candidate = os.path.join(local_app_data, "Programs", "Ollama", "ollama.exe")
            if os.path.isfile(candidate):
                return candidate
        prog_files = os.environ.get("ProgramFiles", "")
        if prog_files:
            candidate = os.path.join(prog_files, "Ollama", "ollama.exe")
            if os.path.isfile(candidate):
                return candidate
    return None


class OllamaClient:
    """
    Client for interacting with local Ollama inference server.
    Provides strict health checks, dynamic model discovery, capability inspection,
    streaming completions, background daemon spawning for Windows/local dev,
    and graceful error handling. Does NOT fabricate model responses.
    """

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.timeout = settings.OLLAMA_TIMEOUT_SECONDS
        self._last_health: Optional[Dict[str, Any]] = None
        self._last_health_ts: float = 0.0

    async def check_health(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Checks if Ollama daemon is running, responsive, and measures latency."""
        now = time.time()
        if not force_refresh and self._last_health and (now - self._last_health_ts < 2.0):
            return self._last_health

        start_time = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{self.base_url}/api/version")
                latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
                if res.status_code == 200:
                    version_info = res.json()
                    models = await self.list_models()
                    result = {
                        "status": "online",
                        "version": version_info.get("version", "unknown"),
                        "base_url": self.base_url,
                        "latency_ms": latency_ms,
                        "model_count": len(models),
                        "models": [m.get("name", "") for m in models],
                        "can_start": False,
                    }
                    self._last_health = result
                    self._last_health_ts = now
                    return result
        except Exception as e:
            logger.debug(f"Ollama health check failed: {e}")

        exe_path = find_ollama_executable()
        result = {
            "status": "offline",
            "base_url": self.base_url,
            "latency_ms": None,
            "error": f"Ollama service is not reachable at {self.base_url}.",
            "model_count": 0,
            "models": [],
            "can_start": bool(exe_path),
            "executable_path": exe_path,
        }
        self._last_health = result
        self._last_health_ts = now
        return result

    async def start_daemon(self, timeout_seconds: int = 10) -> Dict[str, Any]:
        """
        Attempts to start the local Ollama daemon if offline on the host machine.
        Returns operational status and verification.
        """
        current_health = await self.check_health(force_refresh=True)
        if current_health.get("status") == "online":
            return {
                "status": "online",
                "message": "Ollama daemon is already online and operational.",
                "version": current_health.get("version"),
                "models": current_health.get("models", []),
            }

        exe = find_ollama_executable()
        if not exe:
            return {
                "status": "error",
                "error": "Ollama executable not found on host machine. Please install Ollama from https://ollama.com.",
                "can_start": False,
            }

        try:
            creationflags = 0
            if platform.system() == "Windows":
                # DETACHED_PROCESS and CREATE_NO_WINDOW
                creationflags = 0x00000008 | 0x08000000

            proc = subprocess.Popen(
                [exe, "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=creationflags,
                shell=False,
            )
            logger.info(f"Spawned Ollama background daemon process PID={proc.pid}")

            # Poll for daemon availability
            start_t = time.perf_counter()
            while time.perf_counter() - start_t < timeout_seconds:
                await asyncio.sleep(0.5)
                h = await self.check_health(force_refresh=True)
                if h.get("status") == "online":
                    return {
                        "status": "online",
                        "message": "Ollama daemon started successfully and is operational.",
                        "pid": proc.pid,
                        "version": h.get("version"),
                        "models": h.get("models", []),
                    }

            return {
                "status": "starting",
                "message": f"Ollama daemon process (PID {proc.pid}) was spawned, but initialization is taking longer than {timeout_seconds}s.",
                "pid": proc.pid,
            }
        except Exception as e:
            logger.error(f"Failed to start Ollama daemon: {e}")
            return {
                "status": "error",
                "error": f"Failed to start Ollama daemon process: {str(e)}",
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
                "To start Ollama locally, click 'Start Ollama' or run in your terminal:\n"
                "```powershell\n"
                "ollama serve\n"
                "```"
            )
            yield {
                "error": err_msg,
                "error_code": "OLLAMA_OFFLINE",
                "done": True,
                "model": model,
                "base_url": self.base_url,
                "can_start": health.get("can_start", False),
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
                "installed_models": installed_names,
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
        except httpx.ConnectError:
            yield {
                "error": f"Connection refused by Ollama daemon at {self.base_url}. The daemon may have stopped or restarted.",
                "error_code": "OLLAMA_OFFLINE",
                "done": True,
                "model": model,
                "can_start": True,
            }
        except httpx.TimeoutException:
            yield {
                "error": f"Inference timed out after {self.timeout} seconds.",
                "error_code": "INFERENCE_TIMEOUT",
                "done": True,
                "model": model,
            }
        except (httpx.RemoteProtocolError, httpx.ReadError) as e:
            yield {
                "error": f"Streaming connection interrupted by server ({type(e).__name__}). Ollama may have crashed or restarted.",
                "error_code": "STREAM_INTERRUPTED",
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
