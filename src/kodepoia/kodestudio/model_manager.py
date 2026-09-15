from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from kodepoia.brain.ollama import OllamaClient
from kodepoia.kodestudio.preferences import ApplicationPreferences

OLLAMA_BASE_URL_KEY = "ollama_base_url"
MODEL_ROLES_KEY = "model_roles"
DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"
MODEL_ROLES = ("fast", "core", "code", "heavy")


@dataclass(frozen=True, slots=True)
class RecommendedModel:
    name: str
    role: str
    description_fr: str
    description_en: str


RECOMMENDED_MODELS = (
    RecommendedModel(
        "granite4.1:3b",
        "fast",
        "Tâches rapides et peu coûteuses.",
        "Fast, low-cost tasks.",
    ),
    RecommendedModel(
        "qwen3.5:4b",
        "fast",
        "Assistant général léger et rapide.",
        "Lightweight and fast general assistant.",
    ),
    RecommendedModel(
        "qwen3.5:9b",
        "core",
        "Raisonnement général plus riche.",
        "Stronger general reasoning.",
    ),
    RecommendedModel(
        "gpt-oss:20b",
        "core",
        "Raisonnement plus lourd quand la machine le permet.",
        "Heavier reasoning when the machine can support it.",
    ),
    RecommendedModel(
        "north-mini-code-1.0:Q4_K_M",
        "code",
        "Candidat spécialisé code issu de la campagne de présélection.",
        "Code-specialist candidate from the preselection campaign.",
    ),
)


def saved_ollama_base_url(preferences: ApplicationPreferences) -> str:
    value = preferences.get(OLLAMA_BASE_URL_KEY, DEFAULT_OLLAMA_BASE_URL)
    text = str(value or DEFAULT_OLLAMA_BASE_URL).strip().rstrip("/")
    return text or DEFAULT_OLLAMA_BASE_URL


def saved_model_roles(preferences: ApplicationPreferences) -> dict[str, str]:
    raw = preferences.get(MODEL_ROLES_KEY, {})
    if not isinstance(raw, dict):
        return {}
    result: dict[str, str] = {}
    for role in MODEL_ROLES:
        value = raw.get(role)
        if isinstance(value, str) and value.strip():
            result[role] = value.strip()
    return result


def preferred_model(preferences: ApplicationPreferences, role: str) -> str | None:
    return saved_model_roles(preferences).get(str(role).strip().lower())


class OllamaModelManager:
    """Preference-backed local model management facade used by KodeStudio."""

    def __init__(
        self,
        preferences: ApplicationPreferences,
        *,
        client_factory: Callable[..., OllamaClient] = OllamaClient,
    ) -> None:
        self.preferences = preferences
        self.client_factory = client_factory

    @property
    def base_url(self) -> str:
        return saved_ollama_base_url(self.preferences)

    def set_base_url(self, value: str) -> str:
        text = str(value).strip().rstrip("/")
        if not text.startswith(("http://", "https://")):
            raise ValueError("Ollama URL must start with http:// or https://")
        self.preferences.update({OLLAMA_BASE_URL_KEY: text})
        return text

    def client(self, *, timeout: float = 15.0) -> OllamaClient:
        return self.client_factory(base_url=self.base_url, timeout=timeout)

    def snapshot(self) -> dict[str, Any]:
        client = self.client(timeout=8.0)
        return {
            "base_url": self.base_url,
            "version": client.version(),
            "models": sorted(client.list_models(), key=str.casefold),
            "roles": saved_model_roles(self.preferences),
        }

    def install(self, model: str) -> None:
        self.client(timeout=3600.0).pull_model(model, timeout=3600.0)

    def delete(self, model: str) -> None:
        self.client(timeout=120.0).delete_model(model)

    def save_roles(self, values: dict[str, str | None]) -> dict[str, str]:
        roles: dict[str, str] = {}
        for role in MODEL_ROLES:
            value = values.get(role)
            if isinstance(value, str) and value.strip():
                roles[role] = value.strip()
        self.preferences.update({MODEL_ROLES_KEY: roles})
        return roles


