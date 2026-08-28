from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator, ValidationError

from kodepoia.backend.contracts import BackendServiceKind
from kodepoia.backend.intent import (
    BACKEND_DNA_SERVICE_KINDS,
    BackendProjectProfile,
    backend_runtime_intents,
    backend_wizard_questions,
)
from kodepoia.backend.product_intent import (
    BACKEND_PRODUCT_REQUIREMENT_ID,
    apply_backend_product_intent,
    backend_product_constraints,
)
from kodepoia.product.spec import ProductSpec
from kodepoia.project.dna import DecisionState, Platform, ProjectDNA, ProjectType
from kodepoia.project.wizard import ProjectWizardState

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "r14_2"
PROJECT_SCHEMA = ROOT / "schemas" / "project-dna-v1.schema.json"
PROFILE_SCHEMA = ROOT / "schemas" / "r14" / "backend-project-profile.schema.json"
RUNTIME_SCHEMA = ROOT / "schemas" / "r14" / "backend-runtime-intent.schema.json"


def _validator(path: Path) -> Draft202012Validator:
    schema = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _yaml(path: Path) -> dict[str, object]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _enabled(*services: BackendServiceKind) -> BackendProjectProfile:
    return BackendProjectProfile(enabled=True, services=tuple(services))


def test_legacy_offline_fixture_loads_without_backend_and_emits_zero_runtime_intent() -> None:
    path = FIXTURES / "offline_project.yaml"
    dna = ProjectDNA.load(path)
    assert dna.backend is None
    assert "backend" not in dna.to_dict()
    assert backend_runtime_intents(dna.backend) == ()


def test_offline_fixture_remains_valid_project_dna_v1() -> None:
    _validator(PROJECT_SCHEMA).validate(_yaml(FIXTURES / "offline_project.yaml"))


def test_enabled_profile_is_deterministic_and_deduplicated() -> None:
    first = BackendProjectProfile(
        enabled=True,
        services=(
            BackendServiceKind.MATCHMAKING,
            BackendServiceKind.AUTHORITATIVE_SERVER,
            BackendServiceKind.AUTH,
            BackendServiceKind.AUTH,
        ),
    )
    second = BackendProjectProfile(
        enabled=True,
        services=(
            BackendServiceKind.AUTH,
            BackendServiceKind.AUTHORITATIVE_SERVER,
            BackendServiceKind.MATCHMAKING,
        ),
    )
    assert first == second
    assert first.digest() == second.digest()
    assert first.services == tuple(sorted(first.services, key=lambda item: item.value))


def test_disabled_profile_cannot_hide_service_intent() -> None:
    with pytest.raises(ValueError, match="disabled backend profile"):
        BackendProjectProfile(enabled=False, services=(BackendServiceKind.AUTH,))


def test_enabled_profile_requires_at_least_one_service() -> None:
    with pytest.raises(ValueError, match="at least one"):
        BackendProjectProfile(enabled=True)


def test_matchmaking_requires_authoritative_session_intent() -> None:
    with pytest.raises(ValueError, match="authoritative_server"):
        _enabled(BackendServiceKind.MATCHMAKING)


def test_billing_requires_catalog_and_entitlement_intents() -> None:
    with pytest.raises(ValueError, match="catalog, entitlement"):
        _enabled(BackendServiceKind.BILLING)
    with pytest.raises(ValueError, match="entitlement"):
        _enabled(BackendServiceKind.BILLING, BackendServiceKind.CATALOG)


def test_database_and_liveops_are_not_project_dna_service_intents() -> None:
    assert BackendServiceKind.DATABASE not in BACKEND_DNA_SERVICE_KINDS
    assert BackendServiceKind.LIVEOPS not in BACKEND_DNA_SERVICE_KINDS
    with pytest.raises(ValueError, match="not a Project DNA service intent"):
        _enabled(BackendServiceKind.DATABASE)
    with pytest.raises(ValueError, match="not a Project DNA service intent"):
        _enabled(BackendServiceKind.LIVEOPS)


