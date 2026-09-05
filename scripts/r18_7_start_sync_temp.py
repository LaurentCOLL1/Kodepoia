from pathlib import Path
import re

BASE_SHA = "4ccbe4ef1fe66f88e38dfc8c9dfebba7e183efe1"
BRANCH = "r18/07-kodestudio-update-discovery-channel-ux"

roadmap = Path("docs/roadmap/R18_PLAN.md")
roadmap_text = roadmap.read_text(encoding="utf-8")

roadmap_status_pattern = re.compile(r"^Roadmap status: .*?$", re.MULTILINE)
if len(roadmap_status_pattern.findall(roadmap_text)) != 1:
    raise SystemExit("unexpected roadmap status cardinality")
roadmap_text = roadmap_status_pattern.sub(
    "Roadmap status: planning is **ACCEPTED + NORMALIZED** on `main` `bbffc382d4fb8a7d947345da11b56459d0fec825`. "
    "R18.1 is COMPLETE + NORMALIZED on canonical `main` `c611131268041b06f53de66eaadd45120e2b750d`. "
    "R18.2 is **COMPLETE + NORMALIZED** on canonical `main` `c376d0af789e584e1ef307f43e42a62ce024b052`. "
    "R18.3 is **COMPLETE + NORMALIZED** on canonical `main` `66314ff1c86e51d84f1abe15d107a6182ef9e54a`. "
    "R18.4 is **COMPLETE + NORMALIZED** on canonical `main` `b6aa853c59921bf51e346b7860e709cca63a4a2e`. "
    "R18.5 is **COMPLETE + NORMALIZED** on canonical `main` `2f0929c30f717ad608523cc1837ecfb1129a28f1`. "
    "R18.6 TUF-secured update repository and metadata lifecycle is **COMPLETE + NORMALIZED** on canonical `main` `4ccbe4ef1fe66f88e38dfc8c9dfebba7e183efe1` after implementation/evidence PR #393 and unique continuity-only normalization PR #394. "
    "R18.7 KodeStudio update discovery and release-channel UX is **IN_PROGRESS at START-sync** on dedicated branch `r18/07-kodestudio-update-discovery-channel-ux` from that exact normalized R18.6 main; no R18.7 implementation bytes exist before this documentation-only START-sync. "
    "R18.8–R18.11 remain PLANNED. The frozen v1.0/R1–R16 architecture and history are not rewritten.",
    roadmap_text,
    count=1,
)

roadmap_text = roadmap_text.replace(
    "| R18.6 | TUF-secured update repository and metadata lifecycle | COMPLETE at END-sync | NONE | R18.1–R18.3 |\n"
    "| R18.7 | KodeStudio update discovery and release-channel UX | PLANNED | NONE | R18.6 |",
    "| R18.6 | TUF-secured update repository and metadata lifecycle | COMPLETE + NORMALIZED | NONE | R18.1–R18.3 |\n"
    "| R18.7 | KodeStudio update discovery and release-channel UX | IN_PROGRESS | NONE | R18.6 |",
    1,
)
if "| R18.7 | KodeStudio update discovery and release-channel UX | IN_PROGRESS | NONE | R18.6 |" not in roadmap_text:
    raise SystemExit("R18.7 subdivision index transition failed")

r187_heading = "# R18.7 — KodeStudio update discovery and release-channel UX\n"
if roadmap_text.count(r187_heading) != 1:
    raise SystemExit("unexpected R18.7 heading cardinality")
