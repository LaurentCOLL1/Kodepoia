# Kodepoia next actions

Last synchronized: 2026-09-13 22:59 CEST  
Companion state: `docs/continuity/STATE.md`  
Baseline to re-check before any mutation: `main` = `f8e7857da0605f76ae7009181a7e4b9839e9ae41`

## Goal

Resume with the accepted **updater-only** correction exposed by the real Windows `rc5 -> rc6` validation, qualify that correction without weakening trust, then use a subsequent validation candidate for a fresh end-to-end installed-updater transition.

No unrelated feature work should start until this corrective sequence is complete.

## Phase A — re-validate live authority first

Before creating the corrective code branch:

1. Fetch current `main` and confirm whether it still descends from `f8e7857da0605f76ae7009181a7e4b9839e9ae41`.
2. Fetch open PRs and ensure no concurrent updater/release mutation must be reconciled.
3. Fetch `v1.1.0-rc6`, its tag and asset; at the handoff checkpoint the authoritative identities were:
   - tag/source: `fdd88dfd6cee8408bf33de1c4ee4f70103fda340`;
   - installer size: `37712720` bytes;
   - installer SHA-256: `4214f19eea690357ef5aff20b74f9a4733dc1940d8a4315df803e9264ea46e6f`.
4. Re-read current Root/Targets/Snapshot/Timestamp from `main`. Never infer their next versions from older continuity prose.
5. Read the updater discovery/delivery code and existing update/TUF tests from the current head before changing interfaces.

## Phase B — implement the narrow corrective branch

Create one dedicated branch from the revalidated `main` head, recommended name:

`fix/updater-powershell-authenticode-policy`

Keep the delta limited to updater verification plus its tests/documentation.

### B1. Safe PowerShell path transport

Repair every PowerShell-based verifier so a staged installer path is passed as data, not interpolated into executable PowerShell text. The fixed PowerShell code must use `-LiteralPath` when dereferencing the installer. Cover ordinary Windows paths with spaces and the updater staging filename form `.KodepoiaSetup.exe.partial`.

Do not solve quoting by concatenating a user-controlled path into `-Command` text.

### B2. TUF-declared Authenticode policy

Extend the trusted target model/metadata parsing so Authenticode acceptance is explicit and target-scoped.

Required semantics:

- absent policy => require `Valid`;
- explicit signed policy => require `Valid`;
- explicit unsigned-allowed policy => `NotSigned` may be accepted for that exact TUF-authorized target;
- invalid, unknown, malformed, or contradictory policy => fail closed;
- statuses indicating a bad/untrusted signature must never be accepted merely because unsigned payloads are allowed.

The exact schema/key name should be chosen once in code/tests and documented; do not invent multiple aliases silently.

### B3. Preserve mandatory TUF payload verification

The existing exact checks remain mandatory before the installer can be considered staged:

- candidate must come from verified TUF metadata;
- target must not be withdrawn;
- exact authorized length must match;
- exact authorized SHA-256 must match;
- installer identity/version verification must still match the candidate public version.

Authenticode policy is an additional target property, **not** a replacement for TUF authorization, size, digest, or identity verification.

## Phase C — regression / acceptance matrix

Add automated coverage before any release candidate is built.

At minimum cover:

1. staged path ending in `.KodepoiaSetup.exe.partial`;
2. parent directory containing spaces;
3. literal-path handling for both PowerShell verifier paths;
4. signed-required + `Valid` => pass;
5. signed-required + `NotSigned` => fail;
6. policy absent + `NotSigned` => fail;
7. unsigned-allowed + `NotSigned` => pass only after all TUF length/SHA checks pass;
8. unsigned-allowed + invalid/broken signature status => fail;
9. malformed/unknown policy => fail;
10. existing hash, length, withdrawn-target, wrong-version and consent tests remain green.

Run repository guard, Python core/update tests and all release/updater acceptance required by the current repository governance on the **exact corrective head**. Do not reuse green evidence from another SHA.

## Phase D — release sequence after the fix

The intended sequence is:

1. Qualify the updater-only correction first.
2. Produce `1.1.0-rc7` from the qualified corrective source so rc7 contains the repaired updater behavior. rc7 must not contain unrelated features.
3. Install/confirm rc7 on the real Windows machine and verify the updater UI is healthy.
4. Produce a minimal newer `1.1.0-rc8` validation candidate with no unrelated functionality; rc8 exists to exercise the repaired installed rc7 updater against a strictly newer target.
5. Publish/authorize rc8 through the same draft-first + TUF fail-closed ceremony used for prior candidates, using live current metadata and monotonic next versions.
6. Perform the real machine path:

   `installed rc7 -> search -> detect rc8 -> download -> TUF length/SHA verification -> Authenticode policy verification -> installer identity verification -> explicit consent -> installer launch -> upgrade -> restart -> confirm rc8 -> search again`

7. Only after that entire path succeeds may the updater E2E defect be considered closed.

Do not mutate rc6 in place and do not claim rc5 -> rc6 succeeded retroactively.

## Phase E — continuity / normalization after each milestone

After each merged corrective/release step, update at least:

- `docs/continuity/STATE.md` with the new canonical `main` SHA, PR/merge identity and test status;
- `docs/continuity/NEXT.md` with only the still-pending actions;
- the relevant release evidence/acceptance document for rc7 or rc8;
- any long-form continuity authority that is still designated canonical by the repository.

If manual Windows interaction, offline Targets signing, release publication, or another custody-sensitive step is required, stop at that boundary and state exactly what the user must do. Do not continue to later release subdivisions until that manual gate has been completed and verified.

## Ready-to-use next-chat prompt

`@Recherche sur le Web Continue le correctif updater après rc6. Lis d'abord docs/continuity/STATE.md et docs/continuity/NEXT.md, revalide le main, la release rc6 et les métadonnées TUF live, puis poursuis uniquement le correctif PowerShell + politique Authenticode déclarée par TUF et ses tests Windows. Ne contourne aucun échec de vérification.`
