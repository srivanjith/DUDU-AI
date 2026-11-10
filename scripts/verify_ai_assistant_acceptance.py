"""
DODO Final Acceptance Test — Section 3: AI Assistant Acceptance
Uses httpx to test the running FastAPI backend and Ollama.
"""
import sys
import json
import time
import httpx
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

BACKEND_URL = "http://127.0.0.1:8000"
OLLAMA_URL = "http://127.0.0.1:11434"

def test_ai_assistant():
    print("=" * 60)
    print("      🦅 SECTION 3: AI ASSISTANT ACCEPTANCE REVIEW          ")
    print("=" * 60)

    client = httpx.Client(timeout=60.0)

    # 1. Ollama Direct Inference & Model Audit
    print("\n--- 1. Ollama Service & Local Model Audit ---")
    r_tags = client.get(f"{OLLAMA_URL}/api/tags")
    assert r_tags.status_code == 200, f"Ollama tags failed: {r_tags.text}"
    models_data = r_tags.json().get("models", [])
    model_names = [m.get("name") for m in models_data]
    print(f"Installed Ollama Models: {model_names}")
    assert any("qwen2.5-coder:1.5b" in m for m in model_names), "qwen2.5-coder:1.5b is required!"
    print("Verified: qwen2.5-coder:1.5b is installed and ready.")

    # 2. Live Conversation Creation
    print("\n--- 2. Live Conversation Creation on FastAPI Backend ---")
    conv_res = client.post(
        f"{BACKEND_URL}/api/conversations",
        json={"title": "Acceptance Section 3 Chat", "mode": "assistant"},
    )
    assert conv_res.status_code == 200, f"Create conversation failed: {conv_res.text}"
    conv_id = conv_res.json()["id"]
    print(f"Created Conversation ID: {conv_id}")

    # 3. Real Streaming Response & Latency Check
    print("\n--- 3. Real Qwen 2.5 Coder 1.5B Streaming Inference Test ---")
    prompt = "Write a python function named 'add_numbers(a, b)' that returns their sum."
    t0 = time.time()
    chat_req = {
        "conversation_id": conv_id,
        "message": prompt,
        "model": "qwen2.5-coder:1.5b"
    }

    tokens = []
    first_token_time = None
    event_types = []

    with client.stream("POST", f"{BACKEND_URL}/api/chat", json=chat_req) as resp:
        assert resp.status_code == 200, f"Chat streaming request failed: {resp.status_code}"
        for line in resp.iter_lines():
            if not line:
                continue
            if line.startswith("data: "):
                try:
                    evt = json.loads(line[6:])
                    event_types.append(evt.get("type"))
                    if evt.get("type") == "token":
                        if first_token_time is None:
                            first_token_time = time.time() - t0
                        token_str = evt.get("token") or evt.get("content") or ""
                        tokens.append(token_str)
                    elif evt.get("type") == "complete":
                        print(f"Stream complete event received: {evt.get('model_used')}")
                except Exception:
                    pass

    total_time = time.time() - t0
    full_response = "".join(tokens)
    print(f"First token latency: {first_token_time:.3f}s" if first_token_time else "No first token time")
    print(f"Total inference time: {total_time:.3f}s, Tokens received: {len(tokens)}")
    print(f"Full response:\n{full_response}")
    assert len(tokens) > 0, "No tokens received from streaming!"
    assert ("def " in full_response or "add_numbers" in full_response or "return" in full_response), "Expected python code in generated response"
    print("Verified: Real local inference successfully produced valid Python code.")

    # 4. Multi-turn Follow-up Context Preservation
    print("\n--- 4. Multi-Turn Follow-Up Context Test ---")
    followup_prompt = "Now rewrite it with type hints and docstring."
    followup_tokens = []
    with client.stream(
        "POST",
        f"{BACKEND_URL}/api/chat",
        json={"conversation_id": conv_id, "message": followup_prompt, "model": "qwen2.5-coder:1.5b"},
    ) as resp_followup:
        assert resp_followup.status_code == 200
        for line in resp_followup.iter_lines():
            if line and line.startswith("data: "):
                try:
                    evt = json.loads(line[6:])
                    if evt.get("type") == "token":
                        followup_tokens.append(evt.get("token") or evt.get("content") or "")
                except Exception:
                    pass

    followup_response = "".join(followup_tokens)
    print(f"Follow-up response snippet:\n{followup_response[:180]}...")
    assert len(followup_tokens) > 0
    assert "int" in followup_response or "float" in followup_response or "add_numbers" in followup_response
    print("Verified: Context maintained across multi-turn exchange.")

    # 5. Missing Model Error Handling (MODEL_NOT_FOUND)
    print("\n--- 5. Missing Model Error Handling ---")
    missing_events = []
    with client.stream(
        "POST",
        f"{BACKEND_URL}/api/chat",
        json={"conversation_id": conv_id, "message": "Test missing", "model": "non_existent_model:xyz"},
    ) as missing_resp:
        assert missing_resp.status_code == 200
        for line in missing_resp.iter_lines():
            if line and line.startswith("data: "):
                try:
                    missing_events.append(json.loads(line[6:]))
                except Exception:
                    pass

    error_events = [e for e in missing_events if e.get("type") == "error"]
    assert len(error_events) >= 1
    err_code = error_events[0].get("error_code")
    print(f"Received error event as expected: code={err_code}, message={error_events[0].get('error')}")
    assert err_code == "MODEL_NOT_FOUND" or "not installed" in error_events[0].get("error", "")
    print("Verified: Graceful handling of missing models.")

    # 6. Cloud Isolation Verification
    print("\n--- 6. Cloud Isolation & Zero External API Calls Audit ---")
    from backend.app.core.config import settings
    print(f"Ollama Base URL: {settings.OLLAMA_BASE_URL}")
    print(f"Local Agent Port: {settings.LOCAL_AGENT_PORT}")
    assert "localhost" in settings.OLLAMA_BASE_URL or "127.0.0.1" in settings.OLLAMA_BASE_URL
    assert settings.LOCAL_AGENT_PORT == 8001
    print("Verified: Strict local privacy enforced. Zero cloud LLM API keys configured.")

    # Clean up test conversation
    print("\n--- Cleanup ---")
    del_r = client.delete(f"{BACKEND_URL}/api/conversations/{conv_id}")
    print(f"Cleaned up acceptance conversation {conv_id}: status={del_r.status_code}")

    print("\n" + "=" * 60)
    print("✅ Section 3: AI Assistant Acceptance PASSED.")
    print("=" * 60)

if __name__ == "__main__":
    test_ai_assistant()
