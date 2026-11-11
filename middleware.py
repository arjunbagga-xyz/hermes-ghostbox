"""Ghost-Box Middleware: Intercepts mutating tools and redirects them into shadow universes."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .engine import GHOST_MANAGER

logger = logging.getLogger("hermes.ghostbox.middleware")

MUTATING_TOOLS = {
    "bash",
    "execute_code",
    "write_file",
    "edit_file",
    "patch_file",
    "terminal_command",
}


def ghostbox_tool_request_middleware(tool_call: Dict[str, Any], context: Optional[Any] = None) -> Dict[str, Any]:
    """Intercept tool requests and redirect mutating file/command operations into an ephemeral shadow worktree."""
    if not isinstance(tool_call, dict):
        return tool_call

    name = tool_call.get("name", "")
    args = tool_call.get("arguments", {})

    if name in MUTATING_TOOLS and isinstance(args, dict):
        active_id = getattr(context, "active_shadow_id", None) if context else None
        if not active_id:
            spawn_res = GHOST_MANAGER.spawn_shadow(label=f"auto_{name}")
            active_id = spawn_res["shadow_id"]
            if context:
                setattr(context, "active_shadow_id", active_id)

        shadow_info = GHOST_MANAGER.active_shadows.get(active_id)
        if shadow_info:
            shadow_path = shadow_info["path"]
            if "working_directory" in args:
                args["working_directory"] = shadow_path
            elif "cwd" in args:
                args["cwd"] = shadow_path

            tool_call["_ghostbox_shadow_id"] = active_id

    return tool_call


def ghostbox_tool_execution_middleware(result: Any, tool_call: Dict[str, Any], context: Optional[Any] = None) -> Any:
    """Compute blast radius after tool execution and attach the ::ghostbox-card directive."""
    if not isinstance(tool_call, dict):
        return result

    shadow_id = tool_call.get("_ghostbox_shadow_id")
    if shadow_id and shadow_id in GHOST_MANAGER.active_shadows:
        blast = GHOST_MANAGER.compute_blast(shadow_id)
        directive = blast.get("directive", "")

        if isinstance(result, str):
            result += f"\n\n{directive}"
        elif isinstance(result, dict) and "output" in result and isinstance(result["output"], str):
            result["output"] += f"\n\n{directive}"

    return result
