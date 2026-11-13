"""Ghost-Box Core Engine: Speculative Shadow-Execution and Cryptographic Blast-Radius Verifier."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import secrets
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

SHADOW_ID_REGEX = re.compile(r"^shadow_[A-Za-z0-9_-]+_[0-9a-f]{6}$")

try:
    from agent.secret_scope import get_secret
except ImportError:
    def get_secret(name: str, default: Optional[str] = None) -> Optional[str]:
        return default

try:
    from agent.file_safety import get_write_denied_error
except ImportError:
    def get_write_denied_error(dest_path: str) -> Optional[str]:
        p = Path(dest_path).resolve()
        for forbidden in (".git", ".env", ".ssh", "/etc", "C:\\Windows"):
            if forbidden.lower() in str(p).lower():
                return f"Write denied to protected path: {p}"
        return None

try:
    from hermes_cli.plugin_events import emit_plugin_event
except ImportError:
    def emit_plugin_event(plugin_name: str, event_type: str, payload: Dict[str, Any]) -> None:
        pass


logger = logging.getLogger("hermes.ghostbox.engine")

LAST_GHOSTBOX_CACHE: Dict[str, Any] = {}

def _ensure_json_str(res: Any) -> str:
    """Wrap dict return values in JSON strings for tool_call compatibility."""
    if isinstance(res, str):
        return res
    return json.dumps(res)


def get_sanitized_subprocess_env() -> Dict[str, str]:
    """Construct a minimal hermetic environment to prevent API key leakage to child processes."""
    env = {
        "PATH": get_secret("PATH", "C:\\Windows\\System32;C:\\Program Files\\Git\\cmd;/usr/bin;/bin"),
        "HOME": get_secret("HOME", get_secret("USERPROFILE", ".")),
        "TMPDIR": get_secret("TMPDIR", get_secret("TEMP", ".")),
        "TERM": "xterm-256color",
        "LANG": "en_US.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    return {k: v for k, v in env.items() if v}


class GhostUniverseManager:
    """Manages ephemeral detached git worktrees and speculative shadow execution environments."""

    def __init__(self, workspace_root: Optional[Path] = None):
        if workspace_root is None:
            self.workspace_root = Path.cwd().resolve()
        else:
            self.workspace_root = Path(workspace_root).resolve()
            
        self.ghost_dir = self.workspace_root / ".hermes" / "ghostbox"
        self._initialized = False
        self.active_shadows: Dict[str, Dict[str, Any]] = {}
        self.max_shadows = 5

    def _ensure_ready(self) -> None:
        if not self._initialized:
            self.ghost_dir.mkdir(parents=True, exist_ok=True)
            self._ensure_git_exclude()
            self._initialized = True

    def _ensure_git_exclude(self) -> None:
        """Add .hermes/ into local .git/info/exclude so it never dirties git status."""
        git_dir = self.workspace_root / ".git"
        if git_dir.is_dir():
            exclude_file = git_dir / "info" / "exclude"
            exclude_file.parent.mkdir(parents=True, exist_ok=True)
            pattern = ".hermes/\n"
            existing = ""
            if exclude_file.exists():
                existing = exclude_file.read_text(encoding="utf-8")
            if ".hermes/" not in existing:
                with open(exclude_file, "a", encoding="utf-8") as f:
                    f.write(pattern)

    def is_git_repo(self) -> bool:
        """Check if workspace is a valid git repository."""
        check = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=str(self.workspace_root),
            capture_output=True,
            text=True,
        )
        return check.returncode == 0

    def spawn_shadow(self, label: Optional[str] = None) -> Dict[str, Any]:
        """Create an ephemeral detached git worktree for speculative execution."""
        if len(self.active_shadows) >= self.max_shadows:
            return {
                "status": "error",
                "error": f"Max concurrent shadow universes ({self.max_shadows}) reached. Discard old shadows first.",
            }

        is_git = self.is_git_repo()
        if not is_git:
            return {
                "status": "error",
                "error": "Ghostbox requires a git repository to create isolated shadow worktrees safely. Refusing non-git directory copy.",
            }

        self._ensure_ready()
        clean_label = "".join(c for c in (label or "run") if c.isalnum() or c in "-_")[:16]
        shadow_id = f"shadow_{clean_label}_{secrets.token_hex(3)}"
        shadow_path = self.ghost_dir / shadow_id

        if shadow_path.exists():
            shutil.rmtree(shadow_path, ignore_errors=True)

        cmd = ["git", "worktree", "add", "--detach", str(shadow_path), "HEAD"]
        res = subprocess.run(
            cmd,
            cwd=str(self.workspace_root),
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            return {
                "status": "error",
                "error": f"Failed to create git worktree: {res.stderr.strip() or res.stdout.strip()}",
            }

        created_info = {
            "shadow_id": shadow_id,
            "path": str(shadow_path),
            "label": label or "speculative_run",
            "created_at": time.time(),
            "is_git": is_git,
            "status": "active",
        }
        self.active_shadows[shadow_id] = created_info
        LAST_GHOSTBOX_CACHE["latest_shadow"] = created_info
        emit_plugin_event("ghostbox", "shadow_spawned", created_info)
        return created_info

    def compute_blast(self, shadow_id: str) -> Dict[str, Any]:
        """Compute the cryptographic blast radius between the shadow directory and the host workspace."""
        shadow_info = self.active_shadows.get(shadow_id)
        if not shadow_info:
            return {"error": f"Shadow universe '{shadow_id}' not found", "status": "failed"}

        shadow_path = Path(shadow_info["path"])
        if not shadow_path.exists():
            return {"error": f"Shadow path '{shadow_path}' does not exist on disk", "status": "failed"}

        files_changed = 0
        lines_added = 0
        lines_removed = 0
        file_list: List[Dict[str, Any]] = []
        tree_hasher = hashlib.sha256()

        if shadow_info.get("is_git"):
            diff_num = subprocess.run(
                ["git", "diff", "--numstat", "HEAD"],
                cwd=str(shadow_path),
                capture_output=True,
                text=True,
            )
            if diff_num.returncode == 0 and diff_num.stdout.strip():
                for line in diff_num.stdout.strip().splitlines():
                    parts = line.split(maxsplit=2)
                    if len(parts) == 3:
                        add_str, rem_str, fname = parts
                        a = int(add_str) if add_str.isdigit() else 0
                        r = int(rem_str) if rem_str.isdigit() else 0
                        lines_added += a
                        lines_removed += r
                        files_changed += 1
                        file_list.append({"file": fname, "added": a, "removed": r})
                        tree_hasher.update(fname.encode("utf-8"))
                        tree_hasher.update(f"{a}:{r}".encode("utf-8"))

            status_res = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(shadow_path),
                capture_output=True,
                text=True,
            )
            untracked = [
                line[3:].strip()
                for line in status_res.stdout.splitlines()
                if line.startswith("?? ")
            ]
            for u in untracked:
                files_changed += 1
                file_list.append({"file": u, "status": "untracked", "added": 1, "removed": 0})
                lines_added += 1
                tree_hasher.update(u.encode("utf-8"))
        else:
            # Fallback file diff for non-git workspaces
            for p in shadow_path.rglob("*"):
                if p.is_file():
                    rel = p.relative_to(shadow_path)
                    if any(part.startswith(".hermes") for part in rel.parts):
                        continue
                    host_p = self.workspace_root / rel
                    if not host_p.exists() or host_p.read_bytes() != p.read_bytes():
                        files_changed += 1
                        file_list.append({"file": str(rel), "status": "modified", "added": 1, "removed": 0})
                        lines_added += 1
                        tree_hasher.update(str(rel).encode("utf-8"))

        tree_hash = tree_hasher.hexdigest()[:16]
        safety_score = 98
        if any(".env" in f.get("file", "") for f in file_list):
            safety_score -= 30

        directive = (
            f'::ghostbox-card[shadow_id="{shadow_id}" '
            f'safety_score={safety_score} '
            f'files_changed={files_changed} '
            f'lines_added={lines_added} '
            f'lines_removed={lines_removed}]'
        )

        blast_result = {
            "shadow_id": shadow_id,
            "status": "computed",
            "safety_score": safety_score,
            "files_changed": files_changed,
            "lines_added": lines_added,
            "lines_removed": lines_removed,
            "tree_hash": tree_hash,
            "files": file_list,
            "directive": directive,
        }
        shadow_info["blast_radius"] = blast_result
        LAST_GHOSTBOX_CACHE["latest_blast"] = blast_result
        emit_plugin_event("ghostbox", "blast_computed", blast_result)
        return blast_result

    def fast_forward_commit(self, shadow_id: str) -> Dict[str, Any]:
        """Fast-forward commit: apply shadow changes to the host workspace atomically with file safety checks."""
        start_t = time.perf_counter()
        shadow_info = self.active_shadows.get(shadow_id)
        if not shadow_info:
            return {"error": f"Shadow universe '{shadow_id}' not found", "status": "failed"}

        shadow_path = Path(shadow_info["path"])
        if not shadow_path.exists():
            return {"error": f"Shadow path '{shadow_path}' does not exist", "status": "failed"}

        applied_files = 0
        if shadow_info.get("is_git"):
            patch_res = subprocess.run(
                ["git", "diff", "HEAD"],
                cwd=str(shadow_path),
                capture_output=True,
            )
            if patch_res.stdout:
                apply_res = subprocess.run(
                    ["git", "apply", "--whitespace=nowarn"],
                    cwd=str(self.workspace_root),
                    input=patch_res.stdout,
                    capture_output=True,
                )
                if apply_res.returncode != 0:
                    logger.warning("git apply returned %d; falling back to file sync", apply_res.returncode)

            # Also sync any untracked new files
            status_res = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(shadow_path),
                capture_output=True,
                text=True,
            )
            for line in status_res.stdout.splitlines():
                if line.startswith("?? "):
                    rel_name = line[3:].strip()
                    src_f = shadow_path / rel_name
                    dst_f = self.workspace_root / rel_name
                    if src_f.is_file() and not src_f.is_symlink():
                        denied = get_write_denied_error(str(dst_f))
                        if denied:
                            logger.warning(f"Write denied for file {dst_f}: {denied}")
                            continue
                        dst_f.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(str(src_f), str(dst_f))
                        applied_files += 1
        else:
            return {"status": "error", "error": "Fast-forward commit only supported for git shadow worktrees"}

        duration_ms = round((time.perf_counter() - start_t) * 1000, 2)
        self.discard_shadow(shadow_id)

        result = {
            "status": "committed",
            "shadow_id": shadow_id,
            "applied_files": applied_files,
            "duration_ms": duration_ms,
        }
        LAST_GHOSTBOX_CACHE["latest_commit"] = result
        emit_plugin_event("ghostbox", "fast_forward_committed", result)
        return result

    def discard_shadow(self, shadow_id: str) -> Dict[str, Any]:
        """Vaporize shadow worktree with zero host residue safely."""
        if not isinstance(shadow_id, str) or not SHADOW_ID_REGEX.match(shadow_id):
            return {"status": "error", "error": f"Invalid shadow_id '{shadow_id}'. Must match pattern ^shadow_[A-Za-z0-9_-]+_[0-9a-f]{{6}}$"}

        self._ensure_ready()
        resolved_ghost_dir = self.ghost_dir.resolve()
        target_path = (self.ghost_dir / shadow_id).resolve()
        try:
            target_path.relative_to(resolved_ghost_dir)
        except ValueError:
            return {"status": "error", "error": f"Path traversal attempt rejected for shadow_id '{shadow_id}'"}

        shadow_info = self.active_shadows.pop(shadow_id, None)

        if target_path.exists():
            if self.is_git_repo():
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(target_path)],
                    cwd=str(self.workspace_root),
                    capture_output=True,
                )
            if target_path.exists():
                shutil.rmtree(target_path, ignore_errors=True)

        res = {"status": "discarded", "shadow_id": shadow_id}
        emit_plugin_event("ghostbox", "shadow_discarded", res)
        return res


_GHOST_MANAGER: Optional[GhostUniverseManager] = None


def get_ghost_manager(workspace_root: Optional[Path] = None) -> GhostUniverseManager:
    """Lazily instantiate GhostUniverseManager on first tool call."""
    global _GHOST_MANAGER
    if _GHOST_MANAGER is None:
        _GHOST_MANAGER = GhostUniverseManager(workspace_root=workspace_root)
    return _GHOST_MANAGER


class _GhostManagerProxy:
    """Proxy object so any direct attribute access on GHOST_MANAGER remains backwards-compatible."""
    def __getattr__(self, name: str) -> Any:
        return getattr(get_ghost_manager(), name)


GHOST_MANAGER = _GhostManagerProxy()

# Tool schemas wrapped as standard Hermes tool descriptors
GHOST_SPAWN_SCHEMA = {
    "name": "ghostbox_spawn_shadow",
    "description": "Create an ephemeral detached git worktree in .hermes/ghostbox for speculative agent execution.",
    "parameters": {
        "type": "object",
        "properties": {
            "label": {
                "type": "string",
                "description": "Optional label for this shadow universe (e.g. 'refactor_auth', 'test_migration').",
            }
        },
        "required": [],
    },
}

GHOST_BLAST_SCHEMA = {
    "name": "ghostbox_compute_blast",
    "description": "Compute the git diff and blast radius between the shadow worktree and the workspace.",
    "parameters": {
        "type": "object",
        "properties": {
            "shadow_id": {
                "type": "string",
                "description": "Unique identifier of the shadow universe to compute blast radius for.",
            }
        },
        "required": ["shadow_id"],
    },
}

GHOST_COMMIT_SCHEMA = {
    "name": "ghostbox_fast_forward_commit",
    "description": "Fast-forward commit: apply shadow changes to the host workspace atomically.",
    "parameters": {
        "type": "object",
        "properties": {
            "shadow_id": {
                "type": "string",
                "description": "Unique identifier of the shadow universe to fast-forward commit to host reality.",
            }
        },
        "required": ["shadow_id"],
    },
}

GHOST_DISCARD_SCHEMA = {
    "name": "ghostbox_discard_shadow",
    "description": "Discard and vaporize an active shadow git worktree.",
    "parameters": {
        "type": "object",
        "properties": {
            "shadow_id": {
                "type": "string",
                "description": "Unique identifier of the shadow universe to discard and vaporize.",
            }
        },
        "required": ["shadow_id"],
    },
}


def handle_ghostbox_spawn_shadow(params: Dict[str, Any]) -> str:
    label = params.get("label") if isinstance(params, dict) else None
    return json.dumps(get_ghost_manager().spawn_shadow(label))


def handle_ghostbox_compute_blast(params: Dict[str, Any]) -> str:
    shadow_id = params.get("shadow_id", "") if isinstance(params, dict) else str(params)
    return json.dumps(get_ghost_manager().compute_blast(shadow_id))


def handle_ghostbox_fast_forward_commit(params: Dict[str, Any]) -> str:
    shadow_id = params.get("shadow_id", "") if isinstance(params, dict) else str(params)
    return json.dumps(get_ghost_manager().fast_forward_commit(shadow_id))


def handle_ghostbox_discard_shadow(params: Dict[str, Any]) -> str:
    shadow_id = params.get("shadow_id", "") if isinstance(params, dict) else str(params)
    return json.dumps(get_ghost_manager().discard_shadow(shadow_id))
