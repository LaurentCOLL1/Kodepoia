from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from PIL import Image

from kodepoia.core.sandbox import SandboxResult
from kodepoia.kodecode.workspace import WorkspaceViolation
from kodepoia.kodegodot.api import GodotToolAPI
from kodepoia.kodegodot.executor import DEFAULT_GODOT_POLICIES
from kodepoia.kodegodot.runtime import GodotRuntime
from kodepoia.quality.tests import TestCaseStatus
from kodepoia.quality.visual import (
    KodeVisualQA,
    VisualMask,
    VisualPolicy,
    VisualReport,
    VisualStatus,
)


class FakeRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], Path | None, float]] = []

    def run(
        self,
        argv: list[str],
        *,
        cwd: Path | None = None,
        timeout: float = 60.0,
        env=None,
    ) -> SandboxResult:
        del env
        self.calls.append((list(argv), cwd, timeout))
        return SandboxResult(0, "", "")


def _project(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / ".kodepoia").mkdir(exist_ok=True)
    (root / "project.godot").write_text("config_version=5\n", encoding="utf-8")
    (root / "main.tscn").write_text(
        '[gd_scene format=3]\n[node name="Root" type="Node2D"]\n',
        encoding="utf-8",
    )


def _png(path: Path, *, size: tuple[int, int] = (10, 10), value=(0, 0, 0)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, value).save(path, format="PNG")


def _approval(root: Path, *, case_id: str = "ui-home", source: str = "baseline-source.png"):
    visual = KodeVisualQA(root)
    return visual.store.approve_baseline(
        case_id=case_id,
        source_path=source,
        approved_by="r6.4-fixture",
        reason="Deterministic fixture baseline",
        approved_at="2026-08-22T08:00:00Z",
    )


def test_visual_policy_and_masks_validate() -> None:
    policy = VisualPolicy(
        pixel_delta_threshold=2,
        warn_changed_ratio=0.1,
        fail_changed_ratio=0.2,
        warn_perceptual_ratio=0.05,
        fail_perceptual_ratio=0.15,
        masks=(VisualMask(1, 2, 3, 4),),
    )
    assert len(policy.sha256) == 64
    assert policy.masks[0].contains(1, 2)
    assert not policy.masks[0].contains(4, 2)
    with pytest.raises(ValueError, match="warn_changed_ratio"):
        VisualPolicy(warn_changed_ratio=0.3, fail_changed_ratio=0.2)
    with pytest.raises(ValueError, match="positive"):
        VisualMask(0, 0, 0, 1)


def test_exact_match_passes_persists_and_roundtrips(tmp_path: Path) -> None:
    _project(tmp_path)
    _png(tmp_path / "baseline-source.png", value=(10, 20, 30))
    _png(tmp_path / "current.png", value=(10, 20, 30))
    visual = KodeVisualQA(tmp_path)
    baseline = _approval(tmp_path)
    report = visual.compare(
        case_id="ui-home",
        baseline=baseline,
        current_path="current.png",
        generated_at="2026-08-22T08:01:00Z",
    )
    assert report.status is VisualStatus.PASS
    assert report.metrics.exact_file_match is True
    assert report.metrics.pixel_identical is True
    assert report.reasons == ("exact_file_match",)
    assert report.diff is not None
    assert (tmp_path / report.diff.path).is_file()
    latest = visual.store.load_latest("ui-home")
    assert latest.to_dict() == report.to_dict()
    assert VisualReport.from_dict(report.to_dict()) == report


def test_same_pixels_different_encoding_is_pass(tmp_path: Path) -> None:
    _project(tmp_path)
    image = Image.new("RGB", (32, 32), (15, 25, 35))
    image.save(tmp_path / "baseline-source.png", format="PNG", compress_level=0)
    image.save(tmp_path / "current.png", format="PNG", compress_level=9)
    baseline = _approval(tmp_path)
    report = KodeVisualQA(tmp_path).compare(
        case_id="ui-home",
        baseline=baseline,
        current_path="current.png",
    )
    assert report.status is VisualStatus.PASS
    assert report.metrics.exact_file_match is False
    assert report.metrics.pixel_identical is True
    assert report.reasons == ("pixel_identical_encoding_difference",)


