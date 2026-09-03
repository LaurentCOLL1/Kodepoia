from __future__ import annotations

from pathlib import Path

path = Path("scripts/r16_9_supply_chain_acceptance.py")
text = path.read_text(encoding="utf-8")
old = '''        _case(
            "policy-integrity",
            len(policy.digest_sha256) == 64 and len(policy.pins) == 7,
            "policy and verified external action pin identities are digest-bound",
        ),
'''
new = '''        _case(
            "policy-integrity",
            len(policy.digest_sha256) == 64
            and {name: pin.commit_sha for name, pin in policy.pins.items()}
            == {
                "actions/checkout": "11d5960a326750d5838078e36cf38b85af677262",
                "actions/download-artifact": "634f93cb2916e3fdff6788551b99b062d0335ce0",
                "actions/setup-dotnet": "67a3573c9a986a3f9c594539f4ab511d57bb3ce9",
                "actions/setup-java": "cf277c60eb25467037889841efdb72551f06f6c3",
                "actions/setup-python": "a26af69be951a213d495a4c3e4e4022e16d87065",
                "actions/upload-artifact": "ea165f8d65b6e75b540449e92b4886f43607fa02",
                "android-actions/setup-android": "9fc6c4e9069bf8d3d10b2204b1fb8f6ef7065407",
                "gradle/actions": "ed408507eac070d1f99cc633dbcf757c94c7933a",
            },
            "policy and verified external action pin identities are digest-bound",
        ),
'''
if text.count(old) != 1:
    raise SystemExit("R16.9 policy-integrity acceptance anchor drifted")
path.write_text(text.replace(old, new), encoding="utf-8")
