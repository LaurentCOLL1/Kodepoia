from __future__ import annotations

from pathlib import Path
import re
import subprocess

SOURCE_SHA = "56f829f4395138bf90a1a8e0003bff95b67dd878"
CI_DIGEST = "23d3cf13b92f4a1e172c7611f69cba90ea9259c6914051ea444d83d505c6ea6b"


def sync_acceptance() -> None:
    path = Path("docs/roadmap/R13_17_ACCEPTANCE.md")
    path.write_text(
        f"""# R13.17 — Integrated release-readiness acceptance

**Status:** COMPLETE — ACCEPTED TECHNICAL SOURCE; FINAL DOCUMENTATION/EVIDENCE RE-GATES PENDING  
**Manual:** CONDITIONAL / NOT TRIGGERED  
**Integrated PASS report:** AUTHORIZED AFTER THIS END-SYNC  
**CI PASS manifest:** RECORDED

## Scope

Adversarial hardening plus anti-circular Android/iOS phase-level release-readiness acceptance for the frozen R13 Mobile / Platform / Release capability.

Normalized base: `b202af1b4d6fd8d34e351c710db4c0ec719dd8f4`.  
Dedicated branch: `r13/17-integrated-release-readiness`.  
Manual intervention: **CONDITIONAL / NOT TRIGGERED**.

The conditional manual trigger was evaluated from the frozen phase Definition of Done and did **not** trigger. Hosted CI proved the required Android API 36 build/package/runtime path and hosted macOS proved the required Xcode/SwiftUI/XCTest simulator path. R13 does not claim Android or Apple physical-device capability, live Play/App Store/TestFlight state, production signing/provisioning credentials, or automatic public publication.

## Accepted immutable technical source

Accepted R13.17 implementation SHA: **`{SOURCE_SHA}`**.

The predecessor **`e6d7cb3768d80944692596ef6705f3f95a24c8da`** is rejected and none of its decision evidence is reusable. Its Android integrated build and collection succeeded, but the workflow assertion read `target_sdk` at the wrong JSON level. The correction changed exactly one workflow line to read `request.target_sdk`; all required gates were restarted on the new source SHA.

## Exact-head implementation gates

All required gates completed **SUCCESS** on exactly `{SOURCE_SHA}`:

- R0 Repository Guard #1731 / run `33118952255`;
- Python Core #1705 / run `33118952290`;
- KodeStudio UI Smoke #1672 / run `33118952751`;
- R13 Android Build Acceptance #301 / run `33118952332`;
- R13 Android Signing Acceptance #254 / run `33118952213`;
- R13 Android Device Acceptance #239 / run `33118952330`;
- R13 Google Play Readiness Acceptance #222 / run `33118952293`;
- R13 Apple Xcode Acceptance #205 / run `33118952217`;
- R13 Apple SwiftUI Scaffold Acceptance #176 / run `33118953127`;
- R13 Apple Signing Archive Acceptance #151 / run `33118952223`;
- R13 Apple XCTest Acceptance #131 / run `33118952229`;
- R13 Integrated Release Readiness #4 / run `33118952219`.

The integrated workflow itself passed both `r13-integrated-android-ubuntu-latest` and `r13-integrated-apple-macos-26`, including the focused R13.17 adversarial suite, canonical Android build/collection/exact-head assertion, and canonical iOS Simulator XCTest/exact-head assertions.

## Immutable platform artifact authority

The accepted CI manifest binds these GitHub Actions archive identities to the same technical source SHA:

- Android Build Linux artifact `9665811449`, name `r13-4-android-Linux-{SOURCE_SHA}`, archive SHA-256 `4675ea1f8c1adcfc6821b66dcc88a4dec5cba1779dbef45d3d729856fc63dc8d`;
- Android Device artifact `9665845148`, name `r13-6-android-device-{SOURCE_SHA}`, archive SHA-256 `eb7aa4f43b19a519e85e93e288bc349d41ba2c9369e4c529b73460690081517d`;
- Apple XCTest artifact `9665853659`, name `r13-11-apple-xctest-macOS-{SOURCE_SHA}`, archive SHA-256 `f40307954d44d38e80099128b43b5334c8079a72142bfada0d445eb66558cb1b`.

Checked-in CI authority: `docs/roadmap/R13_17_CI_ACCEPTANCE.json`.  
Semantic CI digest: **`{CI_DIGEST}`**.

## Bounded accepted claims

The core PASS is deliberately limited to what the accepted hosted evidence proves:

- `android_hosted_build=true`;
- `android_target_api=36`;
- `android_package_kinds=["aab","apk"]`;
- `android_device_scope="VIRTUAL"` and `android_physical_device_claim=false`;
- `ios_hosted_build_test=true`;
- `ios_scope="SIMULATOR"` and `apple_physical_device_claim=false`;
- `live_store_query_attempted=false`;
- `production_signing_credential_used=false`;
- manual state `conditional_not_triggered`;
- `status=pass`, `blockers=[]` in the accepted CI authority.

No account-free or simulator/virtual evidence may be upgraded into physical-device, live-store, public-release or production-signing proof.

## Anti-circular evidence ordering

1. Freeze the implementation source while both canonical R13 PASS JSON files are absent.
2. Require all 12 exact-head candidate gates on that source SHA.
3. Reject any failed predecessor and restart every decision gate after a source-byte change.
4. Bind the exact Android Build, Android Device and Apple XCTest archive identities/digests.
5. Generate `R13_17_CI_ACCEPTANCE.json` from only that accepted source/run/artifact set.
6. End-synchronize this acceptance, `R13_PLAN.md` and continuity so R13.17 becomes COMPLETE before report generation.
7. Generate `R13_INTEGRATED_ACCEPTANCE.json` with `scripts/r13_17_build_integrated_report.py --source-sha {SOURCE_SHA}`; the report is excluded from its own bindings.
8. Validate the canonical report against current repository bytes and schema/model invariants.
9. Freeze the resulting documentation/evidence head and rerun the same required exact-head gate family before PR #253 may merge with `expected_head_sha`.
10. After merge, create exactly one continuity-only R13 normalization branch, run fresh R0 + full Python Core + KodeStudio UI Smoke, and merge with expected SHA.
11. Only that normalization merge makes R13 **COMPLETE + NORMALIZED** and authorizes R14 planning.

## Evidence state at end-sync

Start-of-subdivision synchronization: **DONE**.  
Accepted technical source: **`{SOURCE_SHA}`**.  
Implementation candidate gates: **12/12 SUCCESS**.  
Manual state: **CONDITIONAL / NOT TRIGGERED (`conditional_not_triggered`)**.  
CI manifest: **RECORDED / PASS** with semantic digest **`{CI_DIGEST}`**.  
End-of-subdivision plan/continuity synchronization: **DONE in this evidence cycle; R13.17 is COMPLETE**.  
Canonical integrated report: **generated only after these bound bytes are finalized**.  
Final documentation/evidence exact-head gates and merge results: **must be recorded in PR metadata and then in the single post-merge continuity normalization, not by mutating this report-bound acceptance**.

## Failure policy

Any failed final documentation/evidence gate rejects that exact final head. Correct only R13.17 evidence/documentation, freeze a new final head and restart every required final gate. Missing/stale runs, substituted artifacts, forged semantic digests, mutated bound files, physical/live-store claim escalation or prior R12 evidence substitution never manufacture PASS.
""",
        encoding="utf-8",
    )


