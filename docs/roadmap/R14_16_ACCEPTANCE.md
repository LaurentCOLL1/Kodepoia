# R14.16 Acceptance — CLI + KodeStudio Backend/LiveOps UX

## Decision

**PASS — technical source accepted.**

Immutable technical source: `3c0507ed497d9607218b9d9a50c2e5729d786c87`.

R14.16 is technically accepted with manual state **NONE**. This document records decision evidence only; R14.17 remains unauthorized until the R14.16 END-head passes fresh exact-head gates, the implementation PR merges with expected-head protection, and the unique post-merge continuity-only normalization passes fresh R0/Python/UI and merges.

## Scope accepted

The accepted source exposes R14 backend/LiveOps capability through structured CLI and KodeStudio adapters while preserving existing domain authority. The surface covers backend profile, local-stack status/control, migration preview/apply, provider capability/status, lobby/save/progression inspection, entitlement reconciliation preview, remote-config/content/campaign preview and governed rollout/rollback, event-replay preview, and health/load/backup reporting.

The accepted UX does not expose a raw shell, raw endpoint/URL authority, raw secret/token/password fields, or automatic production publish/deployment. Environment and mode are explicit. Inspect/preview remains the default where required. Confirmation is user intent only and never grants domain permission.

## Immutable source and exact-head gates

- START-head: `3b0ad3bf666f1e6247699b8ef611b436f836b60a`.
- Immutable technical source: `3c0507ed497d9607218b9d9a50c2e5729d786c87`.
- START→source: 14 commits, exactly 13 intended technical/test/evidence files; no staging helper survives.
- R0 Repository Guard #2005 / run `33260302790`: **SUCCESS** on Ubuntu + Windows.
- Python Core #1980 / run `33260302771`: **SUCCESS 5/5** (Ubuntu/Windows core, Ubuntu/Windows package-build, KodeStudio UI-in-core).
- KodeStudio UI Smoke #1945 / run `33260302782`: **SUCCESS**.
- R14 CLI KodeStudio LiveOps UX Acceptance #2 / run `33260302752`: **SUCCESS** on Ubuntu 24.04 + Windows 2025.
- Full Ubuntu Python Core: **1752 passed / 14 skipped / 46 warnings**; R7/R8/R9 integrated acceptance validation PASS.
- Dedicated focused acceptance regression: **26 passed** on Ubuntu; Windows completed the same focused test step successfully.

## Deterministic acceptance evidence

All **31/31** frozen checks PASS:

1. action/mode mismatch rejected;
2. authorized mutation only via domain authority;
3. authorized mutation output redacted;
4. backup report makes no production PITR claim;
5. catalog forbids raw authority inputs;
6. catalog contains all 15 operations;
7. preview defaults frozen;
8. catalog schema v1;
9. CLI exposes no raw escape flags;
10. confirmation does not self-grant permission;
11. explicit confirmation required before mutation;
12. endpoint-like payload value rejected;
13. English localization available;
14. French localization available;
15. load report makes no external-load claim;
16. local-stack mutation restricted to local/test;
17. nested token field rejected;
18. nested password redacted;
19. secret reference redacted;
20. token redacted;
21. preview uses typed domain port;
22. production requires separate authority;
23. project fallback never authorizes mutation;
24. provider status truthfully unavailable when unbound;
25. pseudo-locale expands the R14 surface;
26. raw command field rejected;
27. raw endpoint field rejected;
28. resource-ID endpoint escape rejected;
29. stable JSON deterministic;
30. UI exposes only structured governed controls;
31. Backend/LiveOps page is wired into KodeStudio.

Evidence flags are exactly:

- `manual_state=none`
- `provider_live_claim=false`
- `external_provider_required=false`
- `secrets_exposed=false`
- `raw_command_input_exposed=false`
- `raw_endpoint_input_exposed=false`
- `automatic_production_publish=false`
- `operation_count=15`
- `check_count=31`
- `passed_count=31`

Canonical evidence digests:

- catalog: `f0ac90c20d06d7e6ffdff22756bf65499c5e9d839098fb51ec8a7f1738dc351b`
- preview: `ff1089d254637027bd959a669cae6b3cc6f82252c2c1883cb24c1878fe418719`
- authorized mutation: `c809c93458f425b48a7546afc78bd21dff3b412a6a17c3ba203d1c615cdc8c13`

The decoded Ubuntu and Windows JSON evidence objects are **exactly equal**, each 2245 bytes with canonical evidence-file SHA-256 `396588f20a03bb555c1a69cfd9b076151e850d11c8842b9ef9a94708a6a7eea2`.

GitHub artifact records:

- Ubuntu: artifact `9717060425`, ZIP digest `sha256:2e53b8fab1bfb5acd0e8197ee79e8475b975e3aecc017c264347bd00c73a607a`, 1076 bytes.
- Windows: artifact `9717061707`, ZIP digest `sha256:39308eb7833026dc06184ec5e753fe229279898f95693fd55181ee78f1ef6907`, 1076 bytes.

## Rejected / superseded candidates

- `1707ca57a325a3187bfbe5327002bc2f30dc34d7`: rejected as decision authority after the Windows KodeStudio smoke exposed the stale R6.6 navigation-count regression and missing R14 pseudo-locale coverage. The fix added real R14 pseudo-localization plus an explicit R14 UI assertion; none of the failed candidate evidence is reused.
- `c6a62355bf58a49c0bc4fc41a0ef29e6d0168825`: rejected as decision authority because the first dedicated Ubuntu acceptance could not import PySide6 (`libEGL.so.1` absent on the runner). This was a runner dependency failure before R14 business assertions; the workflow now installs the required Linux Qt runtime libraries. No evidence from that candidate is reused.

## Security / authority conclusions

- Confirmation and authorization remain separate. A confirmed mutation without domain authority is `BLOCKED`.
- Production mutation requires separate production authority in addition to ordinary domain authorization.
- The default project fallback can inspect/preview truthful local state but never self-authorizes mutation.
- Missing provider binding remains `UNAVAILABLE`; provider-live capability is not inferred.
- Raw command, shell, endpoint, URL, token, password, DSN, private-key and secret inputs are rejected at the UX boundary.
- Returned token/password/secret-reference fixture data is recursively redacted before stable JSON serialization.
- No external account, credential, provider quota, public domain/TLS state, production deployment, production PITR, Internet-scale or destructive load proof is required or claimed.

## Manual intervention

**NONE.**

No user-side action, external provider account, credential, production endpoint or destructive production operation is required for the accepted R14.16 core.

## END-sync requirement

The immutable source must not change. END-sync may change only `docs/roadmap/R14_PLAN.md`, this acceptance document, and `docs/continuity/KODEPOIA_CONTINUITY.md`. The resulting exact END-head must pass fresh R0 Repository Guard, full Python Core, KodeStudio UI Smoke and R14 CLI KodeStudio LiveOps UX Acceptance before the implementation PR may merge with `expected_head_sha`.
