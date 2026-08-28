from pathlib import Path
import re

plan = Path('docs/roadmap/R14_PLAN.md')
s = plan.read_text(encoding='utf-8')
new_checkpoint = "**Execution checkpoint:** R1–R13 are COMPLETE + NORMALIZED; R14 planning is ACCEPTED + NORMALIZED. R14.1 is COMPLETE + NORMALIZED. R14.2 is COMPLETE + NORMALIZED on `main` `bf66970f358df580d5fe15b1ac1f8ed2cb13b09d`: immutable technical source `4e04812380a495dd799e1d7b9e96741d8688de31` passed R0 #1761 / `33143230642`, Python #1735 / `33143230580`, UI #1702 / `33143230613`; final END-head `cc034784b6b3350f3e24ece55e5d2304fa60705c` passed R0 #1766 / `33143514421`, Python #1740 / `33143514423`, UI #1707 / `33143514466`; PR #259 merged as `ad5de7c1697d061946bf75220420c75b73851531`; single continuity-only normalization head `b3587acf2a9c37d2e407a62bc1e805863f553564` passed R0 #1768 / `33145379528`, Python #1742 / `33145379581`, UI #1709 / `33145379554`; PR #260 merged as normalized `main` `bf66970f358df580d5fe15b1ac1f8ed2cb13b09d`. R14.3 is IN_PROGRESS on `r14/03-local-backend-runtime`; R14.4–R14.17 remain PLANNED. Manual state for R14.3 is NONE."
s, n = re.subn(r'(?m)^\*\*Execution checkpoint:\*\*.*$', new_checkpoint, s, count=1)
if n != 1:
    raise SystemExit('execution checkpoint replacement failed')
old_row = '| R14.3 | Deterministic local backend scaffold/runtime + environments/config/secrets/health | PLANNED | NONE | R14.1–R14.2 + R8/R12 patterns |'
new_row = '| R14.3 | Deterministic local backend scaffold/runtime + environments/config/secrets/health | IN_PROGRESS | NONE | R14.1–R14.2 + R8/R12 patterns |'
if old_row not in s:
    raise SystemExit('R14.3 index row not found')
s = s.replace(old_row, new_row, 1)
old_status = '- Current subdivision status: `COMPLETE` at technical/evidence level. R14.3 remains `PLANNED` until R14.2 implementation merge and single continuity-only normalization are accepted.'
new_status = "- Final END-head `cc034784b6b3350f3e24ece55e5d2304fa60705c` passed R0 #1766 / `33143514421`, Python Core #1740 / `33143514423`, and UI #1707 / `33143514466`; PR #259 merged as `ad5de7c1697d061946bf75220420c75b73851531`.\n- Single continuity-only normalization head `b3587acf2a9c37d2e407a62bc1e805863f553564` passed R0 #1768 / `33145379528`, Python Core #1742 / `33145379581`, and UI #1709 / `33145379554`; PR #260 merged as normalized `main` `bf66970f358df580d5fe15b1ac1f8ed2cb13b09d`.\n- Current subdivision status: `COMPLETE + NORMALIZED`. R14.3 is authorized and starts from that exact normalized main."
if old_status not in s:
    raise SystemExit('R14.2 completion status marker not found')
s = s.replace(old_status, new_status, 1)
plan.write_text(s, encoding='utf-8')

cont = Path('docs/continuity/KODEPOIA_CONTINUITY.md')
c = cont.read_text(encoding='utf-8')
new_prompt = "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.2 COMPLETE + NORMALIZED. R14.3 IN_PROGRESS on `r14/03-local-backend-runtime`; R14.4–R14.17 remain PLANNED.** R14.2 immutable technical source `4e04812380a495dd799e1d7b9e96741d8688de31` passed R0 #1761 / `33143230642`, Python #1735 / `33143230580`, UI #1702 / `33143230613`; END-head `cc034784b6b3350f3e24ece55e5d2304fa60705c` passed R0 #1766 / `33143514421`, Python #1740 / `33143514423`, UI #1707 / `33143514466`; PR #259 merged as `ad5de7c1697d061946bf75220420c75b73851531`; normalization head `b3587acf2a9c37d2e407a62bc1e805863f553564` passed R0 #1768 / `33145379528`, Python #1742 / `33145379581`, UI #1709 / `33145379554`; PR #260 merged as normalized `main` `bf66970f358df580d5fe15b1ac1f8ed2cb13b09d`. R14.3 starts exactly from that main. Manual state is NONE."
c, n = re.subn(r'(?m)^> Kodepoia, architecture v1\.0 gelée\..*$', new_prompt, c, count=1)
if n != 1:
    raise SystemExit('continuity prompt replacement failed')
new_global = "- R14 planning: **ACCEPTED + NORMALIZED**. R14.1–R14.2 are **COMPLETE + NORMALIZED**. R14.2 normalized main is **`bf66970f358df580d5fe15b1ac1f8ed2cb13b09d`** after implementation/evidence PR #259 and continuity-only normalization PR #260. R14.3 is **IN_PROGRESS** on `r14/03-local-backend-runtime`; R14.4–R14.17 remain PLANNED. Manual **NONE**."
c, n = re.subn(r'(?m)^- R14 planning:.*$', new_global, c, count=1)
if n != 1:
    raise SystemExit('continuity R14 global replacement failed')
old_decl = '- This normalization candidate declares the resulting main state **R14.2 COMPLETE + NORMALIZED** and keeps R14.3 **PLANNED**. The declaration becomes authoritative only when this exact candidate passes fresh R0 Repository Guard + full Python Core + KodeStudio UI Smoke and its PR merges with expected-head protection.'
new_decl = "- Final normalization head `b3587acf2a9c37d2e407a62bc1e805863f553564` changed exactly this continuity file and passed R0 #1768 / `33145379528`, Python Core #1742 / `33145379581`, and UI #1709 / `33145379554`, all SUCCESS.\n- Normalization PR #260 merged with expected-head protection as normalized `main` `bf66970f358df580d5fe15b1ac1f8ed2cb13b09d`. Therefore R14.2 is authoritatively **COMPLETE + NORMALIZED** and R14.3 is authorized."
if old_decl not in c:
    raise SystemExit('R14.2 normalization declaration marker not found')
c = c.replace(old_decl, new_decl, 1)
anchor = '## R14.1 post-merge normalization authority\n'
r14_3 = """## R14.3 start authority\n\n- Dedicated branch: `r14/03-local-backend-runtime`.\n- Exact branch point: normalized `main` `bf66970f358df580d5fe15b1ac1f8ed2cb13b09d`.\n- R14.1–R14.2 are COMPLETE + NORMALIZED; R14.3 is IN_PROGRESS; R14.4–R14.17 remain PLANNED.\n- Frozen R14.3 scope: deterministic local backend scaffold/workspace, repository-owned bounded local runner, typed configuration/environment overlays, KodeSecrets references, loopback-first bind policy, health/readiness/liveness, graceful shutdown, redacted logs and reproducible fixture service. No public deployment, auth semantics, production TLS termination, managed hosting or later R14 service semantics.\n- Manual intervention: **NONE**.\n\n"""
if anchor not in c:
    raise SystemExit('R14.3 continuity anchor not found')
c = c.replace(anchor, r14_3 + anchor, 1)
cont.write_text(c, encoding='utf-8')
print('R14.3 START-sync applied')
