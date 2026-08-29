from pathlib import Path
import subprocess

technical = "e049a8f5c8155accb1d64ca4028deec5f85c4aa8"
start = "ba719dd9d556909b08606d6c7ebb4d4ef18dbd37"
base = "ac1101d9e67f5e0b36d8daaca2287e625d88787b"

design = Path("docs/roadmap/R15_3_DESIGN.md")
assert not design.exists()
design.write_text(
    f"""# R15.3 — Sanitization, privacy, license/provenance governance and revocation

**Status:** TECHNICAL SOURCE ACCEPTED / EXACT END-HEAD RE-GATES PENDING
**Normalized base:** `{base}`
**Clean START:** `{start}`
**Immutable technical source:** `{technical}`
**Manual state:** NONE

## Design

R15.3 is a deterministic governance layer after R15.2 raw capture. It never treats successful redaction as authorization. Training authorization remains the conjunction of independent source-scope, consent, provenance, license and privacy decisions.

The sanitizer creates a distinct sanitized content reference, SHA-256 output identity and digest-bound `TransformationRef`. Reports expose only categories, counts, digests, policy decisions and blockers; detected values and governed storage paths are never copied into the report.

License handling supports SPDX-style compound expressions with `AND`, `OR`, `WITH`, parentheses and case-insensitive operators. Policy is fail-closed: missing licenses stay `UNKNOWN`; unsupported/custom/unknown expressions stay `REVIEW`; explicit deny rules produce `DENY`; only explicitly allowlisted identifiers/exceptions produce `ALLOW`.

Revocation is lineage-aware. A governed source revocation transitions training-eligible records to `REVOKED`, observed records to `QUARANTINED`, computes downstream invalidation through dependency identities and stores only a reason digest in the safe report.

## Security invariants

- no sanitizer result can promote `UNKNOWN`, `REVIEW` or `DENY` authorization axes;
- benchmark-protected content remains quarantined even when all other authorization axes allow;
- raw secrets/private paths do not appear in sanitization reports;
- policy and transformation digests make sanitizer decisions reproducible;
- revocation invalidates derived artifact identities without copying source payloads;
- no network, external dataset, legal-advice claim or manual intervention is required for R15.3 acceptance.
""",
    encoding="utf-8",
    newline="\n",
)

acceptance = Path("docs/roadmap/R15_3_ACCEPTANCE.md")
assert not acceptance.exists()
acceptance.write_text(
    f"""# R15.3 — Acceptance record

**Acceptance state:** TECHNICAL SOURCE ACCEPTED / EXACT END-HEAD RE-GATES PENDING
**Technical source:** `{technical}`
**Manual:** NONE

## Exact technical evidence

- R15.3 Experience Governance Acceptance #6 / `33281437119`: SUCCESS on Ubuntu + Windows; 49 R15.1–R15.3 tests per OS, Ruff and compile.
- R0 Repository Guard #2081 / `33281437161`: SUCCESS.
- Python Core #2056 / `33281437215`: SUCCESS 5/5.
- KodeStudio UI Smoke #2021 / `33281437163`: SUCCESS.

## Adversarial coverage

Acceptance proves deterministic secret/email/path redaction; zero detected values/storage paths in safe reports; deterministic policy/output digests; consent non-laundering; missing/unknown/denied/compound/license-ref behavior; case-insensitive SPDX operators; source deny precedence; benchmark protection; configured privacy denials; governance-policy conflict rejection; revocation cascade; observed-source quarantine; and source-scoped revocation isolation.

The technical source is frozen. This document plus the END state must receive fresh exact-head R15.3/R0/Python/UI gates before merge; technical-source evidence is not reused as END-head evidence.
""",
    encoding="utf-8",
    newline="\n",
)

