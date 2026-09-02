from pathlib import Path

PATH = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
BASE = "e6c11e986ad2e0ee5b1cdd50c0ae2061117ca974"
END_HEAD = "162abd7b9050bd9f9e35d0b2bf8049b1ed86984c"
TECH_SOURCE = "499292dd553460bb48f3092112d5bcb81544242b"
NORMALIZATION_BRANCH = "r16/10-continuity-normalization"

NEW_TOP = (
    "> Kodepoia, architecture v1.0 gelée. **R1–R15 COMPLETE + NORMALIZED. R16 planning ACCEPTED + NORMALIZED. "
    "R16.1–R16.10 COMPLETE + NORMALIZED. R16.11–R16.18 remain PLANNED.** "
    f"R16.10 immutable technical source `{TECH_SOURCE}`; final exact-END head `{END_HEAD}` passed fresh "
    "R16.10 #27 / `33641853721` SUCCESS Ubuntu + Windows, R16.9 #26 / `33641853768` SUCCESS Ubuntu + Windows, "
    "R0 #2337 / `33641909778` attempt 2 SUCCESS Ubuntu + Windows, Python Core #2308 / `33641853756` SUCCESS 5/5 "
    "and KodeStudio UI Smoke #2273 / `33641853653` SUCCESS; implementation/evidence PR #353 merged with "
    f"`expected_head_sha={END_HEAD}` as `main` `{BASE}`. This continuity record is the unique post-merge R16.10 "
    "normalization authority and becomes authoritative only after its own fresh exact-head R0/Python/UI gates and "
    "exact-head normalization merge. R16.11 is authorized only from the resulting normalized `main`. Manual NONE."
)

GLOBAL_BULLET = (
    f"- R16.10 : **COMPLETE + NORMALIZED** — normalized R16.9 `main` `3957a30053da791facb2de7fbbbb0614d0fa03d6`; "
    f"immutable technical source `{TECH_SOURCE}`; technical R16.10 #20 / `33638816914` SUCCESS Ubuntu + Windows; "
    f"final exact-END head `{END_HEAD}` passed fresh R16.10 #27 / `33641853721` SUCCESS Ubuntu + Windows, "
    "R16.9 #26 / `33641853768` SUCCESS Ubuntu + Windows, R0 #2337 / `33641909778` attempt 2 SUCCESS Ubuntu + Windows, "
    "Python Core #2308 / `33641853756` SUCCESS 5/5 and UI #2273 / `33641853653` SUCCESS; PR #353 merged with exact "
    f"expected head as implementation/evidence `main` `{BASE}`. Acceptance remains 10/10 PASS per OS, `security_claim=true`, "
    "`critical_veto=false`, Godot `capability_absent` on hosted runners, zero network calls, no live credentials and no destructive "
    "host action. This record is the unique post-merge continuity-only R16.10 normalization authority when its exact candidate "
    "passes fresh R0/Python/UI and merges; manual NONE. R16.11 is authorized only from the resulting normalized `main`."
)

NORMALIZATION_SECTION = [
    "## R16.10 post-merge normalization authority",
    "",
    f"- Implementation/evidence merge base: `{BASE}`, produced only after final exact-END head `{END_HEAD}` passed fresh R16.10 #27 / `33641853721` Ubuntu + Windows, R16.9 #26 / `33641853768` Ubuntu + Windows, R0 #2337 / `33641909778` attempt 2 Ubuntu + Windows, Python Core #2308 / `33641853756` 5/5 and KodeStudio UI Smoke #2273 / `33641853653`.",
    f"- Dedicated normalization branch: `{NORMALIZATION_BRANCH}`, created exactly from that implementation/evidence merge.",
    "- The authoritative normalization tree changes only `docs/continuity/KODEPOIA_CONTINUITY.md`; `docs/roadmap/R16_PLAN.md` and all implementation/evidence bytes remain identical to the implementation merge. Any temporary normalization helper is absent from the decision head.",
    "- This is the single authorized post-merge normalization for R16.10. This continuity record becomes authoritative only after its exact normalization candidate passes fresh R0 Repository Guard + full Python Core + KodeStudio UI Smoke and the normalization PR merges with exact expected-head protection. No second R16.10 normalization is permitted.",
    "- Manual state remains **NONE**. R16.11 START-sync is authorized only from the resulting normalized `main`; it remains unauthorized from the implementation merge or from any unmerged normalization candidate.",
    "",
]

NEXT_ACTION = (
    "R16.11 — **Representative real Godot 3D beta project** — is the next authorized subdivision only on the normalized `main` "
    "produced when this unique R16.10 continuity-only normalization PR passes fresh exact-head R0/Python/UI and merges. Do not "
    f"begin R16.11 from implementation merge `{BASE}` or from an unmerged normalization candidate. After normalization merge, "
    "create the dedicated R16.11 branch from that exact normalized `main` and perform START-sync before implementation. Frozen scope: "
    "representative repository-owned Godot 3D scenes/resources, meshes/materials/animation references where already supported, "
    "KodeGodot execution/diagnostics, asset lineage, edits/rollback, resource budgets and malicious metadata/text controls. Manual NONE."
)

text = PATH.read_text(encoding="utf-8")
lines = text.splitlines()

if not lines or "R16.10 COMPLETE at END-sync" not in lines[0]:
    raise SystemExit("Unexpected continuity header; refusing normalization")
if "## R16.10 END authority" not in lines:
    raise SystemExit("Missing R16.10 END authority")
if "## R16 status index" not in lines:
    raise SystemExit("Missing R16 status index")

lines[0] = NEW_TOP

if not any(line.startswith("- R16.10 : **COMPLETE + NORMALIZED**") for line in lines):
    r169 = [i for i, line in enumerate(lines) if line.startswith("- R16.9 : **COMPLETE + NORMALIZED**")]
    if not r169:
        raise SystemExit("Missing R16.9 global record")
    lines.insert(r169[0] + 1, GLOBAL_BULLET)

if "## R16.10 post-merge normalization authority" not in lines:
    status_idx = lines.index("## R16 status index")
    lines[status_idx:status_idx] = NORMALIZATION_SECTION

old_status = "| R16.10 | COMPLETE | NONE |"
new_status = "| R16.10 | COMPLETE + NORMALIZED | NONE |"
count = sum(1 for line in lines if line == old_status)
if count != 1:
    raise SystemExit(f"Expected exactly one R16.10 status row, found {count}")
lines = [new_status if line == old_status else line for line in lines]

status_idx = lines.index("## R16 status index")
next_idx = next(i for i in range(status_idx + 1, len(lines)) if lines[i] == "## Next authorized action")
perm_idx = next(i for i in range(next_idx + 1, len(lines)) if lines[i] == "## Permanent R-phase execution rule")
lines[next_idx + 1:perm_idx] = ["", NEXT_ACTION, ""]

out = "\n".join(lines) + "\n"
if out == text:
    raise SystemExit("Normalization produced no change")
PATH.write_text(out, encoding="utf-8")
