from pathlib import Path

BASE = "41f0775731c405a6b208baec8910bdb36a78d10e"
PLAN = Path("docs/roadmap/R14_PLAN.md")
CONT = Path("docs/continuity/KODEPOIA_CONTINUITY.md")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


plan = PLAN.read_text(encoding="utf-8")
plan = replace_once(
    plan,
    "**Execution checkpoint:** R1–R13 are COMPLETE + NORMALIZED and R14 planning is ACCEPTED + NORMALIZED on `main` `27af7b80072678f509f7092cf2759683efe1224f`. R14.1 accepted immutable technical source `84972d283f6f530ae46ebf6c0452188927b178ff` passed R0 Repository Guard #1752 / `33140670364`, Python Core #1726 / `33140670445`, and KodeStudio UI Smoke #1693 / `33140670391`, all SUCCESS; Ubuntu full suite recorded 1445 passed / 13 skipped and Windows Core also passed. R14.1 is COMPLETE at technical/evidence level; final END-synchronized documentation head must pass fresh exact-head R0 + full Python Core + KodeStudio UI Smoke before PR #257 may merge. R14.2–R14.17 remain PLANNED.",
    "**Execution checkpoint:** R1–R13 are COMPLETE + NORMALIZED; R14 planning is ACCEPTED + NORMALIZED. R14.1 is COMPLETE + NORMALIZED on `main` `41f0775731c405a6b208baec8910bdb36a78d10e`: immutable technical source `84972d283f6f530ae46ebf6c0452188927b178ff` passed R0 #1752 / `33140670364`, Python Core #1726 / `33140670445`, and UI #1693 / `33140670391`; final END-head `75e5d68752a56b8a21fa4842e803d86f772f7468` passed R0 #1757 / `33140864294`, Python #1731 / `33140864327`, and UI #1698 / `33140864338`; PR #257 merged as `6059b6d706d1208fdcad102c9fa217abaf31d099`; single continuity-only normalization head `5f5624d9ce0a5cca0d112c0cf338f8cf6292eff9` passed R0 #1759 / `33141096835`, Python #1733 / `33141096889`, and UI #1700 / `33141096815`, then PR #258 merged as normalized `main` `41f0775731c405a6b208baec8910bdb36a78d10e`. R14.2 is IN_PROGRESS on `r14/02-backend-service-intent`; R14.3–R14.17 remain PLANNED. Manual state for R14.2 is NONE.",
    "plan checkpoint",
)
plan = replace_once(
    plan,
    "| R14.2 | Project DNA/KodeProduct backend profiles + Wizard conditional service intent | PLANNED | NONE | R14.1 + R2/R13 profile patterns |",
    "| R14.2 | Project DNA/KodeProduct backend profiles + Wizard conditional service intent | IN_PROGRESS | NONE | R14.1 + R2/R13 profile patterns |",
    "R14.2 table status",
)
plan = replace_once(
    plan,
    "- Final END-synchronized documentation/evidence re-gates and implementation PR #257 merge remain pending.\n- Current subdivision status: `COMPLETE` at technical/evidence level, not `COMPLETE + NORMALIZED` until post-merge continuity normalization.",
    "- Final END-head `75e5d68752a56b8a21fa4842e803d86f772f7468` passed R0 #1757 / `33140864294`, Python Core #1731 / `33140864327`, and UI #1698 / `33140864338`; PR #257 merged as `6059b6d706d1208fdcad102c9fa217abaf31d099`.\n- Single continuity-only normalization head `5f5624d9ce0a5cca0d112c0cf338f8cf6292eff9` passed R0 #1759 / `33141096835`, Python Core #1733 / `33141096889`, and UI #1700 / `33141096815`; PR #258 merged as normalized `main` `41f0775731c405a6b208baec8910bdb36a78d10e`.\n- Current subdivision status: `COMPLETE + NORMALIZED`. R14.2 is authorized and starts from that exact normalized main.",
    "R14.1 completion authority",
)
PLAN.write_text(plan, encoding="utf-8", newline="\n")

