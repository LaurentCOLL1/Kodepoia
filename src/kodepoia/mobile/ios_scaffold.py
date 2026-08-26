from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Iterable
from xml.sax.saxutils import escape as xml_escape

from kodepoia.core.audit import AuditLog
from kodepoia.core.backup import BackupManager
from kodepoia.core.safe_change import SafeChangeManager
from kodepoia.desktop.app_model import DesktopAppModel, StateValueKind
from kodepoia.mobile.boundary import MobileBoundaryError, MobileToolchainBoundary
from kodepoia.mobile.contracts import MobileFormFactor, MobileSourceKind, MobileToolKind, canonical_json_bytes
from kodepoia.project.dna import Platform, ProjectDNA, ProjectType

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SOURCE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_STABLE_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{0,127}$")
_SCHEME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_LOCALE_RE = re.compile(r"^[A-Za-z]{2,3}(?:[-_][A-Za-z0-9]{2,8})*$")
_VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+){0,3}$")
_WINDOWS_RESERVED = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _require_sha(value: str, label: str) -> None:
    if _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")


def _require_stable_id(value: str, label: str) -> None:
    if _STABLE_ID_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be a stable identifier")


def _normalize_text(value: str, *, label: str, maximum: int = 4096) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be text")
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized.strip() or len(normalized) > maximum or "\x00" in normalized:
        raise ValueError(f"{label} exceeds its bounded text policy")
    if any(ord(ch) < 32 and ch not in "\n\t" for ch in normalized):
        raise ValueError(f"{label} contains forbidden control characters")
    return normalized


