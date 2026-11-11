# Ghost-Box: Speculative Shadow Sandbox & Blast-Radius Verifier

**Ghost-Box** eliminates execution risk and developer confirmation fatigue for autonomous agents in Hermes.

Instead of running irreversible commands (`bash`, `write_file`, database scripts) directly on your live workspace, Ghost-Box intercepts mutating actions, speculatively runs them in an ephemeral detached Git worktree with an isolated hermetic environment, and computes a cryptographic blast-radius report.

You see the exact files modified, lines changed, and safety score directly in the Hermes Desktop chat transcript—then apply the changes in **1 millisecond** with Fast-Forward Commit, or discard them with zero residue.

---

## ⚡ Core Features

* **Speculative Git Worktrees**: Spawns isolated detached shadow universes (`.hermes/ghostbox/<id>`) in under 15ms.
* **Cryptographic Blast-Radius Verification**: Exact inode counts, Myers diff, and SHA256 tree hashing before any host file changes.
* **Hermetic Subprocess Environment**: Zero API key or secret leakage to child processes.
* **1-Millisecond Fast-Forward Commit**: Applies verified shadow diffs atomically without re-running commands.
* **Hermes Desktop Directives**: Glassmorphic transcript card (`::ghostbox-card`) with live metrics and one-click actions.

---

## 🛠️ Provided Tools

1. `ghostbox_spawn_shadow(label)`: Spawns an ephemeral detached worktree.
2. `ghostbox_compute_blast(shadow_id)`: Generates cryptographic blast-radius metrics and desktop card.
3. `ghostbox_fast_forward_commit(shadow_id)`: Atomically merges shadow changes to the host workspace.
4. `ghostbox_discard_shadow(shadow_id)`: Vaporizes the shadow worktree, leaving zero host mutations.

---

## 💻 Desktop Directive

Renders natively in Hermes Desktop via `::ghostbox-card`:
```
::ghostbox-card[shadow_id="shadow_7f8a" status="verified" safety_score=98 files_changed=2 lines_added=24 lines_removed=6 secrets_leaked=0 egress_blocked=0]
```

---

## 📄 License

MIT © 2026 Arjun Bagga
