# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 25 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning ACCEPTED + NORMALIZED. R12.1–R12.11 COMPLETE + NORMALIZED. R12.11 normalization PR #208 merged as `1f2d18b01e79845473fefbda98f722485310d92a`, sole normalized base for R12.12. R12.12 branch `r12/12-local-ipc`, PR #209, accepted candidate `2ba561745f59b2701e5578df0915e58dab2345e0`; R0 #1556, Python #1530, UI #1497, WPF #53, WinUI #43, Avalonia #39, Qt #34 and Tauri #25 are all SUCCESS. Python Core proved real hosted Windows `AF_PIPE` and Linux `AF_UNIX` roundtrips, so manual R12.12 CONDITIONAL was NOT TRIGGERED. Evidence-recording documentation bytes now require a fresh exact-head re-gate before expected-SHA merge. R12.13 remains forbidden until the single R12.12 post-merge normalization is accepted and merged.**

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; normalized `main` after each accepted normalization merge is source of truth.
- R1–R11 : **COMPLETE + NORMALIZED**.
- R12 planning : **ACCEPTED + NORMALIZED**.
- R12.1–R12.11 : **COMPLETE + NORMALIZED**.
- R12.12 : **IMPLEMENTED / CANDIDATE ACCEPTED / FINAL DOCUMENTATION RE-GATE PENDING**.
- R12.13–R12.16 : **PLANNED / NOT STARTED**.

## R12.11 closure authority

- Base normalized `main`: `25b3e94b58d6ac08511b2510a98148354f5144f2`.
- PR #207 final-documentation head `4e0aaa34b1c45dd35741e7930bdbdaa06740c5e7` passed R0 #1552, Python #1526, UI #1493, WPF #51, WinUI #41, Avalonia #37, Qt #32 and Tauri #23; merged as `86e1663eb4f68f74cdba23687161c8d38849f11e`.
- Single normalization PR #208 head `ea3244b5b031d37d7e2d4e3557c75e369aeff24b` passed R0 #1554, Python #1528, UI #1495, WPF #52, WinUI #42, Avalonia #38, Qt #33 and Tauri #24; merged as `1f2d18b01e79845473fefbda98f722485310d92a`.
- **R12.11 COMPLETE + NORMALIZED**.

## R12.12 execution authority

- Base normalized `main`: `1f2d18b01e79845473fefbda98f722485310d92a`.
- Dedicated branch: `r12/12-local-ipc`.
- PR: #209.
- Manual state: **CONDITIONAL / NOT TRIGGERED**.
- Frozen scope: versioned local IPC envelope and endpoint identity; bounded length framing; HMAC authentication; peer session/role/method authorization; replay rejection; stale/malformed/oversized/truncated failure; `AF_PIPE` Windows and `AF_UNIX` Linux local transports; no network fallback; owned endpoint cleanup.
- Accepted implementation candidate: `2ba561745f59b2701e5578df0915e58dab2345e0`.
- Exact-head candidate evidence: R0 #1556 / run `32825111226`; Python #1530 / `32825111135`; UI #1497 / `32825111255`; WPF #53 / `32825111230`; WinUI #43 / `32825111274`; Avalonia #39 / `32825111277`; Qt #34 / `32825111137`; Tauri #25 / `32825111146` — all SUCCESS.
- Hosted `python-core-windows-latest` and `python-core-ubuntu-latest` both completed the focused transport tests successfully. Required OS semantics are proven by hosted CI; no manual evidence is required.
- Security claim remains bounded: Kodepoia does not claim Python's high-level `AF_PIPE` wrapper installs a custom Windows DACL. Application HMAC/session/method authorization and local-machine addressing are proven; no TCP/network fallback is present.
- Evidence-recording docs changed after the accepted candidate; therefore the final PR #209 documentation HEAD must pass the same fresh exact-head standard and regression gates before merge with `expected_head_sha`.
- After PR #209 merge, create exactly one continuity-only `r12/12-postmerge-continuity-normalization` PR, gate its exact HEAD, merge it, and only then authorize R12.13.

## Frozen R12 subdivision index

| ID | Titre | Manuel |
| --- | --- | --- |
| R12.1 | Desktop contracts, identities, capability model + secure toolchain boundaries | NONE |
| R12.2 | Project DNA/KodeProduct desktop profiles + Project Wizard target selection | NONE |
| R12.3 | Deterministic desktop scaffold/template/workspace manifest engine | NONE |
| R12.4 | Framework-neutral MVVM/state/navigation/command/service contracts | NONE |
| R12.5 | WPF/.NET desktop adapter + build/test bridge | CONDITIONAL |
| R12.6 | WinUI 3/Windows App SDK adapter + Windows identity/deployment bridge | CONDITIONAL |
| R12.7 | Avalonia cross-platform desktop adapter | CONDITIONAL |
| R12.8 | Qt 6/CMake desktop adapter | CONDITIONAL |
| R12.9 | Tauri v2/Rust/WebView2 desktop adapter | CONDITIONAL |
| R12.10 | SQLite persistence, schema migrations, transactions + backup/recovery | NONE |
| R12.11 | Async/concurrency, cancellation, progress + UI-thread lifecycle safety | NONE |
| R12.12 | Local IPC contracts, framing, authorization + lifecycle isolation | CONDITIONAL |
| R12.13 | Accessibility, localization, theming, keyboard/focus + DPI/scaling QA | CONDITIONAL |
| R12.14 | Packaging/install/update/signing-state + rollback model | CONDITIONAL |
| R12.15 | CLI + KodeStudio Desktop workspace and governed Wizard workflow | NONE |
| R12.16 | Adversarial hardening + Wizard-to-Windows integrated acceptance | CONDITIONAL |

## Permanent boundaries

Workspace/R8 Vault boundaries; ProcessSandbox + KillSwitch; Guardian/PermissionSet; SafeChange/Backup/Recovery/Audit; KodeSecrets/redaction; R6 governance/security/privacy/license/build/accessibility/localization; R7 ResearchGuard; R8 lineage/provenance/cache/export; R9 AI resource arbitration; R10 3D authority; R11 media/runtime/privacy/evidence boundaries remain in force. Structured APIs only. Network off by default. Exact-head evidence mandatory. Missing evidence never manufactures PASS.

## Execution rule

Each R12 subdivision: dedicated branch from normalized `main` → implementation + focused tests → exact-head standard + subdivision-specific gates → satisfy triggered manual state → evidence/re-gate if bytes change → merge with `expected_head_sha` → exactly one continuity-only post-merge normalization + exact-head gates + merge → only then next subdivision.

If any CONDITIONAL manual gate triggers, stop before the next subdivision and provide exact bounded user commands/prerequisites/evidence path.

## Next authorized action

**R12.12 only:** re-gate the final documentation HEAD of PR #209 exactly. If all required gates remain SUCCESS, merge PR #209 with `expected_head_sha`, then perform exactly one continuity-only post-merge normalization with fresh exact-head gates. R12.13 is authorized only after that normalization merge. Manual R12.12 is **CONDITIONAL / NOT TRIGGERED**.
