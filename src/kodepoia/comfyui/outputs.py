from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import uuid
from dataclasses import dataclass, replace
from enum import StrEnum
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from kodepoia.assets.contracts import (
    AssetId,
    AssetKind,
    AssetRevisionId,
    PreservationPolicy,
    ReuseScope,
)
from kodepoia.assets.service import AssetService
from kodepoia.assets.transforms import (
    DeterminismState,
    ToolIdentity,
    TransformRecipe,
    TransformRegistry,
    TransformService,
)

from .client import ComfyUIClient
from .contracts import ComfyOutputReference, ComfyRunState
from .errors import ComfyGovernanceError, ComfyProtocolError
from .execution import ComfyRunManifest, ComfyRunStore
from .serialization import canonical_json_bytes, canonical_sha256, make_envelope, parse_envelope

_CAPTURE_SCHEMA = "kodepoia.comfy-output-capture"
_CAPTURE_VERSION = 1
_SAFE_RUN_RE = re.compile(r"^run_[0-9a-f]{32}$")
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_IMAGE_KINDS = frozenset({AssetKind.IMAGE, AssetKind.TEXTURE, AssetKind.UI})
_MAX_CAPTURE_OUTPUTS = 4096
_MAX_DISPLAY_NAME = 512


class ComfyCaptureState(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"


class ComfyPartialCaptureError(ComfyProtocolError):
    """Raised when a post-validation promotion failed after at least one READY output was created."""


@dataclass(frozen=True, slots=True)
class ComfyOutputSpec:
    node_id: str
    output_index: int
    asset_kind: AssetKind
    display_name: str
    output_asset_id: AssetId | None = None
    expected_sha256: str | None = None
    expected_length: int | None = None

    def __post_init__(self) -> None:
        if not self.node_id or len(self.node_id) > 128:
            raise ValueError("node_id must be a non-empty bounded string")
        if isinstance(self.output_index, bool) or not isinstance(self.output_index, int) or self.output_index < 0:
            raise ValueError("output_index must be a non-negative integer")
        if not self.display_name.strip() or len(self.display_name) > _MAX_DISPLAY_NAME:
            raise ValueError("display_name must be non-empty and bounded")
        if self.expected_sha256 is not None and not _HEX64_RE.fullmatch(self.expected_sha256):
            raise ValueError("expected_sha256 must be a lowercase SHA-256 digest")
        if self.expected_length is not None and (
            isinstance(self.expected_length, bool) or not isinstance(self.expected_length, int) or self.expected_length < 0
        ):
            raise ValueError("expected_length must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class ComfyCapturedOutput:
    node_id: str
    output_index: int
    asset_id: str
    revision_id: str
    kind: str
    content_sha256: str
    content_length: int

    def canonical(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "output_index": self.output_index,
            "asset_id": self.asset_id,
            "revision_id": self.revision_id,
            "kind": self.kind,
            "content_sha256": self.content_sha256,
            "content_length": self.content_length,
        }


@dataclass(frozen=True, slots=True)
class ComfyOutputCaptureManifest:
    run_id: str
    run_manifest_digest_sha256: str
    evidence_revision_id: str
    state: ComfyCaptureState
    outputs: tuple[ComfyCapturedOutput, ...]
    capture_digest_sha256: str

    def canonical_without_digest(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "run_manifest_digest_sha256": self.run_manifest_digest_sha256,
            "evidence_revision_id": self.evidence_revision_id,
            "state": self.state.value,
            "outputs": [item.canonical() for item in self.outputs],
        }

    def payload(self) -> dict[str, Any]:
        result = self.canonical_without_digest()
        result["capture_digest_sha256"] = self.capture_digest_sha256
        return result

    def envelope(self) -> dict[str, Any]:
        return make_envelope(schema=_CAPTURE_SCHEMA, version=_CAPTURE_VERSION, payload=self.payload())


class ComfyOutputCaptureStore:
    """Immutable run-linked capture evidence separate from canonical R8 asset manifests."""

    def __init__(self, root: Path | str) -> None:
        raw = Path(root)
        if raw.exists() and raw.is_symlink():
            raise ComfyProtocolError("Comfy output capture root must not be a symlink")
        raw.mkdir(parents=True, exist_ok=True)
        self.root = raw.resolve()

    def save(self, manifest: ComfyOutputCaptureManifest) -> Path:
        _validate_capture_manifest(manifest)
        path = self._path(manifest.run_id)
        data = canonical_json_bytes(manifest.envelope())
        if path.exists():
            if path.is_symlink() or path.read_bytes() != data:
                raise ComfyProtocolError("Comfy output capture evidence is immutable and conflicts with existing evidence")
            return path
        temporary = self.root / f".{manifest.run_id}.{uuid.uuid4().hex}.tmp"
        try:
            with temporary.open("xb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
        return path

    def load(self, run_id: str) -> ComfyOutputCaptureManifest:
        path = self._path(run_id)
        if path.is_symlink():
            raise ComfyProtocolError("Comfy output capture evidence must not be a symlink")
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise KeyError(run_id) from exc
        except json.JSONDecodeError as exc:
            raise ComfyProtocolError("Comfy output capture evidence is invalid JSON") from exc
        if not isinstance(document, dict):
            raise ComfyProtocolError("Comfy output capture evidence root must be an object")
        payload = parse_envelope(document, expected_schema=_CAPTURE_SCHEMA)
        manifest = _capture_manifest_from_payload(payload)
        _validate_capture_manifest(manifest)
        return manifest

    def _path(self, run_id: str) -> Path:
        if not isinstance(run_id, str) or not _SAFE_RUN_RE.fullmatch(run_id):
            raise ValueError("run_id must be a generated R9 run identifier")
        path = (self.root / f"{run_id}.json").resolve(strict=False)
        if not path.is_relative_to(self.root):
            raise ComfyProtocolError("Comfy output capture path escapes its root")
        return path


class _CapturedBytesTransform:
    transform_id = "comfyui.generated-output.capture.v1"
    tool_identity = ToolIdentity("kodepoia-comfyui-output-capture", "1")

    def __init__(self, content_by_digest: dict[str, bytes]) -> None:
        self._content = dict(content_by_digest)

    def execute(self, inputs: tuple[Path, ...], output_dir: Path, parameters: dict[str, Any]) -> tuple[Path, ...]:
        if not inputs:
            raise ValueError("ComfyUI capture transform requires generation evidence input")
        digest = parameters.get("content_sha256")
        if not isinstance(digest, str) or digest not in self._content:
            raise ValueError("ComfyUI capture transform content digest is unavailable")
        data = self._content[digest]
        if hashlib.sha256(data).hexdigest() != digest:
            raise ComfyProtocolError("Captured output bytes changed after validation")
        output = output_dir / "captured-output.bin"
        output.write_bytes(data)
        return (output,)


class ComfyOutputCaptureService:
    """Retrieve reconciled outputs and bridge them into canonical R8 DERIVED revisions."""

    def __init__(
        self,
        client: ComfyUIClient,
        run_store: ComfyRunStore,
        asset_service: AssetService,
        capture_store: ComfyOutputCaptureStore | None = None,
    ) -> None:
        self.client = client
        self.run_store = run_store
        self.assets = asset_service
        self.capture_store = capture_store or ComfyOutputCaptureStore(run_store.root / ".captures")

    def capture(
        self,
        run_id: str,
        specs: tuple[ComfyOutputSpec, ...],
        *,
        source_revision_ids: tuple[AssetRevisionId, ...] = (),
    ) -> ComfyOutputCaptureManifest:
        manifest = self.run_store.load(run_id)
        self._verify_run(manifest)
        if not specs or len(specs) > _MAX_CAPTURE_OUTPUTS:
            raise ValueError("R9.6 requires between 1 and 4096 explicit output specs")
        if len({(item.node_id, item.output_index) for item in specs}) != len(specs):
            raise ValueError("R9.6 output specs must be unique by node/output index")

        references = {(item.node_id, item.output_index): item for item in manifest.output_references}
        if len(references) != len(manifest.output_references):
            raise ComfyProtocolError("Run manifest contains duplicate output references")

        stage_root = self.assets.project.resolve(f".kodepoia/comfyui/output-staging/{manifest.run_id}")
        if stage_root.exists():
            if stage_root.is_symlink():
                raise ComfyProtocolError("Comfy output staging root must not be a symlink")
            shutil.rmtree(stage_root)
        stage_root.mkdir(parents=True, exist_ok=False)
        validated: list[tuple[ComfyOutputSpec, ComfyOutputReference, bytes, str, int]] = []
        try:
            for index, spec in enumerate(specs):
                try:
                    reference = references[(spec.node_id, spec.output_index)]
                except KeyError as exc:
                    raise ComfyProtocolError("Requested output spec has no reconciled output reference") from exc
                self._verify_reference(manifest, reference)
                data = self.client.retrieve_output(reference)
                digest = hashlib.sha256(data).hexdigest()
                length = len(data)
                if spec.expected_sha256 is not None and digest != spec.expected_sha256:
                    raise ComfyProtocolError("Retrieved ComfyUI output SHA-256 does not match expected evidence")
                if spec.expected_length is not None and length != spec.expected_length:
                    raise ComfyProtocolError("Retrieved ComfyUI output byte length does not match expected evidence")
                _verify_media_bytes(spec.asset_kind, reference.server_filename, data)
                stage = stage_root / f"{index:04d}-{digest}.part"
                stage.write_bytes(data)
                if hashlib.sha256(stage.read_bytes()).hexdigest() != digest or stage.stat().st_size != length:
                    raise ComfyProtocolError("Managed output staging verification failed")
                validated.append((spec, reference, data, digest, length))

            evidence_revision = self._persist_generation_evidence(manifest, validated, source_revision_ids)
            content_map = {digest: data for _spec, _ref, data, digest, _length in validated}
            registry = TransformRegistry()
            registry.register(_CapturedBytesTransform(content_map))
            transform = TransformService(
                self.assets.store,
                registry,
                environment_identity={
                    "capability_identity_sha256": manifest.capability_identity_sha256,
                    "comfyui_version": manifest.comfyui_version or "unknown",
                    "python_version": manifest.python_version or "unknown",
                    "endpoint": manifest.capability_endpoint,
                },
            )
            lineage_inputs = _unique_revision_ids((evidence_revision,) + tuple(source_revision_ids))
            captured: list[ComfyCapturedOutput] = []
            for spec, reference, _data, digest, length in validated:
                output_asset_id = spec.output_asset_id or AssetId.from_seed(
                    "r9.6-comfy-output",
                    f"{manifest.run_id}:{spec.node_id}:{spec.output_index}",
                )
                recipe = TransformRecipe(
                    transform_id=_CapturedBytesTransform.transform_id,
                    schema_version=1,
                    parameters={
                        "run_id": manifest.run_id,
                        "run_manifest_digest_sha256": manifest.manifest_digest_sha256,
                        "definition_id": manifest.definition_id,
                        "definition_digest_sha256": manifest.definition_digest_sha256,
                        "model_resolution_digest_sha256": manifest.model_resolution_digest_sha256,
                        "instance_digest_sha256": manifest.instance_digest_sha256,
                        "prompt_digest_sha256": manifest.prompt_digest_sha256,
                        "parameter_values": dict(manifest.parameter_values),
                        "input_bindings": dict(manifest.input_bindings),
                        "seed_values": dict(manifest.seed_values),
                        "output_node_id": reference.node_id,
                        "output_index": reference.output_index,
                        "output_reference_sha256": canonical_sha256(reference.canonical()),
                        "content_sha256": digest,
                        "content_length": length,
                    },
                    output_kind=spec.asset_kind,
                    determinism=DeterminismState.DETERMINISTIC,
                )
                try:
                    result = transform.run(
                        lineage_inputs,
                        recipe,
                        output_asset_id=output_asset_id,
                        display_name=spec.display_name,
                    )
                except Exception as exc:
                    if captured:
                        partial = _seal_capture(
                            ComfyOutputCaptureManifest(
                                run_id=manifest.run_id,
                                run_manifest_digest_sha256=manifest.manifest_digest_sha256,
                                evidence_revision_id=str(evidence_revision),
                                state=ComfyCaptureState.PARTIAL,
                                outputs=tuple(captured),
                                capture_digest_sha256="",
                            )
                        )
                        self.capture_store.save(partial)
                        raise ComfyPartialCaptureError(
                            "ComfyUI multi-output promotion became PARTIAL; promoted revisions are preserved in capture evidence"
                        ) from exc
                    raise
                revision_id = result.output_revision_ids[0]
                detail = self.assets.show(revision_id)
                if detail.summary.role != "derived" or detail.content_sha256 != digest or detail.content_length != length:
                    raise ComfyProtocolError("R8 promoted revision does not match validated ComfyUI output evidence")
                captured.append(
                    ComfyCapturedOutput(
                        node_id=reference.node_id,
                        output_index=reference.output_index,
                        asset_id=str(output_asset_id),
                        revision_id=str(revision_id),
                        kind=spec.asset_kind.value,
                        content_sha256=digest,
                        content_length=length,
                    )
                )

            result = _seal_capture(
                ComfyOutputCaptureManifest(
                    run_id=manifest.run_id,
                    run_manifest_digest_sha256=manifest.manifest_digest_sha256,
                    evidence_revision_id=str(evidence_revision),
                    state=ComfyCaptureState.COMPLETE,
                    outputs=tuple(captured),
                    capture_digest_sha256="",
                )
            )
            self.capture_store.save(result)
            return result
        finally:
            shutil.rmtree(stage_root, ignore_errors=True)

    def _verify_run(self, manifest: ComfyRunManifest) -> None:
        if manifest.state is not ComfyRunState.SUCCEEDED:
            raise ComfyGovernanceError("Only reconciled SUCCEEDED runs may promote generated outputs")
        if self.client.endpoint.origin != manifest.capability_endpoint:
            raise ComfyGovernanceError("Output capture client origin does not match the accepted run environment")
        if not manifest.output_references:
            raise ComfyProtocolError("Succeeded run has no output references to capture")

    @staticmethod
    def _verify_reference(manifest: ComfyRunManifest, reference: ComfyOutputReference) -> None:
        if reference.prompt_id != manifest.prompt_id:
            raise ComfyProtocolError("Output reference belongs to a different prompt")
        if reference.storage_type not in {"output", "temp"}:
            raise ComfyProtocolError("Output capture accepts only output/temp ComfyUI storage types")
        _safe_server_filename(reference.server_filename)
        _safe_server_subfolder(reference.server_subfolder)

    def _persist_generation_evidence(
        self,
        manifest: ComfyRunManifest,
        outputs: list[tuple[ComfyOutputSpec, ComfyOutputReference, bytes, str, int]],
        source_revision_ids: tuple[AssetRevisionId, ...],
    ) -> AssetRevisionId:
        evidence = {
            "schema_version": 1,
            "run_id": manifest.run_id,
            "run_manifest_digest_sha256": manifest.manifest_digest_sha256,
            "prompt_id_sha256": hashlib.sha256(manifest.prompt_id.encode("utf-8")).hexdigest(),
            "definition_id": manifest.definition_id,
            "definition_digest_sha256": manifest.definition_digest_sha256,
            "capability_identity_sha256": manifest.capability_identity_sha256,
            "comfyui_version": manifest.comfyui_version,
            "python_version": manifest.python_version,
            "model_resolution_digest_sha256": manifest.model_resolution_digest_sha256,
            "model_resolution_evidence": manifest.model_resolution_evidence(),
            "instance_digest_sha256": manifest.instance_digest_sha256,
            "prompt_digest_sha256": manifest.prompt_digest_sha256,
            "parameter_values": dict(manifest.parameter_values),
            "input_bindings": dict(manifest.input_bindings),
            "seed_values": dict(manifest.seed_values),
            "source_revision_ids": [str(item) for item in _unique_revision_ids(source_revision_ids)],
            "outputs": [
                {
                    "node_id": reference.node_id,
                    "output_index": reference.output_index,
                    "reference_sha256": canonical_sha256(reference.canonical()),
                    "content_sha256": digest,
                    "content_length": length,
                    "kind": spec.asset_kind.value,
                }
                for spec, reference, _data, digest, length in outputs
            ],
        }
        relative = f".kodepoia/comfyui/generation-evidence/{manifest.run_id}.json"
        path = self.assets.project.resolve(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = canonical_json_bytes(evidence) + b"\n"
        if path.exists():
            if path.is_symlink() or path.read_bytes() != data:
                raise ComfyProtocolError("Generation evidence file conflicts with immutable run evidence")
        else:
            temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
            try:
                with temporary.open("xb") as handle:
                    handle.write(data)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, path)
            finally:
                temporary.unlink(missing_ok=True)
        asset_id = AssetId.from_seed("r9.6-comfy-run-evidence", manifest.run_id)
        detail = self.assets.ingest(
            relative,
            kind=AssetKind.DOCUMENT,
            display_name=f"ComfyUI run evidence {manifest.run_id}",
            asset_id=asset_id,
            reuse_scope=ReuseScope.VAULT_LOCAL,
            preservation=PreservationPolicy.REFERENCED,
        )
        if detail.summary.revision_id is None:
            raise ComfyProtocolError("R8 AssetService did not return a generation evidence revision")
        return AssetRevisionId(detail.summary.revision_id)


def _safe_server_filename(value: str) -> str:
    if not value or "\\" in value:
        raise ComfyProtocolError("ComfyUI output filename must be a relative POSIX basename")
    posix = PurePosixPath(value)
    windows = PureWindowsPath(value)
    if posix.is_absolute() or windows.is_absolute() or bool(windows.drive) or len(posix.parts) != 1 or ".." in posix.parts:
        raise ComfyProtocolError("ComfyUI output filename escapes the accepted relative basename boundary")
    return value


def _safe_server_subfolder(value: str) -> str:
    if not value:
        return ""
    if "\\" in value:
        raise ComfyProtocolError("ComfyUI output subfolder must use relative POSIX segments")
    posix = PurePosixPath(value)
    windows = PureWindowsPath(value)
    if posix.is_absolute() or windows.is_absolute() or bool(windows.drive) or any(part in {"", ".", ".."} for part in posix.parts):
        raise ComfyProtocolError("ComfyUI output subfolder escapes the accepted relative boundary")
    return value


def _verify_media_bytes(kind: AssetKind, filename: str, data: bytes) -> None:
    if not data:
        raise ComfyProtocolError("ComfyUI output is empty")
    if kind not in _IMAGE_KINDS:
        return
    lower = filename.lower()
    detected: str | None = None
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        detected = ".png"
    elif data.startswith(b"\xff\xd8\xff"):
        detected = ".jpg"
    elif data.startswith((b"GIF87a", b"GIF89a")):
        detected = ".gif"
    elif len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        detected = ".webp"
    if detected is None:
        raise ComfyProtocolError("Image-like ComfyUI output has an unsupported or invalid image signature")
    accepted_suffixes = {detected}
    if detected == ".jpg":
        accepted_suffixes.add(".jpeg")
    if not any(lower.endswith(suffix) for suffix in accepted_suffixes):
        raise ComfyProtocolError("ComfyUI output extension does not match verified image bytes")


def _unique_revision_ids(values: tuple[AssetRevisionId, ...]) -> tuple[AssetRevisionId, ...]:
    result: list[AssetRevisionId] = []
    seen: set[str] = set()
    for item in values:
        key = str(item)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return tuple(result)


def _seal_capture(manifest: ComfyOutputCaptureManifest) -> ComfyOutputCaptureManifest:
    if not _SAFE_RUN_RE.fullmatch(manifest.run_id):
        raise ComfyProtocolError("Capture run_id is invalid")
    if not _HEX64_RE.fullmatch(manifest.run_manifest_digest_sha256):
        raise ComfyProtocolError("Capture run manifest digest is invalid")
    AssetRevisionId(manifest.evidence_revision_id)
    if not manifest.outputs or len(manifest.outputs) > _MAX_CAPTURE_OUTPUTS:
        raise ComfyProtocolError("Capture output count is invalid")
    for item in manifest.outputs:
        AssetId(item.asset_id)
        AssetRevisionId(item.revision_id)
        AssetKind(item.kind)
        if not _HEX64_RE.fullmatch(item.content_sha256) or item.content_length < 0:
            raise ComfyProtocolError("Capture output content evidence is invalid")
    normalized = replace(manifest, capture_digest_sha256="")
    return replace(normalized, capture_digest_sha256=canonical_sha256(normalized.canonical_without_digest()))


def _validate_capture_manifest(manifest: ComfyOutputCaptureManifest) -> None:
    sealed = _seal_capture(manifest)
    if sealed.capture_digest_sha256 != manifest.capture_digest_sha256:
        raise ComfyProtocolError("Comfy output capture digest does not match canonical evidence")


def _capture_manifest_from_payload(payload: dict[str, Any]) -> ComfyOutputCaptureManifest:
    expected = {
        "run_id",
        "run_manifest_digest_sha256",
        "evidence_revision_id",
        "state",
        "outputs",
        "capture_digest_sha256",
    }
    if set(payload) != expected or not isinstance(payload["outputs"], list):
        raise ComfyProtocolError("Comfy output capture payload fields are invalid")
    try:
        state = ComfyCaptureState(payload["state"])
        outputs = tuple(ComfyCapturedOutput(**item) for item in payload["outputs"] if isinstance(item, dict))
    except (TypeError, ValueError) as exc:
        raise ComfyProtocolError("Comfy output capture payload is invalid") from exc
    if len(outputs) != len(payload["outputs"]):
        raise ComfyProtocolError("Comfy output capture contains invalid output records")
    return ComfyOutputCaptureManifest(
        run_id=payload["run_id"],
        run_manifest_digest_sha256=payload["run_manifest_digest_sha256"],
        evidence_revision_id=payload["evidence_revision_id"],
        state=state,
        outputs=outputs,
        capture_digest_sha256=payload["capture_digest_sha256"],
    )
