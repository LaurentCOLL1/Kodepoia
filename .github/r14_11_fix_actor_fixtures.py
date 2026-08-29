from pathlib import Path

DEFAULT_TEST_OBJECTS = '''DEFAULT_AUTHORIZED_OBJECTS = (
    "a",
    "b",
    "base",
    "base.enabled",
    "c",
    "cycle",
    "cycle.a",
    "cycle.b",
    "dependent",
    "feature.alpha",
    "feature.expiring",
    "layout",
    "message",
    "message.banner",
    "missing",
    "other",
    "prod-s1",
    "production",
    "s1",
    "s2",
    "test",
    "test-s1",
    "tiny.flag",
    "tiny-v1",
    "tiny-v2",
    "unauthorized",
    "unauthorized.flag",
)


'''

path = Path("tests/test_r14_11_remote_config.py")
text = path.read_text(encoding="utf-8")
anchor = '''class Clock:
    def __init__(self, value: int = 1_000_000) -> None:
        self.value = value

    def __call__(self) -> int:
        return self.value


'''
assert text.count(anchor) == 1, text.count(anchor)
text = text.replace(anchor, anchor + DEFAULT_TEST_OBJECTS)
old = 'def actor(*, permissions: tuple[str, ...] = ("*",), objects: tuple[str, ...] = ("*",)) -> AuthorityActorContext:'
new = 'def actor(*, permissions: tuple[str, ...] = ("*",), objects: tuple[str, ...] = DEFAULT_AUTHORIZED_OBJECTS) -> AuthorityActorContext:'
assert text.count(old) == 1, text.count(old)
text = text.replace(old, new)
path.write_text(text, encoding="utf-8")

DEFAULT_ACCEPTANCE_OBJECTS = '''DEFAULT_AUTHORIZED_OBJECTS = (
    "base.enabled",
    "cycle",
    "cycle.a",
    "cycle.b",
    "feature.alpha",
    "feature.expiring",
    "message.banner",
    "prod-v1",
    "production",
    "test",
    "test-v1",
    "test-v2",
    "tiny.flag",
    "tiny-v1",
    "tiny-v2",
    "unauthorized",
    "unauthorized.flag",
)


'''
path = Path("scripts/r14_11_remote_config_acceptance.py")
text = path.read_text(encoding="utf-8")
anchor = '_SHA_RE = re.compile(r"^[0-9a-f]{40}$")\n\n\n'
assert text.count(anchor) == 1, text.count(anchor)
text = text.replace(anchor, anchor + DEFAULT_ACCEPTANCE_OBJECTS)
old = '    objects: tuple[str, ...] = ("*",),'
new = '    objects: tuple[str, ...] = DEFAULT_AUTHORIZED_OBJECTS,'
assert text.count(old) == 1, text.count(old)
text = text.replace(old, new)
path.write_text(text, encoding="utf-8")
