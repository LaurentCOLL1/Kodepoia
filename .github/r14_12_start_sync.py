from pathlib import Path
import re

BASE = "71ceb529e89b13be343be76527e9b9b0b419ceda"

plan_path = Path("docs/roadmap/R14_PLAN.md")
plan = plan_path.read_text(encoding="utf-8")

checkpoint_pattern = re.compile(r"^\*\*Execution checkpoint:\*\* .*R14\.12–R14\.17 remain PLANNED\..*$", re.MULTILINE)
checkpoint_replacement = (
    "**Execution checkpoint:** R1–R13 are COMPLETE + NORMALIZED; R14 planning is ACCEPTED + NORMALIZED. "
    "R14.1–R14.11 are COMPLETE + NORMALIZED on normalized `main` `71ceb529e89b13be343be76527e9b9b0b419ceda`. "
    "R14.11 immutable technical source `a58a0cf48a5e2311b5f6e671655f107e92c4645e`; END-head `ef39e7898abbca5466073bb78a95df829a33d836`; "
    "PR #277 merge `a32b62c4e961ed2f5fe66dd5e30c453abb64d9f1`; single continuity-only normalization head `5356f2354d8c2237ccb6a3957b1c2cde21d4de80` "
    "passed R0 #1865 / `33242852652`, Python Core #1839 / `33242852691`, UI #1806 / `33242852613`, and PR #278 merged with expected-head as normalized `main` "
    "`71ceb529e89b13be343be76527e9b9b0b419ceda`. R14.12 is IN_PROGRESS on `r14/12-content-delivery`; R14.13–R14.17 remain PLANNED. "
    "R14.12 manual state is CONDITIONAL / NOT TRIGGERED; `provider_live_claim=false`."
)
plan, n = checkpoint_pattern.subn(checkpoint_replacement, plan, count=1)
assert n == 1, n

old_row = "| R14.12 | Content delivery: immutable manifests/bundles, channels, cache + rollback | PLANNED | CONDITIONAL | R14.5/R14.11 + R8/R13 release provenance |"
new_row = "| R14.12 | Content delivery: immutable manifests/bundles, channels, cache + rollback | IN_PROGRESS | CONDITIONAL / NOT TRIGGERED | R14.5/R14.11 + R8/R13 release provenance |"
assert plan.count(old_row) == 1, plan.count(old_row)
plan = plan.replace(old_row, new_row)

section_start = plan.index("# R14.12 — Content delivery: immutable manifests/bundles, channels, cache + rollback")
section_end = plan.index("# R14.13 — Events/telemetry pipeline: typed envelopes, dedupe, replay, retention + OTel bridge")
section = plan[section_start:section_end]
anchor = "## Completion record\n\nTo be appended when accepted."
assert section.count(anchor) == 1, section.count(anchor)
start_authority = """## START authority

- Dedicated branch: `r14/12-content-delivery`.
- Exact branch point: normalized R14.11 `main` `71ceb529e89b13be343be76527e9b9b0b419ceda`.
- R14.11 closure authority: immutable technical source `a58a0cf48a5e2311b5f6e671655f107e92c4645e`; final END-head `ef39e7898abbca5466073bb78a95df829a33d836`; fresh END gates R0 #1863 / `33235110200`, Python Core #1837 / `33235110228`, UI #1804 / `33235110215`, R14 Remote Config #27 / `33235110216` all SUCCESS; PR #277 expected-head merge `a32b62c4e961ed2f5fe66dd5e30c453abb64d9f1`.
- Single R14.11 post-merge normalization head `5356f2354d8c2237ccb6a3957b1c2cde21d4de80` changed only continuity, passed R0 #1865 / `33242852652`, Python Core #1839 / `33242852691`, UI #1806 / `33242852613`, and PR #278 merged with expected-head as normalized `main` `71ceb529e89b13be343be76527e9b9b0b419ceda`.
- START state: R14.1–R14.11 COMPLETE + NORMALIZED; R14.12 IN_PROGRESS; R14.13–R14.17 PLANNED.
- Trust invariants: content identities/manifests/bundles are immutable and hash-addressed; executable/self-modifying payloads are rejected; dependency graphs are acyclic and bounded; client/schema compatibility is explicit; channel promotion is atomic and rollback selects a prior immutable manifest; downloads/cache promotion require exact size/hash verification; cache corruption purges rather than silently serves; external URLs are never accepted from untrusted project/content data without existing allowlist/network authorization.
- Core acceptance uses a deterministic local content provider and local HTTP fixture. No external CDN account/domain/credential is required or claimed. `provider_live_claim=false`.
- Manual intervention: CONDITIONAL / NOT TRIGGERED. External CDN/provider proof is deferred unless explicitly requested later; secrets/tokens must never be supplied through model-visible text or committed evidence.

## Completion record

To be appended when accepted."""
section = section.replace(anchor, start_authority)
plan = plan[:section_start] + section + plan[section_end:]
plan_path.write_text(plan, encoding="utf-8")

cont_path = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
cont = cont_path.read_text(encoding="utf-8")

prompt_pattern = re.compile(r"^> Kodepoia, architecture v1\.0 gelée\..*$", re.MULTILINE)
prompt = (
    "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.11 COMPLETE + NORMALIZED. R14.12 IN_PROGRESS. R14.13–R14.17 PLANNED.** "
    "Normalized `main` d’autorité `71ceb529e89b13be343be76527e9b9b0b419ceda`; branche active `r14/12-content-delivery`. "
    "R14.12 doit conserver des manifests/bundles immuables et hash-addressed, rejeter tout contenu exécutable, vérifier dépendances/compatibilité/taille/hash avant promotion/cache atomique, et permettre rollback vers un manifest immuable antérieur. "
    "Core provider = local deterministic; manual state CONDITIONAL / NOT TRIGGERED; `provider_live_claim=false`."
)
cont, n = prompt_pattern.subn(prompt, cont, count=1)
assert n == 1, n

