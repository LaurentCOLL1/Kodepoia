from __future__ import annotations

import pathlib
import subprocess

REPO = pathlib.Path.cwd()
SOURCE = "7e2e513a166097d2727a8105695b8c62d370750d"
TARGET_BRANCH = "r18/10-revocation-rollback-compromised-release-drills"

ROADMAP_APPEND = r'''

## R18.10 END-sync authority

- **Latest-state authority:** R18.10 synthetic incident/recovery implementation is accepted on immutable technical source `7e2e513a166097d2727a8105695b8c62d370750d`; R18.11 remains **PLANNED / unauthorized** until R18.10 exact-END merge and its single post-merge normalization complete.
- Historical technical candidate `4298dbb9f93d5013219c31747d5795c1ee50aa9d` is NON-AUTHORITATIVE for final closure because full Python Core exposed an optional-UI dependency leak: `tests/test_r18_10_kodestudio_incident.py` imported PySide6 during collection even when the `ui` extra was not installed. The accepted source moves Qt imports behind `pytest.importorskip`, preserving actual Qt execution in UI jobs while making Core correctly independent of the optional UI extra.
- Fresh same-source gates on `7e2e513a166097d2727a8105695b8c62d370750d` are all SUCCESS: R18.10 Revocation Rollback Compromised Release Drills Acceptance #5 / `34050275249` Ubuntu + Windows; R16.9 Supply Chain Provenance #196 / `34050275120` Ubuntu + Windows; R0 Repository Guard #2546 / `34050275186` Ubuntu + Windows; full Python Core #2518 / `34050275022` 5/5; KodeStudio UI Smoke #2483 / `34050275280` Windows.
- Deterministic R18.10 report is PASS with **11/11** scenario verdicts, `critical_bypass_count=0`, `manual_intervention=NONE`, `project_data_mutation=false` and `provider_effect_count=0`; report SHA-256 is `2c8d93615a6b9b7190f3ed1f7d094176431d839ee1596509a3fca4727ef6b823`.
- Accepted scenario families cover compromised certificate denial; sequential TUF Root rotation; Root/Timestamp/Snapshot/Targets rollback/freeze denial; withdrawn and superseded release denial; tampered asset denial; and verified last-known-good recovery.
- Exact R18.10 Actions artifacts: Linux ID `9994351724`, `r18-10-incident-drills-Linux-7e2e513a166097d2727a8105695b8c62d370750d`, ZIP digest `sha256:9ce38f35c8d67abeedf6c7d6494c131551198928ab7e89db3ad5547c1ac953b1`; Windows ID `9994393802`, `r18-10-incident-drills-Windows-7e2e513a166097d2727a8105695b8c62d370750d`, ZIP digest `sha256:a21b606e9d05f1126ec4211ec3875694ab4fb0aac237b290dfdb1d66a76b1e6b`.
- Provider-side actions are explicitly recorded `NOT_EXECUTED`: production Authenticode certificate revocation, production TUF Root-key rotation, public GitHub Release withdrawal/deletion, public tag/asset deletion, GitHub artifact-attestation deletion and public WinGet supersession/submission. No network publication/effect call or project-data mutation occurred.
- Core manual state is **NONE**. Real certificate revocation, production TUF custody/rotation, public release/tag/asset or attestation mutation, repository immutable-release setting changes, production signing and public WinGet effects remain **CONDITIONAL / NOT TRIGGERED**.
- Because this END-sync changes documentation bytes, the resulting exact END head must pass fresh R18.10 + R16.9 + R0 + full Python Core + KodeStudio UI Smoke before PR #401 may merge with `expected_head_sha` equal to that exact head. Exactly one post-merge continuity-only R18.10 normalization must then pass fresh R0/Python/UI; only the resulting normalized `main` authorizes R18.11 START-sync.
'''

