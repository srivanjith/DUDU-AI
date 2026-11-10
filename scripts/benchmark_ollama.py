"""
DODO Ollama Performance Benchmarking Script
Measures inference latency, tokens-per-second, time-to-first-token (TTFT),
and validates error recovery on the installed local model.
"""
import asyncio
import json
import time
from typing import Any, Dict
from pathlib import Path
import sys

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from backend.app.intelligence.ollama_client import ollama_client


async def run_benchmark():
    print("==================================================")
    print("      🦅 DODO AI Performance Benchmark Suite       ")
    print("==================================================")

    # 1. Health & Discovery Check
    health = await ollama_client.check_health()
    print(f"\n[Ollama Status]: {health.get('status')} (v{health.get('version')})")
    print(f"[Installed Models]: {health.get('models')}")

    if not health.get("models"):
        print("❌ No models detected. Aborting benchmark.")
        return

    model_name = "qwen2.5-coder:1.5b"
    print(f"\nTarget Model: {model_name}")

    # 2. Benchmark 1: Coding Generation Speed & TTFT
    test_prompt = "Write a Python function to compute the Fibonacci sequence up to n using iteration."
    messages = [
        {"role": "system", "content": "You are an expert Python engineer. Provide concise code."},
        {"role": "user", "content": test_prompt},
    ]

    print("\n--- Benchmark 1: Streaming Inference & Token Throughput ---")
    start_time = time.perf_counter()
    first_token_time = None
    accumulated_tokens = 0
    token_chunks = []

    try:
        async for chunk in ollama_client.chat_stream(model_name, messages, options={"temperature": 0.2}):
            if first_token_time is None and chunk.get("content"):
                first_token_time = time.perf_counter()
            content = chunk.get("content", "")
            if content:
                accumulated_tokens += 1
                token_chunks.append(content)
            if chunk.get("done"):
                break
    except Exception as e:
        print(f"Error during streaming benchmark: {e}")
        return

    total_duration = time.perf_counter() - start_time
    ttft_ms = round((first_token_time - start_time) * 1000, 2) if first_token_time else 0.0
    tokens_per_sec = round(accumulated_tokens / max(0.001, total_duration - (ttft_ms / 1000.0)), 2)

    print(f"  • Total Time: {total_duration:.2f}s")
    print(f"  • Time to First Token (TTFT): {ttft_ms} ms")
    print(f"  • Tokens Generated: {accumulated_tokens}")
    print(f"  • Inference Speed: {tokens_per_sec} tokens/second")

    # 3. Benchmark 2: Graceful Unavailable Model Handling
    print("\n--- Benchmark 2: Missing Model Fallback & Error Handling ---")
    missing_model = "nonexistent-model-xyz:99b"
    caught_error = False
    async for chunk in ollama_client.chat_stream(missing_model, messages):
        if "error" in chunk:
            print(f"  • Expected error captured cleanly: '{chunk['error']}' (code: {chunk.get('error_code')})")
            caught_error = True
            break
    if not caught_error:
        print("  ⚠️ Warning: Did not receive expected error object for missing model.")
    else:
        print("  ✅ Missing model scenario handled gracefully.")

    print("\n==================================================")
    print("🎉 Benchmark complete.")


if __name__ == "__main__":
    asyncio.run(run_benchmark())

