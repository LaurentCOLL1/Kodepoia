from pathlib import Path

PLAN = Path("docs/roadmap/R15_PLAN.md")
CONTINUITY = Path("docs/continuity/KODEPOIA_CONTINUITY.md")

plan = PLAN.read_text(encoding="utf-8")
continuity = CONTINUITY.read_text(encoding="utf-8")

plan_replacements = {
    "**Execution checkpoint:** R1–R14 are COMPLETE + NORMALIZED; R15 planning is ACCEPTED + NORMALIZED. R15.1–R15.3 are COMPLETE + NORMALIZED. R15.4 is COMPLETE with immutable technical source `b82c7595f69f94e173a6e7893073585c9f8c1aae`; implementation merge + unique post-merge continuity-only normalization are pending. R15.5–R15.17 remain PLANNED.":
        "**Execution checkpoint:** R1–R14 are COMPLETE + NORMALIZED; R15 planning is ACCEPTED + NORMALIZED. R15.1–R15.4 are COMPLETE + NORMALIZED. R15.5 is IN_PROGRESS from normalized R15.4 `main` `8744df5f3a408595693c67819a29f95b3a82f1d7` on dedicated branch `r15/05-immutable-dataset-builder`; R15.6–R15.17 remain PLANNED.",
    "| R15.5 | Immutable dataset builder, group-safe deterministic splits, manifests + dataset cards | PLANNED | NONE | R15.1–R15.4 |":
        "| R15.5 | Immutable dataset builder, group-safe deterministic splits, manifests + dataset cards | IN_PROGRESS | NONE | R15.1–R15.4 |",
    "**COMPLETE — implementation merge pending.**": "**COMPLETE.**",
    "- final clean END-head and its fresh exact-head gates remain mandatory before PR merge.":
        "- final END-head: `e91a2f18ef79f66672e42bdf04ad4d731ec7bf8d`; exact-END R15.4 #16 / `33284334173`, R0 #2097 / `33284334475`, Python Core #2072 / `33284334142`, and KodeStudio UI Smoke #2037 / `33284334250` all SUCCESS;\n- PR #302 merged with `expected_head_sha=e91a2f18ef79f66672e42bdf04ad4d731ec7bf8d` as `195920e06fb6487fe58be4247ba9b90a75b96dad`;\n- unique continuity-only normalization head `8aee5b6f69c61c513e0c3dcd56cba1035c365d18` passed R0 #2099 / `33287315588`, Python Core #2074 / `33287315591`, and UI #2039 / `33287315606`; normalization PR #303 merged with exact expected head as normalized `main` `8744df5f3a408595693c67819a29f95b3a82f1d7`."
}

for old, new in plan_replacements.items():
    count = plan.count(old)
    if count != 1:
        raise SystemExit(f"plan replacement count={count}: {old[:100]!r}")
    plan = plan.replace(old, new, 1)

continuity_replacements = {
    "> Kodepoia, architecture v1.0 gelée. **R1–R14 COMPLETE + NORMALIZED. R15 planning ACCEPTED + NORMALIZED. R15.1–R15.4 COMPLETE + NORMALIZED; R15.5–R15.17 PLANNED.** R15.4 immutable technical source `b82c7595f69f94e173a6e7893073585c9f8c1aae`; final END-head `e91a2f18ef79f66672e42bdf04ad4d731ec7bf8d`; exact-END R15.4 #16 / `33284334173`, R0 #2097 / `33284334475`, Python #2072 / `33284334142`, UI #2037 / `33284334250` SUCCESS; PR #302 merged with `expected_head_sha=e91a2f18ef79f66672e42bdf04ad4d731ec7bf8d` as `195920e06fb6487fe58be4247ba9b90a75b96dad`; manual NONE. This record is the unique post-merge continuity-only R15.4 normalization authority; only its merged normalized `main` authorizes R15.5 START-sync.":
        "> Kodepoia, architecture v1.0 gelée. **R1–R14 COMPLETE + NORMALIZED. R15 planning ACCEPTED + NORMALIZED. R15.1–R15.4 COMPLETE + NORMALIZED; R15.5 IN_PROGRESS; R15.6–R15.17 PLANNED.** R15.5 exact branch point is normalized R15.4 `main` `8744df5f3a408595693c67819a29f95b3a82f1d7`; dedicated branch `r15/05-immutable-dataset-builder`; manual NONE. Dataset construction remains fail-closed: only curated, fully authorized, sanitized, uncontaminated records may enter; R15.4 duplicate groups must remain split-atomic and protected holdouts remain forbidden.",
    "| R15.5 | PLANNED | NONE |": "| R15.5 | IN_PROGRESS | NONE |",
    "**R15.4 implementation is merged as `195920e06fb6487fe58be4247ba9b90a75b96dad`. This branch is the unique continuity-only post-merge normalization: require fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke, then merge only with `expected_head_sha`. Only the resulting normalized `main` authorizes R15.5 START-sync; `docs/roadmap/R15_PLAN.md` must not change.**":
        "**R15.5 START-sync is the active authority on `r15/05-immutable-dataset-builder`, based exactly on normalized R15.4 `main` `8744df5f3a408595693c67819a29f95b3a82f1d7`. Complete START synchronization and repository validation before implementation; then implement the immutable dataset builder, deterministic group-safe splits, manifests/cards/exporters and focused adversarial acceptance. R15.6 remains unauthorized until R15.5 completes, merges, and receives its unique post-merge normalization.**"
}

for old, new in continuity_replacements.items():
    count = continuity.count(old)
    if count != 1:
        raise SystemExit(f"continuity replacement count={count}: {old[:100]!r}")
    continuity = continuity.replace(old, new, 1)

r15_4_anchor = "- R15.4 : **COMPLETE + NORMALIZED**"
idx = continuity.find(r15_4_anchor)
if idx < 0:
    raise SystemExit("R15.4 continuity anchor missing")
line_end = continuity.find("\n", idx)
if line_end < 0:
    raise SystemExit("R15.4 continuity line end missing")
new_line = (
    "- R15.5 : **IN_PROGRESS** — exact branch point normalized R15.4 `main` "
    "`8744df5f3a408595693c67819a29f95b3a82f1d7`; branch `r15/05-immutable-dataset-builder`; "
    "START-sync only, no R15.5 implementation precedes this state; manual NONE.\n"
)
if "- R15.5 : **IN_PROGRESS**" in continuity:
    raise SystemExit("R15.5 IN_PROGRESS continuity line already present")
continuity = continuity[: line_end + 1] + new_line + continuity[line_end + 1 :]

PLAN.write_text(plan, encoding="utf-8", newline="\n")
CONTINUITY.write_text(continuity, encoding="utf-8", newline="\n")
