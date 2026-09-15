from __future__ import annotations

import json

import pytest

from kodepoia.kodestudio.kaggle_quota import (
    KaggleQuotaError,
    KaggleQuotaService,
    format_quota_entry,
    parse_kaggle_quota_json,
)
from kodepoia.tuning.kaggle_remote import CommandResult


class FakeRunner:
    def __init__(self, results: list[CommandResult]) -> None:
        self.results = list(results)
        self.calls: list[list[str]] = []

    def run(self, argv: list[str], *, cwd=None, timeout: float = 120.0) -> CommandResult:
        del cwd, timeout
        self.calls.append(argv)
        return self.results.pop(0)


def test_parse_official_gpu_tpu_quota_shape() -> None:
    entries = parse_kaggle_quota_json(
        json.dumps(
            [
                {
                    "resource": "GPU",
                    "used": "4.50h",
                    "remaining": "25.50h",
                    "total": "30.00h",
                    "refreshAt": "2026-09-21T00:00:00Z",
                },
                {
                    "resource": "TPU",
                    "used": 2,
                    "remaining": 18,
                    "total": 20,
                    "refreshAt": None,
                },
            ]
        )
    )
    assert len(entries) == 2
    assert entries[0].resource == "GPU"
    assert entries[0].remaining_hours == 25.5
    assert entries[0].total_hours == 30.0
    assert entries[1].resource == "TPU"
    assert entries[1].used_hours == 2.0


def test_parse_clamps_negative_remaining_and_ignores_unknown_resource() -> None:
    entries = parse_kaggle_quota_json(
        [
            {"resource": "GPU", "used": 31, "remaining": -1, "total": 30},
            {"resource": "OTHER", "used": 1, "remaining": 2, "total": 3},
        ]
    )
    assert len(entries) == 1
    assert entries[0].remaining_hours == 0.0


def test_malformed_quota_is_rejected() -> None:
    with pytest.raises(KaggleQuotaError, match="valid JSON"):
        parse_kaggle_quota_json("not-json")
    with pytest.raises(KaggleQuotaError, match="GPU.used"):
        parse_kaggle_quota_json([{"resource": "GPU", "used": "bad", "remaining": 1, "total": 2}])


def test_service_uses_official_quota_json_command() -> None:
    runner = FakeRunner(
        [
            CommandResult(0, "Kaggle API 2.2.3\n", ""),
            CommandResult(
                0,
                json.dumps(
                    [
                        {
                            "resource": "GPU",
                            "used": "5h",
                            "remaining": "25h",
                            "total": "30h",
                            "refreshAt": "2026-09-21T00:00:00Z",
                        }
                    ]
                ),
                "",
            ),
        ]
    )
    service = KaggleQuotaService(runner=runner, kaggle_executable="kaggle-test")
    snapshot = service.snapshot()
    assert snapshot.version == "Kaggle API 2.2.3"
    assert snapshot.for_resource("gpu").remaining_hours == 25.0  # type: ignore[union-attr]
    assert runner.calls == [
        ["kaggle-test", "--version"],
        ["kaggle-test", "quota", "--format", "json"],
    ]


def test_service_surfaces_cli_or_auth_failure_without_credentials() -> None:
    runner = FakeRunner(
        [
            CommandResult(0, "Kaggle API 2.2.3\n", ""),
            CommandResult(1, "", "401 authentication required"),
        ]
    )
    service = KaggleQuotaService(runner=runner, kaggle_executable="kaggle-test")
    with pytest.raises(KaggleQuotaError, match="2.2.1\+ and authentication"):
        service.snapshot()


def test_quota_formatting_is_bilingual() -> None:
    entry = parse_kaggle_quota_json(
        [{"resource": "GPU", "used": 5, "remaining": 25, "total": 30, "refreshAt": None}]
    )[0]
    assert "25.00 h restantes" in format_quota_entry(entry, locale="fr")
    assert "25.00 h remaining" in format_quota_entry(entry, locale="en")
