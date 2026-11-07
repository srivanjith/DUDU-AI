from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.app.tools.terminal_tools import execute_terminal_command

router = APIRouter(prefix="/terminal", tags=["Terminal"])


class TerminalRunRequest(BaseModel):
    command: str
    cwd: Optional[str] = ""
    timeout_seconds: Optional[int] = 60


@router.post("/execute")
async def run_command(req: TerminalRunRequest):
    res = await execute_terminal_command(
        command=req.command,
        cwd=req.cwd or "",
        timeout_seconds=req.timeout_seconds or 60,
    )
    return res

