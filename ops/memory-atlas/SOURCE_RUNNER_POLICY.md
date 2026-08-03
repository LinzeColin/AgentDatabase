# Memory Atlas source-runner policy

Codex is disabled and is not a runtime dependency. Do not install a new Codex Automation.

The authoritative Mac source path is:

```text
user crontab (wake every 30 minutes)
→ run_due.py (at most one successful capture per local calendar day)
→ memory_atlas_source_capture_entry.py
→ content-addressed R2 objects
→ Private-Database facts
→ OVH reconcile / Atlas refresh / self-heal
```

The 30-minute wake-up is only a catch-up mechanism after sleep or network loss. A successful capture records `last_success_local_date`; all later wakes that local day are skipped. A failure remains retryable at the next wake. macOS launchd and an active Agent session are both forbidden.

`automation_lifecycle.py` exists only to:

1. snapshot and hash the failed historical encrypted Codex Automation;
2. verify the archive;
3. atomically set the old Automation to `PAUSED`;
4. retire its directory only after all six replacement gates prove the generic source runner, R2 readback, Private-Database fact commit, Atlas refresh and isolated restore.

There is deliberately no `install-new` command.
