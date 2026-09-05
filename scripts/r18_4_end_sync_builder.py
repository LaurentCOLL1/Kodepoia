from __future__ import annotations

from pathlib import Path
import re

TECH_HEAD = "760d03efd2acdc372ed1e75f064f66d41c82573e"
ROADMAP = Path("docs/roadmap/R18_PLAN.md")
CONTINUITY = Path("docs/continuity/KODEPOIA_CONTINUITY.md")


def patch_roadmap() -> None:
    text = ROADMAP.read_text(encoding="utf-8")
    text = re.sub(
        r"^Roadmap status:.*$",
        "Roadmap status: planning is **ACCEPTED + NORMALIZED** on `main` `bbffc382d4fb8a7d947345da11b56459d0fec825`. R18.1 is COMPLETE + NORMALIZED on canonical `main` `c611131268041b06f53de66eaadd45120e2b750d`. R18.2 is **COMPLETE + NORMALIZED** on canonical `main` `c376d0af789e584e1ef307f43e42a62ce024b052`. R18.3 SBOM, provenance and artifact attestations is **COMPLETE + NORMALIZED** on canonical `main` `66314ff1c86e51d84f1abe15d107a6182ef9e54a` after implementation/evidence PR #386 and unique continuity-only normalization PR #388. R18.4 Windows Authenticode signing and verification boundary is **COMPLETE at END-sync** on immutable technical source `760d03efd2acdc372ed1e75f064f66d41c82573e`; fresh exact-END gates, PR #389 exact-head merge and the unique post-merge continuity normalization remain required. R18.5 remains PLANNED and is not authorized until that normalization completes. The frozen v1.0/R1–R16 architecture and history are not rewritten.",
        text,
        count=1,
        flags=re.M,
    )
    old_row = "| R18.4 | Windows Authenticode signing and verification boundary | PLANNED | CONDITIONAL | R18.2–R18.3 |"
    new_row = "| R18.4 | Windows Authenticode signing and verification boundary | COMPLETE at END-sync | CONDITIONAL / NOT TRIGGERED | R18.2–R18.3 |"
    if old_row not in text:
        raise RuntimeError("R18.4 index row not found")
    text = text.replace(old_row, new_row, 1)

    marker = "\n## Rollback / recovery\n"
    r3_start = text.index("# R18.3 — SBOM, provenance and artifact attestations")
    r4_start = text.index("# R18.4 — Windows Authenticode signing and verification boundary")
    r3 = text[r3_start:r4_start]
    r3_completion = (
        "\nPost-merge completion: final exact-END `4d28a1c5a8f9763d8d620b581a9a6222c7c9cd31` passed specialized R18.3 run `33956408408` and broad exact-END gate run `33956444966` with all 7 required jobs SUCCESS. PR #386 merged that exact head with expected-head protection as implementation/evidence `main` `6a6c1a523cb3b96949fd4a072d2bd33ba175749c`. Unique post-merge continuity-only normalization PR #388 at head `5fd8cae770997af88d057a720ed6a1f16148cd01` passed fresh R0 Repository Guard `33957456524` Ubuntu + Windows, full Python Core `33957456658` and KodeStudio UI Smoke `33957456505`, then merged with exact expected-head protection as canonical normalized `main` `66314ff1c86e51d84f1abe15d107a6182ef9e54a`. R18.3 is therefore COMPLETE + NORMALIZED; no second R18.3 normalization is authorized.\n"
    )
    if "Post-merge completion: final exact-END `4d28a1c5" not in r3:
        if marker not in r3:
            raise RuntimeError("R18.3 rollback marker not found")
        r3 = r3.replace(marker, r3_completion + marker, 1)
        text = text[:r3_start] + r3 + text[r4_start:]

    r4_start = text.index("# R18.4 — Windows Authenticode signing and verification boundary")
    r5_start = text.index("# R18.5 — Immutable GitHub Release staging and promotion")
    r4 = text[r4_start:r5_start]
    r4_acceptance = (
        "\nEND-sync technical acceptance: immutable technical source `760d03efd2acdc372ed1e75f064f66d41c82573e`; authoritative R18.4 push run `33968800040` completed SUCCESS for Ubuntu + Windows focused contracts and the actual Windows test-signing path. The Windows path built the unsigned exact-source installer, created an ephemeral CI-only test certificate, test-signed `KodepoiaStudio.exe`, rebuilt `KodepoiaSetup.exe` around that signed standalone executable, test-signed the rebuilt installer with SHA-256 and RFC3161, then verified both subjects as Authenticode `Valid`, SignTool-verified and timestamp-verified. `KodepoiaStudio.exe` changed from pre-sign SHA-256 `25d963bcc34ccfb323301007f9c25a61f991b01a7f7ad722f6e50050ce059e39` to post-sign `7fed4821908e3f898be6966f157087b96ed9cb1501970b686b2f905e9f0691fa`; `KodepoiaSetup.exe` changed from `71656ab41d208244e38ad0bfb9cbd49d76a57c6a29b4fe8ada32217c6b0c1c73` to `8de3ac7911b290e97b75aa0082fab6505bd79c952c7b15e51b2e20b046ed2b5d`. The PE hashed-section tamper negative control at section 0 / offset 1040 failed closed with SignTool verify failure and WinVerifyTrust `0x80096010`. CI signer identity is `CN=Kodepoia R18.4 CI Test Signing`, public thumbprint `5C904F3DDF1276533C7D2281F9A796D1BE66B03F`; `production_signed=false`, `public_trust_claim=false`; the ephemeral certificate was removed after acceptance. Actions artifact `9970604356` / `r18-4-authenticode-760d03efd2acdc372ed1e75f064f66d41c82573e` is 33,542,746 bytes with artifact ZIP digest `sha256:8410a8d469fdcbaf98889017e08933a90e19174907aa38576d4ecef7ec112b27`. Exact technical-head gates R0 Repository Guard #2465 / `33968802338`, full Python Core #2437 / `33968802320` 5/5, KodeStudio UI Smoke #2402 / `33968802246`, and R16.9 #128 / `33968802353` are SUCCESS. Manual production-signing state remains CONDITIONAL / NOT TRIGGERED; public GitHub Release publication and public WinGet submission remain NOT TRIGGERED. Because this END-sync changes documentation bytes, fresh R18.4 + R16.9 + R0 + full Python Core + KodeStudio UI Smoke gates on the resulting exact END-head are mandatory before PR #389 may merge with `expected_head_sha`; exactly one post-merge continuity-only R18.4 normalization must then pass fresh R0/Python/UI before R18.5 START is authorized.\n"
    )
    if "END-sync technical acceptance: immutable technical source `760d03ef" not in r4:
        if marker not in r4:
            raise RuntimeError("R18.4 rollback marker not found")
        r4 = r4.replace(marker, r4_acceptance + marker, 1)
        text = text[:r4_start] + r4 + text[r5_start:]

    ROADMAP.write_text(text, encoding="utf-8", newline="\n")


