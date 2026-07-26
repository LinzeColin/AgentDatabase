# Version policy v3 draft

Status: **DRAFT_NON_ACTIVE_CONSUMER_FIRST_REQUIRED**

This isolated Mechanism-owned draft closes the six MAJOR trigger codes missing
from `version-policy:v2` and makes the separation between global SRV and daily
Auto transactions explicit. It preserves the notification-only MAJOR contract:
planned writes require provider `SENT`, owner approval/reply remain false, and
the real recipient mapping stays repo-external.

The current instance deliberately does not choose between `04:15` and `05:30`.
It records both observed candidates, keeps `daily_schedule_local=null`, and
sets `schedule_activation_permitted=false`. Only later direct Owner authority
may select a time; neither this builder nor a consumer may infer one.

These files are not members of the trusted 31-schema/5-policy candidate. A
consumer-first compatibility Phase and a later coordinated bundle
materialization are required before any activation.

The draft interface declares RFC 8785 JCS, exact self-pointer exclusion, and
SHA-256 semantics. It is not its own trust root: every later consumer must
receive the verified Git object, expected raw interface SHA-256, canonical
path, and `DRAFT_NON_ACTIVE_VERSION_POLICY` mode from repo-external state.

Rebuild and verify deterministically from the repository root:

```bash
/usr/bin/python3 -B \
  CodexSkills/governance/tools/build_version_policy_v3_draft.py --write
/usr/bin/python3 -B \
  CodexSkills/governance/tools/build_version_policy_v3_draft.py --check
```