old_global = "- R14.11 : **COMPLETE + NORMALIZED** — source technique `a58a0cf48a5e2311b5f6e671655f107e92c4645e`; END-head `ef39e7898abbca5466073bb78a95df829a33d836`; PR #277 merge `a32b62c4e961ed2f5fe66dd5e30c453abb64d9f1`; unique normalization branch `r14/11-normalization`.\n- R14.12–R14.17 : **PLANNED**."
new_global = "- R14.11 : **COMPLETE + NORMALIZED** — source technique `a58a0cf48a5e2311b5f6e671655f107e92c4645e`; END-head `ef39e7898abbca5466073bb78a95df829a33d836`; PR #277 merge `a32b62c4e961ed2f5fe66dd5e30c453abb64d9f1`; normalization head `5356f2354d8c2237ccb6a3957b1c2cde21d4de80`; normalized `main` `71ceb529e89b13be343be76527e9b9b0b419ceda` via PR #278.\n- R14.12 : **IN_PROGRESS** sur `r14/12-content-delivery`, exact branch point `71ceb529e89b13be343be76527e9b9b0b419ceda`.\n- R14.13–R14.17 : **PLANNED**."
assert cont.count(old_global) == 1, cont.count(old_global)
cont = cont.replace(old_global, new_global)

old_row = "| R14.12 | PLANNED | CONDITIONAL |"
new_row = "| R14.12 | IN_PROGRESS | CONDITIONAL / NOT TRIGGERED |"
assert cont.count(old_row) == 1, cont.count(old_row)
cont = cont.replace(old_row, new_row)

closure_tail = "- Unique post-merge normalization branch: `r14/11-normalization`, created exactly from merge `a32b62c4e961ed2f5fe66dd5e30c453abb64d9f1`. Its final tree delta must contain only this continuity file and must pass fresh exact-head R0/Python/UI before expected-head merge.\n- R14.11 final state is COMPLETE + NORMALIZED once that unique normalization PR merges; R14.12–R14.17 remain PLANNED until then."
closure_done = "- Unique post-merge normalization head `5356f2354d8c2237ccb6a3957b1c2cde21d4de80` changed only this continuity file and passed fresh exact-head R0 #1865 / `33242852652`, Python Core #1839 / `33242852691`, and UI #1806 / `33242852613`.\n- Normalization PR #278 merged with `expected_head_sha=5356f2354d8c2237ccb6a3957b1c2cde21d4de80` as normalized `main` `71ceb529e89b13be343be76527e9b9b0b419ceda`.\n- R14.11 final state: COMPLETE + NORMALIZED; R14.12 is authorized from that exact normalized `main`."
assert cont.count(closure_tail) == 1, cont.count(closure_tail)
cont = cont.replace(closure_tail, closure_done)

next_heading = "## Next authorized action\n\n"
assert cont.count(next_heading) == 1, cont.count(next_heading)
start_block = """## R14.12 START authority

- Dedicated branch: `r14/12-content-delivery`.
- Exact branch point: normalized R14.11 `main` `71ceb529e89b13be343be76527e9b9b0b419ceda`.
- R14.11 normalization: `5356f2354d8c2237ccb6a3957b1c2cde21d4de80`; R0 #1865 / `33242852652`, Python Core #1839 / `33242852691`, UI #1806 / `33242852613` SUCCESS; PR #278 expected-head merge produced the exact normalized base.
- State at START: R14.1–R14.11 COMPLETE + NORMALIZED; R14.12 IN_PROGRESS; R14.13–R14.17 PLANNED.
- Core content authority: immutable manifest/bundle identity + digest, typed compatibility bounds, acyclic bounded dependencies, non-executable payload policy, deterministic local provider, exact size/hash verification, atomic cache promotion, explicit channel promotion/rollback, environment isolation and governed network endpoints.
- Manual state: CONDITIONAL / NOT TRIGGERED. No external CDN/domain/account/credential is required for core acceptance; `provider_live_claim=false`.

"""
pos = cont.index(next_heading)
cont = cont[:pos] + start_block + cont[pos:]

old_next = "If this file is read from `r14/11-normalization`, verify its exact diff from merge `a32b62c4e961ed2f5fe66dd5e30c453abb64d9f1` contains only this continuity file, run fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke, and merge the single normalization PR only with `expected_head_sha` equal to that exact normalization head. If this file is read from `main` after that protected merge, R14.11 is COMPLETE + NORMALIZED and R14.12 becomes the next authorized subdivision; start R14.12 only from that normalized `main` with a dedicated branch and START-sync. Manual state for R14.11 remains NONE."
new_next = "Verify the final R14.12 START head differs from normalized `main` `71ceb529e89b13be343be76527e9b9b0b419ceda` only by `docs/roadmap/R14_PLAN.md` and this continuity file. Only after that clean compare may R14.12 implementation begin. Implement immutable/hash-addressed content manifest/bundle/channel/cache/rollback contracts with non-executable payload rejection, dependency/compatibility/integrity checks, bounded local delivery and deterministic evidence. Do not claim external CDN/provider success or request credentials. Manual state remains CONDITIONAL / NOT TRIGGERED."
assert cont.count(old_next) == 1, cont.count(old_next)
cont = cont.replace(old_next, new_next)
cont_path.write_text(cont, encoding="utf-8")
