from pathlib import Path
import re


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"Expected exactly one occurrence, found {count}: {old[:100]!r}")
    return text.replace(old, new, 1)


roadmap_path = Path("docs/roadmap/R18_PLAN.md")
roadmap = roadmap_path.read_text(encoding="utf-8")
roadmap = replace_once(roadmap, "Status: **IN_PROGRESS**", "Status: **COMPLETE + NORMALIZED**")

pattern = r"Roadmap status: .*?\n\n## Phase objective"
replacement = (
    "Roadmap status: R18 planning is **ACCEPTED + NORMALIZED**. R18.1–R18.11 are all **COMPLETE + NORMALIZED**. "
    "Final R18.11 exact-END `c64bac012ef3afa332526a539901b11428fd966f` passed fresh exact-head R18.11 / R16.9 / R0 / Python Core / KodeStudio UI gates before PR #403 merged as implementation/evidence `main` `0ea7b14f03a4e3d0539ce3e7d4fc932427fdb104`. "
    "The single authorized phase-level continuity-only normalization candidate `996cb8adc7a203350473057d3dbe2dcbc8482b8e` then passed fresh R0 Repository Guard Ubuntu + Windows, Python Core 5/5 and KodeStudio UI Smoke before PR #404 merged as canonical normalized `main` `4632e988e5b04b717c86356eda638827c0252e02`. "
    "The frozen R18 scope ends at R18.11; no R18.12 or additional R18 subdivision is authorized. Production signing, public GitHub Release publication/mutation, production TUF key custody/rotation and public WinGet submission remain **CONDITIONAL / NOT TRIGGERED**.\n\n## Phase objective"
)
roadmap, count = re.subn(pattern, replacement, roadmap, count=1)
if count != 1:
    raise SystemExit(f"Expected one Roadmap status block, replaced {count}")

table_replacements = {
    "| R18.1 | Canonical release identity, versions and channels | COMPLETE | NONE | R17 normalized main |": "| R18.1 | Canonical release identity, versions and channels | COMPLETE + NORMALIZED | NONE | R17 normalized main |",
    "| R18.2 | Deterministic release bundle and manifest contract | COMPLETE | NONE | R18.1 |": "| R18.2 | Deterministic release bundle and manifest contract | COMPLETE + NORMALIZED | NONE | R18.1 |",
    "| R18.3 | SBOM, provenance and artifact attestations | COMPLETE | NONE | R18.2 |": "| R18.3 | SBOM, provenance and artifact attestations | COMPLETE + NORMALIZED | NONE | R18.2 |",
    "| R18.4 | Windows Authenticode signing and verification boundary | COMPLETE | CONDITIONAL / NOT TRIGGERED | R18.2–R18.3 |": "| R18.4 | Windows Authenticode signing and verification boundary | COMPLETE + NORMALIZED | CONDITIONAL / NOT TRIGGERED | R18.2–R18.3 |",
    "| R18.5 | Immutable GitHub Release staging and promotion | COMPLETE | CONDITIONAL / NOT TRIGGERED | R18.2–R18.4 |": "| R18.5 | Immutable GitHub Release staging and promotion | COMPLETE + NORMALIZED | CONDITIONAL / NOT TRIGGERED | R18.2–R18.4 |",
    "| R18.8 | Verified download, user-consented install and rollback | COMPLETE at END-sync | NONE | R18.4, R18.6–R18.7 |": "| R18.8 | Verified download, user-consented install and rollback | COMPLETE + NORMALIZED | NONE | R18.4, R18.6–R18.7 |",
    "| R18.9 | WinGet manifest generation and validation | PLANNED | CONDITIONAL | R18.2, R18.4–R18.5 |": "| R18.9 | WinGet manifest generation and validation | COMPLETE + NORMALIZED | CONDITIONAL / NOT TRIGGERED | R18.2, R18.4–R18.5 |",
    "| R18.10 | Revocation, rollback and compromised-release drills | PLANNED | NONE | R18.4–R18.9 |": "| R18.10 | Revocation, rollback and compromised-release drills | COMPLETE + NORMALIZED | NONE | R18.4–R18.9 |",
    "| R18.11 | Integrated adversarial release/update acceptance | PLANNED | NONE | R18.1–R18.10 |": "| R18.11 | Integrated adversarial release/update acceptance | COMPLETE + NORMALIZED | NONE | R18.1–R18.10 |",
}
for old, new in table_replacements.items():
    roadmap = replace_once(roadmap, old, new)

