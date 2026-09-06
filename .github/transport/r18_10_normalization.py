from __future__ import annotations

import pathlib
import subprocess

REPO = pathlib.Path.cwd()
BASE = "11a9fbe79059a99a465a76c131cda6fae47624fd"
TARGET_BRANCH = "r18/10-continuity-normalization"
CONTINUITY = pathlib.Path("docs/continuity/KODEPOIA_CONTINUITY.md")

APPEND = r'''

## R18.10 post-merge normalization authority

- R18.10 implementation/evidence PR #401 merged the exact END head `f3929c128b626e350315636ea6cbb6a5690a18d1` with exact `expected_head_sha` protection as `main` `11a9fbe79059a99a465a76c131cda6fae47624fd`.
- Fresh exact-END gates on `f3929c128b626e350315636ea6cbb6a5690a18d1` were all SUCCESS: R18.10 Revocation Rollback Compromised Release Drills Acceptance #8 / `34051356143`; R16.9 Supply Chain Provenance Acceptance #198 / `34051356104`; R0 Repository Guard #2548 / `34051356113` Ubuntu + Windows; Python Core #2520 / `34051356081` 5/5; KodeStudio UI Smoke #2485 / `34051356088`.
- Canonical deterministic incident evidence remains 11/11 PASS with report SHA-256 `2c8d93615a6b9b7190f3ed1f7d094176431d839ee1596509a3fca4727ef6b823`, `critical_bypass_count=0`, `manual_intervention=NONE`, `project_data_mutation=false` and `provider_effect_count=0`.
- R16.17 #143 / `34051356122` is explicitly NON-AUTHORITATIVE for R18.10 closure: its focused tests and reproducible package builds succeed, then its legacy release-readiness assertion rejects the already-authoritative R18 identity because it still expects `1.0.0rc1` while R18 is `1.1.0rc1`. It is not part of the frozen R18.10 gate set and does not invalidate the R18.10 exact-END evidence.
- Dedicated normalization branch: `r18/10-continuity-normalization`, created exactly from implementation/evidence merge `11a9fbe79059a99a465a76c131cda6fae47624fd`. The authoritative normalization tree changes only `docs/continuity/KODEPOIA_CONTINUITY.md`; `docs/roadmap/R18_PLAN.md` and all implementation/evidence bytes remain identical to the implementation merge. Any temporary transport helper is absent from the decision tree.
- This is the single authorized post-merge normalization for R18.10. Its exact candidate head must pass fresh R0 Repository Guard Ubuntu + Windows, Python Core 5/5 and KodeStudio UI Smoke before exact-head merge; no second R18.10 normalization is permitted.
- Core manual state remains **NONE**. Production certificate revocation, production TUF key/root rotation, public GitHub Release/tag/asset or attestation mutation and public WinGet effects remain **CONDITIONAL / NOT TRIGGERED**.
- Once this exact gated normalization merges, R18.10 is **COMPLETE + NORMALIZED** and R18.11 START-sync is authorized only from the resulting normalized `main`.
'''


def out(*args: str) -> str:
    return subprocess.check_output(args, cwd=REPO, text=True).strip()


subprocess.run(["git", "fetch", "origin", TARGET_BRANCH], cwd=REPO, check=True)
subprocess.run(["git", "checkout", "-B", "normalization-work", f"origin/{TARGET_BRANCH}"], cwd=REPO, check=True)
actual = out("git", "rev-parse", "HEAD")
if actual != BASE:
    raise SystemExit(f"unexpected normalization base: {actual} != {BASE}")

path = REPO / CONTINUITY
text = path.read_text(encoding="utf-8")
if "## R18.10 post-merge normalization authority" in text:
    raise SystemExit("R18.10 normalization authority already present")
path.write_text(text + APPEND, encoding="utf-8", newline="\n")

subprocess.run(["git", "config", "user.name", "github-actions[bot]"], cwd=REPO, check=True)
subprocess.run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"], cwd=REPO, check=True)
subprocess.run(["git", "add", str(CONTINUITY)], cwd=REPO, check=True)
changed = out("git", "diff", "--cached", "--name-only").splitlines()
if changed != [str(CONTINUITY).replace("\\", "/")]:
    raise SystemExit(f"unexpected staged normalization diff: {changed}")
subprocess.run(["git", "commit", "-m", "R18.10 — post-merge continuity normalization"], cwd=REPO, check=True)
subprocess.run(["git", "push", "origin", f"HEAD:refs/heads/{TARGET_BRANCH}"], cwd=REPO, check=True)
