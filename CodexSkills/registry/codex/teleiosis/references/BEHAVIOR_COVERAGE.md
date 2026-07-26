# Behavior Coverage

Task success is insufficient when evaluation never exercises a Skill's critical constraints. `coverage-evaluate` binds a declared constraint contract to recorded trajectories and reports overall and hard-constraint coverage separately.

Formal current-environment claims require every hard constraint to be exercised. Coverage does not prove correctness; it proves that the evaluation actually reached the declared behavior surface. Unknown constraint IDs, uncovered hard behaviors or insufficient coverage produce `INCOMPLETE`.
