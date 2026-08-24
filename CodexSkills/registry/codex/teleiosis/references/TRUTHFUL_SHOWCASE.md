# Truthful Showcase

## Purpose

Luban Skill correctly treats installability, a visible result and public comprehension as product requirements. The failure mode is allowing a showcase to become stronger than the evidence behind it. Teleiosis therefore generates the display from frozen status data and enforces claim boundaries in code.

## Inputs

`showcase` reads:

- one eight-domain status JSON;
- optionally one frozen comparison JSON with `evidence_status`, `claim_scope` and `winner`;
- a title and output path.

All values are HTML-escaped. The output has no external scripts, fonts, analytics or network dependencies.

## Claim rules

- When comparison evidence is not exactly `PROVEN`, `winner` is rendered as `WITHHELD`.
- When outcome, external review and formal promotion are incomplete, the banner states `ENGINEERING CANDIDATE - MARKET LEADERSHIP NOT PROVEN`.
- Control-plane PASS, test count, package integrity or static score cannot promote the banner.
- `UNKNOWN`, `NOT_RUN` and `PARTIAL` remain visible; they never become PASS.
- The generated card itself states that it is not an independent attestation.

## Output

The command writes:

1. a self-contained HTML evidence card;
2. a sibling `.receipt.json` containing output hash, byte size, derived leadership label and claim boundary.

```bash
python3 scripts/wbi.py showcase \
  --status templates/showcase-status.json \
  --output /external/path/teleiosis-evidence-card.html
```

A formal comparison can be added only when its contract and result are already frozen:

```bash
python3 scripts/wbi.py showcase \
  --status /external/path/status-summary.json \
  --comparison /external/path/frozen-comparison.json \
  --output /external/path/teleiosis-evidence-card.html
```

## Reproducibility

The HTML can be regenerated from the same inputs; however, the receipt timestamp will differ. Formal release evidence should bind the exact generated HTML and receipt hashes rather than assuming regeneration is byte-identical across time.