def test_valid_profile_emits_deterministic_runtime_intents_with_dependencies_only() -> None:
    profile = _enabled(
        BackendServiceKind.AUTH,
        BackendServiceKind.AUTHORITATIVE_SERVER,
        BackendServiceKind.MATCHMAKING,
        BackendServiceKind.CATALOG,
        BackendServiceKind.ENTITLEMENT,
        BackendServiceKind.BILLING,
    )
    intents = backend_runtime_intents(profile)
    assert tuple(item.intent_id for item in intents) == tuple(
        f"backend.{service.value}" for service in profile.services
    )
    matchmaking = next(item for item in intents if item.service_kind is BackendServiceKind.MATCHMAKING)
    billing = next(item for item in intents if item.service_kind is BackendServiceKind.BILLING)
    assert matchmaking.dependencies == (BackendServiceKind.AUTHORITATIVE_SERVER,)
    assert billing.dependencies == (
        BackendServiceKind.CATALOG,
        BackendServiceKind.ENTITLEMENT,
    )
    forbidden = {"provider", "credential", "token", "raw_url", "account_id"}
    for intent in intents:
        assert forbidden.isdisjoint(intent.canonical())
        assert len(intent.digest()) == 64


def test_profile_and_runtime_schemas_are_strict_and_accept_generated_evidence() -> None:
    profile = _enabled(
        BackendServiceKind.AUTHORITATIVE_SERVER,
        BackendServiceKind.MATCHMAKING,
    )
    profile_validator = _validator(PROFILE_SCHEMA)
    runtime_validator = _validator(RUNTIME_SCHEMA)
    profile_validator.validate(profile.canonical())
    for intent in profile.runtime_intents():
        runtime_validator.validate(intent.canonical())

    contaminated = {**profile.canonical(), "provider_account_id": "secret-account"}
    with pytest.raises(ValidationError):
        profile_validator.validate(contaminated)
    runtime = profile.runtime_intents()[0].canonical()
    with pytest.raises(ValidationError):
        runtime_validator.validate({**runtime, "token": "secret"})


def test_project_dna_loader_rejects_unknown_backend_provider_or_secret_fields(tmp_path: Path) -> None:
    payload = _yaml(FIXTURES / "offline_project.yaml")
    payload["backend"] = {
        "enabled": True,
        "services": ["auth"],
        "provider_account_id": "account-1",
    }
    path = tmp_path / "project.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported fields"):
        ProjectDNA.load(path)


def test_online_fixture_schema_model_and_roundtrip_are_deterministic(tmp_path: Path) -> None:
    source = FIXTURES / "online_project.yaml"
    payload = _yaml(source)
    _validator(PROJECT_SCHEMA).validate(payload)
    dna = ProjectDNA.load(source)
    assert dna.backend is not None and dna.backend.enabled
    first_digest = dna.backend.digest()
    assert len(backend_runtime_intents(dna.backend)) == len(dna.backend.services)

    target = tmp_path / "project.yaml"
    dna.save(target)
    restored = ProjectDNA.load(target)
    assert restored.backend == dna.backend
    assert restored.backend is not None
    assert restored.backend.digest() == first_digest
    _validator(PROJECT_SCHEMA).validate(_yaml(target))


def test_contradictory_billing_fixture_fails_schema_and_model() -> None:
    path = FIXTURES / "contradictory_billing.yaml"
    with pytest.raises(ValidationError):
        _validator(PROJECT_SCHEMA).validate(_yaml(path))
    with pytest.raises(ValueError, match="catalog, entitlement"):
        ProjectDNA.load(path)


def test_backend_wizard_questions_are_conditional_snapshots() -> None:
    assert backend_wizard_questions(None, backend_relevant=False) == ()
    assert backend_wizard_questions(None, backend_relevant=True) == ("backend_enabled",)

    multiplayer = _enabled(
        BackendServiceKind.AUTHORITATIVE_SERVER,
        BackendServiceKind.MATCHMAKING,
    )
    assert backend_wizard_questions(multiplayer) == (
        "backend_enabled",
        "backend_services",
        "backend_authoritative_state",
        "backend_matchmaking",
    )

    commerce = _enabled(
        BackendServiceKind.CATALOG,
        BackendServiceKind.ENTITLEMENT,
        BackendServiceKind.BILLING,
    )
    assert backend_wizard_questions(commerce) == (
        "backend_enabled",
        "backend_services",
        "backend_commerce",
    )


