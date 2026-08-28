from pathlib import Path

TECH = "4e04812380a495dd799e1d7b9e96741d8688de31"
PLAN = Path("docs/roadmap/R14_PLAN.md")
ACC = Path("docs/roadmap/R14_2_ACCEPTANCE.md")
CONT = Path("docs/continuity/KODEPOIA_CONTINUITY.md")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


plan = PLAN.read_text(encoding="utf-8")
plan = replace_once(
    plan,
    "R14.2 is IN_PROGRESS on `r14/02-backend-service-intent`; R14.3–R14.17 remain PLANNED. Manual state for R14.2 is NONE.",
    "R14.2 accepted immutable technical source `4e04812380a495dd799e1d7b9e96741d8688de31` passed R0 Repository Guard #1761 / `33143230642`, Python Core #1735 / `33143230580`, and KodeStudio UI Smoke #1702 / `33143230613`, all SUCCESS; Ubuntu full suite recorded 1465 passed / 13 skipped / 46 warnings and Windows Core also passed. R14.2 is COMPLETE at technical/evidence level; final END-synchronized documentation head must pass fresh exact-head R0 + full Python Core + KodeStudio UI Smoke before PR #259 may merge. R14.3–R14.17 remain PLANNED. Manual state for R14.2 is NONE.",
    "plan execution checkpoint",
)
plan = replace_once(
    plan,
    "| R14.2 | Project DNA/KodeProduct backend profiles + Wizard conditional service intent | IN_PROGRESS | NONE | R14.1 + R2/R13 profile patterns |",
    "| R14.2 | Project DNA/KodeProduct backend profiles + Wizard conditional service intent | COMPLETE | NONE | R14.1 + R2/R13 profile patterns |",
    "R14.2 table status",
)
plan = replace_once(
    plan,
    "## Completion record\n\nTo be appended when accepted.\n\n---\n\n# R14.3 — Deterministic local backend scaffold/runtime + environments/config/secrets/health",
    "## Completion record\n\n- Accepted immutable technical head: `4e04812380a495dd799e1d7b9e96741d8688de31`.\n- Technical exact-head gates: R0 Repository Guard #1761 / `33143230642` SUCCESS; Python Core #1735 / `33143230580` SUCCESS; KodeStudio UI Smoke #1702 / `33143230613` SUCCESS.\n- Ubuntu full Python suite: 1465 passed, 13 skipped, 46 warnings; Windows Core suite also SUCCESS; both package builds and Python internal UI smoke SUCCESS.\n- Focused prevalidation `33143176492`: 34 passed, 2 skipped; diagnostic only, not acceptance authority.\n- Manual intervention: NONE.\n- Current subdivision status: `COMPLETE` at technical/evidence level. R14.3 remains `PLANNED` until R14.2 implementation merge and single continuity-only normalization are accepted.\n\n---\n\n# R14.3 — Deterministic local backend scaffold/runtime + environments/config/secrets/health",
    "R14.2 completion record",
)
PLAN.write_text(plan, encoding="utf-8", newline="\n")

acc = ACC.read_text(encoding="utf-8")
acc = replace_once(
    acc,
    "**Status: IMPLEMENTATION_CANDIDATE_PENDING**",
    "**Status: TECHNICAL_CANDIDATE_ACCEPTED / FINAL_REGATES_PENDING**",
    "acceptance status",
)
anchor = "A failed/partial/stale head is non-authoritative and its evidence cannot be reused.\n\n"
record = (
    "## Accepted technical candidate record\n\n"
    "- Immutable source SHA: `4e04812380a495dd799e1d7b9e96741d8688de31`.\n"
    "- R0 Repository Guard #1761 / `33143230642`: COMPLETED / SUCCESS.\n"
    "- Python Core #1735 / `33143230580`: COMPLETED / SUCCESS; Ubuntu full `pytest` = **1465 passed, 13 skipped, 46 warnings**; Windows Core = SUCCESS; both package builds and Python internal KodeStudio smoke = SUCCESS.\n"
    "- KodeStudio UI Smoke #1702 / `33143230613`: COMPLETED / SUCCESS.\n"
    "- Focused prevalidation `33143176492`: 34 passed, 2 skipped; diagnostic only and non-authoritative for merge acceptance.\n"
    "- Rejected predecessor technical candidates: NONE. START-sync guard retries were documentation workflow hygiene only and occurred before technical acceptance.\n"
    "- Manual intervention: NONE.\n"
    "- Next authority: END-synchronized documentation/evidence head changing only plan, this ledger and continuity, followed by fresh exact-head R0/Python/UI.\n\n"
)
if anchor not in acc:
    raise SystemExit("acceptance insertion anchor missing")
acc = acc.replace(anchor, anchor + record, 1)
ACC.write_text(acc, encoding="utf-8", newline="\n")

