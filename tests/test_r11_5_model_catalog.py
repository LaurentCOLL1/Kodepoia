from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from kodepoia.models import KodeModelRegistry


def _write_catalog(root: Path, *, payload: bytes = b"model-bytes") -> tuple[KodeModelRegistry, Path]:
    model_dir = root / "models" / "tts" / "piper" / "fr-FR" / "fixture"
    registry_dir = root / "models" / "registry"
    model_dir.mkdir(parents=True)
    registry_dir.mkdir(parents=True)
    model_path = model_dir / "fixture.onnx"
    config_path = model_dir / "fixture.onnx.json"
    model_path.write_bytes(payload)
    config_path.write_text('{"audio":{"sample_rate":22050}}', encoding="utf-8")
    model_sha = hashlib.sha256(model_path.read_bytes()).hexdigest()
    config_sha = hashlib.sha256(config_path.read_bytes()).hexdigest()
    (model_dir / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "model_id": "tts.piper.fr-FR.fixture",
                "purpose": "tts",
                "backend": "piper-compatible",
                "license_id": "cc-by-4.0",
                "provenance_id": "fixture.voice",
                "allowed_uses": ["internal"],
                "locale": "fr-FR",
                "role": "voice",
                "source": "fixture",
                "files": [
                    {"role": "model", "path": "fixture.onnx", "sha256": model_sha, "max_bytes": 1024},
                    {"role": "config", "path": "fixture.onnx.json", "sha256": config_sha, "max_bytes": 1024},
                ],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (registry_dir / "models.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "entries": [
                    {
                        "model_id": "tts.piper.fr-FR.fixture",
                        "manifest": "tts/piper/fr-FR/fixture/manifest.json",
                    }
                ],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return KodeModelRegistry(root), model_path


def test_repository_catalog_manifest_is_registered_without_requiring_payload_in_ci() -> None:
    registry = KodeModelRegistry(Path.cwd())
    model_id = "tts.piper.fr-FR.siwis-medium"
    assert model_id in registry.model_ids()
    manifest = registry.manifest(model_id)
    assert manifest.backend == "piper-compatible"
    assert manifest.locale == "fr-FR"
    assert manifest.license_id == "cc-by-4.0"
    assert manifest.file("model").sha256 == "641d1ab097da2b81128c076810edb052b385decc8be3381814802a64a73baf99"
    assert manifest.file("config").sha256 == "39479916c2db192b5ac9764daddd0c744d83e023ad890c6976c0633ae4df8959"


def test_catalog_resolves_only_exact_sha_bound_local_payload(tmp_path: Path) -> None:
    registry, model_path = _write_catalog(tmp_path)
    assert registry.resolve_file("tts.piper.fr-FR.fixture", "model") == model_path.resolve()
    model_path.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        registry.resolve_file("tts.piper.fr-FR.fixture", "model")


def test_catalog_missing_payload_is_explicit_not_downloaded(tmp_path: Path) -> None:
    registry, model_path = _write_catalog(tmp_path)
    model_path.unlink()
    with pytest.raises(FileNotFoundError):
        registry.resolve_file("tts.piper.fr-FR.fixture", "model")


def test_catalog_rejects_manifest_path_escape(tmp_path: Path) -> None:
    registry_dir = tmp_path / "models" / "registry"
    registry_dir.mkdir(parents=True)
    (registry_dir / "models.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "entries": [
                    {"model_id": "tts.piper.escape", "manifest": "../outside.json"}
                ],
            }
        ),
        encoding="utf-8",
    )
    registry = KodeModelRegistry(tmp_path)
    with pytest.raises(ValueError, match="models root"):
        registry.model_ids()