cont = CONT.read_text(encoding="utf-8")
cont = replace_once(
    cont,
    "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1 COMPLETE + NORMALIZED when this single continuity-only normalization PR merges; R14.2–R14.17 remain PLANNED.** R14.1 accepted immutable technical source `84972d283f6f530ae46ebf6c0452188927b178ff` passed R0 #1752 / `33140670364`, Python Core #1726 / `33140670445`, and UI #1693 / `33140670391`, all SUCCESS. Final END-synchronized head `75e5d68752a56b8a21fa4842e803d86f772f7468` changed only plan/acceptance/continuity relative to the technical source and passed fresh R0 #1757 / `33140864294`, Python Core #1731 / `33140864327`, and UI #1698 / `33140864338`, all SUCCESS. PR #257 merged with exact-head protection as `6059b6d706d1208fdcad102c9fa217abaf31d099`. This branch `r14/01-continuity-normalization` is the single authorized post-merge continuity-only normalization; its COMPLETE + NORMALIZED authority becomes effective only after this exact continuity-only candidate passes fresh R0 + full Python Core + KodeStudio UI Smoke and its PR merges with expected-head protection. R14.2 may start only from the resulting normalized main. Manual state is NONE.",
    "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1 COMPLETE + NORMALIZED. R14.2 IN_PROGRESS on `r14/02-backend-service-intent`; R14.3–R14.17 remain PLANNED.** R14.1 immutable technical source `84972d283f6f530ae46ebf6c0452188927b178ff` passed R0 #1752 / `33140670364`, Python #1726 / `33140670445`, UI #1693 / `33140670391`; END-head `75e5d68752a56b8a21fa4842e803d86f772f7468` passed R0 #1757 / `33140864294`, Python #1731 / `33140864327`, UI #1698 / `33140864338`; PR #257 merged as `6059b6d706d1208fdcad102c9fa217abaf31d099`; normalization head `5f5624d9ce0a5cca0d112c0cf338f8cf6292eff9` passed R0 #1759 / `33141096835`, Python #1733 / `33141096889`, UI #1700 / `33141096815`; PR #258 merged as normalized `main` `41f0775731c405a6b208baec8910bdb36a78d10e`. R14.2 starts exactly from that main. Manual state for R14.2 is NONE.",
    "continuity prompt",
)
cont = replace_once(
    cont,
    "- R14 planning: **ACCEPTED + NORMALIZED**. Normalized planning base is **`27af7b80072678f509f7092cf2759683efe1224f`**. R14.1 accepted technical source **`84972d283f6f530ae46ebf6c0452188927b178ff`** and final END-head **`75e5d68752a56b8a21fa4842e803d86f772f7468`**; implementation/evidence PR #257 merged as **`6059b6d706d1208fdcad102c9fa217abaf31d099`**. R14.1 is **COMPLETE / POST_MERGE_NORMALIZATION_IN_PROGRESS** on `r14/01-continuity-normalization`; R14.2–R14.17 remain PLANNED and R14.2 is forbidden until this single continuity-only normalization passes fresh gates and merges.",
    "- R14 planning: **ACCEPTED + NORMALIZED**. R14.1 is **COMPLETE + NORMALIZED** on normalized `main` **`41f0775731c405a6b208baec8910bdb36a78d10e`** after implementation PR #257 and continuity-only normalization PR #258. R14.2 is **IN_PROGRESS** on `r14/02-backend-service-intent`; R14.3–R14.17 remain PLANNED. Manual **NONE**.",
    "continuity global R14",
)
cont = replace_once(
    cont,
    "- R14.1 implementation branch `r14/01-backend-contracts-boundaries` started exactly from normalized planning main `27af7b80072678f509f7092cf2759683efe1224f`. Accepted immutable technical source `84972d283f6f530ae46ebf6c0452188927b178ff` passed R0 #1752 / `33140670364`, Python Core #1726 / `33140670445`, and UI #1693 / `33140670391`; final END-head `75e5d68752a56b8a21fa4842e803d86f772f7468` passed fresh R0 #1757 / `33140864294`, Python Core #1731 / `33140864327`, and UI #1698 / `33140864338`, all SUCCESS. PR #257 merged with expected-head protection as `6059b6d706d1208fdcad102c9fa217abaf31d099`. The only remaining R14.1 authority step is this single continuity-only normalization; manual intervention remains **NONE**.",
    "- R14.1 implementation branch `r14/01-backend-contracts-boundaries` started exactly from normalized planning main `27af7b80072678f509f7092cf2759683efe1224f`. Accepted immutable technical source `84972d283f6f530ae46ebf6c0452188927b178ff` passed R0 #1752 / `33140670364`, Python Core #1726 / `33140670445`, and UI #1693 / `33140670391`; final END-head `75e5d68752a56b8a21fa4842e803d86f772f7468` passed fresh R0 #1757 / `33140864294`, Python Core #1731 / `33140864327`, and UI #1698 / `33140864338`, all SUCCESS. PR #257 merged as `6059b6d706d1208fdcad102c9fa217abaf31d099`. Single continuity-only normalization head `5f5624d9ce0a5cca0d112c0cf338f8cf6292eff9` passed R0 #1759 / `33141096835`, Python #1733 / `33141096889`, and UI #1700 / `33141096815`; PR #258 merged as normalized main `41f0775731c405a6b208baec8910bdb36a78d10e`. Therefore R14.1 is **COMPLETE + NORMALIZED** and R14.2 is authorized. Manual intervention remains **NONE**.",
    "continuity R14.1 authority",
)
marker = "## R14.1 post-merge normalization authority\n"
insert = "## R14.2 start authority\n\n- Dedicated branch: `r14/02-backend-service-intent`.\n- Exact branch point: normalized `main` `41f0775731c405a6b208baec8910bdb36a78d10e`.\n- R14.1 is COMPLETE + NORMALIZED; R14.2 is IN_PROGRESS; R14.3–R14.17 remain PLANNED.\n- Frozen R14.2 scope: optional Project DNA/KodeProduct backend service intent, deterministic dependency graph, conditional Wizard questions, requirements/acceptance derivation, compatibility validation, backward-compatible disabled default; no provisioning, deployment, credentials or concrete backend service implementation.\n- Manual intervention: **NONE**.\n\n"
if marker not in cont:
    raise SystemExit("continuity insertion marker missing")
cont = cont.replace(marker, insert + marker, 1)
CONT.write_text(cont, encoding="utf-8", newline="\n")

print(f"R14.2 START-sync prepared from {BASE}")
