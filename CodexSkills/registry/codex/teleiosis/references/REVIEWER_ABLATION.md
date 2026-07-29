# Reviewer Ablation

Use reviewer ablation to measure whether 2, 6, or 12 reviewers add distinct supported findings relative to their token, monetary, latency, and human burden. It does **not** amend Genesis `WBI-GB-019`: formal promotion still requires two panels of six independently attested reviewers and a distinct read-only verifier.

The study must contain at least thirteen unique review identities: twelve reviewer records and one verifier. Include cohorts of 2, 6, 12, and 12 plus the distinct verifier. A fixture can validate the pipeline but can never recommend a production panel. A real recommendation requires independently attested reviews and complete token and monetary-cost evidence.

```bash
python3 scripts/wbi.py review-ablation \
  --study /absolute/path/reviewer-ablation-study.json \
  --output /absolute/path/reviewer-ablation-result.json
```

The engineering recommendation is only an efficiency observation. It cannot reduce formal review requirements or convert `INDEPENDENT_REVIEW_UNAVAILABLE` into PASS.
