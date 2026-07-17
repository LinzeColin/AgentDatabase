# Memory Atlas migration-preserved validation

The paused v1.2.1 tests and evidence are preserved in the same scoped Git
history as the runtime. They are not active acceptance merely because they are
reachable.

- Scoped baseline: `dfd6c4f44f7e9d743418c6e8d1bd3021c87a5fee`
- Scoped tip: `b77dc48288786735ee4a0b1ba933f668f7b7c42e`
- Scoped final tree: `7404f1ac43f3042da0e05d5722ada364ed91cb17`
- Task Pack checkpoint: `66/149` (`44.30%`)
- Next task after migration: `S09-P3-T1`

Inspect the exact validation set without changing the working tree:

```bash
git diff --name-status dfd6c4f44f7e9d743418c6e8d1bd3021c87a5fee b77dc48288786735ee4a0b1ba933f668f7b7c42e -- tests apps/memory-atlas/scripts
git show b77dc48288786735ee4a0b1ba933f668f7b7c42e:tests/test_memory_atlas_credential_exclusion.py
git log --reverse --format='%H %s%n%b' dfd6c4f44f7e9d743418c6e8d1bd3021c87a5fee..b77dc48288786735ee4a0b1ba933f668f7b7c42e
```

Before reuse, map old paths to the migrated repository and rerun current
acceptance. Do not use preserved tests to re-enable ChatGPT login, UI scraping,
export download, raw-archive production, or retired profile contracts. Port
only compatible coverage for one bounded task.
