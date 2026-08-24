# Runtime Exploration Algorithm

## 1. Seeds

Seed the crawler from source routes, navigation/menu definitions, documented deep links, API-triggered pages, role dashboards, feature-flag variants and field telemetry. A crawler that starts only from the home page will miss hidden, role-gated and orphaned surfaces.

## 2. State signature

For each state capture:

- URL and route parameters after canonicalization;
- role/auth/tenant/flag/fixture/browser/device/locale/timezone;
- visible interactive accessibility-tree nodes;
- important DOM landmarks and messages;
- active requests, response classes and console state;
- selected database/world-state digest where available.

Hash the canonical representation to detect equivalent states. Preserve the raw trace as evidence.

## 3. Action enumeration

Enumerate enabled actions from semantic controls, not arbitrary coordinates:

- links, buttons, form fields, menus, tabs, dialogs, file inputs, shortcuts;
- browser actions: back, forward, refresh, close/reopen, resize, zoom;
- timing actions: wait, timeout, session expiry, background completion;
- network actions: offline/online, latency, response failure;
- concurrent actions: double-click, duplicate submit, second tab/session.

Each action receives risk, reversibility, expected side effect, authorization requirement and target graph edge.

## 4. Search

1. Prioritize critical and high expected-loss edges.
2. Use breadth-first search for basic reachability and shortest reproduction.
3. Use depth/sequence exploration for multi-step state bugs.
4. Use t-way configuration sampling for role/flag/device/data combinations.
5. Use model-guided exploration only on unclosed or semantically ambiguous regions.
6. Stop revisiting a canonical state unless the action sequence, data, fault or timing condition is materially different.

## 5. Safety

- Destructive actions run only in disposable fixtures or with proven rollback.
- External notifications, payments, irreversible deletion and production writes are disabled by default.
- Active security, load and chaos require their own authorization gate.
- On new P0, permission boundary failure, subject drift or rollback failure, stop and preserve evidence.

## 6. Completion

Completion is not “no more clickable elements”. It requires source/runtime inventory reconciliation, critical node/edge closure, valid oracles, negative controls and explicit residual gaps.
