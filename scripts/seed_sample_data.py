import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Setup environment path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.database.mongodb import db_manager, get_db
from backend.app.database.repositories.conversation_repository import ConversationRepository, MessageRepository
from backend.app.database.repositories.project_repository import TaskRepository, ProjectRepository
from backend.app.database.repositories.model_repository import MemoryRepository, ModelRepository, ToolExecutionRepository, BaseRepository
from backend.app.core.config import settings

def seed():
    print("🌱 Seeding DODO with sample data...")
    db_manager.connect()

    conv_repo = ConversationRepository()
    msg_repo = MessageRepository()
    task_repo = TaskRepository()
    proj_repo = ProjectRepository()
    mem_repo = MemoryRepository()
    model_repo = ModelRepository()
    metrics_repo = BaseRepository("model_metrics")

    # 1. Sample Project
    workspace_path = settings.AUTHORIZED_WORKSPACE_DIR
    proj = proj_repo.create_project(
        name="TaskMaster Pro & E-Commerce Core",
        workspace_path=workspace_path,
        description="Full-stack autonomous reference project featuring FastAPI, MongoDB, React, and automated testing.",
    )
    proj_id = proj["id"]
    print(f"Created sample project: {proj['name']} ({proj_id})")

    # 2. Sample Conversations (Mode A)
    # Conversation 1: Full-Stack Architecture
    c1 = conv_repo.create_conversation(
        title="Full-Stack E-Commerce Architecture",
        mode="assistant",
        project_id=proj_id,
    )
    msg_repo.add_message(
        c1["id"],
        role="user",
        content="What is the recommended architecture for a local-first e-commerce API using FastAPI, MongoDB, and React with high read throughput?"
    )
    msg_repo.add_message(
        c1["id"],
        role="assistant",
        content=(
            "### Recommended Architecture for High-Throughput E-Commerce\n\n"
            "For a local-first architecture on your machine, consider the following topology:\n\n"
            "1. **FastAPI Application Layer**:\n"
            "   - Async routing with dependency injection.\n"
            "   - Pydantic V2 models for input serialization and validation.\n"
            "   - Connection pooling to MongoDB using PyMongo/Motor.\n\n"
            "2. **MongoDB Data Layer**:\n"
            "   - Compound indexes on `(category_id, price)` for catalog filtering.\n"
            "   - Sub-document embedding for order line items to avoid relational joins.\n"
            "   - Read preference secondary or local cache for catalog lookups.\n\n"
            "3. **Frontend (React / Tailwind)**:\n"
            "   - Optimistic UI updates for cart manipulations.\n"
            "   - Server-Sent Events (SSE) for inventory alerts and agent notifications."
        ),
        model_used="qwen2.5-coder:7b"
    )

    # Conversation 2: Vector Search & Semantic Memory
    c2 = conv_repo.create_conversation(
        title="MongoDB Atlas Vector Search vs Local Embeddings",
        mode="assistant",
        project_id=proj_id,
    )
    msg_repo.add_message(
        c2["id"],
        role="user",
        content="How does DODO handle semantic memory retrieval if Atlas Vector Search is not enabled on local Community Server?"
    )
    msg_repo.add_message(
        c2["id"],
        role="assistant",
        content=(
            "**DODO Hybrid Semantic Retrieval Mechanism**:\n\n"
            "- **Tier 1 (Cloud / Atlas)**: When connected to MongoDB Atlas with an active Vector Search index, DODO dispatches `$vectorSearch` aggregation pipelines.\n"
            "- **Tier 2 (Local Community / Standalone)**: DODO automatically falls back to an in-memory cosine-similarity index using `nomic-embed-text` embeddings and MongoDB text scoring.\n"
            "- **Benefit**: Your application never crashes or refuses queries regardless of whether you are offline on an airplane or connected to Atlas."
        ),
        model_used="deepseek-r1:8b"
    )

    # Conversation 3: Performance Optimization
    c3 = conv_repo.create_conversation(
        title="4GB VRAM GPU Model Sizing",
        mode="assistant",
        project_id=proj_id,
    )
    msg_repo.add_message(
        c3["id"],
        role="user",
        content="Can my RTX 3050 Laptop GPU (4GB VRAM) run 7B or 8B parameter models smoothly?"
    )
    msg_repo.add_message(
        c3["id"],
        role="assistant",
        content=(
            "Yes! With **4-bit quantization (Q4_K_M)**:\n\n"
            "- `llama3.2:1b`: Uses ~1.3 GB VRAM (100% offloaded to GPU, >60 tokens/sec).\n"
            "- `qwen2.5-coder:7b`: Uses ~4.7 GB (approx 28/32 layers offloaded directly to your 4GB VRAM, remainder to system RAM, providing ~18-25 tokens/sec).\n"
            "- `deepseek-r1:8b`: Fits comfortably with partial GPU offload for architectural reasoning."
        ),
        model_used="qwen2.5:7b"
    )
    print("Created 3 rich sample conversations.")

    # 3. Sample Autonomous Developer Tasks (Mode B)
    # Task 1: Complete and Verified Full-Stack App
    t1 = task_repo.create_task(
        prompt="Build a complete task management application using React, FastAPI and MongoDB",
        workspace_path=workspace_path,
        project_id=proj_id,
        mode="developer",
    )
    plan1 = {
        "objective": "Build and verify full-stack task management application with React, FastAPI, and MongoDB",
        "analysis": "Generate FastAPI CRUD backend, single-page React frontend, automated pytest verification, and Playwright inspection.",
        "estimated_steps": 7,
        "steps": [
            {"step_id": 1, "title": "Inspect Workspace Environment", "description": "Scan directory structure.", "tool": "list_workspace_files", "status": "completed", "result": "Workspace scanned. 0 conflicts."},
            {"step_id": 2, "title": "Generate Backend Models and Database Connection", "description": "FastAPI and MongoDB endpoints.", "tool": "write_file", "status": "completed", "result": "Created backend_app.py (2.1 KB)"},
            {"step_id": 3, "title": "Generate Single-Page React Web Application", "description": "Tailwind UI with real-time state.", "tool": "write_file", "status": "completed", "result": "Created index.html (3.9 KB)"},
            {"step_id": 4, "title": "Create Automated Verification Suite", "description": "Pytest CRUD verification.", "tool": "write_file", "status": "completed", "result": "Created test_task_manager.py (1.1 KB)"},
            {"step_id": 5, "title": "Execute Automated Pytest Verification Suite", "description": "Run unit and integration tests.", "tool": "execute_terminal_command", "status": "completed", "result": "4 passed in 0.42s"},
            {"step_id": 6, "title": "Browser Automation & UI Verification", "description": "Playwright headless inspection.", "tool": "open_and_inspect_page", "status": "completed", "result": "Page loaded. 0 console errors."},
            {"step_id": 7, "title": "Take Verification UI Screenshot", "description": "Save visual render preview.", "tool": "take_screenshot", "status": "completed", "result": "Saved verification_preview.png (19.8 KB)"},
        ]
    }
    task_repo.update_task_plan(t1["id"], plan1)
    task_repo.complete_task(
        t1["id"],
        status="completed",
        summary=(
            "### 🦅 DODO Task Completion Report\n\n"
            "- **Objective**: Build and verify full-stack task management application with React, FastAPI, and MongoDB\n"
            "- **Execution Status**: Completed and Verified\n"
            "- **Total Steps Executed**: 7\n"
            "- **Errors Encountered**: 0\n"
            "- **Verification Evidence**: Automated pytest suite passed (4/4), Playwright browser inspection verified 0 console errors, and full-page visual screenshot rendered."
        ),
        verified=True
    )

    # Task 2: E-Commerce Store Microservice
    t2 = task_repo.create_task(
        prompt="Create an E-Commerce Product Catalog Microservice with price search and inventory tracking",
        workspace_path=workspace_path,
        project_id=proj_id,
        mode="developer",
    )
    plan2 = {
        "objective": "E-Commerce Product Catalog Microservice",
        "analysis": "Implement product schema, price range filtering, stock decrement endpoint, and tests.",
        "estimated_steps": 4,
        "steps": [
            {"step_id": 1, "title": "Design Product Schema and Indexes", "description": "MongoDB schema with compound pricing indexes.", "tool": "write_file", "status": "completed", "result": "Created models/product.py"},
            {"step_id": 2, "title": "Implement Catalog REST Routes", "description": "GET /products and POST /products/decrement.", "tool": "write_file", "status": "completed", "result": "Created routes/products.py"},
            {"step_id": 3, "title": "Run Unit Test Suite", "description": "Verify price filter logic.", "tool": "execute_terminal_command", "status": "completed", "result": "3 passed"},
            {"step_id": 4, "title": "Deliver Service Blueprint", "description": "Summarize verified microservice.", "tool": "read_file", "status": "completed", "result": "Verified"},
        ]
    }
    task_repo.update_task_plan(t2["id"], plan2)
    task_repo.complete_task(t2["id"], status="completed", summary="Product catalog microservice created and verified.", verified=True)

    print("Created 2 sample autonomous developer tasks.")

    # 4. Sample Persistent Memories
    mem_repo.add_memory("Preferred styling framework is Tailwind CSS with dark mode defaults.", category="preference", project_id=proj_id)
    mem_repo.add_memory("Development machine uses NVIDIA RTX 3050 Laptop GPU with 4GB VRAM. Prefer Q4_K_M quantization for 7B/8B models.", category="project", project_id=proj_id)
    mem_repo.add_memory("All workspace files must remain strictly within D:\\DODO\\workspace path jail.", category="codebase", project_id=proj_id)
    print("Created 3 persistent semantic memories.")

    # 5. Sample Model Benchmark Telemetry Metrics
    models = ["qwen2.5-coder:7b", "llama3.2:1b", "deepseek-r1:8b", "qwen2.5:7b"]
    for m in models:
        metrics_repo.create({
            "model_name": m,
            "task_type": "coding" if "coder" in m else "reasoning" if "r1" in m else "general",
            "latency_ms": 145.2 if "1b" in m else 320.5,
            "tokens_per_second": 58.4 if "1b" in m else 24.1,
            "prompt_tokens": 128,
            "completion_tokens": 340,
            "timestamp": datetime.utcnow() - timedelta(minutes=15),
        })
    print("Created model performance metrics.")

    # 6. Sample Project Files in Workspace
    ws = Path(workspace_path)
    ws.mkdir(parents=True, exist_ok=True)

    # routes/products.py
    routes_dir = ws / "routes"
    routes_dir.mkdir(parents=True, exist_ok=True)
    (routes_dir / "products.py").write_text(
        "from fastapi import APIRouter, HTTPException\n"
        "from pydantic import BaseModel\n"
        "from typing import List, Optional\n"
        "\n"
        "router = APIRouter(prefix='/api/products', tags=['Products'])\n"
        "\n"
        "class Product(BaseModel):\n"
        "    id: str\n"
        "    name: str\n"
        "    price: float\n"
        "    stock: int\n"
        "\n"
        "PRODUCTS_DB = [\n"
        "    {'id': 'prod_1', 'name': 'Mechanical Keyboard', 'price': 99.99, 'stock': 24},\n"
        "    {'id': 'prod_2', 'name': 'UltraWide Monitor', 'price': 349.50, 'stock': 8},\n"
        "    {'id': 'prod_3', 'name': 'Ergonomic Mouse', 'price': 59.00, 'stock': 42},\n"
        "]\n"
        "\n"
        "@router.get('', response_model=List[Product])\n"
        "def list_products(min_price: Optional[float] = None, max_price: Optional[float] = None):\n"
        "    res = PRODUCTS_DB\n"
        "    if min_price is not None:\n"
        "        res = [p for p in res if p['price'] >= min_price]\n"
        "    if max_price is not None:\n"
        "        res = [p for p in res if p['price'] <= max_price]\n"
        "    return res\n"
        "\n"
        "@router.post('/{product_id}/decrement')\n"
        "def decrement_stock(product_id: str, count: int = 1):\n"
        "    p = next((x for x in PRODUCTS_DB if x['id'] == product_id), None)\n"
        "    if not p:\n"
        "        raise HTTPException(status_code=404, detail='Product not found')\n"
        "    if p['stock'] < count:\n"
        "        raise HTTPException(status_code=400, detail='Insufficient stock')\n"
        "    p['stock'] -= count\n"
        "    return {'success': True, 'remaining_stock': p['stock']}\n",
        encoding="utf-8"
    )

    # models/product.py
    models_dir = ws / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    (models_dir / "product.py").write_text(
        "from pydantic import BaseModel, Field\n"
        "from typing import Optional\n"
        "\n"
        "class ProductSchema(BaseModel):\n"
        "    name: str = Field(..., max_length=120)\n"
        "    description: Optional[str] = None\n"
        "    price: float = Field(..., gt=0)\n"
        "    sku: str = Field(..., regex=r'^[A-Z0-9_-]{4,16}$')\n"
        "    stock: int = Field(default=0, ge=0)\n",
        encoding="utf-8"
    )

    # Save to disk
    db_manager.persist_fallback_data()
    print("✅ Sample data seeding successfully completed!")

if __name__ == "__main__":
    seed()

