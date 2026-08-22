# R8 — Vault / AssetPipeline / VCS — Status

**Updated:** 2026-08-23  
**Phase status:** IN PROGRESS  
**Planning:** ACCEPTED  
**Completed subdivisions:** R8.1–R8.6  
**Next authorized subdivision:** R8.7

## Planning authority

`docs/roadmap/R8_PLAN.md` remains the exhaustive frozen structural authority for R8.1–R8.11. Planning was accepted on head `08844fc09501ed8a4974909eca4595021bc73bf4` with R0 #1039 / `32600268817`, Python Core #1013 / `32600268710` 5/5 and UI Smoke #980 / `32600268680`, then merged by PR #83 as `60412afac35678b2a25547a7f0c937891a8a1004`.

## Accepted subdivisions

| ID | Status | Exact accepted head | PR | Merge SHA | Manual final |
| --- | --- | --- | --- | --- | --- |
| R8.1 | COMPLETE | `0e382bcdc82c5d289a9007c40d4a4b6c72120e5c` | #85 | `7001d9042dda5611f4dbcf7dacb7cd29110e6735` | NONE |
| R8.2 | COMPLETE | `2046b981cb9506999c40e3fee1a22608efecaa80` | #86 | `2d68f918b1058c1dd75be236ad74048eb598a3e6` | NONE |
| R8.3 | COMPLETE | `a1b0b6b4e07b15521acdd3a86dd963ebe4acc9c8` | #87 | `ec83fba0e664387ec4abccf047721d1ab77d4a8e` | NONE |
| R8.4 | COMPLETE | `4bf9cbd4892208084cd8ce6554edfd96a971bc04` | #88 | `a35502e0f5f09e07f3ddfd7f929f6d4d4bb490f7` | NONE |
| R8.5 | COMPLETE | `08c90bd8d52a7dd2dfc8da6ce94f6731701469f6` | #89 | `9bb1f169d7f1534b0068ad43691accf1b6a5e14a` | CONDITIONAL NOT TRIGGERED |
| R8.6 | COMPLETE | `8c88aeb8a32abce2e9ecb670da3c2acbb4a31cfe` | #91 | `57c2aa010f438b95a3d753040f1565ae4b68e262` | NONE |

## R8.6 acceptance evidence

- R0 Repository Guard #1057 / `32603562499`: SUCCESS.
- Python Core #1031 / `32603562511`: SUCCESS 5/5.
- Ubuntu authoritative suite: `547 passed / 5 skipped / 46 warnings`.
- KodeStudio UI Smoke #998 / `32603562503`: SUCCESS.
- Rejected precursor `85b6c0a550297934194a58122b735a9d0808c5c6`: fixture-only misuse of frozen contracts; production code was not weakened.

## Remaining frozen subdivisions

- R8.7 — Asset-aware Git/VCS integration — PLANNED / NONE.
- R8.8 — Git LFS tracking, pointer/object integrity + diagnostics — PLANNED / CONDITIONAL.
- R8.9 — Godot 4.7 source/import bridge + rebuild verification — PLANNED / CONDITIONAL.
- R8.10 — CLI + KodeStudio Vault/Asset/VCS UX — PLANNED / NONE.
- R8.11 — Adversarial hardening + R8 integrated acceptance — PLANNED / CONDITIONAL.

R8.7 may start only after this R8.6 normalization itself passes R0 Repository Guard, full Python Core and KodeStudio UI Smoke on one exact head and is merged to `main`.
