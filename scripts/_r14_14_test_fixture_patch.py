from pathlib import Path

PATH = Path("tests/test_r14_14_liveops.py")
text = PATH.read_text(encoding="utf-8")
old = '''        permissions=("*",),
        authorized_object_ids=("*",),
'''
new = '''        permissions=("*",),
        authorized_object_ids=(
            "season.2026.autumn",
            "config.liveops.1",
            "config.other",
            "manifest.liveops.1",
            "product.liveops.1",
            "schema.liveops.1",
            "campaign.autumn.1",
            "campaign.one",
            "campaign.two",
            "test",
            "production",
            "liveops.audience",
        ),
'''
count = text.count(old)
if count != 1:
    raise AssertionError(f"actor fixture anchor count={count}")
PATH.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
