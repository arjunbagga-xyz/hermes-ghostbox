# Ghost-Box: Speculative Shadow Sandbox & Blast-Radius Verifier

**Ghost-Box** provides speculative execution sandboxing and diff verification for autonomous agents in Hermes.

Instead of running mutating commands directly on your live branch, Ghost-Box allows agents to spawn an ephemeral detached Git worktree (`.hermes/ghostbox/<id>`), make speculative changes, and compute a blast-radius report.

You see the exact files modified and lines changed directly in the Hermes Desktop chat transcript—then apply the changes with Fast-Forward Commit, or discard the shadow worktree with zero residue.

---

## ⚡ Core Features

* **Speculative Git Worktrees**: Spawns isolated detached shadow worktrees (`.hermes/ghostbox/<id>`) in a git repository.
* **Blast-Radius Verification**: Exact file counts, git diff analysis, and tree hashing before changes are applied to the workspace.
* **Sanitized Subprocess Environment**: Scrubs non-essential environment variables from child processes.
* **Fast-Forward Commit**: Applies verified shadow diffs atomically to the workspace with destination write safety checks.
* **Hermes Desktop Directives**: Transcript card (`::ghostbox-card`) with diff metrics and one-click actions.

---

## 🛠️ Provided Tools

1. `ghostbox_spawn_shadow(label)`: Spawns an ephemeral detached worktree.
2. `ghostbox_compute_blast(shadow_id)`: Generates blast-radius metrics and desktop card.
3. `ghostbox_fast_forward_commit(shadow_id)`: Merges shadow changes to the host workspace with write protection.
4. `ghostbox_discard_shadow(shadow_id)`: Safely discards and cleans up the shadow worktree.

---

## 💻 Desktop Directive

Renders natively in Hermes Desktop via `::ghostbox-card`:
```
::ghostbox-card[shadow_id="shadow_7f8a" safety_score=98 files_changed=2 lines_added=24 lines_removed=6]
```

---

## 📄 License

MIT © 2026 Arjun Bagga
