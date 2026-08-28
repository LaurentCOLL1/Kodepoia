from pathlib import Path
import re

TECH="4de5036e7a37f949ec64ae68d9ee45e57ac99631"
R0="#1770 / `33146235062`"
PY="#1744 / `33146235104`"
UI="#1711 / `33146235181`"

plan=Path('docs/roadmap/R14_PLAN.md')
s=plan.read_text(encoding='utf-8')
s,n=re.subn(
    r'(?m)^\*\*Execution checkpoint:\*\*.*$',
    "**Execution checkpoint:** R1–R13 are COMPLETE + NORMALIZED; R14 planning is ACCEPTED + NORMALIZED. R14.1–R14.2 are COMPLETE + NORMALIZED on normalized `main` `bf66970f358df580d5fe15b1ac1f8ed2cb13b09d`. R14.3 accepted immutable technical source `4de5036e7a37f949ec64ae68d9ee45e57ac99631` passed R0 #1770 / `33146235062`, Python Core #1744 / `33146235104`, and UI #1711 / `33146235181`, all SUCCESS; Ubuntu full Python suite recorded 1477 passed / 13 skipped / 46 warnings and Windows Core also passed. R14.3 is COMPLETE at technical/evidence level on `r14/03-local-backend-runtime`; final END-synchronized exact-head re-gates and PR #261 merge remain pending. R14.4–R14.17 remain PLANNED. Manual state for R14.3 is NONE.",
    s,count=1)
if n!=1: raise SystemExit('plan execution checkpoint marker not found')
old='| R14.3 | Deterministic local backend scaffold/runtime + environments/config/secrets/health | IN_PROGRESS | NONE | R14.1–R14.2 + R8/R12 patterns |'
new='| R14.3 | Deterministic local backend scaffold/runtime + environments/config/secrets/health | COMPLETE | NONE | R14.1–R14.2 + R8/R12 patterns |'
if old not in s: raise SystemExit('R14.3 index row not found')
s=s.replace(old,new,1)
old='## Completion record\n\nTo be appended when accepted.\n\n---\n\n# R14.4 — Auth, identity, sessions, tokens, passkeys/OIDC provider-neutral boundary'
new='''## Completion record

- Accepted immutable technical head: `4de5036e7a37f949ec64ae68d9ee45e57ac99631`.
- Technical exact-head gates: R0 Repository Guard #1770 / `33146235062` SUCCESS; Python Core #1744 / `33146235104` SUCCESS; KodeStudio UI Smoke #1711 / `33146235181` SUCCESS.
- Ubuntu full Python suite: 1477 passed, 13 skipped, 46 warnings; Windows Core suite also SUCCESS; both package builds and Python internal UI smoke SUCCESS.
- Focused implementation/compatibility prevalidation `33146069094`: 36 passed after compileall.
- Cross-platform focused runtime validation `33146135676`: Ubuntu SUCCESS and Windows SUCCESS. A duplicate cleanup invocation later failed only because another invocation had already removed the temporary workflow/trigger; the tested implementation tree remained unchanged and the cumulative implementation diff contains no temporary files.
- Manual intervention: NONE.
- Current subdivision status: `COMPLETE` at technical/evidence level. R14.4 remains `PLANNED` until R14.3 implementation/evidence merge and single continuity-only normalization are accepted.

---

# R14.4 — Auth, identity, sessions, tokens, passkeys/OIDC provider-neutral boundary'''
if old not in s: raise SystemExit('R14.3 completion block marker not found')
s=s.replace(old,new,1)
plan.write_text(s,encoding='utf-8',newline='\n')

ledger=Path('docs/roadmap/R14_3_ACCEPTANCE.md')
l=ledger.read_text(encoding='utf-8')
l=l.replace('**Status: IMPLEMENTATION_CANDIDATE_PENDING**','**Status: TECHNICAL_CANDIDATE_ACCEPTED / FINAL_REGATES_PENDING**',1)
anchor='## Manual intervention\n\n**NONE.** No provider account, secret, paid quota, public endpoint, production certificate, managed host or device is required for R14.3 acceptance.\n'
record='''## Accepted technical candidate record

- Immutable source SHA: `4de5036e7a37f949ec64ae68d9ee45e57ac99631`.
- R0 Repository Guard #1770 / `33146235062`: COMPLETED / SUCCESS.
- Python Core #1744 / `33146235104`: COMPLETED / SUCCESS; Ubuntu full `pytest` = **1477 passed, 13 skipped, 46 warnings**; Windows Core = SUCCESS; both package builds and Python internal KodeStudio smoke = SUCCESS.
- KodeStudio UI Smoke #1711 / `33146235181`: COMPLETED / SUCCESS.
- Focused implementation/compatibility prevalidation `33146069094`: **36 passed** after compileall; diagnostic only and non-authoritative for merge acceptance.
- Cross-platform focused runtime prevalidation `33146135676`: Ubuntu SUCCESS and Windows SUCCESS. A second duplicate cleanup invocation failed only because the temporary files had already been deleted by the first invocation; no implementation test failed and no temporary file remains in the accepted tree.
- Accepted implementation tree: `693662541c60387ecbb14d0994c66266696a9153`.
- Manual intervention: NONE.
- Next authority: END-synchronized documentation/evidence head changing only plan, this ledger and continuity, followed by fresh exact-head R0/Python/UI.

## End synchronization and normalization

The accepted technical source is immutable. END-sync may change only `docs/roadmap/R14_PLAN.md`, this ledger and `docs/continuity/KODEPOIA_CONTINUITY.md`. That final head must pass fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke before PR #261 may merge with expected-head protection. Then exactly one continuity-only post-merge normalization must pass another fresh exact-head R0/Python/UI before R14.3 is COMPLETE + NORMALIZED and R14.4 is authorized.

'''
if anchor not in l: raise SystemExit('ledger manual marker not found')
l=l.replace(anchor,record+anchor,1)
ledger.write_text(l,encoding='utf-8',newline='\n')

