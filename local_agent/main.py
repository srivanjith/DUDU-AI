import logging
from typing import Any, Dict, Optional
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from local_agent.config import local_settings
from local_agent.security import verify_token
from local_agent.filesystem.manager import fs_manager
from local_agent.terminal.executor import terminal_executor
from local_agent.browser.runner import browser_runner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dodo.local_agent")

app = FastAPI(
    title="DODO Local Agent",
    description="Secure local runtime bridge for DODO development platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExecRequest(BaseModel):
    command: str
    cwd: Optional[str] = ""
    timeout: Optional[int] = 60


class WriteFileRequest(BaseModel):
    path: str
    content: str


@app.get("/health")
def health():
    return {
        "status": "online",
        "agent": "DODO Local Agent",
        "workspace": local_settings.AUTHORIZED_WORKSPACE,
    }


@app.get("/api/fs/list", dependencies=[Depends(verify_token)])
def list_files(subpath: str = ""):
    return fs_manager.list_files(subpath)


@app.get("/api/fs/read", dependencies=[Depends(verify_token)])
def read_file(path: str, start_line: int = 1, end_line: Optional[int] = None):
    return fs_manager.read(path, start_line, end_line)


@app.post("/api/fs/write", dependencies=[Depends(verify_token)])
def write_file(req: WriteFileRequest):
    return fs_manager.write(req.path, req.content)


@app.post("/api/exec", dependencies=[Depends(verify_token)])
async def execute_command(req: ExecRequest):
    return await terminal_executor.execute(req.command, req.cwd or "", req.timeout or 60)


@app.get("/api/browser/inspect", dependencies=[Depends(verify_token)])
async def browser_inspect(url: str):
    return await browser_runner.inspect(url)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=local_settings.HOST, port=local_settings.PORT)

