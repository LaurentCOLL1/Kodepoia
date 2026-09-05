from __future__ import annotations

import re
from pathlib import Path

BASE = "66314ff1c86e51d84f1abe15d107a6182ef9e54a"
BRANCH = "r18/04-windows-authenticode-signing"
ROADMAP = Path("docs/roadmap/R18_PLAN.md")
CONTINUITY = Path("docs/continuity/KODEPOIA_CONTINUITY.md")


def replace_one(text: str, pattern: str, replacement: str, label: str, flags: int = 0) -> str:
    out, n = re.subn(pattern, replacement, text, count=1, flags=flags)
    if n != 1:
        raise SystemExit(f"{label}: expected one match, got {n}")
    return out


def main() -> int:
    roadmap = ROADMAP.read_text(encoding="utf-8")
    roadmap = replace_one(
        roadmap,
        r"Roadmap status: planning is \*\*ACCEPTED \+ NORMALIZED\*\*.*?The frozen v1\.0/R1–R16 architecture and history are not rewritten\.",
        "Roadmap status: planning is **ACCEPTED + NORMALIZED**. R18.1–R18.3 are **COMPLETE + NORMALIZED**; R18.3 canonical normalized `main` is `" + BASE + "`. R18.4 Windows Authenticode signing and verification boundary is **IN_PROGRESS** from that exact normalized main on `" + BRANCH + "`. R18.5 remains PLANNED and unauthorized until R18.4 implementation/evidence merge plus its unique post-merge normalization complete. The frozen v1.0/R1–R16 architecture and history are not rewritten.",
        "roadmap headline",
    )
    roadmap = replace_one(
        roadmap,
        r"\| R18\.4 \| Windows Authenticode signing and verification boundary \| PLANNED \| CONDITIONAL \| R18\.2–R18\.3 \|",
        "| R18.4 | Windows Authenticode signing and verification boundary | IN_PROGRESS | CONDITIONAL | R18.2–R18.3 |",
        "roadmap index",
    )
    marker = "## Dependencies and prerequisites\n\nR18.2 release bundle + R18.3 provenance. Windows SDK/SignTool available in Windows CI or discovered from installed SDK."
    insert = marker + "\n\nSTART-sync authority: R18.4 begins only from R18.3 COMPLETE + NORMALIZED canonical `main` `" + BASE + "` on dedicated branch `" + BRANCH + "`. Current Microsoft SignTool guidance was revalidated on 2026-09-05: file signing explicitly uses `/fd SHA256`; RFC3161 timestamping, when production signing is explicitly exercised, uses `/tr` with `/td SHA256`; verification must inspect the actual PE signature. Production credentials belong only behind an approved CI secret/key-provider boundary. Repository metadata alone can never set `production_signed=true`. The authoritative acceptance path for this subdivision is unsigned + ephemeral non-production test-sign; production signing, public GitHub Release publication and public WinGet submission remain NOT TRIGGERED."
    roadmap = replace_one(roadmap, re.escape(marker), insert, "R18.4 start authority")
    ROADMAP.write_text(roadmap, encoding="utf-8", newline="\n")

    continuity = CONTINUITY.read_text(encoding="utf-8")
    continuity = replace_one(
        continuity,
        r"> Kodepoia, architecture v1\.0 gelée\. \*\*.*?\*\* Production signing, public GitHub Release publication and public WinGet submission remain CONDITIONAL / NOT TRIGGERED\.",
        "> Kodepoia, architecture v1.0 gelée. **R1–R17 COMPLETE + NORMALIZED. R18 planning ACCEPTED + NORMALIZED. R18.1–R18.3 COMPLETE + NORMALIZED. R18.3 canonical normalized `main` is `' + BASE + '`. R18.4 Windows Authenticode signing and verification boundary is STARTED / IN_PROGRESS from that exact normalized main on `' + BRANCH + '`. R18.5 remains PLANNED and unauthorized until R18.4 implementation/evidence merge plus unique post-merge normalization complete.** Production signing, public GitHub Release publication and public WinGet submission remain CONDITIONAL / NOT TRIGGERED.',
        "continuity headline",
    )
    if re.search(r"^- R18\.4 :", continuity, flags=re.MULTILINE):
        continuity = replace_one(
            continuity,
            r"^- R18\.4 : .*?$",
            "- R18.4 : **STARTED / IN_PROGRESS** — authorized base R18.3 COMPLETE + NORMALIZED `main` `" + BASE + "`; dedicated branch `" + BRANCH + "`. Scope: truthful Windows Authenticode signing/verification boundary, `SigningEvidence`, unsigned preservation, ephemeral test-sign CI, tamper/wrong-identity/invalid-validity fail-closed checks and optional RFC3161 production configuration. Manual intervention remains CONDITIONAL only if a real production Authenticode identity is explicitly chosen; currently NONE. `production_signed=false`; production signing/public GitHub Release/public WinGet submission NOT TRIGGERED.",
            "continuity R18.4 state",
            flags=re.MULTILINE,
        )
    else:
        anchor = re.search(r"^- R18\.3 : .*?$", continuity, flags=re.MULTILINE)
        if anchor is None:
            raise SystemExit("continuity R18.3 state missing")
        line = "\n- R18.4 : **STARTED / IN_PROGRESS** — authorized base R18.3 COMPLETE + NORMALIZED `main` `" + BASE + "`; dedicated branch `" + BRANCH + "`. Manual currently NONE; production identity remains CONDITIONAL / NOT TRIGGERED."
        continuity = continuity[:anchor.end()] + line + continuity[anchor.end():]
    continuity = replace_one(
        continuity,
        r"(## Next authorized action\n\n).*?(?=\n## |\Z)",
        r"\1R18.4 is the current authorized subdivision from exact normalized `main` `" + BASE + "`. Implement and validate the unsigned + ephemeral test-sign Authenticode boundary on `" + BRANCH + "`; require actual PE signature verification and fail-closed identity/validity/tamper checks. Production credentials/private keys must never enter Git, logs or prompts and production signing remains NOT TRIGGERED. R18.5 remains unauthorized until R18.4 exact-head implementation/evidence merge and its unique post-merge continuity normalization complete.\n",
        "next action",
        flags=re.DOTALL,
    )
    CONTINUITY.write_text(continuity, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
