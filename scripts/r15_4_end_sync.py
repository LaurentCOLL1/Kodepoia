from pathlib import Path

base = "ffb5a830cce35334b3f62e69fae2e2c02c717080"
start = "68a6d1a5d35430128db8fa450bd9afa4e0c7c36e"
technical = "b82c7595f69f94e173a6e7893073585c9f8c1aae"
focused_run = "33284070954"
r0_run = "33284070915"
python_run = "33284070930"
ui_run = "33284070882"

Path("docs/roadmap/R15_4_DESIGN.md").write_text(
    f"""# R15.4 — Exact/near deduplication, contamination firewall and quarantine

**Status:** TECHNICAL SOURCE ACCEPTED / EXACT END-HEAD RE-GATES PENDING  
**Normalized base:** `{base}`  
**Clean START:** `{start}`  
**Immutable technical source:** `{technical}`  
**Manual state:** NONE

## Design

R15.4 adds a deterministic, local, dependency-light duplicate/contamination authority after R15.3 sanitization. The source sanitized payload remains unchanged; comparison normalization and fingerprints are derived metadata only.

`DedupPolicy` versions normalization, shingle size and near-match threshold and exposes a canonical SHA-256 policy digest. Comparison fingerprints bind exact normalized-content SHA-256, sorted SHA-256 shingle identities, token count and policy digest. Exact and near matches are clustered deterministically with stable group IDs independent of input row order.

Near comparison uses repository-owned token shingles and Jaccard similarity. The threshold is inclusive and policy-bound. A policy change produces a different policy/group identity and therefore cannot silently reuse old derived decisions.

Protected benchmark holdouts live in a separate registry whose safe manifest contains only stable IDs and fingerprint metadata. `scan_contamination` compares candidate fingerprints to registered holdouts; exact and threshold-reaching near matches contaminate the duplicate group, and every member of that group is quarantined for downstream dataset building. Near matches remain review-signaled while still failing closed.

## Security and reproducibility invariants

- benchmark raw content is absent from safe registry/report serialization;
- a contaminated member quarantines its complete duplicate group;
- dedup groups are deterministic across row order and platform;
- fingerprints created under different policy digests cannot be compared or reused;
- split-group identity is established before R15.5 so duplicate variants cannot cross train/validation/test;
- source sanitized content is never rewritten by comparison normalization;
- empty/invalid policy or duplicate/conflicting identities fail closed;
- no external dataset, network service, GPU or manual intervention is required for R15.4 acceptance.

## Technical evidence

- focused R15.4 #7 / `{focused_run}`: SUCCESS Ubuntu + Windows, 68 cumulative R15.1–R15.4 tests per OS + Ruff + compile;
- R0 #2092 / `{r0_run}`: SUCCESS Ubuntu + Windows;
- Python Core #2067 / `{python_run}`: SUCCESS 5/5;
- KodeStudio UI Smoke #2032 / `{ui_run}`: SUCCESS.

Fresh exact END-head gates remain mandatory before merge.
""",
    encoding="utf-8",
    newline="\n",
)

Path("docs/roadmap/R15_4_ACCEPTANCE.md").write_text(
    f"""# R15.4 — Acceptance record

**Acceptance state:** TECHNICAL SOURCE ACCEPTED / EXACT END-HEAD RE-GATES PENDING  
**Technical source:** `{technical}`  
**Manual:** NONE

## Exact technical evidence

- R15.4 Dedup Contamination Acceptance #7 / `{focused_run}`: SUCCESS Ubuntu + Windows; 68 cumulative experience tests per OS, Ruff and compile.
- R0 Repository Guard #2092 / `{r0_run}`: SUCCESS Ubuntu + Windows.
- Python Core #2067 / `{python_run}`: SUCCESS 5/5.
- KodeStudio UI Smoke #2032 / `{ui_run}`: SUCCESS.

## Adversarial coverage

Acceptance proves platform-stable comparison normalization; deterministic policy digests; invalid-policy rejection; row-order-independent exact clustering; inclusive near-threshold behavior and below-threshold separation; transitive cluster grouping; deterministic representatives; duplicate-ID and cross-policy rejection; exact holdout quarantine of the entire duplicate group; near-holdout fail-closed quarantine with review flag; safe below-threshold behavior; zero raw protected/candidate content in safe reports/manifests; idempotent holdout registration with conflicting identity rejection; registry policy binding; JSON-schema validation; group-ID policy sensitivity; and consistent-policy enforcement during contamination scans.

The technical source is frozen. This END state must receive fresh exact-head R15.4/R0/Python/UI gates before merge; technical-source evidence is not reused as END-head evidence.
""",
    encoding="utf-8",
    newline="\n",
)