def _safe_relative_path(value: str) -> str:
    if not value or "\\" in value or "\x00" in value:
        raise ValueError("unsafe Apple scaffold path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("unsafe Apple scaffold path")
    for part in path.parts:
        stem = part.split(".", 1)[0].upper()
        if stem in _WINDOWS_RESERVED or part.endswith((" ", ".")):
            raise ValueError("reserved Apple scaffold path component")
        if any(ch in '<>:"|?*' for ch in part):
            raise ValueError("forbidden Apple scaffold path character")
    return path.as_posix()


def _version_tuple(value: str) -> tuple[int, ...]:
    if _VERSION_RE.fullmatch(value) is None:
        raise ValueError("Apple platform version must be bounded numeric dotted form")
    return tuple(int(part) for part in value.split("."))


def _swift_symbol(logical_id: str, prefix: str) -> str:
    raw = re.sub(r"[^A-Za-z0-9_]", "_", logical_id)
    if not raw or raw[0].isdigit():
        raw = f"item_{raw}"
    digest = hashlib.sha256(logical_id.encode("utf-8")).hexdigest()[:8]
    return f"{prefix}_{raw}_{digest}"


def _swift_string(value: str) -> str:
    normalized = _normalize_text(value, label="Swift string", maximum=4096)
    return json.dumps(normalized, ensure_ascii=False)


def _pbx_quote(value: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_./$() -]+", value) and '"' not in value:
        return f'"{value}"'
    return json.dumps(value, ensure_ascii=False)


def _plist_text(value: str) -> str:
    return xml_escape(_normalize_text(value, label="plist text", maximum=512), {"\"": "&quot;", "'": "&apos;"})


def _strings_text(value: str) -> str:
    return json.dumps(_normalize_text(value, label="localized string", maximum=4096), ensure_ascii=False)


class AppleFileOwnership(StrEnum):
    KODEPOIA = "kodepoia"
    USER = "user"


class ApplePreviewAction(StrEnum):
    CREATE = "create"
    REPLACE = "replace"
    UNCHANGED = "unchanged"
    PRESERVE = "preserve"
    CONFLICT = "conflict"


class AppleStateStrategy(StrEnum):
    OBSERVATION = "observation"
    OBSERVABLE_OBJECT_COMPAT = "observable_object_compat"


@dataclass(frozen=True, slots=True)
class AppleStringCatalog:
    locale: str
    values: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        if _LOCALE_RE.fullmatch(self.locale) is None:
            raise ValueError("invalid Apple locale")
        normalized: list[tuple[str, str]] = []
        seen: set[str] = set()
        for key, value in self.values:
            _require_stable_id(key, "Apple localization key")
            if key in seen:
                raise ValueError("duplicate Apple localization key")
            seen.add(key)
            normalized.append((key, _normalize_text(value, label=f"localized string {key}", maximum=4096)))
        if not normalized:
            raise ValueError("Apple string catalog cannot be empty")
        object.__setattr__(self, "values", tuple(sorted(normalized)))

    def to_dict(self) -> dict[str, object]:
        return {"locale": self.locale, "values": {key: value for key, value in self.values}}

    def digest(self) -> str:
        return _sha256_bytes(canonical_json_bytes(self.to_dict()))


@dataclass(frozen=True, slots=True)
class GodotIOSExportBridgeDefinition:
    bridge_id: str = "godot.ios.xcode-export"
    export_preset: str = "iOS"
    expected_container_suffix: str = ".xcodeproj"
    execution_owned_by_r5: bool = True

    def __post_init__(self) -> None:
        _require_stable_id(self.bridge_id, "Godot iOS bridge id")
        if self.export_preset != "iOS":
            raise ValueError("Godot iOS export preset is repository-owned and fixed")
        if self.expected_container_suffix != ".xcodeproj":
            raise ValueError("Godot iOS bridge container suffix is fixed")
        if self.execution_owned_by_r5 is not True:
            raise ValueError("Godot export execution must remain owned by R5")

    def to_dict(self) -> dict[str, object]:
        return {
            "bridge_id": self.bridge_id,
            "export_preset": self.export_preset,
            "expected_container_suffix": self.expected_container_suffix,
            "execution_owned_by_r5": self.execution_owned_by_r5,
        }


@dataclass(frozen=True, slots=True)
class AppleScaffoldLineage:
    dna_sha256: str
    product_sha256: str

    def validate(self) -> None:
        _require_sha(self.dna_sha256, "dna_sha256")
        _require_sha(self.product_sha256, "product_sha256")


@dataclass(frozen=True, slots=True)
class AppleScaffoldDefinition:
    schema_version: int
    definition_id: str
    bundle_id: str
    app_name: str
    minimum_os_version: str
    target_os_version: str
    form_factors: tuple[MobileFormFactor, ...]
    app_model_sha256: str
    string_catalogs: tuple[AppleStringCatalog, ...]
    source_kind: MobileSourceKind = MobileSourceKind.NATIVE
    state_strategy: AppleStateStrategy = AppleStateStrategy.OBSERVATION
    godot_export_bridge: GodotIOSExportBridgeDefinition | None = None

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported Apple scaffold definition schema version")
        _require_stable_id(self.definition_id, "Apple scaffold definition id")
        _normalize_text(self.app_name, label="Apple app name", maximum=128)
        minimum = _version_tuple(self.minimum_os_version)
        target = _version_tuple(self.target_os_version)
        if minimum > target:
            raise ValueError("Apple minimum OS version cannot exceed target OS version")
        _require_sha(self.app_model_sha256, "app_model_sha256")
        factors = tuple(sorted(set(self.form_factors), key=lambda item: item.value))
        if not factors or any(item not in {MobileFormFactor.PHONE, MobileFormFactor.TABLET} for item in factors):
            raise ValueError("Apple scaffold requires phone and/or tablet form factors")
        object.__setattr__(self, "form_factors", factors)
        catalogs = tuple(sorted(self.string_catalogs, key=lambda item: item.locale))
        if not catalogs or not any(item.locale == "en" for item in catalogs):
            raise ValueError("Apple scaffold requires an en string catalog")
        if len({item.locale for item in catalogs}) != len(catalogs):
            raise ValueError("duplicate Apple locale catalog")
        object.__setattr__(self, "string_catalogs", catalogs)
        expected_strategy = (
            AppleStateStrategy.OBSERVATION
            if minimum >= (17,)
            else AppleStateStrategy.OBSERVABLE_OBJECT_COMPAT
        )
        if self.state_strategy is not expected_strategy:
            raise ValueError("Apple state strategy does not match minimum deployment target")
        if self.source_kind is MobileSourceKind.NATIVE:
            if self.godot_export_bridge is not None:
                raise ValueError("native SwiftUI scaffold cannot carry a Godot export bridge")
        elif self.source_kind is MobileSourceKind.GODOT_EXPORT:
            if self.godot_export_bridge is None:
                raise ValueError("Godot iOS source requires explicit R5-owned bridge metadata")
        else:
            raise ValueError("unsupported Apple scaffold source kind")

    @classmethod
    def from_project(
        cls,
        dna: ProjectDNA,
        app_model: DesktopAppModel,
        *,
        catalogs: Iterable[AppleStringCatalog] = (),
    ) -> "AppleScaffoldDefinition":
        dna.validate()
        app_model.validate()
        if Platform.IOS not in dna.platforms or dna.mobile is None:
            raise ValueError("Apple scaffold requires an iOS mobile profile")
        mobile = dna.mobile
        if mobile.apple_bundle_id is None or mobile.apple_min_version is None or mobile.apple_target_version is None:
            raise ValueError("Apple bundle and OS version intent are required")
        default_catalog = AppleStringCatalog("en", (("app_name", dna.name.strip()), ("status_ready", "Ready")))
        supplied = tuple(catalogs)
        by_locale = {item.locale: item for item in supplied}
        by_locale.setdefault("en", default_catalog)
        minimum = _version_tuple(mobile.apple_min_version)
        strategy = AppleStateStrategy.OBSERVATION if minimum >= (17,) else AppleStateStrategy.OBSERVABLE_OBJECT_COMPAT
        if mobile.source_kind is MobileSourceKind.NATIVE:
            if dna.project_type is not ProjectType.MOBILE_APP:
                raise ValueError("native Apple scaffold requires a mobile_app Project DNA")
            bridge = None
            definition_id = "project.apple.native"
        else:
            if dna.project_type is not ProjectType.GAME:
                raise ValueError("Godot iOS bridge requires a game Project DNA")
            bridge = GodotIOSExportBridgeDefinition()
            definition_id = "project.apple.godot-export"
        return cls(
            schema_version=1,
            definition_id=definition_id,
            bundle_id=mobile.apple_bundle_id,
            app_name=dna.name.strip(),
            minimum_os_version=mobile.apple_min_version,
            target_os_version=mobile.apple_target_version,
            form_factors=mobile.form_factors,
            app_model_sha256=app_model.digest(),
            string_catalogs=tuple(by_locale.values()),
            source_kind=mobile.source_kind,
            state_strategy=strategy,
            godot_export_bridge=bridge,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "definition_id": self.definition_id,
            "bundle_id": self.bundle_id,
            "app_name": self.app_name,
            "minimum_os_version": self.minimum_os_version,
            "target_os_version": self.target_os_version,
            "form_factors": [item.value for item in self.form_factors],
            "app_model_sha256": self.app_model_sha256,
            "string_catalogs": [item.to_dict() for item in self.string_catalogs],
            "source_kind": self.source_kind.value,
            "state_strategy": self.state_strategy.value,
            "godot_export_bridge": self.godot_export_bridge.to_dict() if self.godot_export_bridge else None,
        }

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_dict())

    def digest(self) -> str:
        return _sha256_bytes(self.canonical_bytes())


@dataclass(frozen=True, slots=True)
class AppleGeneratedFile:
    path: str
    content: str
    sha256: str
    ownership: AppleFileOwnership


