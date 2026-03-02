"""Application-level utility routes (non-chat endpoints)."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Simple health endpoint for quick service checks."""
    return {"status": "ok"}
