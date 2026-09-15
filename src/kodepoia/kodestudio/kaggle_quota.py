from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from kodepoia.tuning.kaggle_remote import CommandRunner, SubprocessCommandRunner


class KaggleQuotaError(RuntimeError):
    """Raised when Kaggle accelerator quota cannot be queried safely."""


@dataclass(frozen=True, slots=True)
class KaggleQuotaEntry:
    resource: str
    used_hours: float
    remaining_hours: float
    total_hours: float
    refresh_at: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "refresh_at": self.refresh_at,
            "remaining_hours": self.remaining_hours,
            "resource": self.resource,
            "total_hours": self.total_hours,
            "used_hours": self.used_hours,
        }


@dataclass(frozen=True, slots=True)
class KaggleQuotaSnapshot:
    version: str | None
    entries: tuple[KaggleQuotaEntry, ...]

    def for_resource(self, resource: str) -> KaggleQuotaEntry | None:
        target = str(resource).strip().upper()
        return next((item for item in self.entries if item.resource == target), None)

    def to_dict(self) -> dict[str, object]:
        return {
            "entries": [item.to_dict() for item in self.entries],
            "version": self.version,
        }


def _hours(value: object, *, field: str) -> float:
    if isinstance(value, bool):
        raise KaggleQuotaError(f"Kaggle quota field {field} is not numeric")
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().lower()
    if text.endswith("h"):
        text = text[:-1].strip()
    try:
        return float(text)
    except (TypeError, ValueError) as exc:
        raise KaggleQuotaError(f"Kaggle quota field {field} is not numeric: {value!r}") from exc


def parse_kaggle_quota_json(payload: str | bytes | object) -> tuple[KaggleQuotaEntry, ...]:
    """Parse `kaggle quota --format json` without trusting display strings."""

    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")
    if isinstance(payload, str):
        try:
            raw = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise KaggleQuotaError("Kaggle quota did not return valid JSON") from exc
    else:
        raw = payload

    if isinstance(raw, dict):
        candidate = raw.get("rows") or raw.get("quota") or raw.get("quotas")
        rows = candidate if isinstance(candidate, list) else [raw]
    elif isinstance(raw, list):
        rows = raw
    else:
        raise KaggleQuotaError("Kaggle quota JSON must contain a list of quota rows")

    entries: list[KaggleQuotaEntry] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise KaggleQuotaError(f"Kaggle quota row {index} is not an object")
        resource = str(row.get("resource", "")).strip().upper()
        if resource not in {"GPU", "TPU"}:
            # The official command currently reports GPU and TPU only. Ignore
            # future unrelated resources rather than mislabelling them in KodeStudio.
            continue
        used = _hours(row.get("used"), field=f"{resource}.used")
        remaining = max(0.0, _hours(row.get("remaining"), field=f"{resource}.remaining"))
        total = _hours(row.get("total"), field=f"{resource}.total")
        refresh_raw = row.get("refreshAt")
        refresh_at = None if refresh_raw in {None, ""} else str(refresh_raw).strip()
        entries.append(
            KaggleQuotaEntry(
                resource=resource,
                used_hours=used,
                remaining_hours=remaining,
                total_hours=total,
                refresh_at=refresh_at,
            )
        )
    return tuple(entries)


class KaggleQuotaService:
    """Read-only Kaggle accelerator quota facade for KodeStudio.

    Authentication remains entirely owned by the official Kaggle CLI. Kodepoia
    never reads, stores, or serializes Kaggle credentials in this service.
    """

    def __init__(
        self,
        *,
        runner: CommandRunner | None = None,
        kaggle_executable: str | None = None,
    ) -> None:
        self.runner = runner or SubprocessCommandRunner()
        self.kaggle_executable = kaggle_executable or shutil.which("kaggle") or "kaggle"

    def snapshot(self) -> KaggleQuotaSnapshot:
        executable = (
            shutil.which(self.kaggle_executable)
            if self.kaggle_executable == "kaggle"
            else self.kaggle_executable
        )
        if not executable:
            raise KaggleQuotaError("Kaggle CLI is not installed or not on PATH")

        version_result = self.runner.run([executable, "--version"], timeout=30.0)
        version = version_result.stdout.strip() or version_result.stderr.strip() or None
        if version_result.returncode != 0:
            raise KaggleQuotaError("Kaggle CLI version check failed")

        result = self.runner.run(
            [executable, "quota", "--format", "json"],
            timeout=60.0,
        )
        if result.returncode != 0:
            reason = result.stderr.strip() or result.stdout.strip()
            suffix = f": {reason[:512]}" if reason else ""
            raise KaggleQuotaError(
                "Kaggle quota query failed. Kaggle CLI 2.2.1+ and authentication are required"
                + suffix
            )
        return KaggleQuotaSnapshot(
            version=version,
            entries=parse_kaggle_quota_json(result.stdout),
        )


