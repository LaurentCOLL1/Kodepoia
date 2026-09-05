from pathlib import Path

PATH = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
lines = PATH.read_text(encoding="utf-8").splitlines()

assert lines and lines[0].startswith("> Kodepoia, architecture v1.0 gelée.")
lines[0] = (
    "> Kodepoia, architecture v1.0 gelée. **R1–R17 COMPLETE + NORMALIZED. "
    "R18 planning ACCEPTED + NORMALIZED. R18.1 Canonical release identity, versions and channels is "
    "COMPLETE + NORMALIZED on canonical `main` `c611131268041b06f53de66eaadd45120e2b750d` after "
    "implementation/evidence PR #382 and the unique exact-head gated normalization PR #383. "
    "R18.2 Deterministic release bundle and manifest contract is STARTED from that exact normalized main on "
    "`r18/02-deterministic-release-bundle`.** Production signing, public GitHub Release publication and public "
    "WinGet submission remain CONDITIONAL / NOT TRIGGERED."
)

r181 = [i for i, line in enumerate(lines) if line.startswith("- R18.1 :")]
assert len(r181) == 1, r181
r182 = (
    "- R18.2 : **IN PROGRESS / START-SYNC** — normalized R18.1 `main` "
    "`c611131268041b06f53de66eaadd45120e2b750d`; dedicated branch "
    "`r18/02-deterministic-release-bundle`; scope frozen to deterministic release bundle and manifest contract "
    "from `docs/roadmap/R18_PLAN.md`. `ReleaseBundleManifest` must bind exact source SHA, canonical release "
    "identity, artifact names, SHA-256, sizes, roles and provenance references; the bundle must contain the "
    "installer, checksums, release manifest, required license/notices and generated release-notes metadata; "
    "verification must fail closed on path traversal, duplicate names, unexpected executables and source-SHA "
    "mismatch; deterministic ordering/timestamps and same-source two-build semantic comparison are required. "
    "The unsigned deterministic payload boundary remains separate from future signing/timestamp layers. Manual "
    "state NONE; production signing/public release/WinGet submission are not authorized by this START."
)
lines = [line for line in lines if not line.startswith("- R18.2 : **IN PROGRESS / START-SYNC**")]
r181 = next(i for i, line in enumerate(lines) if line.startswith("- R18.1 :"))
lines.insert(r181 + 1, r182)

out = "\n".join(lines) + "\n"
assert out.count("- R18.2 : **IN PROGRESS / START-SYNC**") == 1
assert "`c611131268041b06f53de66eaadd45120e2b750d`" in out
assert "r18/02-deterministic-release-bundle" in out
PATH.write_text(out, encoding="utf-8", newline="\n")
