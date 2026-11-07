import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.database.mongodb import db_manager
from backend.app.database.indexes import create_database_indexes
from backend.app.api import health, conversations, tasks, models, workspace, terminal, browser, memory

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("dodo.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize MongoDB and Ensure Directories
    logger.info("Initializing DODO Platform Backend...")
    workspace_dir = Path(settings.AUTHORIZED_WORKSPACE_DIR)
    workspace_dir.mkdir(parents=True, exist_ok=True)

    db_manager.connect()
    create_database_indexes()
    logger.info("DODO Platform ready.")
    yield
    # Shutdown: Close DB connections
    logger.info("Shutting down DODO Platform Backend...")
    db_manager.close()


app = FastAPI(
    title=settings.APP_NAME,
    description="DODO — Your AI. Your Machine. Your Rules.",
    version=settings.VERSION,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(health.router)
app.include_router(conversations.router)
app.include_router(tasks.router)
app.include_router(models.router)
app.include_router(workspace.router)
app.include_router(terminal.router)
app.include_router(browser.router)
app.include_router(memory.router)


@app.get("/")
def get_root():
    return {
        "app": settings.APP_NAME,
        "tagline": settings.TAGLINE,
        "version": settings.VERSION,
        "status": "online",
        "documentation": "/docs",
    }


# Interactive WebSocket Endpoint for Live Terminal / Agent telemetry
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to DODO Real-time Agent Bus",
        })
        while True:
            data = await websocket.receive_text()
            # Echo or handle commands
            await websocket.send_json({
                "type": "ack",
                "received": data,
            })
    except WebSocketDisconnect:
        logger.info("Client disconnected from WebSocket.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)

