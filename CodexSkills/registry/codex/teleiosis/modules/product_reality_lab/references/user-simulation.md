# User Simulation and Human Profiles

## Synthetic profiles

Use profiles to diversify search behavior, not to fabricate market evidence:

- first-time user with no domain knowledge;
- experienced operator optimizing speed;
- administrator with broad permissions;
- restricted user attempting a legitimate task;
- distracted user who double-clicks, backtracks and forgets state;
- accessibility user relying on keyboard, zoom or screen reader;
- weak-device/weak-network user;
- adversarial or curious user testing boundaries;
- returning user with stale tab, old data or expired session;
- multi-tenant user switching organizations/accounts.

## Profile contract

Each model or scripted profile must define:

- goal and success outcome;
- knowledge and assumptions;
- allowed actions and prohibited actions;
- device/network/accessibility constraints;
- expected mistakes;
- stopping and escalation rules;
- evidence class `SYNTHETIC`.

## Human validation

For controlled humans, do not reveal the intended click sequence. Observe whether the participant can reach the outcome independently, how long it takes, wrong turns, hesitation, errors, recovery and support needs.

## Field validation

Real market evidence requires users doing real tasks in the real environment. Synthetic profiles can identify likely problems and create hypotheses, but cannot establish adoption, trust, retention, willingness to pay or real operational reliability.
