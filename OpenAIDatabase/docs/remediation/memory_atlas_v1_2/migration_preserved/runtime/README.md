# Memory Atlas migration-preserved runtime

The paused v1.2.1 runtime and configuration are preserved in a scoped Git
history reachable from `AgentDatabase/main`. They are intentionally absent
from active roots when they conflict with the repository split or current
security contracts.

- Scoped baseline: `dfd6c4f44f7e9d743418c6e8d1bd3021c87a5fee`
- Scoped tip: `b77dc48288786735ee4a0b1ba933f668f7b7c42e`
- Scoped final tree: `7404f1ac43f3042da0e05d5722ada364ed91cb17`
- Task Pack checkpoint: `66/149` (`44.30%`)
- Next task after migration: `S09-P3-T1`

Inspect the exact runtime without changing the working tree:

```bash
git diff --name-status dfd6c4f44f7e9d743418c6e8d1bd3021c87a5fee b77dc48288786735ee4a0b1ba933f668f7b7c42e -- scripts config apps/memory-atlas
git show b77dc48288786735ee4a0b1ba933f668f7b7c42e:scripts/atlasctl.py
git show b77dc48288786735ee4a0b1ba933f668f7b7c42e:apps/memory-atlas/src/App.tsx
```

The scoped chain's `apps/memory-atlas/` maps to active `MemoryAtlas/`.
Do not restore either root wholesale. Port one bounded task at a time under
the current dual-plane governance and security gates. Never restore automated
ChatGPT login, UI scraping, export download, raw-archive production, or retired
command/profile contracts.
