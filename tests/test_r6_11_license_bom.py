from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.quality.health import HealthDimension, HealthStatus
from kodepoia.quality.license_bom import (
    SPDX_BASELINE,
    SPDX_JSONLD_CONTEXT,
    SPDX_SERIALIZATION_VERSION,
    BomComponent,
    BomReport,
    BomStatus,
    BomStore,
    ComponentKind,
    ComponentResolution,
    DependencyRequirement,
    IntegrityEvidence,
    IntegrityStatus,
    KodeBOM,
    KodeLicense,
    LicenseAssertion,
    LicenseAssertionState,
    LicensePolicy,
    LicensePolicyAction,
    LicensePolicyRule,
    LicenseReport,
    LicenseReportStatus,
    LicenseStore,
    canonical_python_name,
    normalize_spdx_expression,
)
from kodepoia.quality.tests import TestCaseStatus


NOW = "2026-08-22T14:00:00Z"


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def spdx(expression: str, source: str = "fixture:license") -> LicenseAssertion:
    return LicenseAssertion(
        state=LicenseAssertionState.SPDX_EXPRESSION,
        expression=expression,
        evidence_source=source,
    )


def noassertion(reason: str = "No exact license conclusion is available.") -> LicenseAssertion:
    return LicenseAssertion(
        state=LicenseAssertionState.NOASSERTION,
        evidence_source="fixture:unknown-license",
        rationale=reason,
    )


def resolved_component(
    name: str = "example",
    *,
    expression: str = "MIT",
    kind: ComponentKind = ComponentKind.PACKAGE,
) -> BomComponent:
    canonical = canonical_python_name(name)
    value = digest(f"artifact:{canonical}:1.2.3")
    return BomComponent(
        id=(f"project:{canonical}" if kind is ComponentKind.PROJECT else f"python:{canonical}"),
        name=name,
        kind=kind,
        resolution=ComponentResolution.RESOLVED,
        version="1.2.3",
        purl=(f"pkg:pypi/{canonical}@1.2.3" if kind is ComponentKind.PACKAGE else ""),
        source_locator="fixture:artifact",
        provenance_source="fixture:resolved-package",
        source_sha256=digest(f"metadata:{canonical}"),
        integrity=IntegrityEvidence(
            status=IntegrityStatus.RECORDED,
            source="fixture:artifact-sha256",
            digest=value,
        ),
        concluded_license=spdx(expression),
        requirements=(
            DependencyRequirement("runtime", f"{name}==1.2.3", "fixture:manifest"),
        ) if kind is ComponentKind.PACKAGE else (),
    )


def proprietary_project() -> BomComponent:
    text_hash = digest("Kodepoia proprietary fixture license")
    assertion = LicenseAssertion(
        state=LicenseAssertionState.SPDX_EXPRESSION,
        expression="LicenseRef-Kodepoia-Proprietary",
        evidence_source="fixture:LICENSE",
        custom_text_sha256=text_hash,
    )
    value = digest("kodepoia-source")
    return BomComponent(
        id="project:kodepoia",
        name="kodepoia",
        kind=ComponentKind.PROJECT,
        resolution=ComponentResolution.RESOLVED,
        version="0.1.0a4",
        source_locator="fixture:pyproject.toml",
        provenance_source="fixture:project-metadata",
        source_sha256=value,
        integrity=IntegrityEvidence(
            status=IntegrityStatus.RECORDED,
            source="fixture:source-manifest",
            digest=value,
        ),
        declared_license=assertion,
        concluded_license=assertion,
    )


def pass_bom() -> BomReport:
    return BomReport.build(
        "kodepoia",
        "fixture-resolved-components",
        (proprietary_project(), resolved_component()),
        inventory_complete=True,
        inventory_review_source="fixture:complete-review",
        generated_at=NOW,
    )


def policy(*, deny_mit: bool = False) -> LicensePolicy:
    return LicensePolicy(
        "fixture-policy",
        rules=(
            LicensePolicyRule(
                "LicenseRef-Kodepoia-Proprietary",
                LicensePolicyAction.ALLOW,
                "fixture:project-policy",
            ),
            LicensePolicyRule(
                "MIT",
                LicensePolicyAction.DENY if deny_mit else LicensePolicyAction.ALLOW,
                "fixture:dependency-policy",
            ),
        ),
    )