def format_quota_entry(entry: KaggleQuotaEntry | None, *, locale: str = "fr") -> str:
    french = locale.lower().startswith("fr")
    if entry is None:
        return "non communiqué" if french else "not reported"
    refresh = ""
    if entry.refresh_at:
        refresh = (
            f" — renouvellement : {entry.refresh_at}"
            if french
            else f" — refresh: {entry.refresh_at}"
        )
    if french:
        return (
            f"{entry.remaining_hours:.2f} h restantes / {entry.total_hours:.2f} h "
            f"({entry.used_hours:.2f} h utilisées){refresh}"
        )
    return (
        f"{entry.remaining_hours:.2f} h remaining / {entry.total_hours:.2f} h "
        f"({entry.used_hours:.2f} h used){refresh}"
    )


def create_kaggle_quota_group(
    *,
    locale: str = "fr",
    service: KaggleQuotaService | None = None,
):
    from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal
    from PySide6.QtWidgets import QGroupBox, QLabel, QPushButton, QVBoxLayout

    quota_service = service or KaggleQuotaService()
    french = locale.lower().startswith("fr")

    def ui(fr: str, en: str) -> str:
        return fr if french else en

    class WorkerSignals(QObject):
        done = Signal(object)
        error = Signal(str)

    class Task(QRunnable):
        def __init__(self, operation: Callable[[], object]) -> None:
            super().__init__()
            self.operation = operation
            self.signals = WorkerSignals()

        def run(self) -> None:
            try:
                value = self.operation()
            except Exception as exc:  # UI boundary: show an actionable local error.
                self.signals.error.emit(str(exc))
            else:
                self.signals.done.emit(value)

    group = QGroupBox(ui("Calcul distant Kaggle", "Kaggle remote compute"))
    group.setObjectName("kaggleQuotaGroup")
    layout = QVBoxLayout(group)

    status = QLabel(ui("État : non vérifié", "Status: not checked"))
    status.setObjectName("kaggleQuotaStatusLabel")
    gpu = QLabel(ui("GPU : non vérifié", "GPU: not checked"))
    gpu.setObjectName("kaggleGpuQuotaLabel")
    tpu = QLabel(ui("TPU : non vérifié", "TPU: not checked"))
    tpu.setObjectName("kaggleTpuQuotaLabel")
    for label in (status, gpu, tpu):
        label.setWordWrap(True)
        layout.addWidget(label)

    refresh = QPushButton(ui("Actualiser le quota GPU/TPU", "Refresh GPU/TPU quota"))
    refresh.setObjectName("refreshKaggleQuotaButton")
    layout.addWidget(refresh)

    note = QLabel(
        ui(
            "Le quota est lu à la demande via la CLI Kaggle officielle. Kodepoia ne stocke "
            "aucun identifiant Kaggle. Le backend R15 utilise actuellement le GPU T4 x2 ; "
            "le TPU v5e-8 reste désactivé tant qu'un backend XLA dédié n'est pas qualifié.",
            "Quota is read on demand through the official Kaggle CLI. Kodepoia stores no "
            "Kaggle credentials. R15 currently targets the T4 x2 GPU; TPU v5e-8 stays "
            "disabled until a dedicated XLA backend is qualified.",
        )
    )
    note.setWordWrap(True)
    layout.addWidget(note)

    pool = QThreadPool.globalInstance()
    workers: list[Task] = []

    def populate(value: object) -> None:
        if not isinstance(value, KaggleQuotaSnapshot):
            return
        gpu_entry = value.for_resource("GPU")
        tpu_entry = value.for_resource("TPU")
        status.setText(
            ui(
                f"État : connecté — {value.version or 'Kaggle CLI'}",
                f"Status: connected — {value.version or 'Kaggle CLI'}",
            )
        )
        gpu.setText(f"GPU : {format_quota_entry(gpu_entry, locale=locale)}")
        tpu.setText(f"TPU : {format_quota_entry(tpu_entry, locale=locale)}")

    def refresh_quota() -> None:
        refresh.setEnabled(False)
        status.setText(ui("État : lecture du quota…", "Status: reading quota…"))
        task = Task(quota_service.snapshot)
        workers.append(task)

        def finished(value: object) -> None:
            refresh.setEnabled(True)
            if task in workers:
                workers.remove(task)
            populate(value)

        def failed(reason: str) -> None:
            refresh.setEnabled(True)
            if task in workers:
                workers.remove(task)
            status.setText(ui(f"État : erreur — {reason}", f"Status: error — {reason}"))

        task.signals.done.connect(finished)
        task.signals.error.connect(failed)
        pool.start(task)

    refresh.clicked.connect(refresh_quota)
    group._kodepoia_quota_service = quota_service
    group._kodepoia_refresh_quota = refresh_quota
    group._kodepoia_workers = workers
    return group


__all__ = [
    "KaggleQuotaEntry",
    "KaggleQuotaError",
    "KaggleQuotaService",
    "KaggleQuotaSnapshot",
    "create_kaggle_quota_group",
    "format_quota_entry",
    "parse_kaggle_quota_json",
]
