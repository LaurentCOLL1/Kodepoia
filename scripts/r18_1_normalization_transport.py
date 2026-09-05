from pathlib import Path

PATH = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
lines = PATH.read_text(encoding="utf-8").splitlines()

new_top = "> Kodepoia, architecture v1.0 gelée. **R1–R17 COMPLETE + NORMALIZED. R18 planning ACCEPTED + NORMALIZED on canonical `main` `bbffc382d4fb8a7d947345da11b56459d0fec825`. R18.1 Canonical release identity, versions and channels is COMPLETE + NORMALIZED effective when this unique post-merge continuity-only normalization record enters `main`; exact-END `73f1d7426902a79a3b3f328debd8ad90d1112913` passed R18.1 #49 / `33938711143`, R0 #2435 / `33938711343`, Python Core #2407 / `33938711189` 5/5 and KodeStudio UI Smoke #2372 / `33938711219`, then implementation/evidence PR #382 merged with that exact expected head as `main` `4e6793f7aa74352dfe63085633f34b61ff8cb215`. R18.2 START-sync is authorized only from the normalized `main` produced by this record's fresh exact-head gated merge.** Production signing, public GitHub Release publication and public WinGet submission remain CONDITIONAL / NOT TRIGGERED."

new_r181 = "- R18.1 : **COMPLETE + NORMALIZED effective when this unique continuity-only normalization record enters `main` through fresh exact-head R0/Python/UI gates and exact expected-head merge** — normalized R18 planning base `bbffc382d4fb8a7d947345da11b56459d0fec825`; dedicated implementation branch `r18/01-release-identity`; immutable technical source `8fda649829acfd5abae2ea31e9c744f8554b8d06`. Exact-source technical R18.1 #34 / `33928967043` SUCCESS Ubuntu + Windows with compile, Ruff, 6/6 focused tests, packaged-wheel canonical identity verification and 21/21 acceptance checks; acceptance `1bf94b74713522149083b608c0664c215ba12304244fb6d6ec04e280291f883d`; canonical identity `Kodepoia` / `kodepoia`, channel `beta`, build type `prerelease`, PEP 440 `1.1.0rc1`, public/installer `1.1.0-rc1`, identity `d0cd93c16846980ac8e633bd23f2930969f2d249040452c5529095de1cd40ef1`, schema `0c4dfdd550cd14bccbdcf03a6f3b1403e0bff3c2afed6b61803f7e1ee6612b4f`, `source_binding=exact-head`; technical R0 #2428 / `33928967169`, Python Core #2400 / `33928967172` and UI #2365 / `33928967128` also SUCCESS. Final exact-END head `73f1d7426902a79a3b3f328debd8ad90d1112913` is one child of the immutable technical source and changes exactly `docs/roadmap/R18_PLAN.md` + this continuity file; fresh exact-END R18.1 #49 / `33938711143` SUCCESS Ubuntu + Windows, R0 #2435 / `33938711343` SUCCESS Ubuntu + Windows, Python Core #2407 / `33938711189` SUCCESS 5/5 and KodeStudio UI Smoke #2372 / `33938711219` SUCCESS Windows. Historical PR #381 is superseded only because its branch lineage was deliberately rebuilt to remove temporary END-sync transports and an accidental line-ending mutation; clean implementation/evidence PR #382 merged with `expected_head_sha=73f1d7426902a79a3b3f328debd8ad90d1112913` as `main` `4e6793f7aa74352dfe63085633f34b61ff8cb215`. Historical R16.17/R16.18 release-readiness failures remain non-authoritative frozen-v1.0 emitters, not R18.1 gates. Manual NONE. Production signing/public GitHub Release/public WinGet submission remain NOT TRIGGERED. This record is the single authorized post-merge continuity-only R18.1 normalization authority; no second R18.1 normalization is authorized. R18.2 START-sync is authorized only from the normalized `main` produced when this exact record passes fresh R0/Python/UI and merges with exact expected-head protection."

new_next = "R18.1 implementation/evidence is merged as `main` `4e6793f7aa74352dfe63085633f34b61ff8cb215` from exact-END `73f1d7426902a79a3b3f328debd8ad90d1112913`, and this record is the unique continuity-only post-merge R18.1 normalization authority. The next authorized action is to run fresh exact-head R0 Repository Guard, full Python Core and KodeStudio UI Smoke on this normalization head, then merge its normalization PR only with that exact expected head. **Once that merge produces the normalized `main`, R18.2 START-sync is authorized from that exact normalized main. Do not start R18.2 from implementation merge `4e6793f7aa74352dfe63085633f34b61ff8cb215` or from this unmerged normalization candidate.**"

new_r18_state = "- State: **PLANNING ACCEPTED + NORMALIZED** — unique planning-normalization PR #380 merged as canonical `main` `bbffc382d4fb8a7d947345da11b56459d0fec825`; R18.1 implementation/evidence PR #382 merged exact-END `73f1d7426902a79a3b3f328debd8ad90d1112913` as `main` `4e6793f7aa74352dfe63085633f34b61ff8cb215`, and its unique continuity-only post-merge normalization is now the only pending R18.1 action. R18.2 is not authorized until that normalization merges."

assert lines[0].startswith("> Kodepoia, architecture v1.0 gelée.")
lines[0] = new_top

r181 = [i for i, line in enumerate(lines) if line.startswith("- R18.1 :")]
assert len(r181) == 1, r181
lines[r181[0]] = new_r181

next_lines = [i for i, line in enumerate(lines) if line.startswith("R18.1 is COMPLETE at END-sync on immutable technical source")]
assert len(next_lines) == 1, next_lines
lines[next_lines[0]] = new_next

state_lines = [i for i, line in enumerate(lines) if line.startswith("- State: **PLANNING ACCEPTED + NORMALIZED**")]
assert len(state_lines) == 1, state_lines
lines[state_lines[0]] = new_r18_state

out = "\n".join(lines) + "\n"
assert "PR #381 merge" not in out
assert "R18.1 is COMPLETE at END-sync" not in out
assert "R18.1 : **COMPLETE + NORMALIZED effective" in out
assert "R18.2 START-sync is authorized only from the normalized `main`" in out
PATH.write_text(out, encoding="utf-8", newline="\n")

# Transport retry marker: workflow stages continuity explicitly.
