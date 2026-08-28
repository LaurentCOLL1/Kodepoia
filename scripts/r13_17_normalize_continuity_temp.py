from pathlib import Path

PATH = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
text = PATH.read_text(encoding="utf-8")

text = text.replace(
    "**Dernière mise à jour : 27 août 2026**",
    "**Dernière mise à jour : 28 août 2026**",
    1,
)

lines = text.splitlines()
for i, line in enumerate(lines):
    if line.startswith("> Kodepoia, architecture v1.0 gelée."):
        lines[i] = (
            "> Kodepoia, architecture v1.0 gelée. **R1–R12 COMPLETE + NORMALIZED. "
            "R13 planning ACCEPTED + NORMALIZED. R13.1–R13.16 COMPLETE + NORMALIZED. "
            "R13.17 COMPLETE / NORMALIZATION IN_PROGRESS on `r13/17-continuity-normalization`. "
            "R13 phase implementation/evidence is COMPLETE; only the single continuity-only post-merge normalization remains.** "
            "Accepted immutable technical source `56f829f4395138bf90a1a8e0003bff95b67dd878`; final documentation/evidence head "
            "`cb0c63bcdcbaf2b58b3066d311780843c2598575` passed the complete fresh 12-workflow exact-head family: "
            "R0 #1744 / `33121176174`, Python Core #1718 / `33121176167`, UI #1685 / `33121176129`, "
            "Android Build #327 / `33121176121`, Signing #274 / `33121176137`, Device #265 / `33121176131`, "
            "Play #248 / `33121176193`, Xcode #231 / `33121176116`, SwiftUI #202 / `33121176166`, "
            "Apple Signing #177 / `33121176186`, XCTest #157 / `33121176106`, and Integrated #30 / `33121176177`, all SUCCESS. "
            "Canonical CI digest is `23d3cf13b92f4a1e172c7611f69cba90ea9259c6914051ea444d83d505c6ea6b`; "
            "canonical R13 integrated digest is `831b155fce200eae6b9fbe91c8eb44e992ea036c0922e508171644b497a4c3c7` with `status=pass`, `blockers=[]`. "
            "PR #253 merged with `expected_head_sha=cb0c63bcdcbaf2b58b3066d311780843c2598575` as implementation/evidence merge "
            "`f56c61dbc82efd93c08e2b29ad1acff33219689f`. The single allowed branch `r13/17-continuity-normalization` starts exactly from that merge and must change only continuity, "
            "pass fresh exact-head R0 + full Python Core + KodeStudio UI Smoke, then merge with `expected_head_sha` before R13 is `COMPLETE + NORMALIZED` and R14 planning is authorized. "
            "Manual remains CONDITIONAL / NOT TRIGGERED; Android proof is VIRTUAL/API 36 and Apple proof SIMULATOR, with no physical-device, live-store or production-signing claim."
        )
        break
else:
    raise SystemExit("prompt line not found")

for i, line in enumerate(lines):
    if line.startswith("- R13 phase status:"):
        lines[i] = "- R13 phase status: **COMPLETE / NORMALIZATION IN_PROGRESS**."
    elif line.startswith("- R13.17:"):
        lines[i] = (
            "- R13.17: **COMPLETE / NORMALIZATION IN_PROGRESS**. Final documentation/evidence head "
            "**`cb0c63bcdcbaf2b58b3066d311780843c2598575`** passed all 12 fresh exact-head final gates; "
            "PR #253 merged with exact-head protection as **`f56c61dbc82efd93c08e2b29ad1acff33219689f`**. "
            "Single continuity-only normalization branch **`r13/17-continuity-normalization`** starts exactly from that merge. "
            "Manual **CONDITIONAL / NOT TRIGGERED**."
        )
    elif line.startswith("- R14 planning:"):
        lines[i] = "- R14 planning: **FORBIDDEN until the R13.17 continuity-only normalization passes fresh gates and merges**."

