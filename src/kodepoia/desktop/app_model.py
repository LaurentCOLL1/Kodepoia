from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .contracts import DesktopFramework


_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]*$")
_OPERATION = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$")


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _require_id(value: str, label: str) -> None:
    if not _ID.fullmatch(value):
        raise ValueError(f"invalid {label}: {value!r}")


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"duplicate {label}")


class StateValueKind(StrEnum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"


class ValidationKind(StrEnum):
    REQUIRED = "required"
    RANGE = "range"
    REGEX = "regex"


class ServiceLifetime(StrEnum):
    SINGLETON = "singleton"
    SCOPED = "scoped"
    TRANSIENT = "transient"


class DialogKind(StrEnum):
    INFORMATION = "information"
    CONFIRMATION = "confirmation"
    INPUT = "input"


@dataclass(frozen=True, slots=True)
class StateField:
    field_id: str
    kind: StateValueKind
    default: str | int | float | bool | None = None

    def validate(self) -> None:
        _require_id(self.field_id, "state field id")
        if self.default is None:
            return
        if self.kind is StateValueKind.STRING and not isinstance(self.default, str):
            raise ValueError(f"state {self.field_id} requires string default")
        if self.kind is StateValueKind.BOOLEAN and not isinstance(self.default, bool):
            raise ValueError(f"state {self.field_id} requires boolean default")
        if self.kind is StateValueKind.INTEGER and (
            not isinstance(self.default, int) or isinstance(self.default, bool)
        ):
            raise ValueError(f"state {self.field_id} requires integer default")
        if self.kind is StateValueKind.FLOAT and (
            not isinstance(self.default, (int, float)) or isinstance(self.default, bool)
        ):
            raise ValueError(f"state {self.field_id} requires numeric default")


@dataclass(frozen=True, slots=True)
class ValidationRule:
    rule_id: str
    field_id: str
    kind: ValidationKind
    argument: str | float | tuple[float, float] | None = None

    def validate(self, fields: dict[str, StateField]) -> None:
        _require_id(self.rule_id, "validation rule id")
        if self.field_id not in fields:
            raise ValueError(f"validation rule references missing state: {self.field_id}")
        field = fields[self.field_id]
        if self.kind is ValidationKind.REQUIRED:
            if self.argument is not None:
                raise ValueError("required validation takes no argument")
        elif self.kind is ValidationKind.RANGE:
            if field.kind not in {StateValueKind.INTEGER, StateValueKind.FLOAT}:
                raise ValueError("range validation requires numeric state")
            if (
                not isinstance(self.argument, tuple)
                or len(self.argument) != 2
                or self.argument[0] > self.argument[1]
            ):
                raise ValueError("range validation requires ordered (min, max)")
        elif self.kind is ValidationKind.REGEX:
            if field.kind is not StateValueKind.STRING or not isinstance(self.argument, str):
                raise ValueError("regex validation requires string state and pattern")
            try:
                re.compile(self.argument)
            except re.error as exc:
                raise ValueError("invalid validation regex") from exc


@dataclass(frozen=True, slots=True)
class ServiceContract:
    service_id: str
    lifetime: ServiceLifetime
    dependencies: tuple[str, ...] = ()
    disposable: bool = False

    def validate(self) -> None:
        _require_id(self.service_id, "service id")
        _unique(list(self.dependencies), f"dependencies for {self.service_id}")
        if self.service_id in self.dependencies:
            raise ValueError(f"service {self.service_id} cannot depend on itself")
        for dependency in self.dependencies:
            _require_id(dependency, "service dependency")


@dataclass(frozen=True, slots=True)
class CommandContract:
    command_id: str
    operation: str
    service_id: str | None = None
    can_execute_field: str | None = None

    def validate(
        self,
        services: dict[str, ServiceContract],
        fields: dict[str, StateField],
    ) -> None:
        _require_id(self.command_id, "command id")
        if not _OPERATION.fullmatch(self.operation):
            raise ValueError(f"invalid command operation: {self.operation!r}")
        if self.service_id is not None and self.service_id not in services:
            raise ValueError(f"command references missing service: {self.service_id}")
        if self.can_execute_field is not None:
            field = fields.get(self.can_execute_field)
            if field is None:
                raise ValueError(
                    f"command references missing can-execute state: {self.can_execute_field}"
                )
            if field.kind is not StateValueKind.BOOLEAN:
                raise ValueError("can-execute state must be boolean")


@dataclass(frozen=True, slots=True)
class ViewModelContract:
    view_model_id: str
    state_fields: tuple[str, ...] = ()
    commands: tuple[str, ...] = ()
    services: tuple[str, ...] = ()

    def validate(
        self,
        fields: dict[str, StateField],
        commands: dict[str, CommandContract],
        services: dict[str, ServiceContract],
    ) -> None:
        _require_id(self.view_model_id, "view-model id")
        _unique(list(self.state_fields), f"state fields for {self.view_model_id}")
        _unique(list(self.commands), f"commands for {self.view_model_id}")
        _unique(list(self.services), f"services for {self.view_model_id}")
        for field_id in self.state_fields:
            if field_id not in fields:
                raise ValueError(f"view-model references missing state: {field_id}")
        for command_id in self.commands:
            if command_id not in commands:
                raise ValueError(f"view-model references missing command: {command_id}")
        for service_id in self.services:
            if service_id not in services:
                raise ValueError(f"view-model references missing service: {service_id}")


@dataclass(frozen=True, slots=True)
class ViewContract:
    view_id: str
    view_model_id: str

    def validate(self, view_models: dict[str, ViewModelContract]) -> None:
        _require_id(self.view_id, "view id")
        if self.view_model_id not in view_models:
            raise ValueError(f"view references missing view-model: {self.view_model_id}")


@dataclass(frozen=True, slots=True)
class RouteContract:
    route_id: str
    path: str
    view_id: str
    parent_route_id: str | None = None

    def validate(self, views: dict[str, ViewContract]) -> None:
        _require_id(self.route_id, "route id")
        if (
            not self.path.startswith("/")
            or ".." in self.path.split("/")
            or "?" in self.path
            or "#" in self.path
        ):
            raise ValueError(f"invalid route path: {self.path!r}")
        if self.view_id not in views:
            raise ValueError(f"route references missing view: {self.view_id}")
        if self.parent_route_id is not None:
            _require_id(self.parent_route_id, "parent route id")
            if self.parent_route_id == self.route_id:
                raise ValueError("route cannot parent itself")


@dataclass(frozen=True, slots=True)
class DialogContract:
    dialog_id: str
    kind: DialogKind
    view_model_id: str

    def validate(self, view_models: dict[str, ViewModelContract]) -> None:
        _require_id(self.dialog_id, "dialog id")
        if self.view_model_id not in view_models:
            raise ValueError(f"dialog references missing view-model: {self.view_model_id}")


@dataclass(frozen=True, slots=True)
class AdapterConformanceProjection:
    framework: DesktopFramework
    logical_model_sha256: str
    state_ids: tuple[str, ...]
    command_ids: tuple[str, ...]
    route_paths: tuple[str, ...]
    service_ids: tuple[str, ...]

    @property
    def logical_signature(self) -> tuple[object, ...]:
        return (
            self.logical_model_sha256,
            self.state_ids,
            self.command_ids,
            self.route_paths,
            self.service_ids,
        )


@dataclass(frozen=True, slots=True)
class DesktopAppModel:
    schema_version: int
    app_id: str
    state_fields: tuple[StateField, ...]
    validation_rules: tuple[ValidationRule, ...]
    services: tuple[ServiceContract, ...]
    commands: tuple[CommandContract, ...]
    view_models: tuple[ViewModelContract, ...]
    views: tuple[ViewContract, ...]
    routes: tuple[RouteContract, ...]
    dialogs: tuple[DialogContract, ...] = ()

    def validate(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported desktop app-model schema version")
        _require_id(self.app_id, "app id")

        self._ensure_unique_ids()
        fields = {item.field_id: item for item in self.state_fields}
        services = {item.service_id: item for item in self.services}
        commands = {item.command_id: item for item in self.commands}
        view_models = {item.view_model_id: item for item in self.view_models}
        views = {item.view_id: item for item in self.views}
        routes = {item.route_id: item for item in self.routes}

        for field in self.state_fields:
            field.validate()
        for service in self.services:
            service.validate()
            for dependency in service.dependencies:
                if dependency not in services:
                    raise ValueError(
                        f"service {service.service_id} references missing dependency: {dependency}"
                    )
        self._validate_service_graph(services)
        for rule in self.validation_rules:
            rule.validate(fields)
        for command in self.commands:
            command.validate(services, fields)
        for view_model in self.view_models:
            view_model.validate(fields, commands, services)
        for view in self.views:
            view.validate(view_models)
        for route in self.routes:
            route.validate(views)
            if route.parent_route_id is not None and route.parent_route_id not in routes:
                raise ValueError(
                    f"route references missing parent: {route.parent_route_id}"
                )
        self._validate_route_graph(routes)
        for dialog in self.dialogs:
            dialog.validate(view_models)
        _unique([item.path for item in self.routes], "route path")

    def _ensure_unique_ids(self) -> None:
        groups = (
            ([item.field_id for item in self.state_fields], "state field id"),
            ([item.rule_id for item in self.validation_rules], "validation rule id"),
            ([item.service_id for item in self.services], "service id"),
            ([item.command_id for item in self.commands], "command id"),
            ([item.view_model_id for item in self.view_models], "view-model id"),
            ([item.view_id for item in self.views], "view id"),
            ([item.route_id for item in self.routes], "route id"),
            ([item.dialog_id for item in self.dialogs], "dialog id"),
        )
        for values, label in groups:
            _unique(values, label)

    @staticmethod
    def _validate_service_graph(services: dict[str, ServiceContract]) -> None:
        rank = {
            ServiceLifetime.TRANSIENT: 1,
            ServiceLifetime.SCOPED: 2,
            ServiceLifetime.SINGLETON: 3,
        }
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(service_id: str) -> None:
            if service_id in visiting:
                raise ValueError("service dependency cycle detected")
            if service_id in visited:
                return
            visiting.add(service_id)
            service = services[service_id]
            for dependency_id in service.dependencies:
                dependency = services[dependency_id]
                if rank[service.lifetime] > rank[dependency.lifetime]:
                    raise ValueError(
                        f"service lifetime conflict: {service.service_id} cannot capture "
                        f"shorter-lived {dependency.service_id}"
                    )
                visit(dependency_id)
            visiting.remove(service_id)
            visited.add(service_id)

        for service_id in sorted(services):
            visit(service_id)

    @staticmethod
    def _validate_route_graph(routes: dict[str, RouteContract]) -> None:
        for route_id in routes:
            seen: set[str] = set()
            current: str | None = route_id
            while current is not None:
                if current in seen:
                    raise ValueError("route parent cycle detected")
                seen.add(current)
                parent = routes[current].parent_route_id
                current = parent

    def service_disposal_order(self) -> tuple[str, ...]:
        self.validate()
        services = {item.service_id: item for item in self.services}
        visited: set[str] = set()
        order: list[str] = []

        def visit(service_id: str) -> None:
            if service_id in visited:
                return
            visited.add(service_id)
            for dependency in services[service_id].dependencies:
                visit(dependency)
            order.append(service_id)

        for service_id in sorted(services):
            visit(service_id)
        return tuple(
            service_id
            for service_id in reversed(order)
            if services[service_id].disposable
        )

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema_version": self.schema_version,
            "app_id": self.app_id,
            "state_fields": [
                {"field_id": i.field_id, "kind": i.kind.value, "default": i.default}
                for i in sorted(self.state_fields, key=lambda x: x.field_id)
            ],
            "validation_rules": [
                {
                    "rule_id": i.rule_id,
                    "field_id": i.field_id,
                    "kind": i.kind.value,
                    "argument": list(i.argument) if isinstance(i.argument, tuple) else i.argument,
                }
                for i in sorted(self.validation_rules, key=lambda x: x.rule_id)
            ],
            "services": [
                {
                    "service_id": i.service_id,
                    "lifetime": i.lifetime.value,
                    "dependencies": sorted(i.dependencies),
                    "disposable": i.disposable,
                }
                for i in sorted(self.services, key=lambda x: x.service_id)
            ],
            "commands": [
                {
                    "command_id": i.command_id,
                    "operation": i.operation,
                    "service_id": i.service_id,
                    "can_execute_field": i.can_execute_field,
                }
                for i in sorted(self.commands, key=lambda x: x.command_id)
            ],
            "view_models": [
                {
                    "view_model_id": i.view_model_id,
                    "state_fields": sorted(i.state_fields),
                    "commands": sorted(i.commands),
                    "services": sorted(i.services),
                }
                for i in sorted(self.view_models, key=lambda x: x.view_model_id)
            ],
            "views": [
                {"view_id": i.view_id, "view_model_id": i.view_model_id}
                for i in sorted(self.views, key=lambda x: x.view_id)
            ],
            "routes": [
                {
                    "route_id": i.route_id,
                    "path": i.path,
                    "view_id": i.view_id,
                    "parent_route_id": i.parent_route_id,
                }
                for i in sorted(self.routes, key=lambda x: x.route_id)
            ],
            "dialogs": [
                {
                    "dialog_id": i.dialog_id,
                    "kind": i.kind.value,
                    "view_model_id": i.view_model_id,
                }
                for i in sorted(self.dialogs, key=lambda x: x.dialog_id)
            ],
        }

    def canonical_bytes(self) -> bytes:
        return _canonical_json(self.to_dict())

    def digest(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()

    def conformance_projection(
        self, framework: DesktopFramework
    ) -> AdapterConformanceProjection:
        self.validate()
        return AdapterConformanceProjection(
            framework=framework,
            logical_model_sha256=self.digest(),
            state_ids=tuple(sorted(item.field_id for item in self.state_fields)),
            command_ids=tuple(sorted(item.command_id for item in self.commands)),
            route_paths=tuple(sorted(item.path for item in self.routes)),
            service_ids=tuple(sorted(item.service_id for item in self.services)),
        )


def canonical_sample_app() -> DesktopAppModel:
    """Deterministic logical fixture consumed by every concrete R12 adapter."""
    return DesktopAppModel(
        schema_version=1,
        app_id="kodepoia.sample.desktop",
        state_fields=(
            StateField("sample.can_refresh", StateValueKind.BOOLEAN, True),
            StateField("sample.status", StateValueKind.STRING, "ready"),
        ),
        validation_rules=(
            ValidationRule("sample.status.required", "sample.status", ValidationKind.REQUIRED),
        ),
        services=(
            ServiceContract(
                "sample.status_service",
                ServiceLifetime.SINGLETON,
                disposable=True,
            ),
        ),
        commands=(
            CommandContract(
                "sample.refresh",
                "refresh",
                service_id="sample.status_service",
                can_execute_field="sample.can_refresh",
            ),
        ),
        view_models=(
            ViewModelContract(
                "sample.main_vm",
                state_fields=("sample.can_refresh", "sample.status"),
                commands=("sample.refresh",),
                services=("sample.status_service",),
            ),
        ),
        views=(ViewContract("sample.main_view", "sample.main_vm"),),
        routes=(RouteContract("sample.home", "/", "sample.main_view"),),
        dialogs=(
            DialogContract(
                "sample.confirm_refresh",
                DialogKind.CONFIRMATION,
                "sample.main_vm",
            ),
        ),
    )
