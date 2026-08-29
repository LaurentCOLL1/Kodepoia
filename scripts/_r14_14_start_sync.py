from pathlib import Path

BASE_SHA = "b56162e0903bf2dc29505dfb6385030ed5d4b9d4"
BRANCH = "r14/14-liveops-campaigns-schedules"
PLAN_PATH = Path("docs/roadmap/R14_PLAN.md")
CONTINUITY_PATH = Path("docs/continuity/KODEPOIA_CONTINUITY.md")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected exactly one occurrence, found {count}")
    return text.replace(old, new, 1)


def replace_line(text: str, prefix: str, replacement: str, label: str) -> str:
    lines = text.splitlines()
    matches = [index for index, line in enumerate(lines) if line.startswith(prefix)]
    if len(matches) != 1:
        raise AssertionError(f"{label}: expected one line with prefix {prefix!r}, found {len(matches)}")
    lines[matches[0]] = replacement
    return "\n".join(lines) + "\n"


plan = PLAN_PATH.read_text(encoding="utf-8")
plan = replace_line(
    plan,
    "**Execution checkpoint:**",
    "**Execution checkpoint:** R1–R13 are COMPLETE + NORMALIZED; R14 planning is ACCEPTED + NORMALIZED. R14.1–R14.13 are COMPLETE + NORMALIZED on normalized `main` `b56162e0903bf2dc29505dfb6385030ed5d4b9d4`. R14.14 is IN_PROGRESS on dedicated branch `r14/14-liveops-campaigns-schedules`; R14.15–R14.17 remain PLANNED. R14.14 manual state is NONE. R14.13 immutable technical source `b1729cabaffb19ac5491dee8a2c18e1bb5877746`; final END-head `5461815da316bf9e20b06352dc7dda8699b46525`; implementation/evidence merge PR #281 `e1109c84a4b55761e4bf948b13457aabd327669e`; unique normalization head `6d302f20ba05544d1a1f122ebed48816dd22c76b`; normalization PR #282 expected-head merge produced normalized `main` `b56162e0903bf2dc29505dfb6385030ed5d4b9d4` after fresh R0 #1902 / `33247706878`, Python Core #1877 / `33247706820`, and UI #1842 / `33247706847` SUCCESS.",
    "plan execution checkpoint",
)
plan = replace_once(
    plan,
    "| R14.14 | LiveOps campaigns, seasons, schedules, rotations, activation + rollback | PLANNED | NONE | R14.10–R14.13 |",
    "| R14.14 | LiveOps campaigns, seasons, schedules, rotations, activation + rollback | IN_PROGRESS | NONE | R14.10–R14.13 |",
    "plan R14.14 status row",
)
start_marker = "# R14.14 — LiveOps campaigns, seasons, schedules, rotations, activation + rollback"
if "## R14.14 START authority" in plan:
    raise AssertionError("plan already contains R14.14 START authority")
if plan.count(start_marker) != 1:
    raise AssertionError("expected exactly one R14.14 heading")
start_block = f"""## R14.14 START authority

- Dedicated branch: `{BRANCH}`.
- Exact branch point: normalized R14.13 `main` `{BASE_SHA}`.
- R14.13 closure authority: immutable technical source `b1729cabaffb19ac5491dee8a2c18e1bb5877746`; final END-head `5461815da316bf9e20b06352dc7dda8699b46525`; fresh END gates R0 #1898 / `33247444761`, Python Core #1873 / `33247444733`, UI #1838 / `33247444748`, R14 Event Pipeline #5 / `33247444765` SUCCESS; PR #281 expected-head merge `e1109c84a4b55761e4bf948b13457aabd327669e`; unique normalization head `6d302f20ba05544d1a1f122ebed48816dd22c76b`; fresh normalization gates R0 #1902 / `33247706878`, Python Core #1877 / `33247706820`, UI #1842 / `33247706847` SUCCESS; PR #282 expected-head merge produced normalized `main` `{BASE_SHA}`.
- START state: R14.1–R14.13 COMPLETE + NORMALIZED; R14.14 IN_PROGRESS; R14.15–R14.17 PLANNED.
- Time authority baseline: scheduler state is canonical UTC instants; named display/recurrence timezone identifiers remain explicit metadata. IANA Time Zone Database `2026c` (released 2026-07-08) is current compatibility evidence, and RFC 5545 is informative recurrence/TZID guidance. These are versioned evidence, not frozen runtime constants.
- Core acceptance remains provider-neutral and network-free. No production LiveOps provider/account/credential is required. Manual intervention: NONE.

---

"""
plan = plan.replace(start_marker, start_block + start_marker, 1)
PLAN_PATH.write_text(plan, encoding="utf-8", newline="\n")

