"""FastAPI web router for Ghost-Box shadow management and status endpoints."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from ..engine import GHOST_MANAGER, LAST_GHOSTBOX_CACHE

router = APIRouter()


@router.get("/status")
def get_ghostbox_status() -> Dict[str, Any]:
    """Return active shadow universes and the latest blast radius summary."""
    return {
        "plugin": "ghostbox",
        "status": "active",
        "active_shadow_count": len(GHOST_MANAGER.active_shadows),
        "active_shadows": list(GHOST_MANAGER.active_shadows.keys()),
        "latest_blast": LAST_GHOSTBOX_CACHE.get("latest_blast"),
        "latest_commit": LAST_GHOSTBOX_CACHE.get("latest_commit"),
    }


@router.post("/commit/{shadow_id}")
def post_commit_shadow(shadow_id: str) -> Dict[str, Any]:
    """Trigger an atomic fast-forward commit from the web dashboard."""
    return GHOST_MANAGER.fast_forward_commit(shadow_id)


@router.delete("/shadow/{shadow_id}")
def delete_discard_shadow(shadow_id: str) -> Dict[str, Any]:
    """Discard and vaporize an active shadow universe."""
    return GHOST_MANAGER.discard_shadow(shadow_id)