plan = Path("docs/roadmap/R15_PLAN.md")
text = plan.read_text(encoding="utf-8")
old_checkpoint = (
    f"**Execution checkpoint:** R1–R14 are COMPLETE + NORMALIZED; R15 planning is ACCEPTED + NORMALIZED. "
    f"R15.1–R15.2 are COMPLETE + NORMALIZED; normalized R15.2 `main` is `{base}`. "
    "R15.3 is IN_PROGRESS on dedicated branch `r15/03-sanitization-governance`; "
    "R15.4–R15.17 remain PLANNED."
)
new_checkpoint = (
    "**Execution checkpoint:** R1–R14 are COMPLETE + NORMALIZED; R15 planning is ACCEPTED + NORMALIZED. "
    "R15.1–R15.2 are COMPLETE + NORMALIZED. "
    f"R15.3 is COMPLETE with immutable technical source `{technical}`; implementation merge + unique "
    "post-merge continuity-only normalization are pending. R15.4–R15.17 remain PLANNED."
)
assert text.count(old_checkpoint) == 1
text = text.replace(old_checkpoint, new_checkpoint, 1)
old_row = (
    "| R15.3 | Sanitization, secret/privacy filtering, license/provenance policy + revocation | "
    "IN_PROGRESS | NONE | R15.1–R15.2 + R6/R7/R8 |"
)
assert text.count(old_row) == 1
text = text.replace(old_row, old_row.replace("IN_PROGRESS", "COMPLETE"), 1)
plan.write_text(text, encoding="utf-8", newline="\n")

continuity = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
lines = continuity.read_text(encoding="utf-8").splitlines()
lines[0] = (
    "> Kodepoia, architecture v1.0 gelée. **R1–R14 COMPLETE + NORMALIZED. R15 planning ACCEPTED + NORMALIZED. "
    "R15.1–R15.2 COMPLETE + NORMALIZED; R15.3 COMPLETE — implementation merge pending; "
    "R15.4–R15.17 PLANNED.** "
    f"R15.3 immutable technical source `{technical}` from clean START `{start}`; exact technical "
    "R15.3 #6 / `33281437119`, R0 #2081 / `33281437161`, Python #2056 / `33281437215`, "
    "UI #2021 / `33281437163` all SUCCESS; manual NONE. Fresh exact END-head re-gates remain mandatory before merge."
)
idx = next(i for i, line in enumerate(lines) if line.startswith("- R15.3 : **IN_PROGRESS**"))
lines[idx] = (
    f"- R15.3 : **COMPLETE — IMPLEMENTATION MERGE PENDING** — clean START `{start}` from normalized "
    f"R15.2 `main` `{base}`; immutable technical source `{technical}`; exact technical R15.3 #6 / "
    "`33281437119` SUCCESS Ubuntu + Windows with 49 R15.1–R15.3 tests per OS + Ruff + compile, "
    "R0 #2081 / `33281437161` SUCCESS, Python #2056 / `33281437215` SUCCESS 5/5, UI #2021 / "
    "`33281437163` SUCCESS; manual NONE. Sanitization is deterministic and non-laundering; "
    "license/provenance/privacy remain fail-closed; revocation propagates by lineage. Final clean END-head "
    "must receive fresh R15.3/R0/Python/UI before merge; R15.4 remains unauthorized until unique post-merge normalization."
)
status = next(i for i, line in enumerate(lines) if line == "| R15.3 | IN_PROGRESS | NONE |")
lines[status] = "| R15.3 | COMPLETE | NONE |"
action = next(i for i, line in enumerate(lines) if line.startswith("**R15.3 START-sync is active"))
lines[action] = (
    "**R15.3 END-sync is complete on `r15/03-sanitization-governance`. Produce one clean END-head with no "
    "helper/marker, require fresh exact-head R15.3 focused + R0 Repository Guard + full Python Core + "
    "KodeStudio UI Smoke, then merge only with `expected_head_sha`. After that merge, perform exactly one "
    "continuity-only post-merge normalization with fresh R0/Python/UI. R15.4 remains unauthorized until "
    "that normalized `main` exists.**"
)
continuity.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

subprocess.run(["git", "diff", "--check"], check=True)
subprocess.run(["python", "scripts/check_repo.py"], check=True)
