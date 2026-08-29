from __future__ import annotations

from pathlib import Path

PLAN = Path("docs/roadmap/R14_PLAN.md")
CONTINUITY = Path("docs/continuity/KODEPOIA_CONTINUITY.md")

plan = PLAN.read_text(encoding="utf-8")
section_start = plan.index("# R14.16 — CLI + KodeStudio Backend/LiveOps UX, local stack control + dry-run/provider status")
section_end = plan.index("# R14.17 — Adversarial integrated backend/platform-services/LiveOps acceptance", section_start)
section = plan[section_start:section_end]
old_completion = "## Completion record\n\nTo be appended when accepted.\n\n---\n\n"
if section.count(old_completion) != 1:
    raise SystemExit(f"R14.16 completion marker count={section.count(old_completion)}")
completion = """## Completion record

- Dedicated branch: `r14/16-cli-kodestudio-liveops-ux`; effective normalized-history branch point `8a7eb312d3fa0d642d6b2b77ef35c2b2d3e7de36`; clean START-head `3b0ad3bf666f1e6247699b8ef611b436f836b60a` preceded implementation.
- Accepted immutable technical source: `3c0507ed497d9607218b9d9a50c2e5729d786c87`. START→source contains exactly 13 intended technical/test/evidence files: governed Backend/LiveOps facade, CLI, KodeStudio panel/localization, CLI/app wiring, four regression files including R6.6 pseudo-locale coverage, deterministic acceptance script, evidence schema and cross-platform workflow. No staging helper survives.
- Technical exact-source gates: R0 Repository Guard #2005 / `33260302790` SUCCESS Ubuntu + Windows; Python Core #1980 / `33260302771` SUCCESS 5/5; KodeStudio UI Smoke #1945 / `33260302782` SUCCESS; R14 CLI KodeStudio LiveOps UX Acceptance #2 / `33260302752` SUCCESS Ubuntu 24.04 + Windows 2025.
- Full Ubuntu Python Core: **1752 passed / 14 skipped / 46 warnings**, with R7/R8/R9 integrated acceptance PASS. Dedicated focused R14.16 regression: **26 passed Ubuntu**, with the same focused test step SUCCESS on Windows.
- All **31/31 deterministic acceptance checks PASS**: typed 15-operation catalog/defaults; confirmation-vs-authorization separation; separate production authority; governed mutation path; redaction; raw command/endpoint/token/resource escape rejection; local/test stack restriction; truthful unavailable provider/load/backup claims; stable JSON; EN/FR/qps-ploc localization; structured KodeStudio controls and wiring.
- Evidence flags: `manual_state=none`, `provider_live_claim=false`, `external_provider_required=false`, `secrets_exposed=false`, `raw_command_input_exposed=false`, `raw_endpoint_input_exposed=false`, `automatic_production_publish=false`, `operation_count=15`, `check_count=31`, `passed_count=31`.
- Evidence digests: catalog `f0ac90c20d06d7e6ffdff22756bf65499c5e9d839098fb51ec8a7f1738dc351b`; preview `ff1089d254637027bd959a669cae6b3cc6f82252c2c1883cb24c1878fe418719`; authorized mutation `c809c93458f425b48a7546afc78bd21dff3b412a6a17c3ba203d1c615cdc8c13`.
- Cross-platform decoded evidence JSON is exactly equal: 2245 bytes and SHA-256 `396588f20a03bb555c1a69cfd9b076151e850d11c8842b9ef9a94708a6a7eea2` on both OS. Artifacts: Ubuntu `9717060425` / `sha256:2e53b8fab1bfb5acd0e8197ee79e8475b975e3aecc017c264347bd00c73a607a`; Windows `9717061707` / `sha256:39308eb7833026dc06184ec5e753fe229279898f95693fd55181ee78f1ef6907`.
- Rejected source `1707ca57a325a3187bfbe5327002bc2f30dc34d7` exposed stale R6.6 nav-count plus missing R14 pseudo-locale coverage; rejected source `c6a62355bf58a49c0bc4fc41a0ef29e6d0168825` exposed a missing Ubuntu Qt runtime dependency (`libEGL.so.1`) before business assertions. Neither candidate nor its failed evidence is reused.
- Security boundary: UI/CLI confirmation is intention only, never permission; mutation requires injected domain authority and production requires separate production authority. Project fallback never authorizes mutation. Raw shell/command/endpoint/secret/token/password/DSN/private-key input and automatic production publish remain forbidden.
- Manual intervention: **NONE**. No external provider account, credential, quota, public domain/TLS state, production deployment, destructive load or production PITR proof is required or claimed.
- Technical state is accepted and R14.16 is ready for END-sync re-gating. R14.17 remains PLANNED and unauthorized until the exact END-head passes fresh R0/Python/UI/R14.16 acceptance, the implementation PR merges with expected-head protection, and exactly one continuity-only post-merge normalization passes fresh R0/Python/UI and merges.

---

"""
section = section.replace(old_completion, completion)
plan = plan[:section_start] + section + plan[section_end:]
PLAN.write_text(plan, encoding="utf-8", newline="\n")

continuity = CONTINUITY.read_text(encoding="utf-8")
lines = continuity.splitlines()
if not lines or "R14.16 IN_PROGRESS" not in lines[0]:
    raise SystemExit("unexpected continuity authority line")
