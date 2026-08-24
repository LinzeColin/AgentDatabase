# Test Data Catalog

## Scalar and text

- empty/null/missing/zero;
- minimum/maximum and just-inside/just-outside boundaries;
- whitespace-only, leading/trailing, repeated spaces and line breaks;
- Chinese, Latin, mixed scripts, emoji, combining characters and RTL where applicable;
- very long text, duplicate values and normalization collisions;
- reserved words and safe security payloads in an authorized environment.

## Time

- past/future/expired, month/year end, leap day;
- timezone conversion, daylight-saving transition where applicable;
- clock skew, delayed jobs, duplicate schedules and cutoff boundaries.

## Files

- empty, valid small, valid large, maximum and over-limit;
- wrong extension/MIME, corrupt, truncated, duplicate and password-protected;
- Unicode filenames, long filenames, archives and nested content within policy.

## Identity and permissions

- anonymous, expired, revoked, role changed, tenant switched;
- owner/non-owner, admin/restricted, cross-tenant ID and stale authorization cache.

## Data lifecycle

- create/read/update/delete/restore/archive;
- duplicate import, partial import, retry after timeout;
- migration from each supported prior version;
- concurrent edits and conflict resolution;
- backup, full restore and selective restore.

## External dependency

- success, 4xx, 5xx, timeout, slow, malformed, duplicate, out-of-order and recovery.
