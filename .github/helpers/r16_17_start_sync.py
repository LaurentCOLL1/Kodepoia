from pathlib import Path

BASE_SHA = "68cc2bb761329b3f1b4932319302db3dcc01cd2b"
BRANCH = "r16/17-v1-packaging-migration-rollback-release-readiness"

plan_path = Path("docs/roadmap/R16_PLAN.md")
continuity_path = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
plan = plan_path.read_text(encoding="utf-8")
continuity = continuity_path.read_text(encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


old_checkpoint = "**Execution checkpoint:** R1–R15 are COMPLETE + NORMALIZED. R16 planning is ACCEPTED + NORMALIZED. R16.1–R16.15 are COMPLETE + NORMALIZED. R16.16 is COMPLETE at END-sync on dedicated branch `r16/16-resource-concurrency-leak-diagnostics-soak` from exact normalized `main` `d19a8b1fa32fa5e28fa23b036407bc5bd902ef92`, with clean START `ff971a012a0066b995d52deb1e4e8b0ac0a413de` and immutable technical source `fb34d4a92131fa5cc51e3211405ac38908246d6c`; R16.17–R16.18 remain PLANNED and unauthorized. Fresh exact-technical-head gates are SUCCESS: R16.16 #6 / `33777526743` Ubuntu + Windows, R16.9 #58 / `33777526756` Ubuntu + Windows, R0 #2380 / `33777526844` Ubuntu + Windows, Python Core #2352 / `33777526769` 5/5 and KodeStudio UI Smoke #2317 / `33777526726`. R16.16 manual state is NONE. Fresh exact-END R16.16/R16.9/R0/Python/UI re-gates, PR #365 exact-head merge and exactly one continuity-only post-merge normalization remain mandatory before R16.17 START."
new_checkpoint = "**Execution checkpoint:** R1–R15 are COMPLETE + NORMALIZED. R16 planning is ACCEPTED + NORMALIZED. R16.1–R16.16 are COMPLETE + NORMALIZED. R16.17 is IN_PROGRESS on dedicated branch `r16/17-v1-packaging-migration-rollback-release-readiness` created directly from exact normalized R16.16 `main` `68cc2bb761329b3f1b4932319302db3dcc01cd2b`; R16.18 remains PLANNED and unauthorized. R16.16 final exact-END `96a1068b678d33778893fc23e096decd3e41e04b` passed R16.16 #9 / `33779722512`, R16.9 #60 / `33779722137`, R0 #2382 / `33779722619`, Python Core #2354 / `33779722505` 5/5 and UI #2319 / `33779722529`; PR #365 merged exact head as implementation/evidence `068f522b052b820c40474ab8a3c689ac47610761`; unique normalization candidate `b260f4c12ae7a9aa84a6fd56a06008e35964abb3` then passed R0 #2384 / `33782242108` Ubuntu + Windows, Python Core #2356 / `33782241929` 5/5 and UI #2321 / `33782241719`, and PR #366 merged exact head as normalized `main` `68cc2bb761329b3f1b4932319302db3dcc01cd2b`. R16.17 core acceptance requires no manual action; production signing, store/public registry publication or provider/domain cutover remain CONDITIONAL / NOT TRIGGERED. No R16.17 implementation bytes precede its START-sync."
plan = replace_once(plan, old_checkpoint, new_checkpoint, "plan checkpoint")

manual_anchor = "**CONDITIONAL.** Required only if production signing, store submission, public registry publication or provider/domain cutover is explicitly requested. Core RC acceptance does not require these actions.\n\n---\n\n# R16.18 — Integrated adversarial + real-project RC acceptance"
start_section = """**CONDITIONAL.** Required only if production signing, store submission, public registry publication or provider/domain cutover is explicitly requested. Core RC acceptance does not require these actions.

## R16.17 START authority

- State: **IN_PROGRESS**; core manual state **CONDITIONAL / NOT TRIGGERED**. R16.18 remains **PLANNED** and unauthorized.
- Exact normalized R16.16 base: `main` `68cc2bb761329b3f1b4932319302db3dcc01cd2b`; dedicated branch `r16/17-v1-packaging-migration-rollback-release-readiness` created directly from that SHA before implementation.
- R16.16 final exact-END `96a1068b678d33778893fc23e096decd3e41e04b` passed R16.16 #9 / `33779722512` Ubuntu + Windows, R16.9 #60 / `33779722137` Ubuntu + Windows, R0 #2382 / `33779722619` Ubuntu + Windows, Python Core #2354 / `33779722505` 5/5 and KodeStudio UI Smoke #2319 / `33779722529`; PR #365 merged with exact expected head as implementation/evidence `main` `068f522b052b820c40474ab8a3c689ac47610761`.
- The unique R16.16 post-merge continuity-only normalization candidate `b260f4c12ae7a9aa84a6fd56a06008e35964abb3` changed only `docs/continuity/KODEPOIA_CONTINUITY.md`, passed fresh R0 #2384 / `33782242108` Ubuntu + Windows, Python Core #2356 / `33782241929` 5/5 and KodeStudio UI Smoke #2321 / `33782241719`, then PR #366 merged with exact expected head as normalized `main` `68cc2bb761329b3f1b4932319302db3dcc01cd2b`. No second R16.16 normalization is authorized.
- Prior state: R16.1–R16.16 **COMPLETE + NORMALIZED**; R16.18 remains **PLANNED** and unauthorized.
- Frozen R16.17 scope: v1.0 RC identity/versioning; deterministic supported package/build artifacts; exact-source manifest/provenance/checksums; dependency/BOM/license evidence; hosted install/extract/consume checks; declared prior-fixture upgrade/migration; rollback/recovery on failure; secure defaults, known limitations and security/privacy/incident/recovery guidance.
- Production signing, store/public registry publication, production credentials and provider/domain cutover remain optional conditional actions and are not inferred from core CI. If explicitly requested, manual intervention becomes required and execution must stop before claiming completion until exact evidence is supplied.
- Core acceptance remains bounded, deterministic, source-bound, non-destructive and free of live production credentials. No public release occurs automatically.
- No R16.17 implementation bytes precede this START-sync.

---

# R16.18 — Integrated adversarial + real-project RC acceptance"""
plan = replace_once(plan, manual_anchor, start_section, "R16.17 START insertion")

old_header = "> Kodepoia, architecture v1.0 gelée. **R1–R15 COMPLETE + NORMALIZED. R16 planning ACCEPTED + NORMALIZED. R16.1–R16.15 COMPLETE + NORMALIZED. R16.16 implementation/evidence is merged and its unique post-merge continuity-only normalization is the only remaining R16.16 action. R16.17–R16.18 remain PLANNED and unauthorized.** Final exact-END `96a1068b678d33778893fc23e096decd3e41e04b` passed R16.16 #9 / `33779722512` Ubuntu + Windows, R16.9 #60 / `33779722137` Ubuntu + Windows, R0 #2382 / `33779722619` Ubuntu + Windows, Python Core #2354 / `33779722505` 5/5 and KodeStudio UI Smoke #2319 / `33779722529`, then PR #365 merged with exact expected head as implementation/evidence `main` `068f522b052b820c40474ab8a3c689ac47610761`. Acceptance remains 36/36 focused + supply-chain tests and 18/18 representative cases per OS, with zero post-cancel mutation/orphan process and truthful sub-50 ms CPU repeatability plus hosted VRAM `INCONCLUSIVE` boundaries. Manual NONE. This single continuity-only normalization must pass fresh R0/Python/UI and merge before R16.17 START is authorized."
new_header = "> Kodepoia, architecture v1.0 gelée. **R1–R15 COMPLETE + NORMALIZED. R16 planning ACCEPTED + NORMALIZED. R16.1–R16.16 COMPLETE + NORMALIZED. R16.17 IN_PROGRESS. R16.18 remains PLANNED and unauthorized.** R16.16 final exact-END `96a1068b678d33778893fc23e096decd3e41e04b` passed all five required authorities, PR #365 merged exact head as implementation/evidence `068f522b052b820c40474ab8a3c689ac47610761`, and unique normalization candidate `b260f4c12ae7a9aa84a6fd56a06008e35964abb3` passed fresh R0 #2384 / `33782242108` Ubuntu + Windows, Python Core #2356 / `33782241929` 5/5 and UI #2321 / `33782241719` before PR #366 merged exact head as normalized `main` `68cc2bb761329b3f1b4932319302db3dcc01cd2b`. R16.17 branch `r16/17-v1-packaging-migration-rollback-release-readiness` is created directly from that normalized main and START-synchronized before implementation. Core manual state is CONDITIONAL / NOT TRIGGERED; production signing/publication/provider cutover remain optional and unclaimed."
continuity = replace_once(continuity, old_header, new_header, "continuity header")

r1616_prefix = "- R16.16 : **COMPLETE + NORMALIZED** —"
lines = continuity.splitlines(keepends=True)
hits = [i for i, line in enumerate(lines) if line.startswith(r1616_prefix)]
if len(hits) != 1:
    raise SystemExit(f"continuity global R16.16 entry: expected one, found {len(hits)}")
i = hits[0]
if i + 1 < len(lines) and lines[i + 1].startswith("- R16.17 :"):
    raise SystemExit("R16.17 global entry already exists")
new_global = (
    "- R16.17 : **IN_PROGRESS** — exact normalized R16.16 base `main` `68cc2bb761329b3f1b4932319302db3dcc01cd2b`; dedicated branch `r16/17-v1-packaging-migration-rollback-release-readiness` created directly from that SHA before implementation. Frozen scope is v1.0 RC packaging/build identity, source-bound manifest/provenance/checksums, dependency/BOM/license evidence, supported install/extract/consume checks, declared prior-fixture migration/upgrade and rollback/recovery, release/security/privacy/operations documentation, with production signing/store or public-registry publication/provider-domain cutover remaining CONDITIONAL / NOT TRIGGERED. No public release occurs automatically; no R16.17 implementation bytes precede START-sync.\n"
)
lines.insert(i + 1, new_global)
continuity = "".join(lines)

marker = "\n## R16 status index\n"
if continuity.count(marker) != 1:
    raise SystemExit(f"R16 status marker: expected one, found {continuity.count(marker)}")
if "## R16.17 START authority" in continuity:
    raise SystemExit("R16.17 continuity START authority already exists")
continuity_start = """

## R16.17 START authority

- Exact normalized R16.16 base: `main` `68cc2bb761329b3f1b4932319302db3dcc01cd2b`; R16.16 is **COMPLETE + NORMALIZED** and no second R16.16 normalization is authorized.
- Dedicated branch `r16/17-v1-packaging-migration-rollback-release-readiness` is created directly from that exact normalized SHA before implementation; this START-sync changes documentation only.
- R16.16 normalization candidate `b260f4c12ae7a9aa84a6fd56a06008e35964abb3` passed fresh R0 #2384 / `33782242108` Ubuntu + Windows, Python Core #2356 / `33782241929` 5/5 and KodeStudio UI Smoke #2321 / `33782241719`, then PR #366 merged with exact expected head as normalized `main` `68cc2bb761329b3f1b4932319302db3dcc01cd2b`.
- R16.17 state is **IN_PROGRESS**. R16.18 remains **PLANNED** and unauthorized.
- Frozen R16.17 scope: RC version/build identity; deterministic supported package/build artifacts; exact-source manifest/provenance/checksums; dependency/BOM/license evidence; hosted install/extract/consume checks; declared prior-fixture migration/upgrade plus rollback/recovery; secure defaults, known limitations, security/privacy documentation and incident/recovery guidance.
- Core manual state is **CONDITIONAL / NOT TRIGGERED**: production signing, store/public registry publication, production credentials and provider/domain cutover are optional and not part of core RC acceptance unless explicitly requested. If triggered, stop before completion and record exact manual evidence requirements.
- No R16.17 implementation bytes precede this START-sync; no public release occurs automatically.
"""
continuity = continuity.replace(marker, continuity_start + marker, 1)

continuity = replace_once(
    continuity,
    "| R16.17 | PLANNED | CONDITIONAL |",
    "| R16.17 | IN_PROGRESS | CONDITIONAL / NOT TRIGGERED |",
    "R16.17 status row",
)

old_next = "R16.16 implementation/evidence is merged as `main` `068f522b052b820c40474ab8a3c689ac47610761` after final exact-END `96a1068b678d33778893fc23e096decd3e41e04b` passed all five required authorities. This file is the single authorized post-merge continuity-only normalization candidate. The next authorized action is fresh R0 Repository Guard Ubuntu + Windows, Python Core 5/5 and KodeStudio UI Smoke on this one exact normalization head, followed only on full SUCCESS by exact-head merge of its normalization PR. R16.17 remains unauthorized until that normalized `main` exists; once it exists, only R16.17 START-sync is authorized before any R16.17 implementation. Manual intervention remains NONE."
new_next = "R16.16 is **COMPLETE + NORMALIZED** on `main` `68cc2bb761329b3f1b4932319302db3dcc01cd2b`. R16.17 is now START-synchronized and **IN_PROGRESS** on dedicated branch `r16/17-v1-packaging-migration-rollback-release-readiness` created directly from that normalized main. The next authorized action is R16.17 implementation strictly within the frozen RC packaging/migration/rollback/release-readiness scope, followed by exact-head technical gates and END-sync under the permanent rule. R16.18 remains unauthorized. Core manual state is CONDITIONAL / NOT TRIGGERED; if production signing, public/store publication, production credentials or provider/domain cutover is explicitly requested, stop and require the corresponding manual evidence before continuing toward completion."
continuity = replace_once(continuity, old_next, new_next, "next authorized action")

if "| R16.18 | PLANNED | CONDITIONAL |" not in continuity:
    raise SystemExit("R16.18 PLANNED invariant missing")
if "| R16.18 | IN_PROGRESS" in continuity:
    raise SystemExit("R16.18 incorrectly started")
if "R16.17 is IN_PROGRESS" not in plan and "R16.17 is **IN_PROGRESS**" not in plan:
    raise SystemExit("plan R16.17 IN_PROGRESS invariant missing")

plan_path.write_text(plan, encoding="utf-8")
continuity_path.write_text(continuity, encoding="utf-8")