start_record = (
    r187_heading
    + "\n## START-sync authority\n\n"
    + "- Exact normalized R18.6 base: `main` `4ccbe4ef1fe66f88e38dfc8c9dfebba7e183efe1`; dedicated branch: `r18/07-kodestudio-update-discovery-channel-ux`.\n"
    + "- State transition: R18.1–R18.6 **COMPLETE + NORMALIZED**; R18.7 **IN_PROGRESS**; R18.8–R18.11 **PLANNED**. This START-sync is documentation-only and precedes every R18.7 implementation byte.\n"
    + "- Frozen scope remains discovery/channel UX only: controller/model + KodeStudio presentation/persistence/localization for trusted update status. Download/install/installer execution remain R18.8 and are not authorized here.\n"
    + "- Current official research re-check: TUF keeps Root/Targets/Snapshot/Timestamp as the required top-level trust roles; Timestamp is the short-lived freshness entry point. Microsoft Windows notification guidance favors clear, valuable, non-noisy notifications and preserving user intent. These are design inputs, not mutable runtime dependencies.\n"
    + "- Core manual state: **NONE**. Production signing, public GitHub Release publication, immutable-release repository setting changes, production TUF key custody/hosting and public WinGet submission remain **CONDITIONAL / NOT TRIGGERED**.\n"
    + "- Before technical acceptance, implementation must preserve offline/local-first startup, treat network/release-note content as untrusted until verified, default conservatively on release channel, expose explicit prerelease warning, and never auto-launch an installer.\n"
)
roadmap_text = roadmap_text.replace(r187_heading, start_record, 1)
with roadmap.open("w", encoding="utf-8", newline="\n") as handle:
    handle.write(roadmap_text)

continuity = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
continuity_text = continuity.read_text(encoding="utf-8")
lines = continuity_text.splitlines()
if not lines or not lines[0].startswith("> Kodepoia, architecture v1.0 gelée."):
    raise SystemExit("unexpected continuity banner")
lines[0] = (
    "> Kodepoia, architecture v1.0 gelée. **R1–R17 COMPLETE + NORMALIZED. R18 planning ACCEPTED + NORMALIZED. "
    "R18.1–R18.5 are COMPLETE + NORMALIZED on their recorded canonical mains. "
    "R18.6 TUF-secured update repository and metadata lifecycle is COMPLETE + NORMALIZED on canonical `main` `4ccbe4ef1fe66f88e38dfc8c9dfebba7e183efe1` after exact-END PR #393 and unique normalization PR #394. "
    "R18.7 KodeStudio update discovery and release-channel UX is IN_PROGRESS at documentation-only START-sync on branch `r18/07-kodestudio-update-discovery-channel-ux` from that exact main; implementation bytes are not authorized before this START-sync. "
    "R18.8–R18.11 remain PLANNED.** Production signing, public GitHub Release publication, immutable-release repository setting changes, production TUF key custody/hosting and public WinGet submission remain CONDITIONAL / NOT TRIGGERED."
)
continuity_text = "\n".join(lines) + "\n"

phase_pattern = re.compile(r"^- State: \*\*IN_PROGRESS\*\* — planning and R18\.1–R18\.5 are COMPLETE \+ NORMALIZED\..*?$", re.MULTILINE)
if len(phase_pattern.findall(continuity_text)) != 1:
    raise SystemExit("unexpected R18 phase status cardinality")
continuity_text = phase_pattern.sub(
    "- State: **IN_PROGRESS** — planning and R18.1–R18.6 are COMPLETE + NORMALIZED. Canonical normalized R18.6 `main` is `4ccbe4ef1fe66f88e38dfc8c9dfebba7e183efe1` after implementation/evidence PR #393 and unique normalization PR #394. R18.7 is **IN_PROGRESS at START-sync** on dedicated branch `r18/07-kodestudio-update-discovery-channel-ux`, created exactly from that normalized main; this documentation-only START-sync precedes all R18.7 implementation bytes. R18.8–R18.11 remain PLANNED. Manual state for core R18.7 is NONE; public/production distribution effects remain CONDITIONAL / NOT TRIGGERED.",
    continuity_text,
    count=1,
)

norm_heading = "## R18.6 post-merge normalization authority\n"
if continuity_text.count(norm_heading) != 1:
    raise SystemExit("unexpected R18.6 normalization heading cardinality")
