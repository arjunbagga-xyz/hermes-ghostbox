"""Smoke test suite for Ghost-Box speculative execution and blast radius verification."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from ghostbox.engine import (
    GhostUniverseManager,
    get_sanitized_subprocess_env,
    handle_ghostbox_compute_blast,
    handle_ghostbox_discard_shadow,
    handle_ghostbox_fast_forward_commit,
    handle_ghostbox_spawn_shadow,
)


def test_sanitized_env():
    env = get_sanitized_subprocess_env()
    assert "PATH" in env
    assert "PYTHONDONTWRITEBYTECODE" in env
    assert env["PYTHONDONTWRITEBYTECODE"] == "1"


def test_ghostbox_lifecycle_in_temp_workspace():
    with tempfile.TemporaryDirectory() as tmpdir:
        ws = Path(tmpdir)
        mgr = GhostUniverseManager(ws)

        # 1. Create a dummy file in workspace
        (ws / "hello.txt").write_text("initial content", encoding="utf-8")

        # 2. Spawn a shadow universe
        shadow = mgr.spawn_shadow("unit_test")
        shadow_id = shadow["shadow_id"]
        shadow_path = Path(shadow["path"])
        assert shadow_path.exists()
        assert shadow_id in mgr.active_shadows

        # 3. Mutate file only inside shadow universe
        (shadow_path / "hello.txt").write_text("shadow updated content\nnew line", encoding="utf-8")
        (shadow_path / "new_module.py").write_text("print('hello')", encoding="utf-8")

        # Verify host workspace remains UNTOUCHED
        assert (ws / "hello.txt").read_text(encoding="utf-8") == "initial content"
        assert not (ws / "new_module.py").exists()

        # 4. Compute blast radius
        blast = mgr.compute_blast(shadow_id)
        assert blast["status"] == "verified"
        assert blast["files_changed"] >= 2
        assert "::ghostbox-card" in blast["directive"]

        # 5. Fast-forward commit
        commit_res = mgr.fast_forward_commit(shadow_id)
        assert commit_res["status"] == "committed"

        # Verify host workspace is now atomically updated!
        assert (ws / "hello.txt").read_text(encoding="utf-8") == "shadow updated content\nnew line"
        assert (ws / "new_module.py").exists()

        # Verify shadow directory was vaporized
        assert not shadow_path.exists()
        assert shadow_id not in mgr.active_shadows


def test_ghostbox_discard_leaves_zero_residue():
    with tempfile.TemporaryDirectory() as tmpdir:
        ws = Path(tmpdir)
        mgr = GhostUniverseManager(ws)

        (ws / "safe.txt").write_text("original", encoding="utf-8")
        shadow = mgr.spawn_shadow("discard_test")
        shadow_id = shadow["shadow_id"]
        shadow_path = Path(shadow["path"])

        # Mutate inside shadow
        (shadow_path / "safe.txt").write_text("corrupted", encoding="utf-8")
        (shadow_path / "unwanted.bin").write_text("junk", encoding="utf-8")

        # Discard shadow
        discard_res = mgr.discard_shadow(shadow_id)
        assert discard_res["status"] == "discarded"

        # Host is pristine
        assert (ws / "safe.txt").read_text(encoding="utf-8") == "original"
        assert not (ws / "unwanted.bin").exists()
        assert not shadow_path.exists()


def test_tool_handlers():
    res_raw = handle_ghostbox_spawn_shadow({"label": "tool_test"})
    assert isinstance(res_raw, str)
    res = json.loads(res_raw)
    assert "shadow_id" in res
    sid = res["shadow_id"]

    blast = json.loads(handle_ghostbox_compute_blast({"shadow_id": sid}))
    assert blast["status"] == "verified"

    discard = json.loads(handle_ghostbox_discard_shadow({"shadow_id": sid}))
    assert discard["status"] == "discarded"
