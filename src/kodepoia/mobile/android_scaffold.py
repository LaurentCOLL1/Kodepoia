from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Iterable, Mapping
from urllib.parse import urlparse
from xml.sax.saxutils import escape as xml_escape

from kodepoia.core.audit import AuditLog
from kodepoia.core.backup import BackupManager
from kodepoia.core.safe_change import SafeChangeManager
from kodepoia.desktop.app_model import DesktopAppModel, StateValueKind
from kodepoia.mobile.contracts import MobileSourceKind, canonical_json_bytes
from kodepoia.project.dna import Platform, ProjectDNA, ProjectType

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_STABLE_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{0,127}$")
_VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+){1,3}$")
_COMPOSE_BOM_RE = re.compile(r"^[0-9]{4}\.[0-9]{2}\.[0-9]{2}$")
_LOCALE_RE = re.compile(r"^[a-z]{2,3}(?:-[A-Z]{2})?$")
_ANDROID_RES_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
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
    if len(normalized) > maximum or "\x00" in normalized:
        raise ValueError(f"{label} exceeds its bounded text policy")
    if any(ord(ch) < 32 and ch not in "\n\t" for ch in normalized):
        raise ValueError(f"{label} contains forbidden control characters")
    return normalized


def _safe_relative_path(value: str) -> str:
    if not value or "\\" in value or "\x00" in value:
        raise ValueError("unsafe Android scaffold path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("unsafe Android scaffold path")
    for part in path.parts:
        stem = part.split(".", 1)[0].upper()
        if stem in _WINDOWS_RESERVED or part.endswith((" ", ".")):
            raise ValueError("reserved Android scaffold path component")
        if any(ch in '<>:"|?*' for ch in part):
            raise ValueError("forbidden Android scaffold path character")
    return path.as_posix()


def _kotlin_string(value: str) -> str:
    value = _normalize_text(value, label="Kotlin string", maximum=2048)
    return (
        '"'
        + value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\t", "\\t")
        + '"'
    )


def _kotlin_symbol(logical_id: str, prefix: str) -> str:
    raw = re.sub(r"[^A-Za-z0-9_]", "_", logical_id.split(".")[-1])
    if not raw or raw[0].isdigit():
        raw = f"item_{raw}"
    digest = hashlib.sha256(logical_id.encode("utf-8")).hexdigest()[:8]
    return f"{prefix}_{raw}_{digest}"


def _android_package_path(application_id: str) -> str:
    return application_id.replace(".", "/")


class AndroidFileOwnership(StrEnum):
    KODEPOIA = "kodepoia"
    USER = "user"


class AndroidPreviewAction(StrEnum):
    CREATE = "create"
    REPLACE = "replace"
    UNCHANGED = "unchanged"
    PRESERVE = "preserve"
    CONFLICT = "conflict"


@dataclass(frozen=True, slots=True)
class AndroidDependencyEvidence:
    evidence_id: str
    android_gradle_plugin: str
    compose_bom: str
    compile_sdk: int
    observed_on: str
    source_urls: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_stable_id(self.evidence_id, "dependency evidence id")
        if _VERSION_RE.fullmatch(self.android_gradle_plugin) is None:
            raise ValueError("Android Gradle Plugin version must be explicit numeric dotted form")
        if _COMPOSE_BOM_RE.fullmatch(self.compose_bom) is None:
            raise ValueError("Compose BOM version must be explicit YYYY.MM.DD form")
        if not isinstance(self.compile_sdk, int) or not 1 <= self.compile_sdk <= 1000:
            raise ValueError("compile_sdk is outside the bounded Android range")
        try:
            date.fromisoformat(self.observed_on)
        except ValueError as exc:
            raise ValueError("observed_on must be an ISO date") from exc
        urls = tuple(sorted(set(self.source_urls)))
        if not urls or len(urls) > 8:
            raise ValueError("dependency evidence requires 1..8 official source URLs")
        for url in urls:
            parsed = urlparse(url)
            if parsed.scheme != "https" or parsed.hostname != "developer.android.com":
                raise ValueError("dependency evidence sources must be developer.android.com HTTPS URLs")
        object.__setattr__(self, "source_urls", urls)

    def to_dict(self) -> dict[str, object]:
        return {
            "evidence_id": self.evidence_id,
            "android_gradle_plugin": self.android_gradle_plugin,
            "compose_bom": self.compose_bom,
            "compile_sdk": self.compile_sdk,
            "observed_on": self.observed_on,
            "source_urls": list(self.source_urls),
        }

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_dict())

    def digest(self) -> str:
        return _sha256_bytes(self.canonical_bytes())


