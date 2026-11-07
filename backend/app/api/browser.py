from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel
from backend.app.tools.browser_tools import open_and_inspect_page, take_screenshot

router = APIRouter(prefix="/browser", tags=["Browser"])


class InspectPageRequest(BaseModel):
    url: str
    wait_ms: Optional[int] = 2000


class ScreenshotRequest(BaseModel):
    url: str
    save_path: Optional[str] = "screenshot.png"


@router.post("/inspect")
async def inspect_url(req: InspectPageRequest):
    return await open_and_inspect_page(req.url, req.wait_ms or 2000)


@router.post("/screenshot")
async def capture_screenshot(req: ScreenshotRequest):
    return await take_screenshot(req.url, req.save_path or "screenshot.png")

