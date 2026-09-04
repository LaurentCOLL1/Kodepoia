from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

from kodepoia.brain.base import BrainMessage
from kodepoia.brain.ollama import OllamaClient
from kodepoia.exceptions import BrainUnavailable


VISION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "goals": {"type": "array", "items": {"type": "string"}},
        "success_metrics": {"type": "array", "items": {"type": "string"}},
        "constraints": {"type": "array", "items": {"type": "string"}},
        "mvp": {"type": "array", "items": {"type": "string"}},
        "out_of_scope": {"type": "array", "items": {"type": "string"}},
        "requirements": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "priority": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "acceptance_criteria": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["id", "priority", "title", "description", "acceptance_criteria"],
            },
        },
        "clarifying_questions": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "summary",
        "goals",
        "success_metrics",
        "constraints",
        "mvp",
        "out_of_scope",
        "requirements",
        "clarifying_questions",
    ],
}


@dataclass(slots=True)
class VisionRequirement:
    id: str
    title: str
    description: str = ""
    priority: str = "P1"
    acceptance_criteria: list[str] = field(default_factory=list)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any], index: int) -> "VisionRequirement":
        req_id = str(value.get("id") or f"REQ-{index:03d}").strip()
        priority = str(value.get("priority") or "P1").strip().upper()
        if priority not in {"P0", "P1", "P2", "P3"}:
            priority = "P1"
        return cls(
            id=req_id,
            priority=priority,
            title=str(value.get("title") or "").strip(),
            description=str(value.get("description") or "").strip(),
            acceptance_criteria=_string_list(value.get("acceptance_criteria")),
        )


@dataclass(slots=True)
class VisionDraft:
    summary: str = ""
    goals: list[str] = field(default_factory=list)
    success_metrics: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    mvp: list[str] = field(default_factory=list)
    out_of_scope: list[str] = field(default_factory=list)
    requirements: list[VisionRequirement] = field(default_factory=list)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any] | None) -> "VisionDraft":
        data = value or {}
        requirements = data.get("requirements")
        reqs: list[VisionRequirement] = []
        if isinstance(requirements, list):
            for index, item in enumerate(requirements, start=1):
                if isinstance(item, Mapping):
                    reqs.append(VisionRequirement.from_mapping(item, index))
        return cls(
            summary=str(data.get("summary") or "").strip(),
            goals=_string_list(data.get("goals")),
            success_metrics=_string_list(data.get("success_metrics")),
            constraints=_string_list(data.get("constraints")),
            mvp=_string_list(data.get("mvp")),
            out_of_scope=_string_list(data.get("out_of_scope")),
            requirements=reqs,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class VisionAssistantResult:
    draft: VisionDraft
    clarifying_questions: list[str] = field(default_factory=list)
    mode: str = "guided"
    model: str | None = None
    assistant_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "draft": self.draft.to_dict(),
            "clarifying_questions": list(self.clarifying_questions),
            "mode": self.mode,
            "model": self.model,
            "assistant_message": self.assistant_message,
        }


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        values = value.replace("\n", ";").split(";")
    elif isinstance(value, (list, tuple, set)):
        values = value
    else:
        values = [value]
    result: list[str] = []
    for item in values:
        text = str(item).strip()
        if text and text not in result:
            result.append(text)
    return result


def _copy_draft(draft: VisionDraft) -> VisionDraft:
    return VisionDraft.from_mapping(draft.to_dict())