@dataclass(frozen=True, slots=True)
class AndroidStringCatalog:
    locale: str
    values: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        if self.locale != "en" and _LOCALE_RE.fullmatch(self.locale) is None:
            raise ValueError("invalid Android locale")
        normalized: list[tuple[str, str]] = []
        seen: set[str] = set()
        for name, value in self.values:
            if _ANDROID_RES_NAME_RE.fullmatch(name) is None:
                raise ValueError("invalid Android resource name")
            if name in seen:
                raise ValueError("duplicate Android string resource")
            seen.add(name)
            normalized.append((name, _normalize_text(value, label=f"string resource {name}", maximum=2048)))
        if not normalized:
            raise ValueError("Android string catalog cannot be empty")
        object.__setattr__(self, "values", tuple(sorted(normalized)))

    def to_dict(self) -> dict[str, object]:
        return {"locale": self.locale, "values": {key: value for key, value in self.values}}

    def digest(self) -> str:
        return _sha256_bytes(canonical_json_bytes(self.to_dict()))


@dataclass(frozen=True, slots=True)
class AndroidScaffoldLineage:
    dna_sha256: str
    product_sha256: str

    def validate(self) -> None:
        _require_sha(self.dna_sha256, "dna_sha256")
        _require_sha(self.product_sha256, "product_sha256")


@dataclass(frozen=True, slots=True)
class AndroidScaffoldDefinition:
    schema_version: int
    definition_id: str
    application_id: str
    namespace: str
    app_name: str
    min_sdk: int
    target_sdk: int
    dependency_evidence: AndroidDependencyEvidence
    app_model_sha256: str
    string_catalogs: tuple[AndroidStringCatalog, ...]
    source_kind: str = "native"

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported Android scaffold definition schema version")
        _require_stable_id(self.definition_id, "Android scaffold definition id")
        if self.source_kind != "native":
            raise ValueError("R13.3 Android native scaffold requires source_kind=native")
        # R13.2 already owns the platform identity grammar. Importing the domain
        # model through ProjectDNA below avoids a second, drifting regex here.
        if self.namespace != self.application_id:
            raise ValueError("Android namespace must match the accepted application id in R13.3")
        _normalize_text(self.app_name, label="Android app name", maximum=128)
        if not (1 <= self.min_sdk <= self.target_sdk <= 1000):
            raise ValueError("Android min/target SDK range is invalid")
        if self.dependency_evidence.compile_sdk < self.target_sdk:
            raise ValueError("compile_sdk evidence cannot be below target_sdk")
        _require_sha(self.app_model_sha256, "app_model_sha256")
        catalogs = tuple(sorted(self.string_catalogs, key=lambda item: item.locale))
        if not catalogs or catalogs[0].locale != "en":
            raise ValueError("Android scaffold requires a default en string catalog")
        if len({item.locale for item in catalogs}) != len(catalogs):
            raise ValueError("duplicate Android locale catalog")
        object.__setattr__(self, "string_catalogs", catalogs)

    @classmethod
    def from_project(
        cls,
        dna: ProjectDNA,
        app_model: DesktopAppModel,
        dependency_evidence: AndroidDependencyEvidence,
        *,
        catalogs: Iterable[AndroidStringCatalog] = (),
    ) -> "AndroidScaffoldDefinition":
        dna.validate()
        app_model.validate()
        if dna.project_type is not ProjectType.MOBILE_APP:
            raise ValueError("Android native scaffold requires a mobile_app Project DNA")
        if Platform.ANDROID not in dna.platforms or dna.mobile is None:
            raise ValueError("Android native scaffold requires an Android mobile profile")
        if dna.mobile.source_kind is not MobileSourceKind.NATIVE:
            raise ValueError("Android native scaffold cannot render a Godot export profile")
        if dna.mobile.android_application_id is None:
            raise ValueError("Android application id is required")
        if dna.mobile.android_min_api is None or dna.mobile.android_target_api is None:
            raise ValueError("Android min/target API intent is required")
        default_catalog = AndroidStringCatalog("en", (("app_name", dna.name.strip()),))
        supplied = tuple(catalogs)
        if supplied:
            by_locale = {item.locale: item for item in supplied}
            by_locale.setdefault("en", default_catalog)
            string_catalogs = tuple(by_locale.values())
        else:
            string_catalogs = (default_catalog,)
        return cls(
            schema_version=1,
            definition_id="project.android.native",
            application_id=dna.mobile.android_application_id,
            namespace=dna.mobile.android_application_id,
            app_name=dna.name.strip(),
            min_sdk=dna.mobile.android_min_api,
            target_sdk=dna.mobile.android_target_api,
            dependency_evidence=dependency_evidence,
            app_model_sha256=app_model.digest(),
            string_catalogs=string_catalogs,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "definition_id": self.definition_id,
            "application_id": self.application_id,
            "namespace": self.namespace,
            "app_name": self.app_name,
            "min_sdk": self.min_sdk,
            "target_sdk": self.target_sdk,
            "dependency_evidence": self.dependency_evidence.to_dict(),
            "app_model_sha256": self.app_model_sha256,
            "string_catalogs": [item.to_dict() for item in self.string_catalogs],
            "source_kind": self.source_kind,
        }

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_dict())

    def digest(self) -> str:
        return _sha256_bytes(self.canonical_bytes())


