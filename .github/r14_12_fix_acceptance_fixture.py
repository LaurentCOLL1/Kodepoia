from pathlib import Path

path = Path("scripts/r14_12_content_delivery_acceptance.py")
text = path.read_text(encoding="utf-8")
old = '''AUTHORIZED_OBJECTS = (
    "bundle.base",
    "bundle.extra",
    "bundle.patch",
    "channel.stable",
    "manifest.prod",
    "manifest.v1",
    "manifest.v2",
    "manifest.v3",
    "production",
    "test",
)
'''
new = '''AUTHORIZED_OBJECTS = (
    "bundle.base",
    "bundle.cycle.a",
    "bundle.cycle.b",
    "bundle.extra",
    "bundle.missing",
    "bundle.patch",
    "bundle.unknown",
    "channel.stable",
    "manifest.cycle",
    "manifest.missing",
    "manifest.prod",
    "manifest.v1",
    "manifest.v2",
    "manifest.v3",
    "production",
    "test",
)
'''
assert text.count(old) == 1, text.count(old)
path.write_text(text.replace(old, new, 1), encoding="utf-8")
