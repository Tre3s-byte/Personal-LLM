from fastapi import APIRouter, Request, HTTPException
from backend.api.handler.chat import handle_chat_request
import logging

router = APIRouter()
api_router = router
logger = logging.getLogger(__name__)


@router.post("/chat")
async def chat(request: Request):
    """Handle /chat endpoint by delegating to chat_handler."""
    try:
        return await handle_chat_request(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unhandled error in /chat")
        raise HTTPException(status_code=500, detail=str(e))
