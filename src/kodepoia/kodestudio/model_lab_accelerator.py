from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

ACCELERATOR_PROJECTION_SCHEMA = "kodepoia.v2.4.5.model-lab-accelerator"
_TOPOLOGY_SCHEMA = "kodepoia.v2.4.1.accelerator-topology"
_STRATEGY_SCHEMA = "kodepoia.v2.4.2.execution-strategy-plan"
_LIVE_SCHEMA = "kodepoia.v2.4.5.kaggle-live-qualification-report"
_MAX_JSON_BYTES = 4 * 1024 * 1024


def _read_json(path: Path) -> dict[str, object] | None:
    try:
        if not path.is_file() or path.stat().st_size > _MAX_JSON_BYTES:
            return None
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _records(root: Path) -> list[tuple[Path, dict[str, object]]]:
    tuning = root / ".kodepoia" / "tuning"
    if not tuning.is_dir():
        return []
    records: list[tuple[Path, dict[str, object]]] = []
    for path in sorted(tuning.rglob("*.json"), key=lambda item: item.as_posix()):
        payload = _read_json(path)
        if payload is not None:
            records.append((path, payload))
    return records


def _digest(value: object) -> str:
    return "" if value is None else str(value)


def _device_rows(topology: Mapping[str, object] | None) -> list[dict[str, object]]:
    if not isinstance(topology, Mapping):
        return []
    observed = topology.get("observed")
    if not isinstance(observed, Mapping):
        return []
    raw_devices = observed.get("devices")
    if not isinstance(raw_devices, list):
        return []
    rows: list[dict[str, object]] = []
    for item in raw_devices:
        if not isinstance(item, Mapping):
            continue
        rows.append(
            {
                "ordinal": item.get("index"),
                "name": str(item.get("name", "")),
                "backend": str(item.get("backend_type", "")),
                "vram_free_bytes": item.get("vram_free_bytes"),
                "vram_total_bytes": item.get("vram_total_bytes"),
            }
        )
    return rows


def _strategy_row(payload: Mapping[str, object]) -> dict[str, object]:
    budgets = payload.get("device_budgets")
    budget_rows = budgets if isinstance(budgets, list) else []
    return {
        "strategy": str(payload.get("strategy", "")),
        "strategy_plan_digest": _digest(payload.get("strategy_plan_digest")),
        "training_plan_digest": _digest(payload.get("training_plan_digest")),
        "topology_report_digest": _digest(payload.get("topology_report_digest")),
        "topology_digest": _digest(payload.get("topology_digest")),
        "world_size": payload.get("world_size"),
        "device_ordinals": list(payload.get("device_ordinals", []))
        if isinstance(payload.get("device_ordinals"), list)
        else [],
        "device_budgets": budget_rows,
        "per_device_batch_size": payload.get("per_device_batch_size"),
        "gradient_accumulation_steps": payload.get("gradient_accumulation_steps"),
        "effective_global_batch_size": payload.get("effective_global_batch_size"),
    }


def accelerator_projection(root: Path) -> dict[str, object]:
    root = Path(root).resolve(strict=False)
    topology: dict[str, object] | None = None
    strategies: list[dict[str, object]] = []
    live: dict[str, object] | None = None
    lineage: dict[str, str] = {}

    for _path, payload in _records(root):
        schema = str(payload.get("schema", ""))
        if schema == _TOPOLOGY_SCHEMA:
            topology = payload
        elif schema == _STRATEGY_SCHEMA:
            strategies.append(_strategy_row(payload))
        elif schema == _LIVE_SCHEMA:
            live = payload

        for key in (
            "training_plan_digest",
            "topology_report_digest",
            "topology_digest",
            "strategy_plan_digest",
            "benchmark_report_digest",
            "execution_plan_digest",
            "recovery_plan_digest",
            "checkpoint_manifest_digest",
        ):
            value = payload.get(key)
            if isinstance(value, str) and value:
                lineage[key] = value

    strategies.sort(key=lambda item: (str(item["strategy"]), str(item["strategy_plan_digest"])))
    provider_request = topology.get("provider_request") if isinstance(topology, dict) else None
    provider = dict(provider_request) if isinstance(provider_request, Mapping) else None
    devices = _device_rows(topology)
    topology_state = "missing"
    if isinstance(topology, dict):
        topology_state = str(topology.get("disposition", "unknown"))

    live_state = "missing"
    production_qualified = False
    live_blockers: list[str] = []
    if isinstance(live, dict):
        live_state = str(live.get("status", live.get("disposition", "unknown")))
        production_qualified = live.get("production_qualified") is True
        blockers = live.get("blockers")
        if isinstance(blockers, list):
            live_blockers = [str(item) for item in blockers]

    return {
        "schema": ACCELERATOR_PROJECTION_SCHEMA,
        "provider_request": provider,
        "topology_state": topology_state,
        "topology_digest": (
            None if topology is None else topology.get("topology_digest")
        ),
        "devices": devices,
        "strategies": strategies,
        "lineage": dict(sorted(lineage.items())),
        "live_qualification": {
            "state": live_state,
            "production_qualified": production_qualified,
            "blockers": live_blockers,
            "report_digest": None if live is None else live.get("report_digest"),
            "source_sha": None if live is None else live.get("source_sha"),
        },
        "pooled_vram_bytes": None,
    }


def provider_runtime_projection(
    accelerator: Mapping[str, object],
    kaggle: Mapping[str, object],
) -> dict[str, object]:
    doctor = kaggle.get("doctor")
    doctor_map = doctor if isinstance(doctor, Mapping) else {}
    quota = kaggle.get("quota")
    quota_map = quota if isinstance(quota, Mapping) else {}
    entries = quota_map.get("entries")
    quota_entries = entries if isinstance(entries, list) else []
    gpu_quota = next(
        (
            dict(item)
            for item in quota_entries
            if isinstance(item, Mapping) and str(item.get("resource", "")).upper() == "GPU"
        ),
        None,
    )
    return {
        **dict(accelerator),
        "provider_state": str(kaggle.get("state", "not_checked")),
        "authenticated": doctor_map.get("authenticated"),
        "cli_available": doctor_map.get("cli_available", doctor_map.get("installed")),
        "provider_version": doctor_map.get("version"),
        "provider_detail": str(kaggle.get("detail", "")),
        "gpu_quota": gpu_quota,
    }


__all__ = [
    "ACCELERATOR_PROJECTION_SCHEMA",
    "accelerator_projection",
    "provider_runtime_projection",
]
