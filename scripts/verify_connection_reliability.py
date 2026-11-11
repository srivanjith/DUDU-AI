import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Ensure quick timeout for offline databases in test mode
os.environ["MONGODB_SERVER_SELECTION_TIMEOUT_MS"] = "500"

from backend.app.core.config import settings
from backend.app.intelligence.ollama_client import ollama_client, find_ollama_executable
from backend.app.intelligence.openrouter_client import (
    openrouter_client,
    NEMOTRON_MODEL_ID,
    NEMOTRON_SUPER_VL_ID,
)
from backend.app.model_router.model_router import model_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("dodo.verify_reliability")


async def run_tests():
    logger.info("=" * 70)
    logger.info("DODO AI CONNECTION RELIABILITY & RECOVERY VERIFICATION SUITE")
    logger.info("=" * 70)

    # -------------------------------------------------------------------------
    # TEST 1: Ollama Binary Discovery & Health Monitoring
    # -------------------------------------------------------------------------
    logger.info("\n[Test 1] Automatic Ollama Health Monitoring & Binary Detection...")
    exe = find_ollama_executable()
    logger.info(f"Ollama binary located: {exe}")
    assert exe is not None and os.path.exists(exe), "FATAL: Ollama executable not found!"

    health = await ollama_client.check_health(force_refresh=True)
    logger.info(f"Ollama Live Health Check: status={health.get('status')}, latency={health.get('latency_ms')}ms, models={health.get('models')}")
    assert health.get("status") in ["online", "offline"], "Invalid health status!"
    assert "models" in health, "Models list missing in health check"
    logger.info("✓ Test 1 PASSED: Real Ollama daemon health monitored accurately.")

    # -------------------------------------------------------------------------
    # TEST 2: Start Ollama Daemon API / Method (Windows background spawn)
    # -------------------------------------------------------------------------
    logger.info("\n[Test 2] Verify Start Ollama Background Spawn Capability...")
    start_res = await ollama_client.start_daemon(timeout_seconds=5)
    logger.info(f"Start Daemon Output: {start_res}")
    assert start_res.get("status") in ["online", "starting"], f"Unexpected start status: {start_res}"
    logger.info("✓ Test 2 PASSED: Start Ollama background executor verified.")

    # -------------------------------------------------------------------------
    # TEST 3: Direct Cloud Model Routing (Zero Ollama Dependency)
    # -------------------------------------------------------------------------
    logger.info("\n[Test 3] Explicit Cloud Model Selection (Zero Ollama Dependency)...")
    cloud_result = await model_router.route(
        prompt="Write a distributed lock algorithm.",
        requested_model=NEMOTRON_MODEL_ID,
    )
    logger.info(f"Cloud Route Result: model={cloud_result.selected_model}, provider={cloud_result.provider}, fit={cloud_result.hardware_fit}")
    assert cloud_result.selected_model == NEMOTRON_MODEL_ID, "Incorrect model selected!"
    assert cloud_result.provider == "OpenRouter", "Incorrect provider assigned!"
    assert cloud_result.hardware_fit == "Cloud Hosted (0% local VRAM)", "Incorrect hardware fit!"

    # Test Vision Model selection
    vision_result = await model_router.route(
        prompt="Analyze this UI layout screenshot.",
        requested_model=NEMOTRON_SUPER_VL_ID,
    )
    logger.info(f"Vision Route Result: model={vision_result.selected_model}, provider={vision_result.provider}")
    assert vision_result.selected_model == NEMOTRON_SUPER_VL_ID
    assert vision_result.provider == "OpenRouter"
    logger.info("✓ Test 3 PASSED: Cloud models bypass local Ollama completely.")

    # -------------------------------------------------------------------------
    # TEST 4: Auto Mode Routing Policy & Exact Handled Model Reporting
    # -------------------------------------------------------------------------
    logger.info("\n[Test 4] Auto Mode Routing Policy & Explicit Handled Model Reporting...")
    # 4.1 Simple greeting / lightweight prompt -> Qwen local
    simple_route = await model_router.route(prompt="hello, what is 2+2?", requested_model="auto")
    logger.info(f"Simple Prompt ('hello') routed to: model={simple_route.selected_model}, role={simple_route.role}, provider={simple_route.provider}")
    assert simple_route.selected_model != "auto", "Auto mode must resolve to a concrete model!"
    assert simple_route.role in ["coding", "general", "lightweight"], f"Unexpected role: {simple_route.role}"

    # 4.2 Complex full-stack architecture prompt -> Nemotron 3 Ultra
    complex_prompt = "Build a full-stack high-concurrency microservices platform with distributed state management from scratch."
    complex_route = await model_router.route(prompt=complex_prompt, requested_model="auto")
    logger.info(f"Complex Architecture Prompt routed to: model={complex_route.selected_model}, role={complex_route.role}, provider={complex_route.provider}")
    assert complex_route.selected_model == NEMOTRON_MODEL_ID, "Complex full-stack architecture must auto-route to Nemotron 3 Ultra!"
    assert complex_route.provider == "OpenRouter"
    logger.info("✓ Test 4 PASSED: Auto mode policy routes correctly and reports exact handled model.")

    # -------------------------------------------------------------------------
    # TEST 5: SSE Chat Stream Routing Event & Model Attribution
    # -------------------------------------------------------------------------
    logger.info("\n[Test 5] SSE Chat Stream Event Verification & Error Resilience...")
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)

    # Test Chat SSE payload emission (omit conversation_id to auto-create)
    res = client.post(
        "/api/chat",
        json={
            "message": "ping",
            "model": "auto",
        },
    )
    assert res.status_code == 200, f"Chat endpoint returned HTTP {res.status_code}"
    lines = res.text.strip().split("\n\n")
    routing_found = False
    routed_model = None

    for line in lines:
        if line.startswith("data: "):
            try:
                data = json.loads(line[6:])
                if data.get("type") == "routing":
                    routing_found = True
                    routed_model = data.get("model")
                    logger.info(f"SSE Received Routing Event: model={routed_model}, provider={data.get('provider')}, role={data.get('role')}")
            except Exception:
                pass

    assert routing_found, "FATAL: SSE stream did not emit initial 'routing' metadata event!"
    assert routed_model is not None and routed_model != "auto", f"Routed model must be concrete, got: {routed_model}"
    logger.info("✓ Test 5 PASSED: SSE stream emits immediate routing metadata.")

    # -------------------------------------------------------------------------
    # TEST 6: Zero Fabrication Guarantee on Missing Models
    # -------------------------------------------------------------------------
    logger.info("\n[Test 6] Verification of Non-Fabrication on Missing Models...")
    fake_model = "non_existent_ghost_model_xyz"
    missing_route = await model_router.route(prompt="Hello", requested_model=fake_model)
    logger.info(f"Missing Model Verification: selected={missing_route.selected_model}, is_installed={missing_route.is_installed}")
    assert missing_route.is_installed is False, "DODO must NOT claim a missing model is installed!"

    # -------------------------------------------------------------------------
    # TEST 7: Ollama Health & Start API Endpoints
    # -------------------------------------------------------------------------
    logger.info("\n[Test 7] Verify Ollama Health & Start API Endpoints...")
    health_api_res = client.get("/api/models/ollama/health")
    assert health_api_res.status_code == 200, f"Health endpoint returned {health_api_res.status_code}"
    health_data = health_api_res.json()
    logger.info(f"API Health response: status={health_data.get('status')}, version={health_data.get('version')}")
    assert health_data.get("status") in ["online", "offline"]
    assert "openrouter" in health_data

    start_api_res = client.post("/api/models/ollama/start")
    assert start_api_res.status_code == 200, f"Start endpoint returned {start_api_res.status_code}"
    start_data = start_api_res.json()
    logger.info(f"API Start response: status={start_data.get('status')}")
    assert start_data.get("status") in ["online", "starting"]
    logger.info("✓ Test 7 PASSED: /api/models/ollama/health and /start endpoints verified.")

    logger.info("\n" + "=" * 70)
    logger.info("ALL 7 AI CONNECTION RELIABILITY & RECOVERY TESTS PASSED!")
    logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_tests())
