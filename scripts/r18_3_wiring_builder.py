from __future__ import annotations

import argparse
import json
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


def patch_bundle() -> None:
    path = Path("src/kodepoia/release/bundle.py")
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "from kodepoia.release.identity import CURRENT_RELEASE\n",
        "from kodepoia.release.identity import CURRENT_RELEASE\n"
        "from kodepoia.release.provenance import (\n"
        "    ATTESTATION_SEMANTICS,\n"
        "    PROVENANCE_NAME,\n"
        "    SBOM_NAME,\n"
        "    SPDX_PREDICATE_TYPE,\n"
        "    ReleaseEvidenceError,\n"
        "    verify_release_evidence_files,\n"
        "    verify_release_evidence_payloads,\n"
        ")\n",
        "bundle imports",
    )
    text = replace_once(
        text,
        '    "release-notes",\n}',
        '    "release-notes",\n    "sbom",\n    "provenance",\n}',
        "bundle roles",
    )
    text = replace_once(
        text,
        "    run_attempt: str | None = None,\n    repository: str | None = None,\n) -> BundleBuildResult:",
        "    run_attempt: str | None = None,\n    repository: str | None = None,\n"
        "    sbom_path: str | Path | None = None,\n"
        "    provenance_path: str | Path | None = None,\n"
        ") -> BundleBuildResult:",
        "bundle signature",
    )
    text = replace_once(
        text,
        "    provenance = _default_provenance(workflow_ref, run_id, run_attempt, repository)\n\n"
        "    payloads: dict[str, tuple[str, bytes]] = {",
        "    provenance = _default_provenance(workflow_ref, run_id, run_attempt, repository)\n"
        "    evidence_summary: dict[str, Any] | None = None\n"
        "    if (sbom_path is None) != (provenance_path is None):\n"
        "        raise ReleaseBundleError(\"R18.3 SBOM and provenance files must be supplied together\")\n"
        "    if sbom_path is not None and provenance_path is not None:\n"
        "        try:\n"
        "            evidence_summary = verify_release_evidence_files(\n"
        "                sbom_path,\n"
        "                provenance_path,\n"
        "                expected_source_sha=source_sha,\n"
        "                expected_repository=provenance[\"repository\"],\n"
        "            )\n"
        "        except (OSError, ReleaseEvidenceError) as exc:\n"
        "            raise ReleaseBundleError(f\"invalid R18.3 release evidence: {exc}\") from exc\n\n"
        "    payloads: dict[str, tuple[str, bytes]] = {",
        "bundle evidence validation",
    )
    text = replace_once(
        text,
        "    }\n    for path, role, payload in _policy_documents(root):\n",
        "    }\n"
        "    if evidence_summary is not None:\n"
        "        payloads[SBOM_NAME] = (\"sbom\", Path(sbom_path).read_bytes())\n"
        "        payloads[PROVENANCE_NAME] = (\"provenance\", Path(provenance_path).read_bytes())\n"
        "    for path, role, payload in _policy_documents(root):\n",
        "bundle evidence payloads",
    )
    text = replace_once(
        text,
        "        \"installer_binary_reproducibility\": \"measured-not-assumed\",\n    }\n    manifest_bytes = _canonical_json_bytes(manifest)\n",
        "        \"installer_binary_reproducibility\": \"measured-not-assumed\",\n    }\n"
        "    if evidence_summary is not None:\n"
        "        manifest[\"release_evidence\"] = {\n"
        "            \"sbom_path\": SBOM_NAME,\n"
        "            \"sbom_sha256\": evidence_summary[\"sbom_sha256\"],\n"
        "            \"provenance_path\": PROVENANCE_NAME,\n"
        "            \"provenance_sha256\": evidence_summary[\"provenance_sha256\"],\n"
        "            \"sbom_predicate_type\": SPDX_PREDICATE_TYPE,\n"
        "            \"attestation_semantics\": ATTESTATION_SEMANTICS,\n"
        "        }\n"
        "    manifest_bytes = _canonical_json_bytes(manifest)\n",
        "bundle manifest evidence",
    )
    text = replace_once(
        text,
        "    if records != sorted(records, key=lambda record: record[\"path\"]):\n"
        "        raise BundleVerificationError(\"bundle manifest file records must be lexicographically ordered\")\n\n"
        "    if not _SHA256_RE.fullmatch(str(manifest.get(\"payload_sha256\", \"\"))):",
        "    if records != sorted(records, key=lambda record: record[\"path\"]):\n"
        "        raise BundleVerificationError(\"bundle manifest file records must be lexicographically ordered\")\n\n"
        "    release_evidence = manifest.get(\"release_evidence\")\n"
        "    evidence_records = [\n"
        "        record for record in records if record[\"role\"] in {\"sbom\", \"provenance\"}\n"
        "    ]\n"
        "    if release_evidence is None:\n"
        "        if evidence_records:\n"
        "            raise BundleVerificationError(\"release evidence files require release_evidence manifest binding\")\n"
        "    else:\n"
        "        required_evidence = {\n"
        "            \"sbom_path\",\n"
        "            \"sbom_sha256\",\n"
        "            \"provenance_path\",\n"
        "            \"provenance_sha256\",\n"
        "            \"sbom_predicate_type\",\n"
        "            \"attestation_semantics\",\n"
        "        }\n"
        "        if not isinstance(release_evidence, dict) or set(release_evidence) != required_evidence:\n"
        "            raise BundleVerificationError(\"release_evidence fields are incomplete or unexpected\")\n"
        "        if (\n"
        "            release_evidence[\"sbom_path\"] != SBOM_NAME\n"
        "            or release_evidence[\"provenance_path\"] != PROVENANCE_NAME\n"
        "        ):\n"
        "            raise BundleVerificationError(\"release evidence paths are not canonical\")\n"
        "        if release_evidence[\"sbom_predicate_type\"] != SPDX_PREDICATE_TYPE:\n"
        "            raise BundleVerificationError(\"release SBOM predicate type mismatch\")\n"
        "        if release_evidence[\"attestation_semantics\"] != ATTESTATION_SEMANTICS:\n"
        "            raise BundleVerificationError(\"release attestation semantics mismatch\")\n"
        "        evidence_by_role = {record[\"role\"]: record for record in evidence_records}\n"
        "        if set(evidence_by_role) != {\"sbom\", \"provenance\"}:\n"
        "            raise BundleVerificationError(\"release bundle must contain exactly one SBOM and provenance record\")\n"
        "        if (\n"
        "            evidence_by_role[\"sbom\"][\"path\"] != SBOM_NAME\n"
        "            or evidence_by_role[\"provenance\"][\"path\"] != PROVENANCE_NAME\n"
        "        ):\n"
        "            raise BundleVerificationError(\"release evidence record paths mismatch\")\n"
        "        if evidence_by_role[\"sbom\"][\"sha256\"] != release_evidence[\"sbom_sha256\"]:\n"
        "            raise BundleVerificationError(\"release SBOM manifest digest binding mismatch\")\n"
        "        if (\n"
        "            evidence_by_role[\"provenance\"][\"sha256\"]\n"
        "            != release_evidence[\"provenance_sha256\"]\n"
        "        ):\n"
        "            raise BundleVerificationError(\"release provenance manifest digest binding mismatch\")\n\n"
        "    if not _SHA256_RE.fullmatch(str(manifest.get(\"payload_sha256\", \"\"))):",
        "bundle manifest evidence verification",
    )
    text = replace_once(
        text,
        "        if checksums != checksummed_records:\n"
        "            raise BundleVerificationError(\"SHA256SUMS.txt does not exactly bind non-checksum payloads\")\n\n"
        "        try:\n            release_notes = json.loads(payload_bytes[RELEASE_NOTES_NAME].decode(\"utf-8\"))",
        "        if checksums != checksummed_records:\n"
        "            raise BundleVerificationError(\"SHA256SUMS.txt does not exactly bind non-checksum payloads\")\n\n"
        "        release_evidence = manifest.get(\"release_evidence\")\n"
        "        if release_evidence is not None:\n"
        "            try:\n"
        "                verified_evidence = verify_release_evidence_payloads(\n"
        "                    payload_bytes[SBOM_NAME],\n"
        "                    payload_bytes[PROVENANCE_NAME],\n"
        "                    expected_source_sha=source_sha,\n"
        "                    expected_repository=manifest[\"provenance\"][\"repository\"],\n"
        "                )\n"
        "            except (KeyError, ReleaseEvidenceError) as exc:\n"
        "                raise BundleVerificationError(\n"
        "                    f\"release evidence payload verification failed: {exc}\"\n"
        "                ) from exc\n"
        "            if verified_evidence[\"sbom_sha256\"] != release_evidence[\"sbom_sha256\"]:\n"
        "                raise BundleVerificationError(\"release SBOM payload digest mismatch\")\n"
        "            if (\n"
        "                verified_evidence[\"provenance_sha256\"]\n"
        "                != release_evidence[\"provenance_sha256\"]\n"
        "            ):\n"
        "                raise BundleVerificationError(\"release provenance payload digest mismatch\")\n\n"
        "        try:\n            release_notes = json.loads(payload_bytes[RELEASE_NOTES_NAME].decode(\"utf-8\"))",
        "bundle payload evidence verification",
    )
    path.write_text(text, encoding="utf-8", newline="\n")