continuity = CONTINUITY_PATH.read_text(encoding="utf-8")
continuity = replace_once(
    continuity,
    "**R14.1–R14.13 COMPLETE + NORMALIZED. R14.14–R14.17 PLANNED.**",
    "**R14.1–R14.13 COMPLETE + NORMALIZED. R14.14 IN_PROGRESS. R14.15–R14.17 PLANNED.**",
    "continuity prompt status",
)
continuity = replace_once(
    continuity,
    "This branch carries the unique continuity-only R14.13 normalization; it still must pass fresh R0 + full Python Core + UI and merge with expected-head before R14.14 is authorized.",
    "R14.13 normalization head `6d302f20ba05544d1a1f122ebed48816dd22c76b` passed fresh R0 #1902 / `33247706878`, Python Core #1877 / `33247706820`, UI #1842 / `33247706847`; PR #282 expected-head merge produced normalized `main` `b56162e0903bf2dc29505dfb6385030ed5d4b9d4`. R14.14 is authorized and IN_PROGRESS from that exact main on `r14/14-liveops-campaigns-schedules`.",
    "continuity prompt normalization clause",
)
continuity = replace_line(
    continuity,
    "- R14.13 : **COMPLETE + NORMALIZED**",
    "- R14.13 : **COMPLETE + NORMALIZED** — source technique `b1729cabaffb19ac5491dee8a2c18e1bb5877746`; END-head `5461815da316bf9e20b06352dc7dda8699b46525`; PR #281 merge `e1109c84a4b55761e4bf948b13457aabd327669e`; normalization head `6d302f20ba05544d1a1f122ebed48816dd22c76b`; normalized `main` `b56162e0903bf2dc29505dfb6385030ed5d4b9d4` via PR #282 after fresh R0 #1902 / `33247706878`, Python Core #1877 / `33247706820`, UI #1842 / `33247706847` SUCCESS.",
    "continuity R14.13 global line",
)
continuity = replace_once(
    continuity,
    "- R14.14–R14.17 : **PLANNED**.",
    "- R14.14 : **IN_PROGRESS** on `r14/14-liveops-campaigns-schedules` from normalized `main` `b56162e0903bf2dc29505dfb6385030ed5d4b9d4`.\n- R14.15–R14.17 : **PLANNED**.",
    "continuity future status line",
)
continuity = replace_once(
    continuity,
    "| R14.14 | PLANNED | NONE |",
    "| R14.14 | IN_PROGRESS | NONE |",
    "continuity R14.14 table row",
)
continuity = replace_once(
    continuity,
    "- Unique post-merge normalization branch `r14/13-normalization` was created exactly from merge `e1109c84a4b55761e4bf948b13457aabd327669e`; its final tree delta must contain only this continuity file and must pass fresh exact-head R0/Python/UI before expected-head merge.",
    "- Unique post-merge normalization head `6d302f20ba05544d1a1f122ebed48816dd22c76b` changed only this continuity file; fresh exact-head R0 #1902 / `33247706878`, Python Core #1877 / `33247706820` (5/5; Ubuntu 1692 passed / 13 skipped / 46 warnings), and UI #1842 / `33247706847` all SUCCESS. PR #282 merged with `expected_head_sha=6d302f20ba05544d1a1f122ebed48816dd22c76b` as normalized `main` `b56162e0903bf2dc29505dfb6385030ed5d4b9d4`.",
    "continuity normalization closure line",
)
continuity = replace_once(
    continuity,
    "- R14.13 final state is COMPLETE + NORMALIZED once that unique normalization PR merges; R14.14–R14.17 remain PLANNED until then.",
    "- R14.13 final state: **COMPLETE + NORMALIZED** on `main` `b56162e0903bf2dc29505dfb6385030ed5d4b9d4`. R14.14 is now IN_PROGRESS; R14.15–R14.17 remain PLANNED.",
    "continuity R14.13 final state",
)
next_marker = "\n## Next authorized action\n"
if continuity.count(next_marker) != 1:
    raise AssertionError("expected exactly one Next authorized action section")
prefix, _old_tail = continuity.split(next_marker, 1)
continuity = prefix + f"""

## R14.14 START authority

- Dedicated branch: `{BRANCH}`.
- Exact branch point and sole authorized base: normalized R14.13 `main` `{BASE_SHA}`.
- START state: R14.1–R14.13 COMPLETE + NORMALIZED; R14.14 IN_PROGRESS; R14.15–R14.17 PLANNED.
- R14.14 scope: campaigns/seasons/schedules/rotations; immutable references to config/content/catalog/event contracts; governed feature-flag audience targeting; canonical UTC activation windows with explicit display/recurrence TZID; preview/simulation without mutation; approval/SafeChange binding; idempotent activation; explicit pause/expiry/rollback/kill; bounded audit/evidence.
- Compatibility evidence: IANA tzdb `2026c` released 2026-07-08; RFC 5545 recurrence/TZID semantics are informative. Runtime authority remains explicit UTC instants plus versioned timezone metadata rather than assuming permanent civil-time rules.
- Manual state: NONE. Core acceptance requires no external LiveOps SaaS, billing provider, CDN, event broker, OTel collector, production account or credential.

## Next authorized action

Implement R14.14 only on `{BRANCH}` after this START-sync head is verified to differ from normalized base `{BASE_SHA}` by plan + continuity only. Build focused/adversarial LiveOps tests and deterministic acceptance on an immutable technical source; do not advance to R14.15 before expected-head merge plus the single continuity-only post-merge normalization of R14.14. If any manual/provider-live gate becomes genuinely required, stop and mark it truthfully instead of synthesizing PASS.
"""
CONTINUITY_PATH.write_text(continuity, encoding="utf-8", newline="\n")
