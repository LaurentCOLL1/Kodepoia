from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.desktop.app_model import (
    CommandContract,
    DesktopAppModel,
    DialogContract,
    DialogKind,
    RouteContract,
    ServiceContract,
    ServiceLifetime,
    StateField,
    StateValueKind,
    ValidationKind,
    ValidationRule,
    ViewContract,
    ViewModelContract,
    canonical_sample_app,
)
from kodepoia.desktop.contracts import DesktopFramework

ROOT = Path(__file__).resolve().parents[1]


def test_r12_4_canonical_sample_is_deterministic_and_schema_valid() -> None:
    first = canonical_sample_app()
    second = canonical_sample_app()
    assert first.canonical_bytes() == second.canonical_bytes()
    assert first.digest() == second.digest()

    schema = json.loads(
        (ROOT / "schemas" / "r12" / "desktop-app-model.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator(schema).validate(first.to_dict())


def test_r12_4_ordering_does_not_change_logical_serialization() -> None:
    model = canonical_sample_app()
    reordered = replace(
        model,
        state_fields=tuple(reversed(model.state_fields)),
        dialogs=tuple(reversed(model.dialogs)),
    )
    assert reordered.canonical_bytes() == model.canonical_bytes()
    assert reordered.digest() == model.digest()


def test_r12_4_duplicate_route_path_and_parent_cycles_fail_closed() -> None:
    model = canonical_sample_app()
    duplicate = replace(
        model,
        routes=(
            *model.routes,
            RouteContract("sample.other", "/", "sample.main_view"),
        ),
    )
    with pytest.raises(ValueError, match="duplicate route path"):
        duplicate.validate()

    views = (
        *model.views,
        ViewContract("sample.child_view", "sample.main_vm"),
    )
    cyclic = replace(
        model,
        views=views,
        routes=(
            RouteContract("sample.a", "/a", "sample.main_view", "sample.b"),
            RouteContract("sample.b", "/b", "sample.child_view", "sample.a"),
        ),
    )
    with pytest.raises(ValueError, match="route parent cycle"):
        cyclic.validate()


def test_r12_4_invalid_command_and_can_execute_state_fail_closed() -> None:
    model = canonical_sample_app()
    missing_service = replace(
        model,
        commands=(CommandContract("sample.bad", "run", service_id="missing.service"),),
        view_models=(
            ViewModelContract(
                "sample.main_vm",
                state_fields=("sample.can_refresh", "sample.status"),
                commands=("sample.bad",),
            ),
        ),
    )
    with pytest.raises(ValueError, match="missing service"):
        missing_service.validate()

    wrong_gate = replace(
        model,
        commands=(
            CommandContract(
                "sample.bad",
                "run",
                service_id="sample.status_service",
                can_execute_field="sample.status",
            ),
        ),
        view_models=(
            ViewModelContract(
                "sample.main_vm",
                state_fields=("sample.status",),
                commands=("sample.bad",),
                services=("sample.status_service",),
            ),
        ),
    )
    with pytest.raises(ValueError, match="can-execute state must be boolean"):
        wrong_gate.validate()

    invalid_operation = replace(
        model,
        commands=(CommandContract("sample.bad", "run; rm -rf"),),
        view_models=(ViewModelContract("sample.main_vm", commands=("sample.bad",)),),
    )
    with pytest.raises(ValueError, match="invalid command operation"):
        invalid_operation.validate()


def test_r12_4_service_cycles_and_lifetime_capture_conflicts_fail_closed() -> None:
    model = canonical_sample_app()
    cycle = replace(
        model,
        services=(
            ServiceContract("service.a", ServiceLifetime.SINGLETON, ("service.b",)),
            ServiceContract("service.b", ServiceLifetime.SINGLETON, ("service.a",)),
        ),
        commands=(),
        view_models=(ViewModelContract("sample.main_vm"),),
    )
    with pytest.raises(ValueError, match="service dependency cycle"):
        cycle.validate()

    capture = replace(
        model,
        services=(
            ServiceContract("service.short", ServiceLifetime.TRANSIENT),
            ServiceContract(
                "service.long",
                ServiceLifetime.SINGLETON,
                ("service.short",),
            ),
        ),
        commands=(),
        view_models=(ViewModelContract("sample.main_vm"),),
    )
    with pytest.raises(ValueError, match="lifetime conflict"):
        capture.validate()


def test_r12_4_disposal_order_releases_dependents_before_dependencies() -> None:
    model = DesktopAppModel(
        schema_version=1,
        app_id="disposal.sample",
        state_fields=(),
        validation_rules=(),
        services=(
            ServiceContract("service.root", ServiceLifetime.SINGLETON, disposable=True),
            ServiceContract(
                "service.child",
                ServiceLifetime.SINGLETON,
                dependencies=("service.root",),
                disposable=True,
            ),
        ),
        commands=(),
        view_models=(ViewModelContract("sample.vm", services=("service.child",)),),
        views=(ViewContract("sample.view", "sample.vm"),),
        routes=(RouteContract("sample.route", "/", "sample.view"),),
    )
    assert model.service_disposal_order() == ("service.child", "service.root")


def test_r12_4_validation_rules_are_typed_and_bounded() -> None:
    base = canonical_sample_app()
    numeric = replace(
        base,
        state_fields=(StateField("sample.count", StateValueKind.INTEGER, 1),),
        validation_rules=(
            ValidationRule("sample.count.range", "sample.count", ValidationKind.RANGE, (0, 10)),
        ),
        commands=(),
        view_models=(ViewModelContract("sample.main_vm", state_fields=("sample.count",)),),
    )
    numeric.validate()

    invalid = replace(
        numeric,
        validation_rules=(
            ValidationRule("sample.count.regex", "sample.count", ValidationKind.REGEX, "[0-9]+"),
        ),
    )
    with pytest.raises(ValueError, match="regex validation requires string"):
        invalid.validate()


def test_r12_4_all_frozen_adapters_receive_equivalent_logical_projection() -> None:
    model = canonical_sample_app()
    projections = [model.conformance_projection(framework) for framework in DesktopFramework]
    assert len(projections) == 5
    assert len({projection.framework for projection in projections}) == 5
    assert len({projection.logical_signature for projection in projections}) == 1


def test_r12_4_dialog_and_binding_references_must_exist() -> None:
    model = canonical_sample_app()
    missing_vm = replace(
        model,
        dialogs=(DialogContract("sample.bad_dialog", DialogKind.INPUT, "missing.vm"),),
    )
    with pytest.raises(ValueError, match="dialog references missing view-model"):
        missing_vm.validate()

    missing_view_vm = replace(
        model,
        views=(ViewContract("sample.main_view", "missing.vm"),),
    )
    with pytest.raises(ValueError, match="view references missing view-model"):
        missing_view_vm.validate()
