# Portability Matrix

A platform-neutral claim is scoped evidence, not a documentation assertion. Freeze a candidate tree, at least two runtimes, at least two model families, and one runtime without independent SubAgent capability. Execute every runtime × model-family cell and bind each result to raw evidence.

```bash
python3 scripts/wbi.py portability-evaluate /absolute/path/workspace \
  --contract /absolute/path/portability-contract.json \
  --results /absolute/path/portability-results.jsonl \
  --output /absolute/path/portability-summary.json
```

A fixture never supports a platform-neutral claim. Missing cells are `INCOMPLETE`. A no-SubAgent runtime must demonstrate truthful formal-promotion blocking. Untested runtimes and models remain `UNVERIFIED`; aggregate success cannot hide a failed cell.
