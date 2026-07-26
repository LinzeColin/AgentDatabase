# Examples

```bash
# First run the namesake gate. The candidate file is the orchestration layer's
# canonical-registry + authoritative-source search result.
python3 scripts/namesake_gate.py --name "Richard Feynman" --candidates-file ./namesake-candidates.json --output ./namesake-gate.json

# Single identity
python3 scripts/init_target.py --name "Richard Feynman" --identity 1 --namesake-gate ./namesake-gate.json --workspace ./workspaces

# Weighted multi identity
python3 scripts/init_target.py --name "Example Person" --identity "1:60+5:40" --namesake-gate ./namesake-gate.json --workspace ./workspaces

# Optional scenario hint
python3 scripts/init_target.py --name "Example Founder" --identity 2 --scenario "公司战略与产品评审" --namesake-gate ./namesake-gate.json --workspace ./workspaces
```