def test_spdx_expression_normalization_and_license_ref() -> None:
    assert normalize_spdx_expression("MIT  or  Apache-2.0") == "MIT OR Apache-2.0"
    assert normalize_spdx_expression("(MIT AND Apache-2.0)") == "(MIT AND Apache-2.0)"
    custom = LicenseAssertion(
        state=LicenseAssertionState.SPDX_EXPRESSION,
        expression="LicenseRef-Kodepoia-Proprietary",
        evidence_source="LICENSE",
        custom_text_sha256=digest("license text"),
    )
    assert custom.spdx_token == "LicenseRef-Kodepoia-Proprietary"
    with pytest.raises(ValueError, match="characters"):
        normalize_spdx_expression("MIT; rm -rf")
    with pytest.raises(ValueError, match="unbalanced"):
        normalize_spdx_expression("(MIT OR Apache-2.0")
    with pytest.raises(ValueError, match="LicenseRef"):
        LicenseAssertion(
            state=LicenseAssertionState.SPDX_EXPRESSION,
            expression="MIT",
            evidence_source="fixture",
            custom_text_sha256=digest("custom"),
        )


def test_noassertion_and_none_are_explicit_known_unknown_states() -> None:
    unknown = noassertion()
    assert unknown.spdx_token == "NOASSERTION"
    none = LicenseAssertion(
        state=LicenseAssertionState.NONE,
        evidence_source="fixture:inspection",
        rationale="Inspection found no license information in this fixture.",
    )
    assert none.spdx_token == "NONE"
    with pytest.raises(ValueError, match="requires rationale"):
        replace(unknown, rationale="")
    with pytest.raises(ValueError, match="cannot carry expression"):
        replace(unknown, expression="MIT")


def test_integrity_evidence_records_unknown_and_mismatch_without_faking_verification() -> None:
    recorded = IntegrityEvidence(
        IntegrityStatus.RECORDED,
        "fixture:hash",
        digest=digest("artifact"),
    )
    assert recorded.digest == digest("artifact")
    unknown = IntegrityEvidence(IntegrityStatus.UNKNOWN, "fixture:no-artifact")
    assert unknown.digest == ""
    mismatch = IntegrityEvidence(
        IntegrityStatus.MISMATCH,
        "fixture:verification",
        digest=digest("observed"),
        expected_digest=digest("expected"),
    )
    assert mismatch.digest != mismatch.expected_digest
    with pytest.raises(ValueError, match="different digests"):
        IntegrityEvidence(
            IntegrityStatus.MISMATCH,
            "fixture",
            digest=digest("same"),
            expected_digest=digest("same"),
        )


def test_bom_status_unknown_warn_pass_and_fail() -> None:
    empty = BomReport.build(
        "x", "fixture", (), inventory_complete=False, generated_at=NOW
    )
    assert empty.status is BomStatus.UNKNOWN

    incomplete = BomReport.build(
        "x",
        "fixture",
        (resolved_component(),),
        inventory_complete=False,
        generated_at=NOW,
    )
    assert incomplete.status is BomStatus.WARN

    unresolved = replace(
        resolved_component(),
        resolution=ComponentResolution.UNRESOLVED,
        version="",
        integrity=IntegrityEvidence(IntegrityStatus.UNKNOWN, "fixture:no-resolution"),
    )
    warn = BomReport.build(
        "x",
        "fixture",
        (unresolved,),
        inventory_complete=True,
        inventory_review_source="fixture:review",
        generated_at=NOW,
    )
    assert warn.status is BomStatus.WARN

    assert pass_bom().status is BomStatus.PASS

    mismatch_component = replace(
        resolved_component(),
        integrity=IntegrityEvidence(
            IntegrityStatus.MISMATCH,
            "fixture:mismatch",
            digest=digest("observed"),
            expected_digest=digest("expected"),
        ),
    )
    failed = BomReport.build(
        "x",
        "fixture",
        (mismatch_component,),
        inventory_complete=True,
        inventory_review_source="fixture:review",
        generated_at=NOW,
    )
    assert failed.status is BomStatus.FAIL
    assert failed.blockers == ("integrity:python:example",)