def create_model_manager_group(
    preferences: ApplicationPreferences,
    *,
    locale: str = "fr",
    manager: OllamaModelManager | None = None,
):
    from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal
    from PySide6.QtWidgets import (
        QComboBox,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QMessageBox,
        QPushButton,
        QVBoxLayout,
    )

    service = manager or OllamaModelManager(preferences)
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
                result = self.operation()
            except Exception as exc:  # UI boundary: surface a human-readable local error.
                self.signals.error.emit(str(exc))
            else:
                self.signals.done.emit(result)

    group = QGroupBox(ui("IA locale / modèles Ollama", "Local AI / Ollama models"))
    group.setObjectName("ollamaModelManagerGroup")
    layout = QVBoxLayout(group)

    endpoint_row = QHBoxLayout()
    endpoint = QLineEdit(service.base_url)
    endpoint.setObjectName("ollamaEndpointInput")
    endpoint_row.addWidget(QLabel(ui("Serveur Ollama", "Ollama server")))
    endpoint_row.addWidget(endpoint, 1)
    save_endpoint = QPushButton(ui("Enregistrer", "Save"))
    save_endpoint.setObjectName("saveOllamaEndpointButton")
    endpoint_row.addWidget(save_endpoint)
    layout.addLayout(endpoint_row)

    status = QLabel(ui("État : non vérifié", "Status: not checked"))
    status.setObjectName("ollamaStatusLabel")
    layout.addWidget(status)

    installed = QListWidget()
    installed.setObjectName("installedOllamaModels")
    installed.setMinimumHeight(110)
    layout.addWidget(QLabel(ui("Modèles installés", "Installed models")))
    layout.addWidget(installed)

    controls = QHBoxLayout()
    refresh = QPushButton(ui("Actualiser", "Refresh"))
    refresh.setObjectName("refreshOllamaModelsButton")
    delete = QPushButton(ui("Supprimer le modèle sélectionné", "Delete selected model"))
    delete.setObjectName("deleteOllamaModelButton")
    controls.addWidget(refresh)
    controls.addWidget(delete)
    controls.addStretch(1)
    layout.addLayout(controls)

    install_row = QHBoxLayout()
    recommendation = QComboBox()
    recommendation.setObjectName("recommendedOllamaModelSelector")
    for item in RECOMMENDED_MODELS:
        description = item.description_fr if french else item.description_en
        recommendation.addItem(
            f"{item.role.upper()} — {item.name} — {description}",
            item.name,
        )
    custom = QLineEdit()
    custom.setObjectName("customOllamaModelInput")
    custom.setPlaceholderText(
        ui("ou saisir un modèle/tag Ollama", "or enter an Ollama model/tag")
    )
    install_button = QPushButton(ui("Installer / mettre à jour", "Install / update"))
    install_button.setObjectName("installOllamaModelButton")
    install_row.addWidget(recommendation, 2)
    install_row.addWidget(custom, 1)
    install_row.addWidget(install_button)
    layout.addLayout(install_row)

    roles_group = QGroupBox(ui("Routage préféré", "Preferred routing"))
    roles_form = QFormLayout(roles_group)
    role_boxes: dict[str, QComboBox] = {}
    role_labels = {
        "fast": ui("Rapide (FAST)", "Fast (FAST)"),
        "core": ui("Principal (CORE)", "Core (CORE)"),
        "code": ui("Code (CODE)", "Code (CODE)"),
        "heavy": ui("Lourd (HEAVY)", "Heavy (HEAVY)"),
    }
    for role in MODEL_ROLES:
        box = QComboBox()
        box.setObjectName(f"ollamaRole{role.title()}Selector")
        box.addItem(ui("Automatique", "Automatic"), None)
        role_boxes[role] = box
        roles_form.addRow(role_labels[role], box)
    save_roles = QPushButton(ui("Enregistrer les rôles", "Save roles"))
    save_roles.setObjectName("saveOllamaRolesButton")
    roles_form.addRow(save_roles)
    layout.addWidget(roles_group)

    note = QLabel(
        ui(
            "Les rôles mémorisent les modèles préférés. Le chat Vision utilise CORE "
            "quand il est disponible ; les autres surfaces peuvent réutiliser ces "
            "préférences progressivement.",
            "Roles store preferred models. Vision chat uses CORE when available; "
            "other surfaces can progressively reuse these preferences.",
        )
    )
    note.setWordWrap(True)
    layout.addWidget(note)

    pool = QThreadPool.globalInstance()
    workers: list[Task] = []

    def set_busy(value: bool) -> None:
        for widget in (refresh, delete, install_button, save_endpoint, save_roles):
            widget.setEnabled(not value)

    def run_task(operation: Callable[[], object], done: Callable[[object], None]) -> None:
        set_busy(True)
        task = Task(operation)
        workers.append(task)

        def finished(value: object) -> None:
            set_busy(False)
            if task in workers:
                workers.remove(task)
            done(value)

        def failed(reason: str) -> None:
            set_busy(False)
            if task in workers:
                workers.remove(task)
            status.setText(ui(f"État : erreur — {reason}", f"Status: error — {reason}"))

        task.signals.done.connect(finished)
        task.signals.error.connect(failed)
        pool.start(task)

    def populate_roles(models: list[str]) -> None:
        saved = saved_model_roles(preferences)
        for role, box in role_boxes.items():
            target = saved.get(role)
            box.blockSignals(True)
            box.clear()
            box.addItem(ui("Automatique", "Automatic"), None)
            for model_name in models:
                box.addItem(model_name, model_name)
            if target:
                index = box.findData(target)
                if index < 0:
                    box.addItem(
                        ui(f"{target} (absent)", f"{target} (missing)"),
                        target,
                    )
                    index = box.findData(target)
                box.setCurrentIndex(index)
            box.blockSignals(False)

    def populate(snapshot: object) -> None:
        if not isinstance(snapshot, dict):
            return
        models = [str(value) for value in snapshot.get("models", [])]
        installed.clear()
        installed.addItems(models)
        populate_roles(models)
        version = snapshot.get("version", "unknown")
        status.setText(
            ui(
                f"État : connecté — Ollama {version}",
                f"Status: connected — Ollama {version}",
            )
        )

    def refresh_models() -> None:
        run_task(service.snapshot, populate)

    def save_endpoint_value() -> None:
        try:
            service.set_base_url(endpoint.text())
        except ValueError as exc:
            QMessageBox.warning(group, "Kodepoia", str(exc))
            return
        refresh_models()

    def install_selected() -> None:
        name = custom.text().strip() or str(recommendation.currentData() or "").strip()
        if not name:
            return
        status.setText(ui(f"Installation de {name}…", f"Installing {name}…"))

        def after_install(_: object) -> None:
            custom.clear()
            refresh_models()

        run_task(lambda: service.install(name), after_install)

    def delete_selected() -> None:
        item = installed.currentItem()
        if item is None:
            return
        name = item.text()
        answer = QMessageBox.question(
            group,
            "Kodepoia",
            ui(f"Supprimer le modèle local {name} ?", f"Delete local model {name}?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        run_task(lambda: service.delete(name), lambda _: refresh_models())

    def save_role_values() -> None:
        values = {
            role: (str(box.currentData()) if box.currentData() else None)
            for role, box in role_boxes.items()
        }
        service.save_roles(values)
        status.setText(ui("État : rôles enregistrés", "Status: roles saved"))

    refresh.clicked.connect(refresh_models)
    save_endpoint.clicked.connect(save_endpoint_value)
    install_button.clicked.connect(install_selected)
    delete.clicked.connect(delete_selected)
    save_roles.clicked.connect(save_role_values)

    group._kodepoia_refresh_models = refresh_models
    group._kodepoia_model_manager = service
    group._kodepoia_workers = workers
    populate_roles([])
    return group


__all__ = [
    "DEFAULT_OLLAMA_BASE_URL",
    "MODEL_ROLES",
    "MODEL_ROLES_KEY",
    "OLLAMA_BASE_URL_KEY",
    "OllamaModelManager",
    "RECOMMENDED_MODELS",
    "RecommendedModel",
    "create_model_manager_group",
    "preferred_model",
    "saved_model_roles",
    "saved_ollama_base_url",
]