continuity_text = continuity_text.replace(
    "- This is the single authorized post-merge normalization for R18.6. Its exact candidate head must pass fresh R0 Repository Guard Ubuntu + Windows, full Python Core 5/5 and KodeStudio UI Smoke before an exact-head merge. No second R18.6 normalization is permitted.\n",
    "- This was the single authorized post-merge normalization for R18.6. Exact candidate `081ecd1bd83a7956b77c309adc27af0b5b2cfc82` passed R0 Repository Guard #2502 / `33993960223` Ubuntu + Windows, full Python Core #2474 / `33993960138` 5/5 and KodeStudio UI Smoke #2439 / `33993960073`; PR #394 merged that exact head with expected-head protection as canonical normalized `main` `4ccbe4ef1fe66f88e38dfc8c9dfebba7e183efe1`. No second R18.6 normalization is permitted.\n",
    1,
)
continuity_text = continuity_text.replace(
    "- Only the normalized `main` produced by this exact gated normalization merge may authorize R18.7 START-sync; R18.7 implementation must still begin with its own documentation-only START-sync before any implementation bytes.\n",
    "- The normalized `main` produced by that exact gated normalization merge is `4ccbe4ef1fe66f88e38dfc8c9dfebba7e183efe1`; it is the sole authorized R18.7 branch point. R18.7 implementation begins only after its documentation-only START-sync recorded below.\n",
    1,
)

next_pattern = re.compile(r"## Next authorized action\n\n.*?(?=\n## R17 — Distribution & Guided Creation UX)", re.DOTALL)
if len(next_pattern.findall(continuity_text)) != 1:
    raise SystemExit("unexpected Next authorized action cardinality")
r187_authority = """## R18.7 START authority

- Exact branch point: canonical normalized R18.6 `main` `4ccbe4ef1fe66f88e38dfc8c9dfebba7e183efe1`.
- Dedicated branch: `r18/07-kodestudio-update-discovery-channel-ux`.
- State transition: R18.1–R18.6 **COMPLETE + NORMALIZED**; R18.7 **IN_PROGRESS**; R18.8–R18.11 **PLANNED**.
- START-sync scope is documentation-only: `docs/roadmap/R18_PLAN.md` + this continuity file. No controller, Qt UI, persistence, localization, transport, workflow or test implementation bytes are authorized before this START record.
- Frozen R18.7 scope: trusted update discovery and release-channel UX only. Required user-visible states are up-to-date, update available, offline, metadata expired, verification failed, channel unavailable and update withdrawn; downloading/installing/installer launch remain R18.8.
- Trust/UX boundary: startup remains usable offline; network/release-note content remains untrusted until R18.6 verification succeeds; channel default is conservative with explicit prerelease warning; no forced update and no automatic installer launch.
- Current official research basis rechecked at START: TUF required top-level roles remain Root/Targets/Snapshot/Timestamp with Timestamp acting as the short-lived freshness entry point; Microsoft notification guidance favors informative, valuable, non-noisy notifications and responding to user intent. No external platform behavior is treated as a mutable runtime dependency.
- Core manual state: **NONE**. Production signing, public GitHub Release publication, immutable-release repository setting changes, production TUF key custody/hosting and public WinGet submission remain **CONDITIONAL / NOT TRIGGERED**.
- Temporary START-sync transport helpers, if any, are non-authoritative and must be absent from the clean START head. The clean START decision tree must differ from `4ccbe4ef1fe66f88e38dfc8c9dfebba7e183efe1` only by `docs/roadmap/R18_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md`.

## Next authorized action

Establish the clean documentation-only R18.7 START head from canonical normalized R18.6 `main` `4ccbe4ef1fe66f88e38dfc8c9dfebba7e183efe1`, verify its net diff contains only `docs/roadmap/R18_PLAN.md` + `docs/continuity/KODEPOIA_CONTINUITY.md`, then begin R18.7 implementation on that same dedicated branch. Technical acceptance must later run on the immutable implementation source before END-sync. R18.8 remains unauthorized.
"""
continuity_text = next_pattern.sub(r187_authority.rstrip(), continuity_text, count=1)
with continuity.open("w", encoding="utf-8", newline="\n") as handle:
    handle.write(continuity_text)
