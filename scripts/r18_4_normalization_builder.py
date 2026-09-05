from __future__ import annotations

from pathlib import Path
import re

IMPLEMENTATION_MAIN = "8b5e09622399d24f87c20a3820e38111d3072b6e"
END_HEAD = "2cad928d86af244a32313587348a4cb989b1ca71"
CONTINUITY = Path("docs/continuity/KODEPOIA_CONTINUITY.md")


def replace_one(pattern: str, replacement: str, text: str, label: str) -> str:
    text, count = re.subn(pattern, replacement, text, count=1, flags=re.M)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, got {count}")
    return text


def main() -> None:
    text = CONTINUITY.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or not lines[0].startswith("> Kodepoia, architecture v1.0 gelée."):
        raise RuntimeError("continuity header not found")
    if "R18.4 Windows Authenticode signing and verification boundary is COMPLETE at END-sync" not in lines[0]:
        raise RuntimeError("R18.4 END-sync header authority not found")

    lines[0] = (
        "> Kodepoia, architecture v1.0 gelée. **R1–R17 COMPLETE + NORMALIZED. R18 planning ACCEPTED + NORMALIZED. "
        "R18.1 Canonical release identity, versions and channels is COMPLETE + NORMALIZED on canonical `main` `c611131268041b06f53de66eaadd45120e2b750d`. "
        "R18.2 Deterministic release bundle and manifest contract is COMPLETE + NORMALIZED on canonical `main` `c376d0af789e584e1ef307f43e42a62ce024b052`. "
        "R18.3 SBOM, provenance and artifact attestations is COMPLETE + NORMALIZED on canonical `main` `66314ff1c86e51d84f1abe15d107a6182ef9e54a` after implementation/evidence PR #386 and unique normalization PR #388. "
        "R18.4 Windows Authenticode signing and verification boundary is COMPLETE + NORMALIZED effective when this unique continuity-only normalization record enters `main` through fresh exact-head R0/Python/UI gates and exact expected-head merge; immutable technical source `760d03efd2acdc372ed1e75f064f66d41c82573e`, final exact-END `2cad928d86af244a32313587348a4cb989b1ca71`, implementation/evidence PR #389 merged as `main` `8b5e09622399d24f87c20a3820e38111d3072b6e`. "
        "R18.5 remains PLANNED and is authorized only from the normalized `main` produced when this exact normalization record merges.** Production signing, public GitHub Release publication and public WinGet submission remain CONDITIONAL / NOT TRIGGERED."
    )
    text = "\n".join(lines) + "\n"

    r18_4_bullet = (
        "- R18.4 : **COMPLETE + NORMALIZED effective when this unique continuity-only normalization record enters `main` through fresh exact-head R0/Python/UI gates and exact expected-head merge** — "
        "immutable technical source `760d03efd2acdc372ed1e75f064f66d41c82573e`; authoritative technical R18.4 run `33968800040` SUCCESS for focused contracts and actual Windows Authenticode test-signing; real `KodepoiaStudio.exe` + rebuilt `KodepoiaSetup.exe` both Authenticode `Valid`, SignTool verified and RFC3161 timestamp verified; hashed-section tamper fails closed with WinVerifyTrust `0x80096010`. "
        "Final exact-END `2cad928d86af244a32313587348a4cb989b1ca71` passed R18.4 `33971108687`, R16.9 `33971108772`, R0 `33971108746`, full Python Core `33971108760` and KodeStudio UI Smoke `33971108733`, all SUCCESS. PR #389 merged that exact head with expected-head protection as implementation/evidence `main` `8b5e09622399d24f87c20a3820e38111d3072b6e`. "
        "Actions artifact `9970604356`, ZIP digest `sha256:8410a8d469fdcbaf98889017e08933a90e19174907aa38576d4ecef7ec112b27`. Test signer only; `production_signed=false`, `public_trust_claim=false`; production signing/public GitHub Release/public WinGet remain CONDITIONAL / NOT TRIGGERED. This record is the single authorized post-merge continuity-only R18.4 normalization authority; no second R18.4 normalization is authorized. R18.5 START-sync is authorized only from the normalized `main` produced when this exact record passes fresh R0/Python/UI and merges with exact expected-head protection."
    )
    text = replace_one(r"^- R18\.4 :.*$", r18_4_bullet, text, "global R18.4 bullet")

    r18_heading = "## R18 — Trusted Release, Updates & Distribution Channels"
    pos = text.index(r18_heading)
    tail = text[pos:]
    state = (
        "- State: **IN_PROGRESS** — planning, R18.1, R18.2 and R18.3 are COMPLETE + NORMALIZED. R18.4 implementation/evidence is merged on `main` `8b5e09622399d24f87c20a3820e38111d3072b6e`; this unique post-merge continuity-only normalization is the sole remaining R18.4 action. "
        "Final exact-END `2cad928d86af244a32313587348a4cb989b1ca71` passed R18.4 `33971108687`, R16.9 `33971108772`, R0 `33971108746`, Python Core `33971108760` and UI `33971108733`. R18.5–R18.11 remain PLANNED; R18.5 is unauthorized until this normalization passes fresh R0/Python/UI and merges exact-head."
    )
    tail = replace_one(r"^- State:.*$", state, tail, "R18 State bullet")
    text = text[:pos] + tail

    authority_start = text.index("## R18.4 END authority")
    r17_start = text.index("## R17 — Distribution & Guided Creation UX", authority_start)
    normalization_section = """## R18.4 normalization authority

- R18.4 state: **COMPLETE + NORMALIZED effective when this unique continuity-only normalization record enters `main` through fresh exact-head R0/Python/UI gates and exact expected-head merge**. Core/test acceptance requires no manual action. The real production-signing effect remains **CONDITIONAL / NOT TRIGGERED**.
- Exact normalized R18.3 base: `main` `66314ff1c86e51d84f1abe15d107a6182ef9e54a`; dedicated implementation branch `r18/04-windows-authenticode-signing`; immutable R18.4 technical source `760d03efd2acdc372ed1e75f064f66d41c82573e`.
- Authoritative technical R18.4 push run `33968800040` is SUCCESS: Ubuntu + Windows focused contracts and actual Windows end-to-end test-signing all passed. The actual path built the unsigned exact-source installer, created an ephemeral CI-only test certificate, signed `KodepoiaStudio.exe` with SHA-256 + RFC3161, rebuilt `KodepoiaSetup.exe` around the signed standalone executable, signed the rebuilt installer, verified both subjects, proved hashed-section tamper fail-closed, removed the certificate and uploaded evidence.
- `KodepoiaStudio.exe`: pre-sign SHA-256 `25d963bcc34ccfb323301007f9c25a61f991b01a7f7ad722f6e50050ce059e39`; post-sign `7fed4821908e3f898be6966f157087b96ed9cb1501970b686b2f905e9f0691fa`; Authenticode `Valid`; SignTool verified; timestamp verified.
- `KodepoiaSetup.exe`: pre-sign SHA-256 `71656ab41d208244e38ad0bfb9cbd49d76a57c6a29b4fe8ada32217c6b0c1c73`; post-sign `8de3ac7911b290e97b75aa0082fab6505bd79c952c7b15e51b2e20b046ed2b5d`; Authenticode `Valid`; SignTool verified; timestamp verified.
- Test certificate public identity: `CN=Kodepoia R18.4 CI Test Signing`; thumbprint `5C904F3DDF1276533C7D2281F9A796D1BE66B03F`; `production_signed=false`; `public_trust_claim=false`. RFC3161 timestamp responder evidence is present and the ephemeral certificate was removed from the runner stores after verification.
- Negative control mutated PE section 0 at offset 1040; SignTool verification returned failure and WinVerifyTrust `0x80096010`, so a content mutation inside the signed image fails closed.
- Technical Actions artifact: ID `9970604356`, name `r18-4-authenticode-760d03efd2acdc372ed1e75f064f66d41c82573e`, 33,542,746 bytes, ZIP digest `sha256:8410a8d469fdcbaf98889017e08933a90e19174907aa38576d4ecef7ec112b27`.
- Same-source technical broad gates are SUCCESS: R0 Repository Guard `33968802338`; full Python Core `33968802320` 5/5; KodeStudio UI Smoke `33968802246`; R16.9 `33968802353`.
- Final exact-END head `2cad928d86af244a32313587348a4cb989b1ca71` is the single documentation-only child of the immutable technical source. Fresh exact-END gates all passed on that exact SHA: R18.4 `33971108687`, R16.9 `33971108772`, R0 `33971108746`, full Python Core `33971108760`, KodeStudio UI Smoke `33971108733`.
- PR #389 merged only that exact head with `expected_head_sha=2cad928d86af244a32313587348a4cb989b1ca71` as implementation/evidence `main` `8b5e09622399d24f87c20a3820e38111d3072b6e`.
- This file is the **single authorized post-merge continuity-only R18.4 normalization record**. It must be the only file changed from implementation/evidence `main` `8b5e09622399d24f87c20a3820e38111d3072b6e`; its exact head must pass fresh R0 Repository Guard, full Python Core and KodeStudio UI Smoke before exact expected-head merge. No second R18.4 normalization is authorized.
- Only the canonical `main` produced by that exact gated normalization merge establishes R18.4 **COMPLETE + NORMALIZED** and authorizes R18.5 START-sync. Production signing, public GitHub Release publication and public WinGet submission remain CONDITIONAL / NOT TRIGGERED.

## Next authorized action

R18.4 post-merge normalization exact-head gating is the sole next action: fresh R0 Repository Guard + full Python Core + KodeStudio UI Smoke on this continuity-only normalization head, followed by exact `expected_head_sha` merge. R18.5 START-sync is authorized only from the canonical normalized `main` produced by that merge. Production signing, public GitHub Release publication and public WinGet submission remain CONDITIONAL / NOT TRIGGERED.

"""
    text = text[:authority_start] + normalization_section + text[r17_start:]

    if text.count("single authorized post-merge continuity-only R18.4 normalization") != 1:
        raise RuntimeError("R18.4 normalization authority marker count is not exactly one")
    if "R18.5 START-sync is authorized only from the canonical normalized `main` produced by that merge" not in text:
        raise RuntimeError("R18.5 authorization guard missing")
    if "production_signed=false" not in text or "public_trust_claim=false" not in text:
        raise RuntimeError("signing truth markers missing")

    CONTINUITY.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
