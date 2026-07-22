# Money and file safety contract

## Money

`parse_money` requires a versioned `MoneyProfile` and an explicit `RoundingLayer`. It never accepts float or bool. Blank input is an error unless the caller explicitly chooses `NULL` or `ZERO`; this choice is an ingestion policy and must later be evidence-bound per source field.

The returned `MoneyValue` contains integer minor units plus audit metadata. A negative-zero input becomes canonical zero but remains flagged. Values with more than six source decimal places, visually confusable Unicode signs, malformed grouping, nonfinite decimals, and values beyond signed 64-bit minor units fail closed.

Profile values use exact YAML types: numeric ceilings must be integers, the float switch must be boolean, and policy fields must be strings. Configuration coercion and any attempt to relax the registered R2 safety policies fail closed.

The six-decimal source ceiling applies to money amounts, not rates. Tax, FX, interest, and allocation rates require their own R8 formula profiles and must not be passed through the money parser as amounts.

## Governed paths and atomic output

Inputs must resolve under an explicit root and be regular files with one hard link. Traversal, backslashes, symlinks, special files, missing files, and size overflow are blockers.

Atomic file publishing never overwrites an existing target. Atomic directory publishing makes the final-looking directory visible only after all contents are ready. Failures clean the current temporary artifact but do not delete a target created by another process.

File publishing uses a same-filesystem hard-link no-replace operation; directory publishing uses the host's atomic no-replace rename primitive. The current implementation supports macOS `renamex_np(RENAME_EXCL)` and Linux `renameat2(RENAME_NOREPLACE)` and blocks on hosts without either primitive.

## ZIP and nested containers

Archive preflight verifies the complete CRC stream after path/type/resource checks. Portable normalization uses compatibility Unicode normalization and case folding, so targets that would collide on a common desktop filesystem are blocked.

Governed source identity and SHA-256 are checked again after preflight. A file that changes during ZIP, OOXML, or PDF inspection is blocked rather than bound to a mixed snapshot.

Members named as nested ZIP/XLSX containers are streamed only into an explicitly supplied existing private scratch directory and recursively checked under one global member/expanded-size budget and depth ceiling. The scratch directory is never selected implicitly. Macro-enabled nested workbooks are blocked immediately.

Archive preflight does not make a nested workbook a validated business source. The later source reader must run OOXML inspection and schema gates on each selected nested workbook before parsing.

## OOXML, XLS, PDF, and output text

OOXML inspection never invokes Excel, WPS, LibreOffice, a formula engine, macro runtime, network client, or external relationship. Formula cells remain blocked until a later governed cached-value reader can distinguish formula text, cached evidence, and calculation provenance.

Legacy XLS is explicitly unsupported rather than silently skipped. PDF preflight validates a conservative container boundary but does not make PDF a calculate source. Image-only sheets are reported as unstructured evidence and blocked from structured ingestion.

Untrusted spreadsheet text is prefixed with an apostrophe when a formula-leading token could be interpreted. Financial numeric values must be written through a numeric writer rather than converted to escaped strings.