cont = CONT.read_text(encoding="utf-8")
cont = replace_once(
    cont,
    "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1 COMPLETE + NORMALIZED. R14.2 IN_PROGRESS on `r14/02-backend-service-intent`; R14.3–R14.17 remain PLANNED.** R14.1 immutable technical source `84972d283f6f530ae46ebf6c0452188927b178ff` passed R0 #1752 / `33140670364`, Python #1726 / `33140670445`, UI #1693 / `33140670391`; END-head `75e5d68752a56b8a21fa4842e803d86f772f7468` passed R0 #1757 / `33140864294`, Python #1731 / `33140864327`, UI #1698 / `33140864338`; PR #257 merged as `6059b6d706d1208fdcad102c9fa217abaf31d099`; normalization head `5f5624d9ce0a5cca0d112c0cf338f8cf6292eff9` passed R0 #1759 / `33141096835`, Python #1733 / `33141096889`, UI #1700 / `33141096815`; PR #258 merged as normalized `main` `41f0775731c405a6b208baec8910bdb36a78d10e`. R14.2 starts exactly from that main. Manual state for R14.2 is NONE.",
    "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1 COMPLETE + NORMALIZED. R14.2 COMPLETE at technical/evidence level on `r14/02-backend-service-intent`; final exact-head documentation re-gates and PR #259 merge remain pending. R14.3–R14.17 remain PLANNED.** R14.2 accepted immutable technical source `4e04812380a495dd799e1d7b9e96741d8688de31` passed R0 #1761 / `33143230642`, Python Core #1735 / `33143230580`, and KodeStudio UI Smoke #1702 / `33143230613`, all SUCCESS; Ubuntu full suite recorded 1465 passed / 13 skipped / 46 warnings and Windows Core also passed. No technical semantics may change during END-sync. After final fresh R0 + Python Core + UI Smoke on the END-synchronized head, merge PR #259 with expected-head protection, then perform exactly one continuity-only post-merge normalization before R14.2 becomes COMPLETE + NORMALIZED and R14.3 is authorized. Manual state is NONE.",
    "continuity prompt",
)
cont = replace_once(
    cont,
    "- R14 planning: **ACCEPTED + NORMALIZED**. R14.1 is **COMPLETE + NORMALIZED** on normalized `main` **`41f0775731c405a6b208baec8910bdb36a78d10e`** after implementation PR #257 and continuity-only normalization PR #258. R14.2 is **IN_PROGRESS** on `r14/02-backend-service-intent`; R14.3–R14.17 remain PLANNED. Manual **NONE**.",
    "- R14 planning: **ACCEPTED + NORMALIZED**. R14.1 is **COMPLETE + NORMALIZED** on normalized `main` **`41f0775731c405a6b208baec8910bdb36a78d10e`**. R14.2 accepted immutable technical source **`4e04812380a495dd799e1d7b9e96741d8688de31`** passed R0 #1761 / `33143230642`, Python Core #1735 / `33143230580`, and UI #1702 / `33143230613`, all SUCCESS. R14.2 is **COMPLETE / FINAL_DOCUMENTATION_REGATES_PENDING**; R14.3–R14.17 remain PLANNED. Manual **NONE**.",
    "continuity global R14",
)
cont = replace_once(
    cont,
    "- R14.1 is COMPLETE + NORMALIZED; R14.2 is IN_PROGRESS; R14.3–R14.17 remain PLANNED.\n- Frozen R14.2 scope: optional Project DNA/KodeProduct backend service intent, deterministic dependency graph, conditional Wizard questions, requirements/acceptance derivation, compatibility validation, backward-compatible disabled default; no provisioning, deployment, credentials or concrete backend service implementation.\n- Manual intervention: **NONE**.",
    "- R14.1 is COMPLETE + NORMALIZED. R14.2 accepted immutable technical source `4e04812380a495dd799e1d7b9e96741d8688de31`, which passed R0 #1761 / `33143230642`, Python Core #1735 / `33143230580`, and UI #1702 / `33143230613`, all SUCCESS. R14.2 is COMPLETE at technical/evidence level; R14.3–R14.17 remain PLANNED pending final documentation re-gates, PR #259 merge and continuity-only normalization.\n- Frozen R14.2 scope: optional Project DNA/KodeProduct backend service intent, deterministic dependency graph, conditional Wizard questions, requirements/acceptance derivation, compatibility validation, backward-compatible disabled default; no provisioning, deployment, credentials or concrete backend service implementation.\n- Manual intervention: **NONE**.",
    "continuity R14.2 start authority",
)
CONT.write_text(cont, encoding="utf-8", newline="\n")

print(f"R14.2 END-sync prepared from immutable technical source {TECH}")
