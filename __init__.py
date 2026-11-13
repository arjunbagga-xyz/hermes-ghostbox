"""Ghost-Box: Speculative Shadow-Execution Sandbox and Blast-Radius Verifier."""

from __future__ import annotations

from typing import Any, Dict

from .engine import (
    _ensure_json_str,
    GHOST_BLAST_SCHEMA,
    GHOST_COMMIT_SCHEMA,
    GHOST_DISCARD_SCHEMA,
    GHOST_SPAWN_SCHEMA,
    handle_ghostbox_compute_blast,
    handle_ghostbox_discard_shadow,
    handle_ghostbox_fast_forward_commit,
    handle_ghostbox_spawn_shadow,
)


def _tool_handler(fn):
    """Wrap a dict-returning engine handler so Hermes tool_call gets a JSON string."""
    def wrapper(args=None, **kwargs):
        result = fn(args if args is not None else {})
        return _ensure_json_str(result)
    return wrapper


def on_session_start_hook(payload: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
    """Hook invoked when a new Hermes agent session initializes."""
    return {"status": "ghostbox-ready", "isolated_mode": True}


def register(ctx: Any) -> None:
    """Register Ghost-Box tools, hooks, and middleware with the Hermes Plugin Context."""
    ctx.register_tool(
        name="ghostbox_spawn_shadow",
        toolset="ghostbox",
        schema=GHOST_SPAWN_SCHEMA,
        handler=_tool_handler(handle_ghostbox_spawn_shadow),
        is_async=False,
        emoji="🔮",
    )
    ctx.register_tool(
        name="ghostbox_compute_blast",
        toolset="ghostbox",
        schema=GHOST_BLAST_SCHEMA,
        handler=_tool_handler(handle_ghostbox_compute_blast),
        is_async=False,
        emoji="📊",
    )
    ctx.register_tool(
        name="ghostbox_fast_forward_commit",
        toolset="ghostbox",
        schema=GHOST_COMMIT_SCHEMA,
        handler=_tool_handler(handle_ghostbox_fast_forward_commit),
        is_async=False,
        emoji="⚡",
    )
    ctx.register_tool(
        name="ghostbox_discard_shadow",
        toolset="ghostbox",
        schema=GHOST_DISCARD_SCHEMA,
        handler=_tool_handler(handle_ghostbox_discard_shadow),
        is_async=False,
        emoji="💥",
    )

    ctx.register_hook("on_session_start", on_session_start_hook)