def patch_continuity() -> None:
    text = CONTINUITY.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or not lines[0].startswith("> Kodepoia, architecture v1.0 gelée."):
        raise RuntimeError("continuity header not found")
    lines[0] = (
        "> Kodepoia, architecture v1.0 gelée. **R1–R17 COMPLETE + NORMALIZED. R18 planning ACCEPTED + NORMALIZED. "
        "R18.1 Canonical release identity, versions and channels is COMPLETE + NORMALIZED on canonical `main` `c611131268041b06f53de66eaadd45120e2b750d`. "
        "R18.2 Deterministic release bundle and manifest contract is COMPLETE + NORMALIZED on canonical `main` `c376d0af789e584e1ef307f43e42a62ce024b052`. "
        "R18.3 SBOM, provenance and artifact attestations is COMPLETE + NORMALIZED on canonical `main` `66314ff1c86e51d84f1abe15d107a6182ef9e54a` after implementation/evidence PR #386 and unique normalization PR #388. "
        "R18.4 Windows Authenticode signing and verification boundary is COMPLETE at END-sync on immutable technical source `760d03efd2acdc372ed1e75f064f66d41c82573e`; fresh exact-END gates, PR #389 merge and the unique post-merge continuity-only normalization remain required. "
        "R18.5 remains PLANNED and unauthorized until that normalization completes.** Production signing, public GitHub Release publication and public WinGet submission remain CONDITIONAL / NOT TRIGGERED."
    )
    text = "\n".join(lines) + "\n"

    text, count = re.subn(
        r"^- R18\.3 :.*$",
        "- R18.3 : **COMPLETE + NORMALIZED** — final exact-END `4d28a1c5a8f9763d8d620b581a9a6222c7c9cd31`; specialized run `33956408408` and broad 7-job run `33956444966` SUCCESS; PR #386 merged exact head as implementation/evidence `main` `6a6c1a523cb3b96949fd4a072d2bd33ba175749c`; unique normalization head `5fd8cae770997af88d057a720ed6a1f16148cd01` passed fresh R0 `33957456524`, Python Core `33957456658` and UI `33957456505`, then PR #388 merged exact head as canonical normalized `main` `66314ff1c86e51d84f1abe15d107a6182ef9e54a`. No second R18.3 normalization is authorized.\n- R18.4 : **COMPLETE at END-sync** — immutable technical source `760d03efd2acdc372ed1e75f064f66d41c82573e`; authoritative push run `33968800040` SUCCESS for both focused contracts and actual Windows Authenticode test-signing; real `KodepoiaStudio.exe` + rebuilt `KodepoiaSetup.exe` both Authenticode `Valid`, SignTool verified and RFC3161 timestamp verified; hashed-section tamper fails closed with WinVerifyTrust `0x80096010`; technical R0 `33968802338`, Python Core `33968802320` 5/5, UI `33968802246` and R16.9 `33968802353` SUCCESS. Artifact `9970604356`, ZIP digest `sha256:8410a8d469fdcbaf98889017e08933a90e19174907aa38576d4ecef7ec112b27`. Test signer only; `production_signed=false`, `public_trust_claim=false`; production signing/public GitHub Release/public WinGet remain CONDITIONAL / NOT TRIGGERED. Fresh exact-END gates + PR #389 exact-head merge + one post-merge normalization remain required before R18.5.",
        text,
        count=1,
        flags=re.M,
    )
    if count != 1:
        raise RuntimeError(f"expected one global R18.3 bullet, got {count}")

    r18_heading = "## R18 — Trusted Release, Updates & Distribution Channels"
    pos = text.index(r18_heading)
    tail = text[pos:]
    tail, count = re.subn(
        r"^- State:.*$",
        "- State: **IN_PROGRESS** — planning, R18.1, R18.2 and R18.3 are COMPLETE + NORMALIZED; canonical normalized R18.3 `main` is `66314ff1c86e51d84f1abe15d107a6182ef9e54a`. R18.4 is COMPLETE at END-sync on immutable technical source `760d03efd2acdc372ed1e75f064f66d41c82573e`; fresh exact-END gates, PR #389 exact-head merge and unique post-merge normalization remain required. R18.5–R18.11 remain PLANNED; R18.5 is unauthorized until R18.4 normalization completes.",
        tail,
        count=1,
        flags=re.M,
    )
    if count != 1:
        raise RuntimeError("R18 State bullet not found")
    text = text[:pos] + tail

    next_heading = "## Next authorized action"
    next_pos = text.index(next_heading)
    r17_pos = text.index("## R17 — Distribution & Guided Creation UX", next_pos)
    end_section = """## R18.4 END authority

- R18.4 state: **COMPLETE at END-sync**; core/test acceptance requires no manual action. The real production-signing effect remains **CONDITIONAL / NOT TRIGGERED**. R18.5 remains PLANNED and unauthorized.
- Exact normalized R18.3 base: `main` `66314ff1c86e51d84f1abe15d107a6182ef9e54a`; dedicated implementation branch `r18/04-windows-authenticode-signing`; immutable technical source `760d03efd2acdc372ed1e75f064f66d41c82573e`.
- Authoritative technical R18.4 push run `33968800040` is SUCCESS: Ubuntu + Windows focused contracts and actual Windows end-to-end test-signing all passed. The actual path built the unsigned exact-source installer, created an ephemeral CI-only test certificate, signed `KodepoiaStudio.exe` with SHA-256 + RFC3161, rebuilt `KodepoiaSetup.exe` around the signed standalone executable, signed the rebuilt installer, verified both subjects, proved hashed-section tamper fail-closed, removed the certificate and uploaded evidence.
- `KodepoiaStudio.exe`: pre-sign SHA-256 `25d963bcc34ccfb323301007f9c25a61f991b01a7f7ad722f6e50050ce059e39`; post-sign `7fed4821908e3f898be6966f157087b96ed9cb1501970b686b2f905e9f0691fa`; Authenticode `Valid`; SignTool verified; timestamp verified.
- `KodepoiaSetup.exe`: pre-sign SHA-256 `71656ab41d208244e38ad0bfb9cbd49d76a57c6a29b4fe8ada32217c6b0c1c73`; post-sign `8de3ac7911b290e97b75aa0082fab6505bd79c952c7b15e51b2e20b046ed2b5d`; Authenticode `Valid`; SignTool verified; timestamp verified.
- Test certificate public identity: `CN=Kodepoia R18.4 CI Test Signing`; thumbprint `5C904F3DDF1276533C7D2281F9A796D1BE66B03F`; `production_signed=false`; `public_trust_claim=false`. RFC3161 timestamp responder evidence is present and the ephemeral certificate was removed from the runner stores after verification.
- Negative control mutated PE section 0 at offset 1040; SignTool verification returned failure and WinVerifyTrust `0x80096010`, so a content mutation inside the signed image fails closed.
- Technical Actions artifact: ID `9970604356`, name `r18-4-authenticode-760d03efd2acdc372ed1e75f064f66d41c82573e`, 33,542,746 bytes, ZIP digest `sha256:8410a8d469fdcbaf98889017e08933a90e19174907aa38576d4ecef7ec112b27`.
- Same-source broad gates are SUCCESS: R0 Repository Guard #2465 / `33968802338`; full Python Core #2437 / `33968802320` 5/5; KodeStudio UI Smoke #2402 / `33968802246`; R16.9 #128 / `33968802353`.
- This END-sync must be exactly one documentation-only child of immutable technical source `760d03efd2acdc372ed1e75f064f66d41c82573e`, changing only `docs/roadmap/R18_PLAN.md` and this continuity file. Its exact resulting head must pass fresh R18.4 actual Windows acceptance, R16.9, R0, full Python Core and KodeStudio UI Smoke before PR #389 may merge with `expected_head_sha` equal to that exact head.
- Exactly one post-merge continuity-only R18.4 normalization is authorized. Only its fresh exact-head R0/Python/UI-gated exact expected-head merge may establish R18.4 **COMPLETE + NORMALIZED** and authorize R18.5 START.

## Next authorized action

R18.4 END-sync exact-head gating is the sole next action: fresh R18.4 actual Windows signing acceptance + R16.9 + R0 + full Python Core + KodeStudio UI Smoke on the resulting exact END head, followed by PR #389 merge with exact `expected_head_sha`, then exactly one post-merge continuity-only normalization with fresh R0/Python/UI. R18.5 START-sync is authorized only from the canonical normalized `main` produced by that normalization. Production signing, public GitHub Release publication and public WinGet submission remain CONDITIONAL / NOT TRIGGERED.

"""
    text = text[:next_pos] + end_section + text[r17_pos:]
    CONTINUITY.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    patch_roadmap()
    patch_continuity()