def test_complete_inventory_requires_review_provenance() -> None:
    with pytest.raises(ValueError, match="inventory_review_source"):
        BomReport.build(
            "x",
            "fixture",
            (resolved_component(),),
            inventory_complete=True,
            generated_at=NOW,
        )


def test_pyproject_collector_keeps_ranges_unresolved_and_noassertion(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[build-system]
requires = ["hatchling>=1.27,<2"]
build-backend = "hatchling.build"

[project]
name = "demo_pkg"
version = "1.0.0"
dependencies = ["PyYAML>=6,<7", "demo-dep>=2,<3"]

[project.optional-dependencies]
ui = ["Demo_Dep>=2,<3", "PySide6>=6.10,<7"]
""".strip() + "\n",
        encoding="utf-8",
    )
    report = KodeBOM.from_pyproject(tmp_path, generated_at=NOW)
    assert report.status is BomStatus.WARN
    assert report.inventory_complete
    components = {item.id: item for item in report.components}
    assert "project:demo-pkg" in components
    assert "python:hatchling" in components
    assert "python:pyyaml" in components
    assert "python:demo-dep" in components
    assert "python:pyside6" in components
    demo = components["python:demo-dep"]
    assert demo.resolution is ComponentResolution.UNRESOLVED
    assert demo.version == ""
    assert demo.purl == "pkg:pypi/demo-dep"
    assert demo.concluded_license.state is LicenseAssertionState.NOASSERTION
    assert {item.group for item in demo.requirements} == {"runtime", "optional:ui"}
    assert report.counts["integrity_unknown"] >= 4


def test_current_kodepoia_pyproject_generates_real_declared_dependency_bom() -> None:
    root = Path(__file__).resolve().parents[1]
    license_hash = hashlib.sha256((root / "LICENSE").read_bytes()).hexdigest()
    project_license = LicenseAssertion(
        state=LicenseAssertionState.SPDX_EXPRESSION,
        expression="LicenseRef-Kodepoia-Proprietary",
        evidence_source="LICENSE",
        custom_text_sha256=license_hash,
    )
    report = KodeBOM.from_pyproject(root, project_license=project_license, generated_at=NOW)
    components = {item.id: item for item in report.components}
    assert report.project_name == "kodepoia"
    assert report.inventory_scope == "python-project-metadata"
    assert report.status is BomStatus.WARN
    assert components["project:kodepoia"].concluded_license.spdx_token == "LicenseRef-Kodepoia-Proprietary"
    for package in ("hatchling", "pyyaml", "keyring", "pillow", "pyside6", "tree-sitter", "pytest"):
        assert f"python:{package}" in components
        assert components[f"python:{package}"].resolution is ComponentResolution.UNRESOLVED
        assert components[f"python:{package}"].concluded_license.state is LicenseAssertionState.NOASSERTION
    assert len({item.source_sha256 for item in report.components}) == 1


def test_spdx_compatibility_view_is_versioned_and_explicitly_not_conformance_claim() -> None:
    view = KodeBOM.spdx_compatibility_view(pass_bom())
    assert view["spdx_baseline"] == SPDX_BASELINE == "3.0"
    assert view["spdx_serialization_version"] == SPDX_SERIALIZATION_VERSION == "3.0.1"
    assert view["jsonld_context"] == SPDX_JSONLD_CONTEXT
    assert view["conformance_claim"] is False
    package = next(item for item in view["packages"] if item["id"] == "python:example")
    assert package["package_url"] == "pkg:pypi/example@1.2.3"
    assert package["concluded_license"] == "MIT"


def test_license_policy_is_exact_evidence_policy_not_legal_inference() -> None:
    with pytest.raises(ValueError, match="silently allow"):
        LicensePolicy("bad", default_action=LicensePolicyAction.ALLOW)
    with pytest.raises(ValueError, match="unique"):
        LicensePolicy(
            "duplicate",
            rules=(
                LicensePolicyRule("MIT", LicensePolicyAction.ALLOW, "one"),
                LicensePolicyRule("MIT", LicensePolicyAction.WARN, "two"),
            ),
        )
    p = LicensePolicy(
        "exact",
        rules=(LicensePolicyRule("MIT", LicensePolicyAction.ALLOW, "fixture:rule"),),
    )
    assert p.evaluate(spdx("MIT"))[0] is LicensePolicyAction.ALLOW
    assert p.evaluate(spdx("Apache-2.0"))[0] is LicensePolicyAction.UNKNOWN
    assert p.evaluate(noassertion())[0] is LicensePolicyAction.UNKNOWN


def test_license_report_pass_warn_fail_and_blockers() -> None:
    passed = LicenseReport.build(pass_bom(), policy(), generated_at=NOW)
    assert passed.status is LicenseReportStatus.PASS
    assert passed.score == 100.0
    assert not passed.blockers

    unknown_component = replace(resolved_component(), concluded_license=noassertion())
    warn_bom = BomReport.build(
        "x",
        "fixture",
        (unknown_component,),
        inventory_complete=True,
        inventory_review_source="fixture:review",
        generated_at=NOW,
    )
    warned = LicenseReport.build(warn_bom, policy(), generated_at=NOW)
    assert warned.status is LicenseReportStatus.WARN
    assert warned.counts["unknown"] == 1

    failed = LicenseReport.build(pass_bom(), policy(deny_mit=True), generated_at=NOW)
    assert failed.status is LicenseReportStatus.FAIL
    assert failed.blockers == ("license:python:example",)
    assert failed.score == 50.0


def test_incomplete_license_inventory_cannot_pass() -> None:
    bom = BomReport.build(
        "x",
        "fixture",
        (resolved_component(),),
        inventory_complete=False,
        generated_at=NOW,
    )
    report = LicenseReport.build(bom, policy(), generated_at=NOW)
    assert report.status is LicenseReportStatus.WARN
    assert report.score == 90.0


def test_bom_and_license_roundtrip_and_tamper_rejection() -> None:
    bom_payload = pass_bom().to_dict()
    assert BomReport.from_dict(bom_payload).to_dict() == bom_payload

    wrong_counts = json.loads(json.dumps(bom_payload))
    wrong_counts["counts"]["resolved"] = 99
    with pytest.raises(ValueError, match="counts"):
        BomReport.from_dict(wrong_counts)

    wrong_hash = json.loads(json.dumps(bom_payload))
    wrong_hash["evidence_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="hash mismatch"):
        BomReport.from_dict(wrong_hash)

    license_payload = LicenseReport.build(pass_bom(), policy(), generated_at=NOW).to_dict()
    assert LicenseReport.from_dict(license_payload).to_dict() == license_payload

    wrong_blocker = json.loads(json.dumps(license_payload))
    wrong_blocker["blockers"] = ["license:invented"]
    with pytest.raises(ValueError, match="blockers"):
        LicenseReport.from_dict(wrong_blocker)

    wrong_action = json.loads(json.dumps(license_payload))
    wrong_action["decisions"][0]["blocking"] = True
    with pytest.raises(ValueError, match="blocker"):
        LicenseReport.from_dict(wrong_action)


def test_component_duplicates_and_requirement_duplicates_fail_closed() -> None:
    component = resolved_component()
    with pytest.raises(ValueError, match="component ids"):
        BomReport.build(
            "x",
            "fixture",
            (component, component),
            inventory_complete=True,
            inventory_review_source="fixture",
            generated_at=NOW,
        )
    duplicate_requirement = DependencyRequirement("runtime", "demo==1", "fixture")
    with pytest.raises(ValueError, match="requirements must be unique"):
        replace(component, requirements=(duplicate_requirement, duplicate_requirement))


def test_health_adapters_preserve_unknown_warn_pass_and_fail() -> None:
    empty = BomReport.build("x", "fixture", (), inventory_complete=False, generated_at=NOW)
    dep_unknown = KodeBOM.to_dependencies_health_metric(empty)
    assert dep_unknown.dimension is HealthDimension.DEPENDENCIES
    assert dep_unknown.status is HealthStatus.UNKNOWN
    assert dep_unknown.score is None

    unresolved = replace(
        resolved_component(),
        resolution=ComponentResolution.UNRESOLVED,
        version="",
        integrity=IntegrityEvidence(IntegrityStatus.UNKNOWN, "fixture"),
    )
    warn_bom = BomReport.build(
        "x", "fixture", (unresolved,), inventory_complete=True,
        inventory_review_source="fixture", generated_at=NOW,
    )
    assert KodeBOM.to_dependencies_health_metric(warn_bom).status is HealthStatus.WARN
    assert KodeBOM.to_dependencies_health_metric(pass_bom()).status is HealthStatus.PASS

    license_pass = KodeLicense.to_health_metric(
        LicenseReport.build(pass_bom(), policy(), generated_at=NOW)
    )
    assert license_pass.dimension is HealthDimension.LICENSES
    assert license_pass.status is HealthStatus.PASS
    assert license_pass.score == 100.0

    license_fail = KodeLicense.to_health_metric(
        LicenseReport.build(pass_bom(), policy(deny_mit=True), generated_at=NOW)
    )
    assert license_fail.status is HealthStatus.FAIL
    assert license_fail.blocking


def test_r6_3_adapters_keep_unknown_as_skip_and_deny_as_fail() -> None:
    unresolved = replace(
        resolved_component(),
        resolution=ComponentResolution.UNRESOLVED,
        version="",
        integrity=IntegrityEvidence(IntegrityStatus.UNKNOWN, "fixture:no-artifact"),
        concluded_license=noassertion(),
    )
    bom = BomReport.build(
        "x",
        "fixture",
        (unresolved,),
        inventory_complete=True,
        inventory_review_source="fixture",
        generated_at=NOW,
    )
    bom_case = KodeBOM.to_test_cases(bom)[0]
    assert bom_case.id == "bom:python:example"
    assert bom_case.status is TestCaseStatus.SKIP

    unknown_license = LicenseReport.build(bom, policy(), generated_at=NOW)
    license_case = KodeLicense.to_test_cases(unknown_license)[0]
    assert license_case.id == "license:python:example"
    assert license_case.status is TestCaseStatus.SKIP

    denied = LicenseReport.build(pass_bom(), policy(deny_mit=True), generated_at=NOW)
    cases = {item.id: item for item in KodeLicense.to_test_cases(denied)}
    assert cases["license:python:example"].status is TestCaseStatus.FAIL


def test_stores_require_initialized_metadata_and_roundtrip(tmp_path: Path) -> None:
    bom = pass_bom()
    license_report = LicenseReport.build(bom, policy(), generated_at=NOW)
    with pytest.raises(FileNotFoundError):
        BomStore(tmp_path).save(bom)
    with pytest.raises(FileNotFoundError):
        LicenseStore(tmp_path).save(license_report)

    (tmp_path / ".kodepoia").mkdir()
    bom_latest, bom_snapshot = BomStore(tmp_path).save(bom)
    license_latest, license_snapshot = LicenseStore(tmp_path).save(license_report)
    assert bom_latest.is_file() and bom_snapshot.is_file()
    assert license_latest.is_file() and license_snapshot.is_file()
    assert BomStore(tmp_path).load_latest("kodepoia").to_dict() == bom.to_dict()
    assert LicenseStore(tmp_path).load_latest("kodepoia").to_dict() == license_report.to_dict()
    assert bom_latest.is_relative_to(tmp_path)
    assert license_latest.is_relative_to(tmp_path)


def test_schemas_accept_canonical_reports() -> None:
    root = Path(__file__).resolve().parents[1]
    bom_schema = json.loads((root / "schemas" / "bom-report-v1.schema.json").read_text(encoding="utf-8"))
    license_schema = json.loads(
        (root / "schemas" / "license-report-v1.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(bom_schema).validate(pass_bom().to_dict())
    Draft202012Validator(license_schema).validate(
        LicenseReport.build(pass_bom(), policy(), generated_at=NOW).to_dict()
    )


def test_component_details_reuse_secret_redaction() -> None:
    component = replace(
        resolved_component(),
        details={"token": "secret-value", "note": "safe"},
    )
    encoded = json.dumps(component.to_dict())
    assert "secret-value" not in encoded
    assert "safe" in encoded