def sync_plan() -> None:
    path = Path("docs/roadmap/R13_PLAN.md")
    text = path.read_text(encoding="utf-8")
    original = text
    text = text.replace(
        "**Status:** IN PROGRESS  ",
        "**Status:** COMPLETE — R13.17 accepted; post-merge normalization pending  ",
        1,
    )
    text = re.sub(
        r"^\*\*Execution checkpoint:\*\*.*$",
        "**Execution checkpoint:** R13.1–R13.16 are `COMPLETE + NORMALIZED`. R13.17 accepted immutable technical source `56f829f4395138bf90a1a8e0003bff95b67dd878` passed all 12 required exact-head standard/platform/integrated gates; rejected predecessor `e6d7cb3768d80944692596ef6705f3f95a24c8da` is not reusable. `R13_17_CI_ACCEPTANCE.json` binds those 12 run identities plus Android Build, Android Device and Apple XCTest archive digests with semantic digest `23d3cf13b92f4a1e172c7611f69cba90ea9259c6914051ea444d83d505c6ea6b`. R13.17 is `COMPLETE`; canonical integrated report generation and fresh final documentation/evidence exact-head re-gates precede PR #253 merge. Manual remains `CONDITIONAL / NOT TRIGGERED`. R13 is COMPLETE at implementation/evidence level but not `COMPLETE + NORMALIZED` until the single post-merge continuity-only normalization succeeds and merges.",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    text = text.replace(
        "R13.17 is **IN_PROGRESS**.",
        "R13.17 is **COMPLETE**; post-merge normalization pending.",
        1,
    )
    text = text.replace(
        "| R13.17 | Adversarial hardening + Android/iOS integrated release-readiness acceptance | IN_PROGRESS | CONDITIONAL | R13.1–R13.16 + R6/R8/R12 evidence |",
        "| R13.17 | Adversarial hardening + Android/iOS integrated release-readiness acceptance | COMPLETE | CONDITIONAL | R13.1–R13.16 + R6/R8/R12 evidence |",
        1,
    )
    completion = (
        "**Completion record:** rejected predecessor **`e6d7cb3768d80944692596ef6705f3f95a24c8da`** is not reusable because the first integrated Android workflow assertion read the accepted collector's API target from the wrong JSON level. Corrected accepted immutable technical source **`56f829f4395138bf90a1a8e0003bff95b67dd878`** changed only that assertion relative to the predecessor and passed all required exact-head gates: R0 #1731 / `33118952255`, Python Core #1705 / `33118952290`, KodeStudio UI Smoke #1672 / `33118952751`, Android Build #301 / `33118952332`, Android Signing #254 / `33118952213`, Android Device #239 / `33118952330`, Google Play Readiness #222 / `33118952293`, Apple Xcode #205 / `33118952217`, Apple SwiftUI #176 / `33118953127`, Apple Signing Archive #151 / `33118952223`, Apple XCTest #131 / `33118952229`, and R13 Integrated Release Readiness #4 / `33118952219`, all SUCCESS. The integrated workflow's Android and Apple jobs both passed. Immutable artifact bindings are Android Build Linux artifact `9665811449` / `4675ea1f8c1adcfc6821b66dcc88a4dec5cba1779dbef45d3d729856fc63dc8d`, Android Device artifact `9665845148` / `eb7aa4f43b19a519e85e93e288bc349d41ba2c9369e4c529b73460690081517d`, and Apple XCTest artifact `9665853659` / `f40307954d44d38e80099128b43b5334c8079a72142bfada0d445eb66558cb1b`. Checked-in `R13_17_CI_ACCEPTANCE.json` has semantic digest **`23d3cf13b92f4a1e172c7611f69cba90ea9259c6914051ea444d83d505c6ea6b`**, `status=pass`, `blockers=[]`, Android scope `VIRTUAL`, iOS scope `SIMULATOR`, no physical-device claim, no live-store query and no production signing credential. Manual remains **CONDITIONAL / NOT TRIGGERED**. This end synchronization marks R13.17 **COMPLETE**; the canonical integrated report is generated only after these bound bytes are frozen, and the resulting evidence/documentation head must pass fresh required exact-head gates before PR #253 may merge. R13 becomes `COMPLETE + NORMALIZED` only after the single post-merge continuity-only normalization passes and merges.\n"
    )
    marker = "\n## Required artifact pattern per subdivision"
    if "**Completion record:** rejected predecessor **`e6d7cb3768d80944692596ef6705f3f95a24c8da`**" not in text:
        if text.count(marker) != 1:
            raise SystemExit("R13_PLAN completion insertion marker drift")
        text = text.replace(marker, "\n" + completion + marker, 1)
    if text == original:
        raise SystemExit("R13_PLAN end-sync made no changes")
    path.write_text(text, encoding="utf-8")


def sync_continuity() -> None:
    path = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
    text = path.read_text(encoding="utf-8")
    original = text
    prompt = (
        "> Kodepoia, architecture v1.0 gelée. **R1–R12 COMPLETE + NORMALIZED. R13 planning ACCEPTED + NORMALIZED. R13.1–R13.16 COMPLETE + NORMALIZED. R13.17 COMPLETE / FINAL EVIDENCE RE-GATES PENDING on `r13/17-integrated-release-readiness`. R13 phase implementation/evidence is COMPLETE but post-merge normalization remains pending.** Accepted immutable technical source `56f829f4395138bf90a1a8e0003bff95b67dd878` passed all 12 required exact-head gates. `R13_17_CI_ACCEPTANCE.json` binds those runs and immutable Android Build/Device + Apple XCTest artifacts with semantic digest `23d3cf13b92f4a1e172c7611f69cba90ea9259c6914051ea444d83d505c6ea6b`. Manual is CONDITIONAL / NOT TRIGGERED; Android evidence is VIRTUAL, Apple evidence SIMULATOR, with no physical-device, live-store or production-signing claim. Generate/verify the canonical R13 integrated report from these end-synchronized bytes, then require fresh exact-head final gates before PR #253 merge. After merge, exactly one continuity-only normalization must pass R0 + full Python Core + KodeStudio UI Smoke and merge before R13 is COMPLETE + NORMALIZED and R14 planning is authorized."
    )
    text = re.sub(
        r"^> Kodepoia, architecture v1\.0 gelée\..*$",
        prompt,
        text,
        count=1,
        flags=re.MULTILINE,
    )
    text = text.replace(
        "- R13 phase status: **IN PROGRESS**.",
        "- R13 phase status: **COMPLETE / NORMALIZATION PENDING**.",
        1,
    )
    text = re.sub(
        r"^- R13\.17: \*\*IN_PROGRESS\*\*.*$",
        "- R13.17: **COMPLETE / FINAL EVIDENCE RE-GATES PENDING** on `r13/17-integrated-release-readiness`. Accepted immutable technical source **`56f829f4395138bf90a1a8e0003bff95b67dd878`** passed all 12 required exact-head gates; CI semantic digest **`23d3cf13b92f4a1e172c7611f69cba90ea9259c6914051ea444d83d505c6ea6b`**. Manual **CONDITIONAL / NOT TRIGGERED**.",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    text = text.replace(
        "- Status: **IN_PROGRESS**. START plan + continuity status synchronization is completed before implementation. Manual starts **CONDITIONAL / NOT TRIGGERED**.",
        "- Status: **COMPLETE / FINAL EVIDENCE RE-GATES PENDING**. START synchronization is complete; accepted immutable technical source **`56f829f4395138bf90a1a8e0003bff95b67dd878`** passed all 12 required exact-head gates. Manual remains **CONDITIONAL / NOT TRIGGERED**.",
        1,
    )
    marker = "- Frozen objective: close R13 with adversarial, anti-circular integrated acceptance"
    authority = (
        "- Accepted technical authority: predecessor `e6d7cb3768d80944692596ef6705f3f95a24c8da` rejected; corrected source **`56f829f4395138bf90a1a8e0003bff95b67dd878`** accepted after R0 #1731, Python #1705, UI #1672, Android Build #301, Signing #254, Device #239, Play #222, Xcode #205, SwiftUI #176, Apple Signing #151, XCTest #131 and Integrated #4 all SUCCESS. `R13_17_CI_ACCEPTANCE.json` semantic digest is **`23d3cf13b92f4a1e172c7611f69cba90ea9259c6914051ea444d83d505c6ea6b`** and binds Android Build artifact `9665811449`, Android Device `9665845148`, Apple XCTest `9665853659`.\n"
    )
    if authority not in text:
        pos = text.find(marker)
        if pos < 0:
            raise SystemExit("continuity R13.17 insertion marker drift")
        text = text[:pos] + authority + text[pos:]
    text = text.replace(
        "| R13.17 | Adversarial hardening + Android/iOS integrated release-readiness acceptance | IN_PROGRESS | CONDITIONAL |",
        "| R13.17 | Adversarial hardening + Android/iOS integrated release-readiness acceptance | COMPLETE | CONDITIONAL |",
        1,
    )
    text = re.sub(
        r"## Next authorized action\n\n.*\Z",
        "## Next authorized action\n\nGenerate and verify `docs/roadmap/R13_INTEGRATED_ACCEPTANCE.json` from the end-synchronized repository bytes with immutable source `56f829f4395138bf90a1a8e0003bff95b67dd878`, then freeze the resulting documentation/evidence head. Require fresh exact-head R0 Repository Guard, full Python Core, KodeStudio UI Smoke, Android Build/Signing/Device/Google Play, Apple Xcode/SwiftUI/Signing/XCTest, and R13 Integrated Release Readiness on that final head. If every gate is SUCCESS, merge PR #253 with `expected_head_sha` equal to that exact final head. Then create exactly one continuity-only R13 normalization branch from the merge; it must pass fresh R0 + full Python Core + KodeStudio UI Smoke and merge before R13 is `COMPLETE + NORMALIZED` and R14 planning becomes authorized. Manual remains CONDITIONAL / NOT TRIGGERED unless a frozen claim unexpectedly requires physical/live-account proof.\n",
        text,
        count=1,
        flags=re.DOTALL,
    )
    if text == original:
        raise SystemExit("continuity end-sync made no changes")
    path.write_text(text, encoding="utf-8")


def main() -> None:
    sync_acceptance()
    sync_plan()
    sync_continuity()
    subprocess.run(
        [
            "python",
            "scripts/r13_17_build_integrated_report.py",
            "--source-sha",
            SOURCE_SHA,
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