@dataclass(frozen=True, slots=True)
class AppleWorkspaceManifest:
    schema_version: int
    definition_sha256: str
    app_model_sha256: str
    dna_sha256: str
    product_sha256: str
    state_strategy: AppleStateStrategy
    files: tuple[AppleGeneratedFile, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "definition_sha256": self.definition_sha256,
            "app_model_sha256": self.app_model_sha256,
            "dna_sha256": self.dna_sha256,
            "product_sha256": self.product_sha256,
            "state_strategy": self.state_strategy.value,
            "files": [
                {"path": item.path, "sha256": item.sha256, "ownership": item.ownership.value}
                for item in self.files
            ],
        }

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_dict())

    def digest(self) -> str:
        return _sha256_bytes(self.canonical_bytes())


@dataclass(frozen=True, slots=True)
class ApplePreviewItem:
    path: str
    action: ApplePreviewAction
    current_sha256: str | None
    desired_sha256: str
    ownership: AppleFileOwnership


@dataclass(frozen=True, slots=True)
class AppleScaffoldPreview:
    manifest: AppleWorkspaceManifest
    items: tuple[ApplePreviewItem, ...]

    @property
    def has_conflicts(self) -> bool:
        return any(item.action is ApplePreviewAction.CONFLICT for item in self.items)

    @property
    def destructive(self) -> bool:
        return any(item.action is ApplePreviewAction.REPLACE for item in self.items)


def build_ios_simulator_build_argv(
    boundary: MobileToolchainBoundary,
    xcodebuild: Path,
    *,
    project_file: Path,
    scheme: str,
    derived_data_path: Path,
) -> tuple[str, ...]:
    if not isinstance(scheme, str) or _SCHEME_RE.fullmatch(scheme) is None:
        raise MobileBoundaryError("Xcode scheme is not a bounded stable identifier")
    tool = boundary.validate_tool(MobileToolKind.XCODEBUILD, xcodebuild)
    project = boundary.validate_xcode_container(project_file)
    derived = boundary.validate_staging_path(derived_data_path)
    selector = "-workspace" if project.suffix == ".xcworkspace" else "-project"
    return (
        str(tool),
        selector,
        str(project),
        "-scheme",
        scheme,
        "-configuration",
        "Debug",
        "-destination",
        "generic/platform=iOS Simulator",
        "-derivedDataPath",
        str(derived),
        "CODE_SIGNING_ALLOWED=NO",
        "CODE_SIGNING_REQUIRED=NO",
        "build",
    )