def test_threshold_boundary_warn_then_fail(tmp_path: Path) -> None:
    _project(tmp_path)
    _png(tmp_path / "baseline-source.png")
    baseline = _approval(tmp_path)
    policy = VisualPolicy(
        warn_changed_ratio=0.01,
        fail_changed_ratio=0.02,
        warn_perceptual_ratio=1.0,
        fail_perceptual_ratio=1.0,
    )

    first = Image.new("RGB", (10, 10), (0, 0, 0))
    first.putpixel((0, 0), (255, 255, 255))
    first.save(tmp_path / "current.png", format="PNG")
    warn = KodeVisualQA(tmp_path).compare(
        case_id="ui-home",
        baseline=baseline,
        current_path="current.png",
        policy=policy,
        generated_at="2026-08-22T08:02:00Z",
    )
    assert warn.metrics.changed_ratio == 0.01
    assert warn.status is VisualStatus.WARN
    assert "changed_ratio_warn" in warn.reasons

    second = first.copy()
    second.putpixel((1, 0), (255, 255, 255))
    second.save(tmp_path / "current.png", format="PNG")
    fail = KodeVisualQA(tmp_path).compare(
        case_id="ui-home",
        baseline=baseline,
        current_path="current.png",
        policy=policy,
        generated_at="2026-08-22T08:03:00Z",
    )
    assert fail.metrics.changed_ratio == 0.02
    assert fail.status is VisualStatus.FAIL
    assert "changed_ratio_fail" in fail.reasons


def test_policy_mask_excludes_declared_pixels_and_is_hash_bound(tmp_path: Path) -> None:
    _project(tmp_path)
    _png(tmp_path / "baseline-source.png")
    baseline = _approval(tmp_path)
    current = Image.new("RGB", (10, 10), (0, 0, 0))
    current.putpixel((0, 0), (255, 255, 255))
    current.save(tmp_path / "current.png", format="PNG")
    unmasked = VisualPolicy(warn_changed_ratio=0.01, fail_changed_ratio=0.02)
    masked = VisualPolicy(
        warn_changed_ratio=0.01,
        fail_changed_ratio=0.02,
        masks=(VisualMask(0, 0, 1, 1),),
    )
    assert masked.sha256 != unmasked.sha256
    report = KodeVisualQA(tmp_path).compare(
        case_id="ui-home",
        baseline=baseline,
        current_path="current.png",
        policy=masked,
    )
    assert report.status is VisualStatus.PASS
    assert report.metrics.changed_pixels == 0
    assert report.metrics.masked_pixels == 1
    assert report.policy_sha256 == masked.sha256


def test_resolution_mode_and_format_mismatches_fail_explicitly(tmp_path: Path) -> None:
    _project(tmp_path)
    _png(tmp_path / "baseline-source.png")
    baseline = _approval(tmp_path)
    visual = KodeVisualQA(tmp_path)

    _png(tmp_path / "current.png", size=(11, 10))
    resolution = visual.compare(
        case_id="ui-home", baseline=baseline, current_path="current.png"
    )
    assert resolution.status is VisualStatus.FAIL
    assert "resolution_mismatch" in resolution.reasons
    assert resolution.metrics.comparable is False

    Image.new("RGBA", (10, 10), (0, 0, 0, 255)).save(
        tmp_path / "current.png", format="PNG"
    )
    mode = visual.compare(case_id="ui-home", baseline=baseline, current_path="current.png")
    assert mode.status is VisualStatus.FAIL
    assert "mode_mismatch" in mode.reasons

    Image.new("RGB", (10, 10), (0, 0, 0)).save(
        tmp_path / "current.jpg", format="JPEG", quality=100
    )
    image_format = visual.compare(
        case_id="ui-home", baseline=baseline, current_path="current.jpg"
    )
    assert image_format.status is VisualStatus.FAIL
    assert "format_mismatch" in image_format.reasons


def test_missing_evidence_is_unknown_never_pass(tmp_path: Path) -> None:
    _project(tmp_path)
    _png(tmp_path / "baseline-source.png")
    _png(tmp_path / "current.png")
    visual = KodeVisualQA(tmp_path)
    no_baseline = visual.compare(
        case_id="ui-home", baseline=None, current_path="current.png"
    )
    assert no_baseline.status is VisualStatus.UNKNOWN
    baseline = _approval(tmp_path)
    no_current = visual.compare(
        case_id="ui-home", baseline=baseline, current_path="missing.png"
    )
    assert no_current.status is VisualStatus.UNKNOWN
    test_case = visual.to_test_case(no_current)
    assert test_case.status is TestCaseStatus.ERROR