plan = Path("docs/roadmap/R15_PLAN.md")
text = plan.read_text(encoding="utf-8")
old_checkpoint = (
    "**Execution checkpoint:** R1–R14 are COMPLETE + NORMALIZED; R15 planning is ACCEPTED + NORMALIZED. "
    f"R15.1–R15.3 are COMPLETE + NORMALIZED; normalized R15.3 `main` is `{base}`. "
    "R15.4 is IN_PROGRESS on dedicated branch `r15/04-dedup-contamination`; R15.5–R15.17 remain PLANNED."
)
new_checkpoint = (
    "**Execution checkpoint:** R1–R14 are COMPLETE + NORMALIZED; R15 planning is ACCEPTED + NORMALIZED. "
    f"R15.1–R15.3 are COMPLETE + NORMALIZED. R15.4 is COMPLETE with immutable technical source `{technical}`; "
    "implementation merge + unique post-merge continuity-only normalization are pending. R15.5–R15.17 remain PLANNED."
)
assert text.count(old_checkpoint) == 1
text = text.replace(old_checkpoint, new_checkpoint, 1)
old_row = "| R15.4 | Exact/near deduplication, benchmark-contamination firewall + quarantine | IN_PROGRESS | NONE | R15.1–R15.3 |"
assert text.count(old_row) == 1
text = text.replace(old_row, old_row.replace(" | IN_PROGRESS | ", " | COMPLETE | "), 1)
start_marker = "# R15.4 — Exact/near deduplication, benchmark-contamination firewall + quarantine"
end_marker = "# R15.5 — Immutable dataset builder, group-safe deterministic splits, manifests + dataset cards"
start_pos = text.index(start_marker)
end_pos = text.index(end_marker, start_pos)
section = text[start_pos:end_pos]
old_completion = "## Completion record\n\nTo be appended when accepted."
assert section.count(old_completion) == 1
section = section.replace(
    old_completion,
    f"""## Completion record

**COMPLETE — implementation merge pending.**

- clean START-head: `{start}`;
- immutable technical source: `{technical}`;
- technical R15.4 #7 / `{focused_run}`: SUCCESS Ubuntu + Windows, 68 cumulative tests per OS + Ruff + compile;
- R0 #2092 / `{r0_run}`: SUCCESS Ubuntu + Windows;
- Python Core #2067 / `{python_run}`: SUCCESS 5/5;
- KodeStudio UI Smoke #2032 / `{ui_run}`: SUCCESS;
- manual state: `NONE`;
- final clean END-head and its fresh exact-head gates remain mandatory before PR merge.
""",
    1,
)
text = text[:start_pos] + section + text[end_pos:]
plan.write_text(text, encoding="utf-8", newline="\n")

continuity = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
lines = continuity.read_text(encoding="utf-8").splitlines()
lines[0] = (
    "> Kodepoia, architecture v1.0 gelée. **R1–R14 COMPLETE + NORMALIZED. R15 planning ACCEPTED + NORMALIZED. "
    "R15.1–R15.3 COMPLETE + NORMALIZED; R15.4 COMPLETE — implementation merge pending; R15.5–R15.17 PLANNED.** "
    f"R15.4 immutable technical source `{technical}` from clean START `{start}`; technical R15.4 #7 / `{focused_run}`, "
    f"R0 #2092 / `{r0_run}`, Python #2067 / `{python_run}`, UI #2032 / `{ui_run}` all SUCCESS; manual NONE. "
    "Fresh exact END-head R15.4/R0/Python/UI gates remain mandatory before merge."
)
idx = next(i for i, line in enumerate(lines) if line.startswith("- R15.4 : **IN_PROGRESS**"))
lines[idx] = (
    f"- R15.4 : **COMPLETE — IMPLEMENTATION MERGE PENDING** — clean START `{start}` from normalized R15.3 `main` `{base}`; "
    f"immutable technical source `{technical}`; technical R15.4 #7 / `{focused_run}` SUCCESS Ubuntu + Windows with 68 cumulative tests per OS + Ruff + compile, "
    f"R0 #2092 / `{r0_run}` SUCCESS, Python #2067 / `{python_run}` SUCCESS 5/5, UI #2032 / `{ui_run}` SUCCESS; manual NONE. "
    "Exact/near groups and protected-holdout quarantine are policy-digest-bound and fail closed; raw holdout content is absent from safe reports. "
    "Final clean END-head must receive fresh R15.4/R0/Python/UI before merge; R15.5 remains unauthorized until unique post-merge normalization."
)
status = next(i for i, line in enumerate(lines) if line == "| R15.4 | IN_PROGRESS | NONE |")
lines[status] = "| R15.4 | COMPLETE | NONE |"
action = next(i for i, line in enumerate(lines) if "R15.4 START-sync is active" in line)
lines[action] = (
    "**R15.4 END-sync is complete on `r15/04-dedup-contamination`. Produce one clean END-head with no helper/marker, "
    "require fresh exact-head R15.4 focused + R0 Repository Guard + full Python Core + KodeStudio UI Smoke, then merge only with `expected_head_sha`. "
    "After that merge, perform exactly one continuity-only post-merge normalization with fresh R0/Python/UI. R15.5 remains unauthorized until that normalized `main` exists.**"
)
continuity.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
