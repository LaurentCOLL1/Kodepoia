from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from kodepoia.release.bundle import build_release_bundle
from kodepoia.release.identity import CURRENT_RELEASE

SOURCE_SHA = "0123456789abcdef0123456789abcdef01234567"
BUNDLE_SCHEMA_ID = "https://kodepoia.local/schemas/release_bundle_manifest.schema.json"
IDENTITY_SCHEMA_ID = "https://kodepoia.local/schemas/release_identity.schema.json"


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_generated_release_bundle_manifest_validates_against_repository_schema(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "LICENSE").write_text(
        "synthetic R18.2 schema validation license\n",
        encoding="utf-8",
        newline="\n",
    )

    installer = tmp_path / "KodepoiaSetup.exe"
    installer.write_bytes(b"MZ-r18.2-schema-validation\n")
    identity = CURRENT_RELEASE.bind_source(SOURCE_SHA).to_dict()
    installer_manifest = {
        "version": identity["installer_version"],
        "public_version": identity["public_version"],
        "pep440_version": identity["pep440_version"],
        "installer_version": identity["installer_version"],
        "channel": identity["channel"],
        "build_type": identity["build_type"],
        "package": identity["package"],
        "source_sha": SOURCE_SHA,
        "release_identity_schema": identity["schema_version"],
        "installer": "KodepoiaSetup.exe",
        "sha256": _sha256(installer),
        "standalone_executable": "KodepoiaStudio.exe",
        "production_signed": False,
    }
    installer_manifest_path = tmp_path / "installer-manifest.json"
    installer_manifest_path.write_text(
        json.dumps(installer_manifest, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    result = build_release_bundle(
        installer_path=installer,
        installer_manifest_path=installer_manifest_path,
        source_sha=SOURCE_SHA,
        output_dir=tmp_path / "bundle",
        repo_root=repo_root,
        repository="LaurentCOLL1/Kodepoia",
        workflow_ref="schema-validation",
        run_id="test",
        run_attempt="1",
    )

    bundle_schema = json.loads(
        Path("schemas/release_bundle_manifest.schema.json").read_text(encoding="utf-8")
    )
    identity_schema = json.loads(
        Path("schemas/release_identity.schema.json").read_text(encoding="utf-8")
    )
    assert bundle_schema["$id"] == BUNDLE_SCHEMA_ID
    assert identity_schema["$id"] == IDENTITY_SCHEMA_ID

    registry = Registry().with_resource(
        IDENTITY_SCHEMA_ID,
        Resource.from_contents(identity_schema),
    )
    Draft202012Validator.check_schema(bundle_schema)
    Draft202012Validator(bundle_schema, registry=registry).validate(result.manifest)