class VisionAssistant:
    """Local-first project Vision assistant with a deterministic guided fallback."""

    def __init__(self, client: OllamaClient | None = None) -> None:
        self.client = client or OllamaClient(timeout=8.0)

    def available_models(self) -> list[str]:
        try:
            return self.client.list_models()
        except BrainUnavailable:
            return []

    def refine(
        self,
        user_message: str,
        *,
        current: VisionDraft | None = None,
        model: str | None = None,
        locale: str = "fr",
    ) -> VisionAssistantResult:
        message = user_message.strip()
        if not message:
            raise ValueError("A project idea or clarification is required")
        current_draft = current or VisionDraft()
        if model:
            try:
                return self._refine_with_ollama(
                    message,
                    current=current_draft,
                    model=model,
                    locale=locale,
                )
            except (BrainUnavailable, ValueError, json.JSONDecodeError, TypeError):
                # The user must never be blocked because the local model is unavailable
                # or returned malformed structured data.
                pass
        return self._guided_refine(message, current=current_draft, locale=locale)

    def _refine_with_ollama(
        self,
        message: str,
        *,
        current: VisionDraft,
        model: str,
        locale: str,
    ) -> VisionAssistantResult:
        language = "French" if locale.lower().startswith("fr") else "English"
        system = (
            "You are Kodepoia Vision Guide, a local-first product discovery assistant. "
            "Help a beginner turn an idea into a precise, testable project vision. "
            "Return the COMPLETE revised vision, not a patch. Preserve explicit choices unless "
            "the user clearly changes them. Never silently invent a major product decision: when "
            "information is missing, put a concise question in clarifying_questions. Treat later "
            "messages as possible vision changes and reconcile them explicitly. Return only JSON "
            f"matching the provided schema. Write all human-facing text in {language}."
        )
        context = json.dumps(current.to_dict(), ensure_ascii=False, indent=2)
        response = self.client.chat(
            model,
            [
                BrainMessage("system", system),
                BrainMessage(
                    "user",
                    "Current structured vision:\n"
                    f"{context}\n\nUser message / requested change:\n{message}",
                ),
            ],
            response_schema=VISION_SCHEMA,
            think=False,
            options={"temperature": 0.2},
        )
        payload = json.loads(response.content)
        if not isinstance(payload, dict):
            raise ValueError("Structured vision response must be a JSON object")
        draft = VisionDraft.from_mapping(payload)
        questions = _string_list(payload.get("clarifying_questions"))
        return VisionAssistantResult(
            draft=draft,
            clarifying_questions=questions,
            mode="ollama",
            model=response.model or model,
            assistant_message=_assistant_summary(draft, questions, locale=locale),
        )

    def _guided_refine(
        self,
        message: str,
        *,
        current: VisionDraft,
        locale: str,
    ) -> VisionAssistantResult:
        draft = _copy_draft(current)
        explicit = _apply_explicit_update(draft, message, locale=locale)
        if not explicit:
            _apply_next_guided_answer(draft, message)
        questions = _next_guided_questions(draft, locale=locale)
        return VisionAssistantResult(
            draft=draft,
            clarifying_questions=questions,
            mode="guided",
            assistant_message=_assistant_summary(draft, questions, locale=locale),
        )


def _apply_next_guided_answer(draft: VisionDraft, message: str) -> None:
    values = _string_list(message)
    if not draft.summary:
        draft.summary = message.strip()
    elif not draft.goals:
        draft.goals = values
    elif not draft.success_metrics:
        draft.success_metrics = values
    elif not draft.constraints:
        draft.constraints = values
    elif not draft.mvp:
        draft.mvp = values
    elif not draft.out_of_scope:
        draft.out_of_scope = values
    elif not draft.requirements:
        draft.requirements = [
            VisionRequirement(id=f"REQ-{index:03d}", title=value, priority="P1")
            for index, value in enumerate(values, start=1)
        ]
    else:
        missing = next((item for item in draft.requirements if not item.acceptance_criteria), None)
        if missing is not None:
            missing.acceptance_criteria = values


def _apply_explicit_update(draft: VisionDraft, message: str, *, locale: str) -> bool:
    stripped = message.strip()
    lower = stripped.casefold()
    prefixes: tuple[tuple[tuple[str, ...], str], ...] = (
        (("résumé:", "resume:", "summary:"), "summary"),
        (("objectifs:", "goals:"), "goals"),
        (("mesures de réussite:", "indicateurs de réussite:", "success metrics:"), "success_metrics"),
        (("contraintes:", "constraints:"), "constraints"),
        (("mvp:",), "mvp"),
        (("hors périmètre:", "hors perimetre:", "out of scope:"), "out_of_scope"),
        (("exigences:", "requirements:"), "requirements"),
    )
    for candidates, field_name in prefixes:
        for prefix in candidates:
            if lower.startswith(prefix):
                value = stripped[len(prefix):].strip()
                if field_name == "summary":
                    draft.summary = value
                elif field_name == "requirements":
                    items = _string_list(value)
                    draft.requirements = [
                        VisionRequirement(id=f"REQ-{index:03d}", title=item, priority="P1")
                        for index, item in enumerate(items, start=1)
                    ]
                else:
                    setattr(draft, field_name, _string_list(value))
                return True
    acceptance_prefixes = ("critères d'acceptation:", "criteres d'acceptation:", "acceptance criteria:")
    for prefix in acceptance_prefixes:
        if lower.startswith(prefix):
            values = _string_list(stripped[len(prefix):].strip())
            if not draft.requirements:
                draft.requirements.append(VisionRequirement(id="REQ-001", title="Requirement"))
            target = next((item for item in draft.requirements if not item.acceptance_criteria), draft.requirements[-1])
            target.acceptance_criteria = values
            return True
    return False