@dataclass(frozen=True, slots=True)
class AndroidGeneratedFile:
    path: str
    content: str
    sha256: str
    ownership: AndroidFileOwnership


@dataclass(frozen=True, slots=True)
class AndroidWorkspaceManifest:
    schema_version: int
    definition_sha256: str
    dependency_evidence_sha256: str
    app_model_sha256: str
    dna_sha256: str
    product_sha256: str
    files: tuple[AndroidGeneratedFile, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "definition_sha256": self.definition_sha256,
            "dependency_evidence_sha256": self.dependency_evidence_sha256,
            "app_model_sha256": self.app_model_sha256,
            "dna_sha256": self.dna_sha256,
            "product_sha256": self.product_sha256,
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
class AndroidPreviewItem:
    path: str
    action: AndroidPreviewAction
    current_sha256: str | None
    desired_sha256: str
    ownership: AndroidFileOwnership


@dataclass(frozen=True, slots=True)
class AndroidScaffoldPreview:
    manifest: AndroidWorkspaceManifest
    items: tuple[AndroidPreviewItem, ...]

    @property
    def has_conflicts(self) -> bool:
        return any(item.action is AndroidPreviewAction.CONFLICT for item in self.items)

    @property
    def destructive(self) -> bool:
        return any(item.action is AndroidPreviewAction.REPLACE for item in self.items)


class AndroidScaffoldEngine:
    """Pure deterministic R13.3 renderer.

    It intentionally launches no Gradle/JDK/SDK process. R13.4 owns build/tool
    execution. All generated source is constructed from repository-owned fixed
    builders and typed accepted models, never from arbitrary template code.
    """

    MANIFEST_PATH = ".kodepoia/mobile/android/workspace-manifest.json"

    def render(
        self,
        definition: AndroidScaffoldDefinition,
        app_model: DesktopAppModel,
        lineage: AndroidScaffoldLineage,
    ) -> tuple[tuple[AndroidGeneratedFile, ...], AndroidWorkspaceManifest]:
        app_model.validate()
        lineage.validate()
        if app_model.digest() != definition.app_model_sha256:
            raise ValueError("Android scaffold app-model digest mismatch")

        package_path = _android_package_path(definition.application_id)
        entries: list[tuple[str, str, AndroidFileOwnership]] = [
            ("settings.gradle.kts", self._settings(definition), AndroidFileOwnership.KODEPOIA),
            ("build.gradle.kts", self._root_build(), AndroidFileOwnership.KODEPOIA),
            ("gradle/libs.versions.toml", self._version_catalog(definition), AndroidFileOwnership.KODEPOIA),
            ("gradle.properties", self._gradle_properties(), AndroidFileOwnership.KODEPOIA),
            ("app/build.gradle.kts", self._app_build(definition), AndroidFileOwnership.KODEPOIA),
            ("app/src/main/AndroidManifest.xml", self._manifest(definition), AndroidFileOwnership.KODEPOIA),
            (f"app/src/main/java/{package_path}/MainActivity.kt", self._main_activity(definition), AndroidFileOwnership.KODEPOIA),
            (f"app/src/main/java/{package_path}/KodepoiaAppModel.kt", self._app_model_source(definition, app_model), AndroidFileOwnership.KODEPOIA),
            ("app/src/main/res/values/themes.xml", self._themes(), AndroidFileOwnership.KODEPOIA),
            ("README.md", self._readme(definition), AndroidFileOwnership.USER),
        ]
        for catalog in definition.string_catalogs:
            qualifier = "values" if catalog.locale == "en" else f"values-{catalog.locale}"
            entries.append(
                (f"app/src/main/res/{qualifier}/strings.xml", self._strings(catalog), AndroidFileOwnership.KODEPOIA)
            )

        rendered: list[AndroidGeneratedFile] = []
        seen: set[str] = set()
        for raw_path, raw_content, ownership in entries:
            path = _safe_relative_path(raw_path)
            if path == self.MANIFEST_PATH or path in seen:
                raise ValueError("Android scaffold path collision")
            seen.add(path)
            content = _normalize_text(raw_content, label=f"generated file {path}", maximum=1_000_000)
            digest = _sha256_bytes(content.encode("utf-8"))
            rendered.append(AndroidGeneratedFile(path, content, digest, ownership))
        rendered.sort(key=lambda item: item.path)
        manifest = AndroidWorkspaceManifest(
            schema_version=1,
            definition_sha256=definition.digest(),
            dependency_evidence_sha256=definition.dependency_evidence.digest(),
            app_model_sha256=definition.app_model_sha256,
            dna_sha256=lineage.dna_sha256,
            product_sha256=lineage.product_sha256,
            files=tuple(rendered),
        )
        return tuple(rendered), manifest

    def preview(
        self,
        project_root: Path,
        definition: AndroidScaffoldDefinition,
        app_model: DesktopAppModel,
        lineage: AndroidScaffoldLineage,
    ) -> AndroidScaffoldPreview:
        root = project_root.resolve(strict=False)
        rendered, manifest = self.render(definition, app_model, lineage)
        previous = self._previous_files(root)
        items: list[AndroidPreviewItem] = []
        for desired in rendered:
            target = self._inside(root, desired.path)
            if not target.exists():
                action = AndroidPreviewAction.CREATE
                current = None
            elif not target.is_file():
                action = AndroidPreviewAction.CONFLICT
                current = None
            else:
                current = _sha256_bytes(target.read_bytes())
                prior = previous.get(desired.path)
                if current == desired.sha256:
                    action = AndroidPreviewAction.UNCHANGED
                elif desired.ownership is AndroidFileOwnership.USER:
                    action = AndroidPreviewAction.PRESERVE
                elif prior is not None and prior[0] is AndroidFileOwnership.KODEPOIA and current == prior[1]:
                    action = AndroidPreviewAction.REPLACE
                else:
                    action = AndroidPreviewAction.CONFLICT
            items.append(AndroidPreviewItem(desired.path, action, current, desired.sha256, desired.ownership))
        return AndroidScaffoldPreview(manifest, tuple(items))

    def apply(
        self,
        project_root: Path,
        preview: AndroidScaffoldPreview,
        *,
        safe_change: SafeChangeManager | None = None,
        backup_manager: BackupManager | None = None,
        audit_log: AuditLog | None = None,
        actor: str = "kodepoia",
    ) -> AndroidWorkspaceManifest:
        root = project_root.resolve(strict=False)
        root.mkdir(parents=True, exist_ok=True)
        if preview.has_conflicts:
            raise FileExistsError("refusing Android scaffold apply with ownership/path conflicts")
        replace_paths = [
            self._inside(root, item.path)
            for item in preview.items
            if item.action is AndroidPreviewAction.REPLACE
        ]
        safe_snapshot: Path | None = None
        backup_path: Path | None = None
        if replace_paths:
            if safe_change is None or backup_manager is None:
                raise ValueError("Android scaffold replacement requires SafeChangeManager and BackupManager")
            safe_snapshot = safe_change.snapshot(replace_paths)
            backup_path = backup_manager.create_archive(root, label="android-scaffold")

        by_path = {item.path: item for item in preview.manifest.files}
        for item in preview.items:
            if item.action in {AndroidPreviewAction.UNCHANGED, AndroidPreviewAction.PRESERVE}:
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
                "mobile.android.scaffold",
                "apply",
                actor,
                "success",
                {
                    "workspace_manifest_sha256": preview.manifest.digest(),
                    "definition_sha256": preview.manifest.definition_sha256,
                    "dependency_evidence_sha256": preview.manifest.dependency_evidence_sha256,
                    "safe_snapshot": str(safe_snapshot) if safe_snapshot else None,
                    "backup": str(backup_path) if backup_path else None,
                    "actions": {item.path: item.action.value for item in preview.items},
                },
            )
        return preview.manifest

    def _previous_files(self, root: Path) -> dict[str, tuple[AndroidFileOwnership, str]]:
        path = self._inside(root, self.MANIFEST_PATH)
        if not path.is_file():
            return {}
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if raw.get("schema_version") != 1 or not isinstance(raw.get("files"), list):
                return {}
            result: dict[str, tuple[AndroidFileOwnership, str]] = {}
            for item in raw["files"]:
                relative = _safe_relative_path(str(item["path"]))
                digest = str(item["sha256"])
                _require_sha(digest, "prior file digest")
                result[relative] = (AndroidFileOwnership(str(item["ownership"])), digest)
            return result
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _inside(root: Path, relative: str) -> Path:
        relative = _safe_relative_path(relative)
        target = root.joinpath(*PurePosixPath(relative).parts)
        # Existing ancestors are resolved so a symlink cannot redirect generated
        # files outside the project. Non-existing tails remain deterministic.
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
            raise ValueError("Android scaffold path escapes project root") from exc
        return resolved

    @staticmethod
    def _settings(definition: AndroidScaffoldDefinition) -> str:
        return f'''pluginManagement {{
    repositories {{
        google()
        mavenCentral()
        gradlePluginPortal()
    }}
}}

dependencyResolutionManagement {{
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {{
        google()
        mavenCentral()
    }}
}}

rootProject.name = {_kotlin_string(definition.app_name)}
include(":app")
'''

    @staticmethod
    def _root_build() -> str:
        return '''plugins {
    alias(libs.plugins.android.application) apply false
}
'''

    @staticmethod
    def _version_catalog(definition: AndroidScaffoldDefinition) -> str:
        evidence = definition.dependency_evidence
        return f'''[versions]
agp = "{evidence.android_gradle_plugin}"
compose-bom = "{evidence.compose_bom}"

[libraries]
compose-bom = {{ module = "androidx.compose:compose-bom", version.ref = "compose-bom" }}
compose-ui = {{ module = "androidx.compose.ui:ui" }}
compose-ui-tooling-preview = {{ module = "androidx.compose.ui:ui-tooling-preview" }}
compose-material3 = {{ module = "androidx.compose.material3:material3" }}

[plugins]
android-application = {{ id = "com.android.application", version.ref = "agp" }}
'''

    @staticmethod
    def _gradle_properties() -> str:
        return '''org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
android.useAndroidX=true
android.nonTransitiveRClass=true
'''

    @staticmethod
    def _app_build(definition: AndroidScaffoldDefinition) -> str:
        return f'''plugins {{
    alias(libs.plugins.android.application)
}}

android {{
    namespace = "{definition.namespace}"
    compileSdk = {definition.dependency_evidence.compile_sdk}

    defaultConfig {{
        applicationId = "{definition.application_id}"
        minSdk = {definition.min_sdk}
        targetSdk = {definition.target_sdk}
        versionCode = 1
        versionName = "0.1.0"
    }}

    buildFeatures {{
        compose = true
    }}
}}

dependencies {{
    implementation(platform(libs.compose.bom))
    implementation(libs.compose.ui)
    implementation(libs.compose.ui.tooling.preview)
    implementation(libs.compose.material3)
}}
'''

    @staticmethod
    def _manifest(definition: AndroidScaffoldDefinition) -> str:
        return '''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application
        android:allowBackup="false"
        android:label="@string/app_name"
        android:theme="@style/Theme.Kodepoia">
        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
'''

    @staticmethod
    def _main_activity(definition: AndroidScaffoldDefinition) -> str:
        return f'''package {definition.namespace}

import android.app.Activity
import android.os.Bundle
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.ComposeView
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp

class MainActivity : Activity() {{
    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)
        setContentView(ComposeView(this).apply {{
            setContent {{ KodepoiaApp() }}
        }})
    }}
}}

@Composable
fun KodepoiaApp() {{
    MaterialTheme {{
        Scaffold {{ innerPadding ->
            BoxWithConstraints(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(innerPadding)
                    .semantics {{ contentDescription = "Application content" }}
            ) {{
                val adaptivePadding = if (maxWidth < 600.dp) 16.dp else 32.dp
                Column(
                    modifier = Modifier.padding(adaptivePadding),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {{
                    Text(text = {_kotlin_string(definition.app_name)}, style = MaterialTheme.typography.headlineMedium)
                    Text(text = "Kodepoia deterministic Android scaffold")
                }}
            }}
        }}
    }}
}}
'''

    @staticmethod
    def _app_model_source(definition: AndroidScaffoldDefinition, model: DesktopAppModel) -> str:
        state_lines: list[str] = []
        for field in sorted(model.state_fields, key=lambda item: item.field_id):
            symbol = _kotlin_symbol(field.field_id, "state")
            if field.kind is StateValueKind.STRING:
                kotlin_type = "String"
                default = _kotlin_string(field.default if isinstance(field.default, str) else "")
            elif field.kind is StateValueKind.INTEGER:
                kotlin_type = "Int"
                default = str(field.default if isinstance(field.default, int) and not isinstance(field.default, bool) else 0)
            elif field.kind is StateValueKind.FLOAT:
                kotlin_type = "Double"
                numeric = float(field.default) if isinstance(field.default, (int, float)) and not isinstance(field.default, bool) else 0.0
                default = repr(numeric)
            else:
                kotlin_type = "Boolean"
                default = "true" if field.default is True else "false"
            state_lines.append(f"    val {symbol}: {kotlin_type} = {default}, // {field.field_id}")
        if not state_lines:
            state_lines.append("    val kodepoiaEmpty: Boolean = true,")

        routes = ",\n".join(
            f"    RouteSpec({_kotlin_string(route.route_id)}, {_kotlin_string(route.path)})"
            for route in sorted(model.routes, key=lambda item: item.route_id)
        )
        commands = ",\n".join(
            f"    CommandSpec({_kotlin_string(command.command_id)}, {_kotlin_string(command.operation)})"
            for command in sorted(model.commands, key=lambda item: item.command_id)
        )
        return f'''package {definition.namespace}

// Logical projection of accepted Kodepoia app contracts.
data class KodepoiaState(
{chr(10).join(state_lines)}
)

data class RouteSpec(val id: String, val path: String)
data class CommandSpec(val id: String, val operation: String)

val KodepoiaRoutes: List<RouteSpec> = listOf(
{routes}
)

val KodepoiaCommands: List<CommandSpec> = listOf(
{commands}
)

const val KodepoiaLogicalModelSha256: String = "{model.digest()}"
'''

    @staticmethod
    def _strings(catalog: AndroidStringCatalog) -> str:
        lines = ["<?xml version=\"1.0\" encoding=\"utf-8\"?>", "<resources>"]
        for name, value in catalog.values:
            escaped = xml_escape(value, {'"': "&quot;", "'": "&apos;"})
            lines.append(f'    <string name="{name}">{escaped}</string>')
        lines.append("</resources>")
        return "\n".join(lines) + "\n"

    @staticmethod
    def _themes() -> str:
        return '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="Theme.Kodepoia" parent="android:style/Theme.Material.Light.NoActionBar" />
</resources>
'''

    @staticmethod
    def _readme(definition: AndroidScaffoldDefinition) -> str:
        return f'''# {definition.app_name}

Generated by Kodepoia R13.3 from accepted Project DNA/Product intent.

This file is user-owned and is preserved on regeneration.
Build, SDK, signing, device and store execution are intentionally outside R13.3.
'''


__all__ = [
    "AndroidDependencyEvidence",
    "AndroidFileOwnership",
    "AndroidGeneratedFile",
    "AndroidPreviewAction",
    "AndroidScaffoldDefinition",
    "AndroidScaffoldEngine",
    "AndroidScaffoldLineage",
    "AndroidScaffoldPreview",
    "AndroidStringCatalog",
    "AndroidWorkspaceManifest",
]