text = "\n".join(lines)
start = text.index("## R13.17 execution authority")
end = text.index("## Frozen R13 subdivision index", start)
replacement = """## R13.17 normalization authority

- Authorized normalized base before R13.17: **`b202af1b4d6fd8d34e351c710db4c0ec719dd8f4`**, produced by R13.16 normalization PR #252.
- Dedicated implementation branch: **`r13/17-integrated-release-readiness`**; implementation/evidence PR **#253**.
- Rejected predecessor **`e6d7cb3768d80944692596ef6705f3f95a24c8da`** is not reusable for decision authority: its Android integrated build/collection succeeded, but the workflow assertion read `target_sdk` from the wrong JSON level.
- Accepted immutable technical source **`56f829f4395138bf90a1a8e0003bff95b67dd878`** passed the complete required candidate family. Checked-in `R13_17_CI_ACCEPTANCE.json` binds the accepted runs and immutable Android Build/Device + Apple XCTest artifacts with semantic digest **`23d3cf13b92f4a1e172c7611f69cba90ea9259c6914051ea444d83d505c6ea6b`**.
- Canonical `docs/roadmap/R13_INTEGRATED_ACCEPTANCE.json` has **`status=pass`**, **`blockers=[]`**, immutable technical `source_sha=56f829f4395138bf90a1a8e0003bff95b67dd878`, and semantic digest **`831b155fce200eae6b9fbe91c8eb44e992ea036c0922e508171644b497a4c3c7`**.
- Final documentation/evidence head **`cb0c63bcdcbaf2b58b3066d311780843c2598575`** changed no accepted implementation semantics and passed fresh exact-head R0 Repository Guard #1744 / **`33121176174`**, Python Core #1718 / **`33121176167`**, KodeStudio UI Smoke #1685 / **`33121176129`**, Android Build #327 / **`33121176121`**, Android Signing #274 / **`33121176137`**, Android Device #265 / **`33121176131`**, Google Play Readiness #248 / **`33121176193`**, Apple Xcode #231 / **`33121176116`**, Apple SwiftUI #202 / **`33121176166`**, Apple Signing Archive #177 / **`33121176186`**, Apple XCTest #157 / **`33121176106`**, and R13 Integrated Release Readiness #30 / **`33121176177`**, all SUCCESS.
- Integrated #30 passed both hosted platform jobs: Android canonical APK/AAB/unit-test evidence with exact-head assertions and Apple canonical iOS Simulator XCTest with simulator-only exact-head assertions. No virtual/simulator evidence is promoted to physical-device proof.
- PR #253 merged with **`expected_head_sha=cb0c63bcdcbaf2b58b3066d311780843c2598575`** as implementation/evidence merge **`f56c61dbc82efd93c08e2b29ad1acff33219689f`**.
- Single continuity-only normalization branch **`r13/17-continuity-normalization`** was created exactly from implementation/evidence merge `f56c61dbc82efd93c08e2b29ad1acff33219689f` and is the only allowed post-merge normalization. It must change exactly `docs/continuity/KODEPOIA_CONTINUITY.md`; no plan/code/schema/test/workflow bytes are permitted in the final diff.
- Frozen core boundaries remain unchanged: Android proof is **VIRTUAL / API 36**, Apple proof is **SIMULATOR**; physical devices, live Play/App Store/TestFlight state, production signing/provisioning credentials and automatic public publication remain outside the frozen core PASS claim.
- Manual remained **CONDITIONAL / NOT TRIGGERED**. No physical device, live store account, production signing secret, Apple Developer/App Store Connect credential, paid provider quota or user-machine Android SDK/Xcode installation was required.
- R13.17 is not yet authoritatively `COMPLETE + NORMALIZED` until this single continuity-only branch passes fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke and merges with `expected_head_sha`.

"""
text = text[:start] + replacement + text[end:]

next_heading = "## Next authorized action\n\n"
idx = text.index(next_heading)
text = text[: idx + len(next_heading)] + (
    "Verify that `r13/17-continuity-normalization` differs from implementation/evidence merge "
    "`f56c61dbc82efd93c08e2b29ad1acff33219689f` by exactly `docs/continuity/KODEPOIA_CONTINUITY.md`, "
    "open the single normalization PR to `main`, pass fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke on its exact head, "
    "and merge it with `expected_head_sha`. **Only the resulting normalized `main` makes R13 authoritatively `COMPLETE + NORMALIZED` and authorizes R14 planning.** "
    "Do not modify `R13_PLAN.md`, code, tests, schemas or workflows during the final normalization. Manual remains CONDITIONAL / NOT TRIGGERED.\n"
)

PATH.write_text(text, encoding="utf-8")
