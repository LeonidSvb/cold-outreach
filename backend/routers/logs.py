"""
Logs Router - Receive logs from frontend
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Optional
from modules.logging.shared.universal_logger import get_logger

router = APIRouter(prefix="/api", tags=["logs"])
logger = get_logger("frontend")


class FrontendLogEntry(BaseModel):
    """Frontend log entry model"""
    timestamp: str
    level: str
    message: str
    data: Optional[Dict] = {}
    userAgent: Optional[str] = ""
    url: Optional[str] = ""


@router.post("/logs")
async def receive_frontend_log(entry: FrontendLogEntry):
    """
    Receive logs from Next.js frontend
    Forwards to centralized logging system

    Frontend logs appear in same log file with module="frontend"
    """

    # Get appropriate log method (error, warning, info, debug)
    log_method = getattr(logger, entry.level.lower(), logger.info)

    # Log with all context
    log_method(
        entry.message,
        user_agent=entry.userAgent,
        url=entry.url,
        **(entry.data or {})
    )

    return {"success": True}
