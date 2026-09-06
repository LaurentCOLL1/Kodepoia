from __future__ import annotations

import pathlib
import subprocess

REPO = pathlib.Path.cwd()
BASE = "c7f0e6a7801fb37ca044b4d3d8360694c911e824"
TARGET_BRANCH = "r18/11-integrated-adversarial-release-update-acceptance"
ROADMAP = pathlib.Path("docs/roadmap/R18_PLAN.md")
CONTINUITY = pathlib.Path("docs/continuity/KODEPOIA_CONTINUITY.md")

ROADMAP_APPEND = r'''

## R18.11 START-sync authority

- Exact normalized branch point: `main` `c7f0e6a7801fb37ca044b4d3d8360694c911e824`, produced by the single R18.10 post-merge normalization PR #402 after exact candidate `50d549f8717882502195eb562617178d1fdab613` passed fresh R0 Repository Guard #2550 / `34052009856` Ubuntu + Windows, full Python Core #2522 / `34052009992` 5/5 and KodeStudio UI Smoke #2487 / `34052009974` Windows.
- Dedicated branch: `r18/11-integrated-adversarial-release-update-acceptance`, created directly from that exact normalized `main` before any R18.11 implementation byte.
- State transition: R18.1–R18.10 **COMPLETE + NORMALIZED**; R18.11 **IN_PROGRESS**. R18 phase completion remains unauthorized until R18.11 exact-END merge and the single phase-level post-merge continuity normalization complete.
- Frozen scope remains the planned integrated adversarial release/update acceptance: consume exact-source machine-readable R18.1–R18.10 authorities; build the final Windows RC; prove clean install, packaged smoke, accepted older-fixture-to-candidate update and uninstall health; exercise tamper, rollback, freeze, wrong-channel, wrong-signature and wrong-digest fail-closed controls; emit one deterministic integrated report with `blockers=[]` and `critical_veto=false` only when every critical obligation passes.
- The harness must reuse accepted release/update trust boundaries rather than create a parallel stack: canonical identity, deterministic bundle, provenance/SBOM, signing truth, release staging, TUF metadata, discovery/channel policy, verified delivery/recovery, WinGet readiness and R18.10 incident verdicts remain authoritative inputs. Exact-source equality and evidence freshness are mandatory; stale workflow success may not substitute for fresh R18.11 evidence.
- Windows acceptance must use repository packaging paths and a real packaged executable. An older accepted fixture may be reconstructed from an immutable pre-R18 source only for local CI upgrade testing; no production endpoint, publication, signing certificate or external package-manager submission may be invoked.
- Critical negative controls are fail-closed. Any unexpected acceptance of tampered bytes, rollback/freeze metadata, wrong channel/signature/digest or compromised release state sets `critical_veto=true`, adds a blocker and prevents R18 completion.
- Core manual intervention is **NONE**. Production signing, public GitHub Release publication/mutation, production TUF key custody/rotation and public WinGet submission remain **CONDITIONAL / NOT TRIGGERED** and must be reported truthfully as such.
- This START-sync is documentation-only. No R18.11 integrated module, script, schema, workflow, test, fixture or implementation byte may precede this clean START decision head; temporary transport helpers are non-authoritative and absent from the R18.11 branch lineage.
'''

CONTINUITY_APPEND = r'''

## R18.11 START authority

- R18.10 is **COMPLETE + NORMALIZED** on canonical `main` `c7f0e6a7801fb37ca044b4d3d8360694c911e824`. Its unique continuity-only normalization PR #402 used exact candidate `50d549f8717882502195eb562617178d1fdab613`, with fresh R0 #2550 / `34052009856` Ubuntu + Windows, Python Core #2522 / `34052009992` 5/5 and KodeStudio UI Smoke #2487 / `34052009974` all SUCCESS before exact-head merge.
- R18.11 dedicated branch `r18/11-integrated-adversarial-release-update-acceptance` is created directly from that normalized main. R18.1–R18.10 are **COMPLETE + NORMALIZED**; R18.11 is **IN_PROGRESS**.
- Frozen R18.11 authority is integrated and non-circular: machine-readable R18.1–R18.10 evidence, final Windows RC build/install/update/uninstall health, exact-source provenance/freshness checks and adversarial tamper/rollback/freeze/channel/signature/digest rejection feed one deterministic report. `blockers=[]` and `critical_veto=false` are required for acceptance.
- The real Windows acceptance must remain local to CI and use repository packaging boundaries; public release, production signing, production TUF custody/rotation and public WinGet effects are not authorized by this START.
- Manual state: **NONE** for core R18.11. External production effects remain **CONDITIONAL / NOT TRIGGERED**.
- This START decision is documentation-only and precedes every R18.11 implementation byte. R18 phase completion remains unauthorized until R18.11 exact-END is freshly gated and merged and exactly one continuity-only phase normalization is freshly gated and merged.
'''


def out(*args: str) -> str:
    return subprocess.check_output(args, cwd=REPO, text=True).strip()


subprocess.run(["git", "fetch", "origin", TARGET_BRANCH], cwd=REPO, check=True)
subprocess.run(["git", "checkout", "-B", "r18-11-start-work", f"origin/{TARGET_BRANCH}"], cwd=REPO, check=True)
actual = out("git", "rev-parse", "HEAD")
if actual != BASE:
    raise SystemExit(f"unexpected R18.11 branch point: {actual} != {BASE}")

for relative, append, heading in (
    (ROADMAP, ROADMAP_APPEND, "## R18.11 START-sync authority"),
    (CONTINUITY, CONTINUITY_APPEND, "## R18.11 START authority"),
):
    path = REPO / relative
    text = path.read_text(encoding="utf-8")
    if heading in text:
        raise SystemExit(f"START authority already present in {relative}")
    path.write_text(text + append, encoding="utf-8", newline="\n")

subprocess.run(["git", "config", "user.name", "github-actions[bot]"], cwd=REPO, check=True)
subprocess.run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"], cwd=REPO, check=True)
expected = [str(CONTINUITY).replace("\\", "/"), str(ROADMAP).replace("\\", "/")]
subprocess.run(["git", "add", *expected], cwd=REPO, check=True)
changed = out("git", "diff", "--cached", "--name-only").splitlines()
if changed != expected:
    raise SystemExit(f"unexpected R18.11 START diff: {changed}")
subprocess.run(["git", "commit", "-m", "R18.11 — START-sync integrated adversarial acceptance"], cwd=REPO, check=True)
subprocess.run(["git", "push", "origin", f"HEAD:refs/heads/{TARGET_BRANCH}"], cwd=REPO, check=True)