class AppleScaffoldEngine:
    """Pure deterministic R13.9 renderer; Xcode execution is a separate governed seam."""

    PROJECT_NAME = "KodepoiaIOS"
    PROJECT_PATH = f"{PROJECT_NAME}.xcodeproj"
    SCHEME_NAME = PROJECT_NAME
    MANIFEST_PATH = ".kodepoia/mobile/apple/workspace-manifest.json"

    def render(
        self,
        definition: AppleScaffoldDefinition,
        app_model: DesktopAppModel,
        lineage: AppleScaffoldLineage,
    ) -> tuple[tuple[AppleGeneratedFile, ...], AppleWorkspaceManifest]:
        app_model.validate()
        lineage.validate()
        if definition.source_kind is not MobileSourceKind.NATIVE:
            raise ValueError("Godot iOS export is bridge metadata only; R5 owns export execution")
        if app_model.digest() != definition.app_model_sha256:
            raise ValueError("Apple scaffold app-model digest mismatch")

        entries: list[tuple[str, str, AppleFileOwnership]] = [
            (f"{self.PROJECT_PATH}/project.pbxproj", self._pbxproj(definition, app_model), AppleFileOwnership.KODEPOIA),
            (f"{self.PROJECT_PATH}/xcshareddata/xcschemes/{self.SCHEME_NAME}.xcscheme", self._scheme(), AppleFileOwnership.KODEPOIA),
            (f"{self.PROJECT_NAME}/{self.PROJECT_NAME}App.swift", self._app_source(), AppleFileOwnership.KODEPOIA),
            (f"{self.PROJECT_NAME}/AppState.swift", self._state_source(definition, app_model), AppleFileOwnership.KODEPOIA),
            (f"{self.PROJECT_NAME}/AppModelContract.swift", self._contract_source(app_model), AppleFileOwnership.KODEPOIA),
            (f"{self.PROJECT_NAME}/ContentView.swift", self._content_view(definition, app_model), AppleFileOwnership.KODEPOIA),
            (f"{self.PROJECT_NAME}/Info.plist", self._info_plist(definition), AppleFileOwnership.KODEPOIA),
            (f"{self.PROJECT_NAME}/Assets.xcassets/Contents.json", self._asset_catalog(), AppleFileOwnership.KODEPOIA),
            ("README.md", self._readme(definition), AppleFileOwnership.USER),
        ]
        for catalog in definition.string_catalogs:
            entries.append(
                (
                    f"{self.PROJECT_NAME}/{catalog.locale}.lproj/Localizable.strings",
                    self._strings(catalog),
                    AppleFileOwnership.KODEPOIA,
                )
            )

        rendered: list[AppleGeneratedFile] = []
        seen: set[str] = set()
        for raw_path, raw_content, ownership in entries:
            path = _safe_relative_path(raw_path)
            if path == self.MANIFEST_PATH or path in seen:
                raise ValueError("Apple scaffold path collision")
            seen.add(path)
            content = _normalize_text(raw_content, label=f"generated file {path}", maximum=1_000_000)
            rendered.append(AppleGeneratedFile(path, content, _sha256_bytes(content.encode("utf-8")), ownership))
        rendered.sort(key=lambda item: item.path)
        manifest = AppleWorkspaceManifest(
            schema_version=1,
            definition_sha256=definition.digest(),
            app_model_sha256=definition.app_model_sha256,
            dna_sha256=lineage.dna_sha256,
            product_sha256=lineage.product_sha256,
            state_strategy=definition.state_strategy,
            files=tuple(rendered),
        )
        return tuple(rendered), manifest

    def preview(
        self,
        project_root: Path,
        definition: AppleScaffoldDefinition,
        app_model: DesktopAppModel,
        lineage: AppleScaffoldLineage,
    ) -> AppleScaffoldPreview:
        root = Path(project_root).resolve(strict=False)
        rendered, manifest = self.render(definition, app_model, lineage)
        previous = self._previous_files(root)
        items: list[ApplePreviewItem] = []
        for desired in rendered:
            target = self._inside(root, desired.path)
            if not target.exists():
                action = ApplePreviewAction.CREATE
                current = None
            elif not target.is_file():
                action = ApplePreviewAction.CONFLICT
                current = None
            else:
                current = _sha256_bytes(target.read_bytes())
                prior = previous.get(desired.path)
                if current == desired.sha256:
                    action = ApplePreviewAction.UNCHANGED
                elif desired.ownership is AppleFileOwnership.USER:
                    action = ApplePreviewAction.PRESERVE
                elif prior is not None and prior[0] is AppleFileOwnership.KODEPOIA and current == prior[1]:
                    action = ApplePreviewAction.REPLACE
                else:
                    action = ApplePreviewAction.CONFLICT
            items.append(ApplePreviewItem(desired.path, action, current, desired.sha256, desired.ownership))
        return AppleScaffoldPreview(manifest, tuple(items))

    def apply(
        self,
        project_root: Path,
        preview: AppleScaffoldPreview,
        *,
        safe_change: SafeChangeManager | None = None,
        backup_manager: BackupManager | None = None,
        audit_log: AuditLog | None = None,
        actor: str = "kodepoia",
    ) -> AppleWorkspaceManifest:
        root = Path(project_root).resolve(strict=False)
        root.mkdir(parents=True, exist_ok=True)
        if preview.has_conflicts:
            raise FileExistsError("refusing Apple scaffold apply with ownership/path conflicts")
        replace_paths = [self._inside(root, item.path) for item in preview.items if item.action is ApplePreviewAction.REPLACE]
        safe_snapshot: Path | None = None
        backup_path: Path | None = None
        if replace_paths:
            if safe_change is None or backup_manager is None:
                raise ValueError("Apple scaffold replacement requires SafeChangeManager and BackupManager")
            safe_snapshot = safe_change.snapshot(replace_paths)
            backup_path = backup_manager.create_archive(root, label="apple-scaffold")

        by_path = {item.path: item for item in preview.manifest.files}
        for item in preview.items:
            if item.action in {ApplePreviewAction.UNCHANGED, ApplePreviewAction.PRESERVE}:
                continue
            desired = by_path[item.path]
            target = self._inside(root, item.path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(desired.content, encoding="utf-8", newline="\n")
        manifest_path = self._inside(root, self.MANIFEST_PATH)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_bytes(preview.manifest.canonical_bytes() + b"\n")
        if audit_log is not None:
            audit_log.append(
                "mobile.apple.scaffold",
                "apply",
                actor,
                "success",
                {
                    "workspace_manifest_sha256": preview.manifest.digest(),
                    "definition_sha256": preview.manifest.definition_sha256,
                    "state_strategy": preview.manifest.state_strategy.value,
                    "safe_snapshot": str(safe_snapshot) if safe_snapshot else None,
                    "backup": str(backup_path) if backup_path else None,
                    "actions": {item.path: item.action.value for item in preview.items},
                },
            )
        return preview.manifest

    def _previous_files(self, root: Path) -> dict[str, tuple[AppleFileOwnership, str]]:
        path = self._inside(root, self.MANIFEST_PATH)
        if not path.is_file():
            return {}
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if raw.get("schema_version") != 1 or not isinstance(raw.get("files"), list):
                return {}
            result: dict[str, tuple[AppleFileOwnership, str]] = {}
            for item in raw["files"]:
                relative = _safe_relative_path(str(item["path"]))
                digest = str(item["sha256"])
                _require_sha(digest, "prior file digest")
                result[relative] = (AppleFileOwnership(str(item["ownership"])), digest)
            return result
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _inside(root: Path, relative: str) -> Path:
        relative = _safe_relative_path(relative)
        target = root.joinpath(*PurePosixPath(relative).parts)
        ancestor = target
        tail: list[str] = []
        while not ancestor.exists() and ancestor != root:
            tail.append(ancestor.name)
            ancestor = ancestor.parent
        resolved = ancestor.resolve(strict=False)
        for part in reversed(tail):
            resolved = resolved / part
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise ValueError("Apple scaffold path escapes project root") from exc
        return resolved

    @staticmethod
    def _state_default(kind: StateValueKind, value: object) -> str:
        if value is None:
            if kind is StateValueKind.STRING:
                return '""'
            if kind is StateValueKind.BOOLEAN:
                return "false"
            if kind is StateValueKind.INTEGER:
                return "0"
            return "0.0"
        if kind is StateValueKind.STRING:
            return _swift_string(str(value))
        if kind is StateValueKind.BOOLEAN:
            return "true" if value is True else "false"
        if kind is StateValueKind.INTEGER:
            return str(int(value))
        return repr(float(value))

    @staticmethod
    def _swift_type(kind: StateValueKind) -> str:
        return {
            StateValueKind.STRING: "String",
            StateValueKind.BOOLEAN: "Bool",
            StateValueKind.INTEGER: "Int",
            StateValueKind.FLOAT: "Double",
        }[kind]

    def _state_source(self, definition: AppleScaffoldDefinition, app_model: DesktopAppModel) -> str:
        fields: list[str] = []
        for item in app_model.state_fields:
            name = _swift_symbol(item.field_id, "state")
            default = self._state_default(item.kind, item.default)
            type_name = self._swift_type(item.kind)
            if definition.state_strategy is AppleStateStrategy.OBSERVATION:
                fields.append(f"    var {name}: {type_name} = {default}")
            else:
                fields.append(f"    @Published var {name}: {type_name} = {default}")
        body = "\n".join(fields) if fields else "    var placeholder: Bool = false"
        if definition.state_strategy is AppleStateStrategy.OBSERVATION:
            return f'''import Observation\n\n@Observable\n@MainActor\nfinal class KodepoiaAppState {{\n{body}\n}}\n'''
        return f'''import Combine\n\n@MainActor\nfinal class KodepoiaAppState: ObservableObject {{\n{body}\n}}\n'''

    @staticmethod
    def _contract_source(app_model: DesktopAppModel) -> str:
        state_ids = ", ".join(_swift_string(item.field_id) for item in app_model.state_fields)
        command_ids = ", ".join(_swift_string(item.command_id) for item in app_model.commands)
        service_ids = ", ".join(_swift_string(item.service_id) for item in app_model.services)
        route_paths = ", ".join(_swift_string(item.path) for item in app_model.routes)
        return f'''enum KodepoiaAppModelContract {{\n    static let logicalModelSHA256 = {_swift_string(app_model.digest())}\n    static let stateIDs = [{state_ids}]\n    static let commandIDs = [{command_ids}]\n    static let serviceIDs = [{service_ids}]\n    static let routePaths = [{route_paths}]\n}}\n'''

    @staticmethod
    def _app_source() -> str:
        return '''import SwiftUI\n\n@main\nstruct KodepoiaIOSApp: App {\n    var body: some Scene {\n        WindowGroup {\n            ContentView()\n        }\n    }\n}\n'''

    def _content_view(self, definition: AppleScaffoldDefinition, app_model: DesktopAppModel) -> str:
        state_decl = (
            "    @State private var state = KodepoiaAppState()"
            if definition.state_strategy is AppleStateStrategy.OBSERVATION
            else "    @StateObject private var state = KodepoiaAppState()"
        )
        field_lines = []
        for item in app_model.state_fields[:8]:
            name = _swift_symbol(item.field_id, "state")
            field_lines.append(
                f'                LabeledContent({_swift_string(item.field_id)}) {{ Text(String(describing: state.{name})) }}'
            )
        fields = "\n".join(field_lines) if field_lines else '                Text("No state fields")'
        route_lines = "\n".join(
            f'                Text({_swift_string(item.path)}).accessibilityLabel({_swift_string("Route " + item.path)})'
            for item in app_model.routes[:16]
        ) or '                Text("/")'
        return f'''import SwiftUI\n\nstruct ContentView: View {{\n{state_decl}\n\n    var body: some View {{\n        NavigationStack {{\n            List {{\n                Section(String(localized: "status_ready")) {{\n{fields}\n                }}\n                Section("Routes") {{\n{route_lines}\n                }}\n            }}\n            .navigationTitle(String(localized: "app_name"))\n        }}\n    }}\n}}\n'''

    @staticmethod
    def _targeted_device_family(definition: AppleScaffoldDefinition) -> str:
        values: list[str] = []
        if MobileFormFactor.PHONE in definition.form_factors:
            values.append("1")
        if MobileFormFactor.TABLET in definition.form_factors:
            values.append("2")
        return ",".join(values)

    def _pbxproj(self, definition: AppleScaffoldDefinition, app_model: DesktopAppModel) -> str:
        locales = sorted({item.locale for item in definition.string_catalogs})
        file_ids = {
            "app": "A10000000000000000000001",
            "state": "A10000000000000000000002",
            "contract": "A10000000000000000000003",
            "content": "A10000000000000000000004",
            "plist": "A10000000000000000000005",
            "assets": "A10000000000000000000006",
            "product": "A10000000000000000000007",
        }
        build_ids = {
            "app": "B10000000000000000000001",
            "state": "B10000000000000000000002",
            "contract": "B10000000000000000000003",
            "content": "B10000000000000000000004",
            "assets": "B10000000000000000000005",
        }
        locale_file_ids = {locale: f"A2{index:022X}" for index, locale in enumerate(locales, start=1)}
        locale_build_ids = {locale: f"B2{index:022X}" for index, locale in enumerate(locales, start=1)}
        pbx_build = [
            f"\t\t{build_ids['app']} /* KodepoiaIOSApp.swift in Sources */ = {{isa = PBXBuildFile; fileRef = {file_ids['app']} /* KodepoiaIOSApp.swift */; }};",
            f"\t\t{build_ids['state']} /* AppState.swift in Sources */ = {{isa = PBXBuildFile; fileRef = {file_ids['state']} /* AppState.swift */; }};",
            f"\t\t{build_ids['contract']} /* AppModelContract.swift in Sources */ = {{isa = PBXBuildFile; fileRef = {file_ids['contract']} /* AppModelContract.swift */; }};",
            f"\t\t{build_ids['content']} /* ContentView.swift in Sources */ = {{isa = PBXBuildFile; fileRef = {file_ids['content']} /* ContentView.swift */; }};",
            f"\t\t{build_ids['assets']} /* Assets.xcassets in Resources */ = {{isa = PBXBuildFile; fileRef = {file_ids['assets']} /* Assets.xcassets */; }};",
        ]
        pbx_build.extend(
            f"\t\t{locale_build_ids[locale]} /* {locale}.lproj/Localizable.strings in Resources */ = {{isa = PBXBuildFile; fileRef = {locale_file_ids[locale]} /* {locale}.lproj/Localizable.strings */; }};"
            for locale in locales
        )
        file_refs = [
            f"\t\t{file_ids['app']} /* KodepoiaIOSApp.swift */ = {{isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = KodepoiaIOSApp.swift; sourceTree = \"<group>\"; }};",
            f"\t\t{file_ids['state']} /* AppState.swift */ = {{isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = AppState.swift; sourceTree = \"<group>\"; }};",
            f"\t\t{file_ids['contract']} /* AppModelContract.swift */ = {{isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = AppModelContract.swift; sourceTree = \"<group>\"; }};",
            f"\t\t{file_ids['content']} /* ContentView.swift */ = {{isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = ContentView.swift; sourceTree = \"<group>\"; }};",
            f"\t\t{file_ids['plist']} /* Info.plist */ = {{isa = PBXFileReference; lastKnownFileType = text.plist.xml; path = Info.plist; sourceTree = \"<group>\"; }};",
            f"\t\t{file_ids['assets']} /* Assets.xcassets */ = {{isa = PBXFileReference; lastKnownFileType = folder.assetcatalog; path = Assets.xcassets; sourceTree = \"<group>\"; }};",
            f"\t\t{file_ids['product']} /* KodepoiaIOS.app */ = {{isa = PBXFileReference; explicitFileType = wrapper.application; includeInIndex = 0; path = KodepoiaIOS.app; sourceTree = BUILT_PRODUCTS_DIR; }};",
        ]
        file_refs.extend(
            f"\t\t{locale_file_ids[locale]} /* {locale}.lproj/Localizable.strings */ = {{isa = PBXFileReference; lastKnownFileType = text.plist.strings; path = {locale}.lproj/Localizable.strings; sourceTree = \"<group>\"; }};"
            for locale in locales
        )
        locale_children = "\n".join(f"\t\t\t\t{locale_file_ids[locale]} /* {locale}.lproj/Localizable.strings */," for locale in locales)
        source_build_lines = "\n".join(
            f"\t\t\t\t{build_ids[key]} /* {name} in Sources */,"
            for key, name in (("app", "KodepoiaIOSApp.swift"), ("state", "AppState.swift"), ("contract", "AppModelContract.swift"), ("content", "ContentView.swift"))
        )
        resource_lines = [f"\t\t\t\t{build_ids['assets']} /* Assets.xcassets in Resources */, "]
        resource_lines.extend(f"\t\t\t\t{locale_build_ids[locale]} /* {locale}.lproj/Localizable.strings in Resources */," for locale in locales)
        known_regions = "\n".join(f"\t\t\t\t{locale}," for locale in locales)
        targeted = self._targeted_device_family(definition)
        return f'''// !$*UTF8*$!\n{{\n\tarchiveVersion = 1;\n\tclasses = {{\n\t}};\n\tobjectVersion = 77;\n\tobjects = {{\n\n/* Begin PBXBuildFile section */\n{chr(10).join(pbx_build)}\n/* End PBXBuildFile section */\n\n/* Begin PBXFileReference section */\n{chr(10).join(file_refs)}\n/* End PBXFileReference section */\n\n/* Begin PBXFrameworksBuildPhase section */\n\t\tC10000000000000000000001 /* Frameworks */ = {{\n\t\t\tisa = PBXFrameworksBuildPhase;\n\t\t\tbuildActionMask = 2147483647;\n\t\t\tfiles = (\n\t\t\t);\n\t\t\trunOnlyForDeploymentPostprocessing = 0;\n\t\t}};\n/* End PBXFrameworksBuildPhase section */\n\n/* Begin PBXGroup section */\n\t\tD10000000000000000000001 = {{\n\t\t\tisa = PBXGroup;\n\t\t\tchildren = (\n\t\t\t\tD10000000000000000000002 /* KodepoiaIOS */,\n\t\t\t\tD10000000000000000000003 /* Products */,\n\t\t\t);\n\t\t\tsourceTree = \"<group>\";\n\t\t}};\n\t\tD10000000000000000000002 /* KodepoiaIOS */ = {{\n\t\t\tisa = PBXGroup;\n\t\t\tchildren = (\n\t\t\t\t{file_ids['app']} /* KodepoiaIOSApp.swift */,\n\t\t\t\t{file_ids['state']} /* AppState.swift */,\n\t\t\t\t{file_ids['contract']} /* AppModelContract.swift */,\n\t\t\t\t{file_ids['content']} /* ContentView.swift */,\n\t\t\t\t{file_ids['plist']} /* Info.plist */,\n\t\t\t\t{file_ids['assets']} /* Assets.xcassets */,\n{locale_children}\n\t\t\t);\n\t\t\tpath = KodepoiaIOS;\n\t\t\tsourceTree = \"<group>\";\n\t\t}};\n\t\tD10000000000000000000003 /* Products */ = {{\n\t\t\tisa = PBXGroup;\n\t\t\tchildren = (\n\t\t\t\t{file_ids['product']} /* KodepoiaIOS.app */,\n\t\t\t);\n\t\t\tname = Products;\n\t\t\tsourceTree = \"<group>\";\n\t\t}};\n/* End PBXGroup section */\n\n/* Begin PBXNativeTarget section */\n\t\tE10000000000000000000001 /* KodepoiaIOS */ = {{\n\t\t\tisa = PBXNativeTarget;\n\t\t\tbuildConfigurationList = E10000000000000000000002 /* Build configuration list for PBXNativeTarget \"KodepoiaIOS\" */;\n\t\t\tbuildPhases = (\n\t\t\t\tF10000000000000000000001 /* Sources */,\n\t\t\t\tC10000000000000000000001 /* Frameworks */,\n\t\t\t\tF10000000000000000000002 /* Resources */,\n\t\t\t);\n\t\t\tbuildRules = (\n\t\t\t);\n\t\t\tdependencies = (\n\t\t\t);\n\t\t\tname = KodepoiaIOS;\n\t\t\tproductName = KodepoiaIOS;\n\t\t\tproductReference = {file_ids['product']} /* KodepoiaIOS.app */;\n\t\t\tproductType = \"com.apple.product-type.application\";\n\t\t}};\n/* End PBXNativeTarget section */\n\n/* Begin PBXProject section */\n\t\tE20000000000000000000001 /* Project object */ = {{\n\t\t\tisa = PBXProject;\n\t\t\tattributes = {{\n\t\t\t\tBuildIndependentTargetsInParallel = 1;\n\t\t\t\tLastSwiftUpdateCheck = 2600;\n\t\t\t\tLastUpgradeCheck = 2600;\n\t\t\t\tTargetAttributes = {{\n\t\t\t\t\tE10000000000000000000001 = {{\n\t\t\t\t\t\tCreatedOnToolsVersion = 26.0;\n\t\t\t\t\t}};\n\t\t\t\t}};\n\t\t\t}};\n\t\t\tbuildConfigurationList = E20000000000000000000002 /* Build configuration list for PBXProject \"KodepoiaIOS\" */;\n\t\t\tcompatibilityVersion = \"Xcode 15.0\";\n\t\t\tdevelopmentRegion = en;\n\t\t\thasScannedForEncodings = 0;\n\t\t\tknownRegions = (\n{known_regions}\n\t\t\t\tBase,\n\t\t\t);\n\t\t\tmainGroup = D10000000000000000000001;\n\t\t\tproductRefGroup = D10000000000000000000003 /* Products */;\n\t\t\tprojectDirPath = \"\";\n\t\t\tprojectRoot = \"\";\n\t\t\ttargets = (\n\t\t\t\tE10000000000000000000001 /* KodepoiaIOS */,\n\t\t\t);\n\t\t}};\n/* End PBXProject section */\n\n/* Begin PBXResourcesBuildPhase section */\n\t\tF10000000000000000000002 /* Resources */ = {{\n\t\t\tisa = PBXResourcesBuildPhase;\n\t\t\tbuildActionMask = 2147483647;\n\t\t\tfiles = (\n{chr(10).join(resource_lines)}\n\t\t\t);\n\t\t\trunOnlyForDeploymentPostprocessing = 0;\n\t\t}};\n/* End PBXResourcesBuildPhase section */\n\n/* Begin PBXSourcesBuildPhase section */\n\t\tF10000000000000000000001 /* Sources */ = {{\n\t\t\tisa = PBXSourcesBuildPhase;\n\t\t\tbuildActionMask = 2147483647;\n\t\t\tfiles = (\n{source_build_lines}\n\t\t\t);\n\t\t\trunOnlyForDeploymentPostprocessing = 0;\n\t\t}};\n/* End PBXSourcesBuildPhase section */\n\n/* Begin XCBuildConfiguration section */\n\t\t010000000000000000000001 /* Debug */ = {{\n\t\t\tisa = XCBuildConfiguration;\n\t\t\tbuildSettings = {{\n\t\t\t\tCLANG_ENABLE_MODULES = YES;\n\t\t\t\tSWIFT_ACTIVE_COMPILATION_CONDITIONS = DEBUG;\n\t\t\t\tSWIFT_OPTIMIZATION_LEVEL = \"-Onone\";\n\t\t\t}};\n\t\t\tname = Debug;\n\t\t}};\n\t\t010000000000000000000002 /* Release */ = {{\n\t\t\tisa = XCBuildConfiguration;\n\t\t\tbuildSettings = {{\n\t\t\t\tCLANG_ENABLE_MODULES = YES;\n\t\t\t\tSWIFT_COMPILATION_MODE = wholemodule;\n\t\t\t}};\n\t\t\tname = Release;\n\t\t}};\n\t\t010000000000000000000003 /* Debug */ = {{\n\t\t\tisa = XCBuildConfiguration;\n\t\t\tbuildSettings = {{\n\t\t\t\tCURRENT_PROJECT_VERSION = 1;\n\t\t\t\tGENERATE_INFOPLIST_FILE = NO;\n\t\t\t\tINFOPLIST_FILE = KodepoiaIOS/Info.plist;\n\t\t\t\tIPHONEOS_DEPLOYMENT_TARGET = {definition.minimum_os_version};\n\t\t\t\tMARKETING_VERSION = 0.1.0;\n\t\t\t\tPRODUCT_BUNDLE_IDENTIFIER = {_pbx_quote(definition.bundle_id)};\n\t\t\t\tPRODUCT_NAME = \"$(TARGET_NAME)\";\n\t\t\t\tSDKROOT = iphoneos;\n\t\t\t\tSUPPORTED_PLATFORMS = \"iphoneos iphonesimulator\";\n\t\t\t\tSUPPORTS_MACCATALYST = NO;\n\t\t\t\tSWIFT_VERSION = 5.0;\n\t\t\t\tTARGETED_DEVICE_FAMILY = \"{targeted}\";\n\t\t\t}};\n\t\t\tname = Debug;\n\t\t}};\n\t\t010000000000000000000004 /* Release */ = {{\n\t\t\tisa = XCBuildConfiguration;\n\t\t\tbuildSettings = {{\n\t\t\t\tCURRENT_PROJECT_VERSION = 1;\n\t\t\t\tGENERATE_INFOPLIST_FILE = NO;\n\t\t\t\tINFOPLIST_FILE = KodepoiaIOS/Info.plist;\n\t\t\t\tIPHONEOS_DEPLOYMENT_TARGET = {definition.minimum_os_version};\n\t\t\t\tMARKETING_VERSION = 0.1.0;\n\t\t\t\tPRODUCT_BUNDLE_IDENTIFIER = {_pbx_quote(definition.bundle_id)};\n\t\t\t\tPRODUCT_NAME = \"$(TARGET_NAME)\";\n\t\t\t\tSDKROOT = iphoneos;\n\t\t\t\tSUPPORTED_PLATFORMS = \"iphoneos iphonesimulator\";\n\t\t\t\tSUPPORTS_MACCATALYST = NO;\n\t\t\t\tSWIFT_VERSION = 5.0;\n\t\t\t\tTARGETED_DEVICE_FAMILY = \"{targeted}\";\n\t\t\t}};\n\t\t\tname = Release;\n\t\t}};\n/* End XCBuildConfiguration section */\n\n/* Begin XCConfigurationList section */\n\t\tE10000000000000000000002 /* Build configuration list for PBXNativeTarget \"KodepoiaIOS\" */ = {{\n\t\t\tisa = XCConfigurationList;\n\t\t\tbuildConfigurations = (\n\t\t\t\t010000000000000000000003 /* Debug */,\n\t\t\t\t010000000000000000000004 /* Release */,\n\t\t\t);\n\t\t\tdefaultConfigurationIsVisible = 0;\n\t\t\tdefaultConfigurationName = Release;\n\t\t}};\n\t\tE20000000000000000000002 /* Build configuration list for PBXProject \"KodepoiaIOS\" */ = {{\n\t\t\tisa = XCConfigurationList;\n\t\t\tbuildConfigurations = (\n\t\t\t\t010000000000000000000001 /* Debug */,\n\t\t\t\t010000000000000000000002 /* Release */,\n\t\t\t);\n\t\t\tdefaultConfigurationIsVisible = 0;\n\t\t\tdefaultConfigurationName = Release;\n\t\t}};\n/* End XCConfigurationList section */\n\t}};\n\trootObject = E20000000000000000000001 /* Project object */;\n}}\n'''

    @staticmethod
    def _scheme() -> str:
        return '''<?xml version="1.0" encoding="UTF-8"?>\n<Scheme LastUpgradeVersion="2600" version="1.7">\n  <BuildAction parallelizeBuildables="YES" buildImplicitDependencies="YES">\n    <BuildActionEntries>\n      <BuildActionEntry buildForTesting="YES" buildForRunning="YES" buildForProfiling="YES" buildForArchiving="YES" buildForAnalyzing="YES">\n        <BuildableReference BuildableIdentifier="primary" BlueprintIdentifier="E10000000000000000000001" BuildableName="KodepoiaIOS.app" BlueprintName="KodepoiaIOS" ReferencedContainer="container:KodepoiaIOS.xcodeproj"/>\n      </BuildActionEntry>\n    </BuildActionEntries>\n  </BuildAction>\n  <TestAction buildConfiguration="Debug" selectedDebuggerIdentifier="Xcode.DebuggerFoundation.Debugger.LLDB" selectedLauncherIdentifier="Xcode.DebuggerFoundation.Launcher.LLDB" shouldUseLaunchSchemeArgsEnv="YES"/>\n  <LaunchAction buildConfiguration="Debug" selectedDebuggerIdentifier="Xcode.DebuggerFoundation.Debugger.LLDB" selectedLauncherIdentifier="Xcode.DebuggerFoundation.Launcher.LLDB" launchStyle="0" useCustomWorkingDirectory="NO" ignoresPersistentStateOnLaunch="NO" debugDocumentVersioning="YES" debugServiceExtension="internal" allowLocationSimulation="YES">\n    <BuildableProductRunnable runnableDebuggingMode="0">\n      <BuildableReference BuildableIdentifier="primary" BlueprintIdentifier="E10000000000000000000001" BuildableName="KodepoiaIOS.app" BlueprintName="KodepoiaIOS" ReferencedContainer="container:KodepoiaIOS.xcodeproj"/>\n    </BuildableProductRunnable>\n  </LaunchAction>\n  <ProfileAction buildConfiguration="Release" shouldUseLaunchSchemeArgsEnv="YES" savedToolIdentifier="" useCustomWorkingDirectory="NO" debugDocumentVersioning="YES">\n    <BuildableProductRunnable runnableDebuggingMode="0">\n      <BuildableReference BuildableIdentifier="primary" BlueprintIdentifier="E10000000000000000000001" BuildableName="KodepoiaIOS.app" BlueprintName="KodepoiaIOS" ReferencedContainer="container:KodepoiaIOS.xcodeproj"/>\n    </BuildableProductRunnable>\n  </ProfileAction>\n  <AnalyzeAction buildConfiguration="Debug"/>\n  <ArchiveAction buildConfiguration="Release" revealArchiveInOrganizer="YES"/>\n</Scheme>\n'''

    @staticmethod
    def _info_plist(definition: AppleScaffoldDefinition) -> str:
        return f'''<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n<plist version="1.0">\n<dict>\n  <key>CFBundleDevelopmentRegion</key>\n  <string>en</string>\n  <key>CFBundleDisplayName</key>\n  <string>{_plist_text(definition.app_name)}</string>\n  <key>CFBundleExecutable</key>\n  <string>$(EXECUTABLE_NAME)</string>\n  <key>CFBundleIdentifier</key>\n  <string>$(PRODUCT_BUNDLE_IDENTIFIER)</string>\n  <key>CFBundleInfoDictionaryVersion</key>\n  <string>6.0</string>\n  <key>CFBundleName</key>\n  <string>$(PRODUCT_NAME)</string>\n  <key>CFBundlePackageType</key>\n  <string>APPL</string>\n  <key>CFBundleShortVersionString</key>\n  <string>$(MARKETING_VERSION)</string>\n  <key>CFBundleVersion</key>\n  <string>$(CURRENT_PROJECT_VERSION)</string>\n  <key>LSRequiresIPhoneOS</key>\n  <true/>\n  <key>UILaunchScreen</key>\n  <dict/>\n</dict>\n</plist>\n'''

    @staticmethod
    def _asset_catalog() -> str:
        return json.dumps({"info": {"author": "xcode", "version": 1}}, sort_keys=True, indent=2) + "\n"

    @staticmethod
    def _strings(catalog: AppleStringCatalog) -> str:
        return "\n".join(f"{_strings_text(key)} = {_strings_text(value)};" for key, value in catalog.values) + "\n"

    @staticmethod
    def _readme(definition: AppleScaffoldDefinition) -> str:
        bridge = "none" if definition.godot_export_bridge is None else definition.godot_export_bridge.bridge_id
        return f'''# {definition.app_name}\n\nGenerated by the governed Kodepoia R13.9 Apple scaffold.\n\n- Bundle ID: `{definition.bundle_id}`\n- Minimum iOS/iPadOS: `{definition.minimum_os_version}`\n- Target intent: `{definition.target_os_version}`\n- State strategy: `{definition.state_strategy.value}`\n- Godot export bridge: `{bridge}`\n\nThe generated Xcode project does not contain signing credentials or a Development Team. Simulator builds are performed by a separate governed fixed argv builder with signing disabled.\n'''