lines[0] = (
    "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. "
    "R14.1–R14.15 COMPLETE + NORMALIZED. R14.16 COMPLETE on `r14/16-cli-kodestudio-liveops-ux` with immutable technical source "
    "`3c0507ed497d9607218b9d9a50c2e5729d786c87`; END-sync re-gating/merge/normalization pending; R14.17 remains PLANNED and unauthorized.** "
    "R14.16 technical gates: R0 #2005 / `33260302790`, Python Core #1980 / `33260302771`, UI #1945 / `33260302782`, "
    "R14.16 Acceptance #2 / `33260302752` all SUCCESS; 31/31 deterministic checks PASS cross-platform; manual state NONE. "
    "Only a fresh exact-END gate set, expected-head implementation merge and the unique continuity-only post-merge normalization may authorize R14.17."
)
continuity = "\n".join(lines) + "\n"
old_global = "- R14.16 : **IN_PROGRESS** — branch `r14/16-cli-kodestudio-liveops-ux`; effective base `8a7eb312d3fa0d642d6b2b77ef35c2b2d3e7de36`; normalized R14.15 anchor `1f10d7a13f49cb6e931e5e0694f083228ed24070`; manual **NONE**."
new_global = "- R14.16 : **COMPLETE (technical + END-sync; merge/normalization pending)** — immutable source `3c0507ed497d9607218b9d9a50c2e5729d786c87`; branch `r14/16-cli-kodestudio-liveops-ux`; effective base `8a7eb312d3fa0d642d6b2b77ef35c2b2d3e7de36`; manual **NONE**."
if continuity.count(old_global) != 1:
    raise SystemExit(f"global R14.16 marker count={continuity.count(old_global)}")
continuity = continuity.replace(old_global, new_global)
old_index = "| R14.16 | IN_PROGRESS | NONE |"
new_index = "| R14.16 | COMPLETE (merge/normalization pending) | NONE |"
if continuity.count(old_index) != 1:
    raise SystemExit(f"index R14.16 marker count={continuity.count(old_index)}")
continuity = continuity.replace(old_index, new_index)
old_next = """## Next authorized action

Implement R14.16 only on `r14/16-cli-kodestudio-liveops-ux` after this START-sync, preserving the frozen scope above. Freeze an immutable technical source before decision evidence, run focused/adversarial tests plus fresh exact-head gates, and do not authorize R14.17 until R14.16 implementation/END-sync/merge and its unique continuity-only normalization are complete.
"""
new_next = """## R14.16 technical closure authority

- Clean START-head: `3b0ad3bf666f1e6247699b8ef611b436f836b60a`; immutable technical source: `3c0507ed497d9607218b9d9a50c2e5729d786c87`.
- START→source changed exactly 13 intended technical/test/evidence files; no staging helper survives the accepted source.
- Exact technical-source gates: R0 Repository Guard #2005 / `33260302790` SUCCESS Ubuntu + Windows; Python Core #1980 / `33260302771` SUCCESS 5/5; KodeStudio UI Smoke #1945 / `33260302782` SUCCESS; R14 CLI KodeStudio LiveOps UX Acceptance #2 / `33260302752` SUCCESS Ubuntu 24.04 + Windows 2025.
- Full Ubuntu Python Core: **1752 passed / 14 skipped / 46 warnings**; R7/R8/R9 integrated acceptance PASS. Dedicated focused acceptance: **26 passed Ubuntu**, with Windows focused step SUCCESS.
- Dedicated evidence: **31/31 checks PASS** with 15 governed operations. Decoded Ubuntu/Windows JSON objects are exactly equal, 2245 bytes, SHA-256 `396588f20a03bb555c1a69cfd9b076151e850d11c8842b9ef9a94708a6a7eea2`.
- Evidence digests: catalog `f0ac90c20d06d7e6ffdff22756bf65499c5e9d839098fb51ec8a7f1738dc351b`; preview `ff1089d254637027bd959a669cae6b3cc6f82252c2c1883cb24c1878fe418719`; authorized mutation `c809c93458f425b48a7546afc78bd21dff3b412a6a17c3ba203d1c615cdc8c13`.
- Artifacts: Ubuntu `9717060425` / `sha256:2e53b8fab1bfb5acd0e8197ee79e8475b975e3aecc017c264347bd00c73a607a`; Windows `9717061707` / `sha256:39308eb7833026dc06184ec5e753fe229279898f95693fd55181ee78f1ef6907`.
- `manual_state=none`; `provider_live_claim=false`; `external_provider_required=false`; `secrets_exposed=false`; raw command/endpoint exposure false; automatic production publish false.
- Confirmation is never authorization; mutations require domain authority, production requires separate production authority, and project fallback never self-authorizes mutation. No external provider account/credential/production endpoint is required or claimed.
- Rejected candidates `1707ca57a325a3187bfbe5327002bc2f30dc34d7` and `c6a62355bf58a49c0bc4fc41a0ef29e6d0168825` are NON-AUTHORITATIVE; none of their failed evidence is reused.

## Next authorized action

Run fresh exact-END R0 Repository Guard, full Python Core, KodeStudio UI Smoke and R14 CLI KodeStudio LiveOps UX Acceptance on the clean documentation-only END-head. If and only if all are green, open/merge the R14.16 implementation PR with `expected_head_sha` equal to that exact END-head, then perform exactly one continuity-only post-merge normalization with fresh R0/Python/UI. **R14.17 remains unauthorized until that normalization merges.**
"""
if continuity.count(old_next) != 1:
    raise SystemExit(f"next-action marker count={continuity.count(old_next)}")
continuity = continuity.replace(old_next, new_next)
CONTINUITY.write_text(continuity, encoding="utf-8", newline="\n")