def test_project_wizard_offline_default_has_no_backend_question_or_profile() -> None:
    state = ProjectWizardState(
        name="Offline",
        project_type=ProjectType.TOOL,
        platforms=[Platform.WINDOWS],
        engine=None,
        engine_version=None,
        dimension=None,
        inputs=[],
    )
    assert not any(item.startswith("backend_") for item in state.relevant_questions())
    dna = state.build()
    assert dna.backend is None
    assert backend_runtime_intents(dna.backend) == ()


def test_project_wizard_online_intent_asks_opt_in_without_manufacturing_services() -> None:
    state = ProjectWizardState(
        name="Online",
        project_type=ProjectType.GAME,
        platforms=[Platform.WINDOWS],
        online=DecisionState.YES,
    )
    backend_questions = tuple(
        item for item in state.relevant_questions() if item.startswith("backend_")
    )
    assert backend_questions == ("backend_enabled",)
    assert state.build().backend is None


def test_project_wizard_builds_valid_selected_profile() -> None:
    state = ProjectWizardState(
        name="Session",
        project_type=ProjectType.GAME,
        platforms=[Platform.WINDOWS],
        online=DecisionState.YES,
        multiplayer=DecisionState.YES,
        backend_enabled=True,
        backend_services=(
            BackendServiceKind.MATCHMAKING,
            BackendServiceKind.AUTHORITATIVE_SERVER,
            BackendServiceKind.AUTH,
        ),
    )
    dna = state.build()
    assert dna.backend is not None
    assert dna.backend.services == (
        BackendServiceKind.AUTH,
        BackendServiceKind.AUTHORITATIVE_SERVER,
        BackendServiceKind.MATCHMAKING,
    )
    backend_questions = tuple(
        item for item in state.relevant_questions() if item.startswith("backend_")
    )
    assert backend_questions == (
        "backend_enabled",
        "backend_services",
        "backend_identity",
        "backend_authoritative_state",
        "backend_matchmaking",
    )


def test_kodeproduct_mapping_is_zero_for_disabled_and_idempotent_for_enabled() -> None:
    product = ProductSpec(1, "Example", "Example vision", constraints=["existing=true"])
    apply_backend_product_intent(product, None)
    assert product.constraints == ["existing=true"]
    assert all(item.id != BACKEND_PRODUCT_REQUIREMENT_ID for item in product.requirements)

    profile = _enabled(
        BackendServiceKind.AUTH,
        BackendServiceKind.CATALOG,
        BackendServiceKind.ENTITLEMENT,
        BackendServiceKind.BILLING,
    )
    apply_backend_product_intent(product, profile)
    first_constraints = list(product.constraints)
    first_requirement = product.requirement(BACKEND_PRODUCT_REQUIREMENT_ID)
    apply_backend_product_intent(product, profile)
    assert product.constraints == first_constraints
    assert product.requirement(BACKEND_PRODUCT_REQUIREMENT_ID) == first_requirement
    assert sum(item.id == BACKEND_PRODUCT_REQUIREMENT_ID for item in product.requirements) == 1
    assert tuple(item for item in product.constraints if item.startswith("backend.")) == backend_product_constraints(profile)


def test_kodeproduct_mapping_replaces_only_reserved_backend_intent() -> None:
    first = _enabled(BackendServiceKind.AUTH)
    second = _enabled(BackendServiceKind.CLOUD_SAVE)
    product = ProductSpec(1, "Example", "Example vision", constraints=["other=value"])
    apply_backend_product_intent(product, first)
    apply_backend_product_intent(product, second)
    assert product.constraints == ["other=value", "backend.service=cloud_save"]
    requirement = product.requirement(BACKEND_PRODUCT_REQUIREMENT_ID)
    assert "cloud_save" in requirement.acceptance[0].text
    assert "auth" not in requirement.acceptance[0].text


def test_backend_profile_is_client_platform_independent() -> None:
    profile = _enabled(BackendServiceKind.AUTH, BackendServiceKind.CLOUD_SAVE)
    windows = ProjectDNA(
        1,
        "Windows",
        ProjectType.TOOL,
        [Platform.WINDOWS],
        backend=profile,
    )
    web = ProjectDNA(
        1,
        "Web",
        ProjectType.TOOL,
        [Platform.WEB],
        backend=profile,
    )
    windows.validate()
    web.validate()
    assert windows.backend is not None and web.backend is not None
    assert windows.backend.digest() == web.backend.digest()