if "## R18 final closure authority" in roadmap:
    raise SystemExit("R18 final closure authority already exists")
closure = """

## R18 final closure authority

- R18.11 final exact-END head `c64bac012ef3afa332526a539901b11428fd966f` passed fresh R18.11 Integrated Adversarial Release Update Acceptance #8 / `34058165771`, R16.9 Supply Chain Provenance #204 / `34058165647`, R0 Repository Guard #2556 / `34058165607` Ubuntu + Windows, Python Core #2528 / `34058165818` 5/5 and KodeStudio UI Smoke #2493 / `34058165759`; PR #403 then merged with exact expected-head protection as implementation/evidence `main` `0ea7b14f03a4e3d0539ce3e7d4fc932427fdb104`.
- The single authorized phase-level continuity-only normalization candidate `996cb8adc7a203350473057d3dbe2dcbc8482b8e` changed only `docs/continuity/KODEPOIA_CONTINUITY.md` (+12/-0), passed fresh R0 Repository Guard #2558 / `34073457900` Ubuntu + Windows, Python Core #2530 / `34073457973` 5/5 and KodeStudio UI Smoke #2495 / `34073457927`, and PR #404 merged with exact expected-head protection as canonical normalized `main` `4632e988e5b04b717c86356eda638827c0252e02`.
- **R18 is COMPLETE + NORMALIZED. R18.1–R18.11 are all COMPLETE + NORMALIZED.** No second R18 phase normalization, R18.12, or additional R18 subdivision is authorized.
- Core manual state is **NONE**. Production signing, public GitHub Release publication/mutation, production TUF key custody/rotation and public WinGet submission remain **CONDITIONAL / NOT TRIGGERED**. Phase completion does not imply any public/production distribution action.
"""
roadmap_path.write_text(roadmap.rstrip() + closure, encoding="utf-8")

readme_path = Path("README.md")
readme = readme_path.read_text(encoding="utf-8")
readme = replace_once(readme, "- Roadmap R1–R16 : **COMPLETE + NORMALIZED**.", "- Roadmap R1–R18 : **COMPLETE + NORMALIZED**.")
readme = replace_once(
    readme,
    "- `main` v1.0 canonique au démarrage de R17 : `11194ec5bbb6a986d0fa206517ad3759378a80cf`.",
    "- `main` v1.0 canonique au démarrage de R17 : `11194ec5bbb6a986d0fa206517ad3759378a80cf`.\n- `main` canonique après clôture et normalisation de R18 : `4632e988e5b04b717c86356eda638827c0252e02`.",
)
readme = replace_once(
    readme,
    "- Évolution en cours : **v1.1 / R17 — Distribution & Guided Creation UX**.",
    "- État v1.1 : **R17 — Distribution & Guided Creation UX** et **R18 — Trusted Release, Updates & Distribution Channels** sont **COMPLETE + NORMALIZED**.",
)
readme = replace_once(
    readme,
    "- R17 ajoute l'installation Windows autonome, le français, la création guidée et le Chat/Vision local.",
    "- R17 a livré l'installation Windows autonome, le français, la création guidée et le Chat/Vision local.\n- R18 a livré l'identité de release canonique, bundles/manifests vérifiables, SBOM/provenance, frontière Authenticode, staging/promotion gouvernés, métadonnées TUF anti-rollback/freeze, découverte et installation consentie des mises à jour, préparation WinGet, drills de révocation/rollback et acceptance adversariale intégrée.",
)
readme = replace_once(
    readme,
    "L'objectif de R17 est qu'un utilisateur **n'ait pas besoin d'installer Python ni d'utiliser `pip`**.",
    "Depuis R17, un utilisateur **n'a pas besoin d'installer Python ni d'utiliser `pip`** pour utiliser l'installateur Windows accepté.",
)
readme = replace_once(
    readme,
    "- `docs/roadmap/R17_PLAN.md`\n- `docs/continuity/KODEPOIA_CONTINUITY.md`",
    "- `docs/roadmap/R17_PLAN.md`\n- `docs/roadmap/R18_PLAN.md`\n- `docs/continuity/KODEPOIA_CONTINUITY.md`",
)
readme_path.write_text(readme, encoding="utf-8")
