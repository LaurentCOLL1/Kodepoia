from pathlib import Path

path = Path("docs/roadmap/R14_11_ACCEPTANCE.md")
text = path.read_text(encoding="utf-8")
old_status = "**Technical status:** ACCEPTED — END synchronization pending  \n"
new_status = "**Technical status:** ACCEPTED — END-head candidate ready for fresh gates  \n"
assert text.count(old_status) == 1, text.count(old_status)
text = text.replace(old_status, new_status)
old_base = "**Exact normalized base:** `a9db57de1c1cc550604edbe6fec095e0a8e13c40`  \n"
new_base = old_base + "**Pull request:** #277  \n"
assert text.count(old_base) == 1, text.count(old_base)
text = text.replace(old_base, new_base)
old_tail = "That exact END-head must pass fresh R0 Repository Guard + full Python Core + KodeStudio UI Smoke + R14 Remote Config Acceptance before merge with `expected_head_sha`. After merge, exactly one continuity-only normalization with fresh R0/Python/UI is required before R14.12 is authorized."
new_tail = old_tail + "\n\nThe assertion-guarded END synchronization completed without any implementation-byte change. PR #277 carries the final R14.11 END-head candidate; its exact diff from the immutable source must remain restricted to the three documentation files above."
assert text.count(old_tail) == 1, text.count(old_tail)
text = text.replace(old_tail, new_tail)
path.write_text(text, encoding="utf-8")