def test_report_tampering_is_rejected(tmp_path: Path) -> None:
    _project(tmp_path)
    _png(tmp_path / "baseline-source.png")
    _png(tmp_path / "current.png")
    baseline = _approval(tmp_path)
    report = KodeVisualQA(tmp_path).compare(
        case_id="ui-home", baseline=baseline, current_path="current.png"
    )
    payload = report.to_dict()
    payload["metrics"]["changed_pixels"] = 1
    with pytest.raises(ValueError):
        VisualReport.from_dict(payload)

    payload = report.to_dict()
    payload["policy"]["pixel_delta_threshold"] = 7
    with pytest.raises(ValueError, match="policy hash"):
        VisualReport.from_dict(payload)

    payload = report.to_dict()
    payload["evidence_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="evidence hash"):
        VisualReport.from_dict(payload)


def test_baseline_artifact_mutation_is_detected(tmp_path: Path) -> None:
    _project(tmp_path)
    _png(tmp_path / "baseline-source.png")
    baseline = _approval(tmp_path)
    artifact = tmp_path / baseline.image.path
    artifact.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="modified after approval"):
        KodeVisualQA(tmp_path).store.load_baseline(
            case_id="ui-home", sha256=baseline.image.sha256
        )


def test_visual_store_rejects_path_and_symlink_escape(tmp_path: Path) -> None:
    project = tmp_path / "project"
    outside = tmp_path / "outside"
    _project(project)
    outside.mkdir()
    _png(outside / "outside.png")
    visual = KodeVisualQA(project)
    with pytest.raises(WorkspaceViolation):
        visual.store.inspect_image("../outside/outside.png")

    link = project / "escape"
    try:
        os.symlink(outside, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation is unavailable on this runner")
    with pytest.raises(WorkspaceViolation):
        visual.store.inspect_image("escape/outside.png")


def test_r6_3_hook_uses_stable_visual_case_id(tmp_path: Path) -> None:
    _project(tmp_path)
    _png(tmp_path / "baseline-source.png")
    _png(tmp_path / "current.png")
    baseline = _approval(tmp_path)
    report = KodeVisualQA(tmp_path).compare(
        case_id="ui-home", baseline=baseline, current_path="current.png"
    )
    result = KodeVisualQA.to_test_case(report)
    assert result.id == "visual:ui-home"
    assert result.status is TestCaseStatus.PASS
    assert result.details["evidence_sha256"] == report.evidence_sha256


def test_visual_report_json_schema_accepts_serialized_report(tmp_path: Path) -> None:
    _project(tmp_path)
    _png(tmp_path / "baseline-source.png")
    _png(tmp_path / "current.png")
    baseline = _approval(tmp_path)
    report = KodeVisualQA(tmp_path).compare(
        case_id="ui-home", baseline=baseline, current_path="current.png"
    )
    schema_path = Path(__file__).parents[1] / "schemas" / "visual-report-v1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER).validate(
        report.to_dict()
    )


def test_godot_runtime_builds_confined_real_render_png_command(tmp_path: Path) -> None:
    _project(tmp_path)
    runner = FakeRunner()
    runtime = GodotRuntime(tmp_path, executable="godot", runner=runner)
    result = runtime.capture_png_sequence(
        scene="main.tscn", output_name="visual.png", frames=3, fps=30, timeout=120
    )
    assert result.ok
    assert runner.calls[-1][0] == [
        "godot",
        "--path",
        ".",
        "--write-movie",
        ".kodepoia/visual_tests/runs/visual.png",
        "--fixed-fps",
        "30",
        "--quit-after",
        "3",
        "--scene",
        "res://main.tscn",
    ]
    assert "--headless" not in runner.calls[-1][0]
    with pytest.raises(ValueError, match=".png"):
        runtime.capture_png_sequence(scene="main.tscn", output_name="visual.avi")
    with pytest.raises(ValueError, match="simple file name"):
        runtime.capture_png_sequence(scene="main.tscn", output_name="../visual.png")


def test_godot_visual_tool_is_structured_and_explicitly_governed(tmp_path: Path) -> None:
    _project(tmp_path)
    api = GodotToolAPI(tmp_path, runtime=GodotRuntime(tmp_path, runner=FakeRunner()))
    catalog = {item["function"]["name"]: item for item in api.catalog()}
    tool = catalog["kodegodot_capture_png_sequence"]
    parameters = tool["function"]["parameters"]
    assert parameters["additionalProperties"] is False
    assert set(parameters["properties"]) == {
        "scene",
        "output_name",
        "frames",
        "fps",
        "timeout",
    }
    for forbidden in ("argv", "command", "cwd", "host", "output_path", "executable"):
        assert forbidden not in parameters["properties"]
    policy = DEFAULT_GODOT_POLICIES["kodegodot_capture_png_sequence"]
    assert policy.extra_write_root == ".kodepoia/visual_tests/runs"
