from pathlib import Path

plan_path = Path("docs/roadmap/R15_PLAN.md")
continuity_path = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
plan = plan_path.read_text(encoding="utf-8")
continuity = continuity_path.read_text(encoding="utf-8")

old_source = "527b498e79306425574dc724d00f5edd4a8d14e3"
new_source = "6f49a72918d4ddb4ae4d779e85513ae721688c49"

if plan.count(old_source) != 1:
    raise SystemExit("R15.11 plan technical-source cardinality mismatch")
plan = plan.replace(old_source, new_source)

if continuity.count(old_source) != 2:
    raise SystemExit("R15.11 continuity technical-source cardinality mismatch")
continuity = continuity.replace(old_source, new_source)

plan_path.write_text(plan, encoding="utf-8")
continuity_path.write_text(continuity, encoding="utf-8")
