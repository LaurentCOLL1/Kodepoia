import json
from pathlib import Path

from jsonschema import validate


def test_tracked_model_catalog_index_schema() -> None:
    index = json.loads(Path("models/registry/models.json").read_text(encoding="utf-8"))
    schema = json.loads(Path("schemas/r11/model-catalog-index.schema.json").read_text(encoding="utf-8"))
    validate(instance=index, schema=schema)


def test_tracked_siwis_manifest_schema() -> None:
    manifest = json.loads(
        Path("models/tts/piper/fr-FR/siwis-medium/manifest.json").read_text(encoding="utf-8")
    )
    schema = json.loads(Path("schemas/r11/model-manifest.schema.json").read_text(encoding="utf-8"))
    validate(instance=manifest, schema=schema)