def _next_guided_questions(draft: VisionDraft, *, locale: str) -> list[str]:
    french = locale.lower().startswith("fr")
    if not draft.goals:
        return [
            "Quels sont les 1 à 3 objectifs principaux que le projet doit atteindre ?"
            if french else "What are the 1–3 main goals the project must achieve?"
        ]
    if not draft.success_metrics:
        return [
            "Comment sauras-tu que le projet est réussi ? Donne des mesures concrètes : FPS, stabilité, utilisateurs, ventes, durée, qualité…"
            if french else "How will you know the project succeeded? Give concrete measures: FPS, stability, users, sales, duration, quality…"
        ]
    if not draft.constraints:
        return [
            "Quelles contraintes sont importantes : public, plateformes, budget, matériel, délai, hors-ligne, équipe ou technologies ?"
            if french else "Which constraints matter: audience, platforms, budget, hardware, deadline, offline use, team or technologies?"
        ]
    if not draft.mvp:
        return [
            "Quelle est la plus petite version jouable/utilisable qui prouverait que l'idée fonctionne ?"
            if french else "What is the smallest playable/usable version that would prove the idea works?"
        ]
    if not draft.out_of_scope:
        return [
            "Que veux-tu explicitement exclure de la première version pour éviter que le projet devienne trop large ?"
            if french else "What should be explicitly excluded from the first version to keep scope under control?"
        ]
    if not draft.requirements:
        return [
            "Quelles capacités sont indispensables ? Écris une ou plusieurs exigences séparées par des points-virgules."
            if french else "Which capabilities are mandatory? Write one or more requirements separated by semicolons."
        ]
    missing = next((item for item in draft.requirements if not item.acceptance_criteria), None)
    if missing is not None:
        return [
            f"Comment vérifier objectivement « {missing.title} » ? Donne un ou plusieurs critères d'acceptation séparés par des points-virgules."
            if french else f"How can “{missing.title}” be verified objectively? Give one or more acceptance criteria separated by semicolons."
        ]
    return []


def _assistant_summary(draft: VisionDraft, questions: list[str], *, locale: str) -> str:
    french = locale.lower().startswith("fr")
    if questions:
        return (
            "J'ai mis à jour la Vision avec ta dernière réponse. Voici la prochaine précision utile."
            if french
            else "I updated the Vision with your latest answer. Here is the next useful clarification."
        )
    return (
        "La Vision contient maintenant les éléments essentiels, les exigences et leurs critères d'acceptation. Tu peux encore modifier un champ avec « Objectifs: … », « Contraintes: … », « MVP: … », etc."
        if french
        else "The Vision now contains its essential elements, requirements and acceptance criteria. You can still change a field using “Goals: …”, “Constraints: …”, “MVP: …”, etc."
    )


def save_vision_draft(path: Path, result: VisionAssistantResult) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def load_vision_draft(path: Path) -> VisionDraft:
    if not path.exists():
        return VisionDraft()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Vision draft must contain a JSON object")
    nested = payload.get("draft", payload)
    if not isinstance(nested, Mapping):
        raise ValueError("Vision draft payload is invalid")
    return VisionDraft.from_mapping(nested)


__all__ = [
    "VISION_SCHEMA",
    "VisionAssistant",
    "VisionAssistantResult",
    "VisionDraft",
    "VisionRequirement",
    "load_vision_draft",
    "save_vision_draft",
]