def patch_bundle_cli() -> None:
    path = Path("scripts/build_release_bundle.py")
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        'description="Build the deterministic Kodepoia R18.2 release bundle."',
        'description="Build the deterministic Kodepoia R18.2/R18.3 release bundle."',
        "bundle cli description",
    )
    text = replace_once(
        text,
        '    parser.add_argument("--run-attempt")\n    args = parser.parse_args()\n',
        '    parser.add_argument("--run-attempt")\n'
        '    parser.add_argument("--sbom")\n'
        '    parser.add_argument("--provenance")\n'
        '    args = parser.parse_args()\n'
        '    if (args.sbom is None) != (args.provenance is None):\n'
        '        parser.error("--sbom and --provenance must be supplied together")\n',
        "bundle cli args",
    )
    text = replace_once(
        text,
        "        run_attempt=args.run_attempt,\n    )",
        "        run_attempt=args.run_attempt,\n"
        "        sbom_path=Path(args.sbom) if args.sbom else None,\n"
        "        provenance_path=Path(args.provenance) if args.provenance else None,\n"
        "    )",
        "bundle cli call",
    )
    path.write_text(text, encoding="utf-8", newline="\n")


def patch_schema() -> None:
    path = Path("schemas/release_bundle_manifest.schema.json")
    schema = json.loads(path.read_text(encoding="utf-8"))
    roles = schema["properties"]["files"]["items"]["properties"]["role"]["enum"]
    for role in ("sbom", "provenance"):
        if role not in roles:
            roles.append(role)
    schema["properties"]["release_evidence"] = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "sbom_path",
            "sbom_sha256",
            "provenance_path",
            "provenance_sha256",
            "sbom_predicate_type",
            "attestation_semantics",
        ],
        "properties": {
            "sbom_path": {"const": "release-sbom.spdx.json"},
            "sbom_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "provenance_path": {"const": "release-provenance.json"},
            "provenance_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "sbom_predicate_type": {"const": "https://spdx.dev/Document/v2.3"},
            "attestation_semantics": {"const": "provenance_only_not_security_verdict"},
        },
    }
    path.write_text(
        json.dumps(schema, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def patch_policy() -> None:
    path = Path("configs/r16_supply_chain_policy.json")
    policy = json.loads(path.read_text(encoding="utf-8"))
    policy["pin_resolution_date"] = "2026-09-05"
    policy["external_action_pins"]["actions/attest"] = {
        "source_ref": "v4",
        "commit_sha": "1e69f48acb82d1966a394da916b4c1698aa569d6",
    }
    workflow_path = ".github/workflows/r18-3-sbom-provenance-attestation-acceptance.yml"
    policy["workflow_policy"]["allow_write_workflows"] = [workflow_path]
    if workflow_path not in policy["workflow_policy"]["immutable_authority_workflows"]:
        policy["workflow_policy"]["immutable_authority_workflows"].append(workflow_path)
    path.write_text(
        json.dumps(policy, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def patch_supply_chain_tests() -> None:
    path = Path("tests/test_supply_chain_r16_9.py")
    text = path.read_text(encoding="utf-8")
    text = replace_once(text, "    assert len(policy.pins) == 8\n", "    assert len(policy.pins) == 9\n", "pin count")
    text = replace_once(
        text,
        '    assert policy.pins["actions/download-artifact"].commit_sha == (\n'
        '        "634f93cb2916e3fdff6788551b99b062d0335ce0"\n'
        '    )\n',
        '    assert policy.pins["actions/download-artifact"].commit_sha == (\n'
        '        "634f93cb2916e3fdff6788551b99b062d0335ce0"\n'
        '    )\n'
        '    assert policy.pins["actions/attest"].commit_sha == (\n'
        '        "1e69f48acb82d1966a394da916b4c1698aa569d6"\n'
        '    )\n',
        "attest pin assertion",
    )
    text = replace_once(text, "    assert len(policy.immutable_authority_workflows) == 24\n", "    assert len(policy.immutable_authority_workflows) == 25\n", "authority count")
    text = replace_once(
        text,
        '    assert (\n        ".github/workflows/r18-2-deterministic-release-bundle-acceptance.yml"\n        in policy.immutable_authority_workflows\n    )\n',
        '    assert (\n        ".github/workflows/r18-2-deterministic-release-bundle-acceptance.yml"\n        in policy.immutable_authority_workflows\n    )\n'
        '    r18_3_workflow = ".github/workflows/r18-3-sbom-provenance-attestation-acceptance.yml"\n'
        '    assert r18_3_workflow in policy.immutable_authority_workflows\n'
        '    assert policy.allow_write_workflows == (r18_3_workflow,)\n',
        "R18.3 authority assertion",
    )
    path.write_text(text, encoding="utf-8", newline="\n")


def patch_bundle_tests() -> None:
    path = Path("tests/test_r18_release_bundle.py")
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "from kodepoia.release.identity import CURRENT_RELEASE\n",
        "from kodepoia.release.identity import CURRENT_RELEASE\n"
        "from kodepoia.release.provenance import write_release_evidence\n",
        "bundle test imports",
    )
    integration = '''\n\ndef test_r18_3_evidence_is_digest_bound_into_bundle_manifest(bundle_inputs, tmp_path: Path) -> None:\n    evidence = write_release_evidence(\n        repo_root=Path(__file__).resolve().parents[1],\n        output_dir=tmp_path / "evidence",\n        source_sha=SOURCE_SHA,\n        repository="LaurentCOLL1/Kodepoia",\n        workflow_ref="test-workflow",\n        run_id="test",\n        run_attempt="1",\n        optional_groups=(),\n        created_at="2026-09-05T00:00:00Z",\n    )\n    repo_root, installer, manifest = bundle_inputs\n    result = build_release_bundle(\n        installer_path=installer,\n        installer_manifest_path=manifest,\n        source_sha=SOURCE_SHA,\n        output_dir=tmp_path / "bundle-with-evidence",\n        repo_root=repo_root,\n        repository="LaurentCOLL1/Kodepoia",\n        workflow_ref="test-workflow",\n        run_id="test",\n        run_attempt="1",\n        sbom_path=evidence.sbom_path,\n        provenance_path=evidence.provenance_path,\n    )\n    verified = verify_bundle_archive(result.archive_path, expected_source_sha=SOURCE_SHA)\n    binding = verified["manifest"]["release_evidence"]\n    assert binding["sbom_sha256"] == evidence.sbom_sha256\n    assert binding["provenance_sha256"] == evidence.provenance_sha256\n    roles = {record["role"] for record in verified["manifest"]["files"]}\n    assert {"sbom", "provenance"}.issubset(roles)\n\n\ndef test_r18_3_partial_evidence_is_rejected(bundle_inputs, tmp_path: Path) -> None:\n    evidence = write_release_evidence(\n        repo_root=Path(__file__).resolve().parents[1],\n        output_dir=tmp_path / "evidence",\n        source_sha=SOURCE_SHA,\n        repository="LaurentCOLL1/Kodepoia",\n        workflow_ref="test-workflow",\n        run_id="test",\n        run_attempt="1",\n        optional_groups=(),\n        created_at="2026-09-05T00:00:00Z",\n    )\n    repo_root, installer, manifest = bundle_inputs\n    with pytest.raises(ReleaseBundleError, match="must be supplied together"):\n        build_release_bundle(\n            installer_path=installer,\n            installer_manifest_path=manifest,\n            source_sha=SOURCE_SHA,\n            output_dir=tmp_path / "partial",\n            repo_root=repo_root,\n            repository="LaurentCOLL1/Kodepoia",\n            sbom_path=evidence.sbom_path,\n        )\n'''
    if "test_r18_3_evidence_is_digest_bound_into_bundle_manifest" in text:
        raise SystemExit("R18.3 bundle integration tests already present")
    path.write_text(text + integration, encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workflow-template", required=True)
    args = parser.parse_args()
    patch_bundle()
    patch_bundle_cli()
    patch_schema()
    patch_policy()
    patch_supply_chain_tests()
    patch_bundle_tests()
    template = Path(args.workflow_template).read_text(encoding="utf-8")
    workflow_path = Path(".github/workflows/r18-3-sbom-provenance-attestation-acceptance.yml")
    workflow_path.write_text(template, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