cont=Path('docs/continuity/KODEPOIA_CONTINUITY.md')
c=cont.read_text(encoding='utf-8')
new_prompt="> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.2 COMPLETE + NORMALIZED. R14.3 COMPLETE at technical/evidence level on `r14/03-local-backend-runtime`; final END-synchronized exact-head re-gates and PR #261 merge remain pending. R14.4–R14.17 remain PLANNED.** R14.3 accepted immutable technical source `4de5036e7a37f949ec64ae68d9ee45e57ac99631` passed R0 #1770 / `33146235062`, Python Core #1744 / `33146235104`, and UI #1711 / `33146235181`, all SUCCESS; Ubuntu full suite recorded 1477 passed / 13 skipped / 46 warnings and Windows Core also passed. Focused prevalidation `33146069094` passed 36 tests; cross-platform runtime validation `33146135676` passed on Ubuntu and Windows. No implementation semantics may change during END-sync. After fresh final R0 + Python Core + UI on the END head, merge #261 with expected-head protection, then perform exactly one continuity-only normalization before R14.3 becomes COMPLETE + NORMALIZED and R14.4 is authorized. Manual state is NONE."
c,n=re.subn(r'(?m)^> Kodepoia, architecture v1\.0 gelée\..*$',new_prompt,c,count=1)
if n!=1: raise SystemExit('continuity prompt not found')
new_global="- R14 planning: **ACCEPTED + NORMALIZED**. R14.1–R14.2 are **COMPLETE + NORMALIZED**. R14.3 accepted immutable technical source **`4de5036e7a37f949ec64ae68d9ee45e57ac99631`** passed R0 #1770 / `33146235062`, Python Core #1744 / `33146235104`, and UI #1711 / `33146235181`, all SUCCESS. R14.3 is **COMPLETE / FINAL_DOCUMENTATION_REGATES_PENDING** on `r14/03-local-backend-runtime`; R14.4–R14.17 remain PLANNED. Manual **NONE**."
c,n=re.subn(r'(?m)^- R14 planning:.*$',new_global,c,count=1)
if n!=1: raise SystemExit('continuity R14 global line not found')
old='''## R14.3 start authority

- Dedicated branch: `r14/03-local-backend-runtime`.
- Exact branch point: normalized `main` `bf66970f358df580d5fe15b1ac1f8ed2cb13b09d`.
- R14.1–R14.2 are COMPLETE + NORMALIZED; R14.3 is IN_PROGRESS; R14.4–R14.17 remain PLANNED.
- Frozen R14.3 scope: deterministic local backend scaffold/workspace, repository-owned bounded local runner, typed configuration/environment overlays, KodeSecrets references, loopback-first bind policy, health/readiness/liveness, graceful shutdown, redacted logs and reproducible fixture service. No public deployment, auth semantics, production TLS termination, managed hosting or later R14 service semantics.
- Manual intervention: **NONE**.
'''
new='''## R14.3 technical acceptance authority

- Dedicated branch: `r14/03-local-backend-runtime`, started exactly from normalized `main` `bf66970f358df580d5fe15b1ac1f8ed2cb13b09d`.
- Mandatory START-sync head `86dd7e43a2d2895909f8ecd95a743099fc37c55f` changed exactly `docs/roadmap/R14_PLAN.md` and continuity before implementation.
- Accepted immutable technical source: `4de5036e7a37f949ec64ae68d9ee45e57ac99631`, tree `693662541c60387ecbb14d0994c66266696a9153`.
- Technical exact-head gates: R0 #1770 / `33146235062`, Python Core #1744 / `33146235104`, KodeStudio UI Smoke #1711 / `33146235181`, all SUCCESS.
- Ubuntu full Python suite: 1477 passed / 13 skipped / 46 warnings; Windows Core, both package builds and Python internal UI smoke also SUCCESS.
- Focused `33146069094`: 36 passed after compileall. Cross-platform focused `33146135676`: runtime tests SUCCESS on Ubuntu and Windows; a duplicate cleanup race did not affect the tested implementation and no temporary file remains in the accepted tree.
- Frozen R14.3 scope: deterministic local backend scaffold/workspace, repository-owned bounded local runner, typed configuration/environment overlays, KodeSecrets references, loopback-first bind policy, health/readiness/liveness, graceful shutdown, redacted logs and reproducible fixture service. No public deployment, auth semantics, production TLS termination, managed hosting or later R14 service semantics.
- R14.3 is COMPLETE at technical/evidence level; R14.4 remains PLANNED pending final END re-gates, PR #261 merge and one continuity-only normalization.
- Manual intervention: **NONE**.
'''
if old not in c: raise SystemExit('R14.3 start authority block not found')
c=c.replace(old,new,1)
cont.write_text(c,encoding='utf-8',newline='\n')
print('R14.3 END-sync applied')
