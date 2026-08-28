from pathlib import Path

OBJECTS = '("points", "ach", "board", "time-ms", "classic", "recurring", "fastest", "other", "missing", "tiny", "score-10")'

for raw in (
    "tests/test_r14_9_progression_leaderboards.py",
    "scripts/r14_9_progression_acceptance.py",
):
    path = Path(raw)
    text = path.read_text(encoding="utf-8")
    old = 'return AuthorityActorContext("ops", "sess-ops", ("*",), ("*",))'
    new = f'return AuthorityActorContext("ops", "sess-ops", ("*",), {OBJECTS})'
    assert text.count(old) == 1, (raw, text.count(old))
    path.write_text(text.replace(old, new), encoding="utf-8")
