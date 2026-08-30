from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.tuning.export import (
    EXPORT_SCHEMA,
    ExportBinding,
    ExportRequest,
    MergeDisposition,
    ModelExportError,
    export_candidate,
)


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _tree_digest(path: Path) -> str:
    rows = []
    files = sorted(
        (item for item in path.rglob("*") if item.is_file()),
        key=lambda item: item.relative_to(path).as_posix(),
    )
    for item in files:
        rows.append(
            {
                "path": item.relative_to(path).as_posix(),
                "sha256": hashlib.sha256(item.read_bytes()).hexdigest(),
                "size_bytes": item.stat().st_size,
            }
        )
    return hashlib.sha256(_canonical(rows).encode()).hexdigest()


def _fixture(tmp_path: Path) -> tuple[Path, ExportBinding, dict[str, object]]:
    adapter = tmp_path / "source-adapter"
    adapter.mkdir(parents=True)
    (adapter / "adapter_config.json").write_text(
        json.dumps(
            {
                "base_model_name_or_path": "fixture/base",
                "revision": "abc123",
                "peft_type": "LORA",
                "task_type": "CAUSAL_LM",
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (adapter / "adapter_model.safetensors").write_bytes(b"tiny-safe-fixture")
    digest = _tree_digest(adapter)
    binding = ExportBinding(
        candidate_id="candidate-1",
        base_model_ref="fixture/base",
        base_model_revision="abc123",
        base_model_digest="1" * 64,
        adapter_digest=digest,
        dataset_digest="2" * 64,
        training_plan_digest="3" * 64,
        evaluation_digest="4" * 64,
        base_license="apache-2.0",
        adapter_license="apache-2.0",
    )
    evaluation = {
        "disposition": "promote_to_export",
        "can_export": True,
        "binding": {
            "candidate_id": binding.candidate_id,
            "base_model_ref": binding.base_model_ref,
            "base_model_digest": binding.base_model_digest,
            "adapter_digest": binding.adapter_digest,
            "dataset_digest": binding.dataset_digest,
            "training_plan_digest": binding.training_plan_digest,
        },
    }
    return adapter, binding, evaluation


def _request(binding: ExportBinding, *, merge: bool = False) -> ExportRequest:
    return ExportRequest(
        binding=binding,
        intended_use="Local fixture inference for Kodepoia specialization.",
        limitations="Fixture-only acceptance; production scope remains governed by the registry.",
        eval_summary="R15.10 candidate disposition is PROMOTE_TO_EXPORT with no critical regressions.",
        merge_requested=merge,
    )


def test_adapter_only_export_is_deterministic_and_source_immutable(tmp_path: Path) -> None:
    adapter, binding, evaluation = _fixture(tmp_path)
    source_before = {p.name: p.read_bytes() for p in adapter.iterdir()}
    smoke = []

    report = export_candidate(
        adapter_dir=adapter,
        output_root=tmp_path / "exports-a",
        request=_request(binding),
        evaluation=evaluation,
        load_smoke=lambda path, bound, merge: smoke.append((path, bound, merge)) or True,
    )
    second = export_candidate(
        adapter_dir=adapter,
        output_root=tmp_path / "exports-b",
        request=_request(binding),
        evaluation=evaluation,
        load_smoke=lambda *_: True,
    )

    assert report.manifest["schema"] == EXPORT_SCHEMA
    assert report.manifest["merge"]["disposition"] == MergeDisposition.NOT_REQUESTED.value
    assert report.manifest_digest == second.manifest_digest
    assert source_before == {p.name: p.read_bytes() for p in adapter.iterdir()}
    assert report.manifest["source_overwritten"] is False
    assert smoke and smoke[0][1] == binding
    assert (report.output_dir / "adapter" / "adapter_model.safetensors").is_file()


def test_base_mismatch_and_non_promoted_candidate_fail_closed(tmp_path: Path) -> None:
    adapter, binding, evaluation = _fixture(tmp_path)
    config = json.loads((adapter / "adapter_config.json").read_text(encoding="utf-8"))
    config["base_model_name_or_path"] = "wrong/base"
    (adapter / "adapter_config.json").write_text(json.dumps(config), encoding="utf-8")
    mismatch_binding = ExportBinding(
        candidate_id=binding.candidate_id,
        base_model_ref=binding.base_model_ref,
        base_model_revision=binding.base_model_revision,
        base_model_digest=binding.base_model_digest,
        adapter_digest=_tree_digest(adapter),
        dataset_digest=binding.dataset_digest,
        training_plan_digest=binding.training_plan_digest,
        evaluation_digest=binding.evaluation_digest,
        base_license=binding.base_license,
        adapter_license=binding.adapter_license,
    )
    evaluation["binding"]["adapter_digest"] = mismatch_binding.adapter_digest
    with pytest.raises(ModelExportError, match="base_model_name_or_path"):
        export_candidate(
            adapter_dir=adapter,
            output_root=tmp_path / "mismatch",
            request=_request(mismatch_binding),
            evaluation=evaluation,
        )

    adapter, binding, evaluation = _fixture(tmp_path / "other")
    evaluation["disposition"] = "reject"
    evaluation["can_export"] = False
    with pytest.raises(ModelExportError, match="PROMOTE_TO_EXPORT"):
        export_candidate(
            adapter_dir=adapter,
            output_root=tmp_path / "rejected",
            request=_request(binding),
            evaluation=evaluation,
        )


def test_merge_support_is_capability_injected_and_unsupported_is_adapter_only(tmp_path: Path) -> None:
    adapter, binding, evaluation = _fixture(tmp_path)

    unsupported = export_candidate(
        adapter_dir=adapter,
        output_root=tmp_path / "unsupported",
        request=_request(binding, merge=True),
        evaluation=evaluation,
        merger=lambda *_: False,
        load_smoke=lambda path, _, disposition: disposition is MergeDisposition.UNSUPPORTED and path.exists(),
    )
    assert unsupported.manifest["merge"] == {"disposition": "unsupported", "files": None}
    assert not (unsupported.output_dir / "merged").exists()

    def merger(_: Path, target: Path, __: ExportBinding) -> bool:
        (target / "config.json").write_text('{"model_type":"fixture"}', encoding="utf-8")
        (target / "model.safetensors").write_bytes(b"merged-fixture")
        return True

    merged = export_candidate(
        adapter_dir=adapter,
        output_root=tmp_path / "merged-export",
        request=_request(binding, merge=True),
        evaluation=evaluation,
        merger=merger,
        load_smoke=lambda path, _, disposition: (
            disposition is MergeDisposition.MERGED and (path / "merged" / "model.safetensors").is_file()
        ),
    )
    assert merged.manifest["merge"]["disposition"] == "merged"
    assert merged.manifest["merge"]["files"]


def test_model_card_has_lineage_without_source_content_or_secret_like_metadata(tmp_path: Path) -> None:
    adapter, binding, evaluation = _fixture(tmp_path)
    report = export_candidate(
        adapter_dir=adapter,
        output_root=tmp_path / "export",
        request=_request(binding),
        evaluation=evaluation,
        load_smoke=lambda *_: True,
    )
    card = (report.output_dir / "README.md").read_text(encoding="utf-8")
    assert binding.base_model_ref in card
    assert binding.dataset_digest in card
    assert str(adapter) not in card
    assert "tiny-safe-fixture" not in card
    assert "No raw training examples" in card

    with pytest.raises(ModelExportError, match="secret-like"):
        ExportRequest(
            binding=binding,
            intended_use="password=hunter2",
            limitations="none",
            eval_summary="accepted",
        )


def test_existing_destination_and_failed_smoke_are_rejected(tmp_path: Path) -> None:
    adapter, binding, evaluation = _fixture(tmp_path)
    root = tmp_path / "exports"
    (root / binding.candidate_id).mkdir(parents=True)
    with pytest.raises(ModelExportError, match="already exists"):
        export_candidate(
            adapter_dir=adapter,
            output_root=root,
            request=_request(binding),
            evaluation=evaluation,
        )

    with pytest.raises(ModelExportError, match="smoke failed"):
        export_candidate(
            adapter_dir=adapter,
            output_root=tmp_path / "smoke",
            request=_request(binding),
            evaluation=evaluation,
            load_smoke=lambda *_: False,
        )


def test_saved_manifest_validates_r15_11_schema(tmp_path: Path) -> None:
    adapter, binding, evaluation = _fixture(tmp_path)
    report = export_candidate(
        adapter_dir=adapter,
        output_root=tmp_path / "export",
        request=_request(binding),
        evaluation=evaluation,
        load_smoke=lambda *_: True,
    )
    schema_path = Path(__file__).parents[1] / "schemas" / "r15-11-model-export.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(report.manifest)