CONTINUITY_APPEND = r'''

## R18.10 END authority

- **Latest-state authority:** R18.10 is **COMPLETE at END-sync** on immutable accepted technical source `7e2e513a166097d2727a8105695b8c62d370750d`; R18.11 remains **PLANNED / unauthorized** until the exact END head is freshly gated, PR #401 merges with exact expected-head protection, and the single continuity-only R18.10 normalization is freshly gated and merged.
- Historical candidate `4298dbb9f93d5013219c31747d5795c1ee50aa9d` is NON-AUTHORITATIVE for final closure because Python Core failed collection when an R18.10 Qt test imported optional PySide6 at module scope. Accepted source `7e2e513a166097d2727a8105695b8c62d370750d` fixes only that dependency-boundary defect by conditionally importing Qt inside the UI test; standalone UI coverage remains active.
- Fresh accepted-source gates are SUCCESS: R18.10 #5 / `34050275249` Ubuntu + Windows; R16.9 #196 / `34050275120` Ubuntu + Windows; R0 Repository Guard #2546 / `34050275186` Ubuntu + Windows; full Python Core #2518 / `34050275022` 5/5; KodeStudio UI Smoke #2483 / `34050275280` Windows.
- Canonical deterministic drill report: 11/11 PASS, report SHA-256 `2c8d93615a6b9b7190f3ed1f7d094176431d839ee1596509a3fca4727ef6b823`, `critical_bypass_count=0`, `manual_intervention=NONE`, `project_data_mutation=false`, `provider_effect_count=0`.
- Accepted scenarios fail closed for compromised signing identity, TUF Root/Timestamp/Snapshot/Targets rollback/freeze, withdrawn/superseded release metadata and tampered asset, while sequential Root rotation and last-known-good recovery pass their positive/recovery verdicts.
- Exact artifacts: Linux `9994351724 / sha256:9ce38f35c8d67abeedf6c7d6494c131551198928ab7e89db3ad5547c1ac953b1`; Windows `9994393802 / sha256:a21b606e9d05f1126ec4211ec3875694ab4fb0aac237b290dfdb1d66a76b1e6b`, both source-bound to `7e2e513a166097d2727a8105695b8c62d370750d`.
- Provider-side incident effects remain explicitly `NOT_EXECUTED`: real production certificate revocation, production TUF key/root rotation, public GitHub Release/tag/asset deletion or withdrawal, GitHub attestation deletion and public WinGet supersession/submission. Core manual state is **NONE**; all production/public effects remain **CONDITIONAL / NOT TRIGGERED**.
- This END-sync is documentation-only relative to the accepted technical source. Its resulting exact head must pass fresh R18.10/R16.9/R0/full-Python/UI before PR #401 exact-head merge. Exactly one continuity-only R18.10 post-merge normalization is then authorized; no R18.11 implementation may start before that normalized `main` exists.
'''


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=REPO, text=True).strip()


run("git", "fetch", "origin", TARGET_BRANCH)
run("git", "checkout", "-B", "transport-work", f"origin/{TARGET_BRANCH}")
actual = run("git", "rev-parse", "HEAD")
if actual != SOURCE:
    raise SystemExit(f"unexpected authority head: {actual} != {SOURCE}")

roadmap = REPO / "docs/roadmap/R18_PLAN.md"
continuity = REPO / "docs/continuity/KODEPOIA_CONTINUITY.md"
roadmap.write_text(roadmap.read_text(encoding="utf-8") + ROADMAP_APPEND, encoding="utf-8", newline="\n")
continuity.write_text(continuity.read_text(encoding="utf-8") + CONTINUITY_APPEND, encoding="utf-8", newline="\n")

changed = run("git", "diff", "--name-only").splitlines()
expected = ["docs/continuity/KODEPOIA_CONTINUITY.md", "docs/roadmap/R18_PLAN.md"]
if changed != expected:
    raise SystemExit(f"unexpected END-sync diff: {changed}")

run("git", "config", "user.name", "github-actions[bot]")
run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
run("git", "add", *expected)
subprocess.check_call(["git", "commit", "-m", "R18.10 — END-sync accepted incident drill evidence"], cwd=REPO)
subprocess.check_call(["git", "push", "origin", f"HEAD:refs/heads/{TARGET_BRANCH}"], cwd=REPO)
