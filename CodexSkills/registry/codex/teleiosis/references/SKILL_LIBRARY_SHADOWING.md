# Skill-Library Shadowing

A Skill can work in isolation and fail after installation into a large library because retrieval, ranking and activation change. `shadowing-evaluate` measures top-1 selection accuracy, top-k recall, false activation, confusion pairs and the outcome delta between isolated and library conditions.

When a Skill library is in scope, a current-environment strength claim requires a passing shadowing result. Missing outcome deltas are blockers rather than zeros. This check remains replaceable and does not bind Teleiosis to a specific retrieval engine.
