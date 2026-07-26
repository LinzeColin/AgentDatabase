# Version policy v3 draft and consumer readiness

Status: **DRAFT_NON_ACTIVE_MECHANISM_CONSUMER_READY**

This isolated Mechanism-owned draft closes the six MAJOR trigger codes missing
from `version-policy:v2` and makes the separation between global SRV and daily
Auto transactions explicit. It preserves the notification-only MAJOR contract:
planned writes require provider `SENT`, owner approval/reply remain false, and
the real recipient mapping stays repo-external.

The current instance deliberately does not choose between `04:15` and `05:30`.
It records both observed candidates, keeps `daily_schedule_local=null`, and
sets `schedule_activation_permitted=false`. Only later direct Owner authority
may select a time; neither this builder nor a consumer may infer one.

These files are not members of the trusted 31-schema/5-policy candidate.
`consumer.py` provides an explicit dual-read interface: v2 is accepted only
as `PREDECESSOR_READ_ONLY`, v3 only as `SUCCESSOR_SHADOW`, and hybrid,
implicit, unknown, or duplicate selection fails closed. Both schedule reads
remain authority-unresolved and cannot authorize activation.

The draft interface declares RFC 8785 JCS, exact self-pointer exclusion, and
SHA-256 semantics. It is not its own trust root: every later consumer must
receive the verified Git object, expected raw interface SHA-256, canonical
path, and `DRAFT_NON_ACTIVE_VERSION_POLICY` mode from repo-external state.

`consumer-readiness.json` proves the Mechanism consumer against independent
immutable roots: candidate `sha1:5ee37d7…` and v3 draft `sha1:07f7925…`.
It also inventories the actual Auto schedule, notification, bootstrap, and
shared-contract consumers from `sha1:1c82955…`. Those Auto consumers remain
v2/candidate-only, so the artifact truthfully keeps
`auto_consumer_first_verified=false`,
`cross_plane_consumer_first_complete=false`, candidate materialization false,
and hands off only to `AUTO_VERSION_POLICY_V3_DUAL_READ_INTEGRATION`.

Rebuild and verify deterministically from the repository root:

```bash
/usr/bin/python3 -B \
  CodexSkills/governance/tools/build_version_policy_v3_draft.py --write
/usr/bin/python3 -B \
  CodexSkills/governance/tools/build_version_policy_v3_draft.py --check
/usr/bin/python3 -B \
  CodexSkills/governance/tools/build_version_policy_v3_consumer_readiness.py \
  --write
/usr/bin/python3 -B \
  CodexSkills/governance/tools/build_version_policy_v3_consumer_readiness.py \
  --check
```
