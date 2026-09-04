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
                    "acceptance_criteria": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": [
                    "id",
                    "priority",
                    "title",
                    "description",
                    "acceptance_criteria",
                ],
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

    def merge(self, newer: "VisionDraft") -> "VisionDraft":
        return VisionDraft(
            summary=newer.summary or self.summary,
            goals=_merge_unique(self.goals, newer.goals),
            success_metrics=_merge_unique(self.success_metrics, newer.success_metrics),
            constraints=_merge_unique(self.constraints, newer.constraints),
            mvp=_merge_unique(self.mvp, newer.mvp),
            out_of_scope=_merge_unique(self.out_of_scope, newer.out_of_scope),
            requirements=_merge_requirements(self.requirements, newer.requirements),
        )


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


def _merge_unique(base: list[str], newer: list[str]) -> list[str]:
    result = list(base)
    for value in newer:
        if value and value not in result:
            result.append(value)
    return result


def _merge_requirements(
    base: list[VisionRequirement], newer: list[VisionRequirement]
) -> list[VisionRequirement]:
    result = list(base)
    positions = {item.id: index for index, item in enumerate(result)}
    for item in newer:
        if item.id in positions:
            result[positions[item.id]] = item
        else:
            positions[item.id] = len(result)
            result.append(item)
    return result


class VisionAssistant:
    """Local-first project vision assistant with a non-LLM guided fallback."""

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
            "Never silently invent a major product decision: when information is missing, "
            "put a concise question in clarifying_questions. Preserve explicit user choices "
            "and treat a later user message as a possible vision change. Return only JSON "
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
        incoming = VisionDraft.from_mapping(payload)
        draft = current.merge(incoming)
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
        incoming = VisionDraft(summary=message if not current.summary else "")
        draft = current.merge(incoming)
        questions = _missing_questions(draft, message=message, locale=locale)
        return VisionAssistantResult(
            draft=draft,
            clarifying_questions=questions,
            mode="guided",
            assistant_message=_assistant_summary(draft, questions, locale=locale),
        )


def _missing_questions(draft: VisionDraft, *, message: str, locale: str) -> list[str]:
    french = locale.lower().startswith("fr")
    lower = message.casefold()
    questions: list[str] = []
    if not draft.goals:
        questions.append(
            "Quels sont les 1 à 3 objectifs principaux que le projet doit atteindre ?"
            if french
            else "What are the 1–3 main goals the project must achieve?"
        )
    if not draft.success_metrics:
        questions.append(
            "Comment sauras-tu que le projet est réussi (FPS, stabilité, utilisateurs, ventes, durée, qualité…) ?"
            if french
            else "How will you know the project succeeded (FPS, stability, users, sales, duration, quality…)?"
        )
    if not draft.constraints:
        questions.append(
            "Quelles contraintes sont importantes : plateformes, budget, matériel, délai, hors-ligne, équipe ou technologies ?"
            if french
            else "Which constraints matter: platforms, budget, hardware, deadline, offline use, team or technologies?"
        )
    if not draft.mvp:
        questions.append(
            "Quelle est la plus petite version jouable/utilisable qui prouverait que l'idée fonctionne ?"
            if french
            else "What is the smallest playable/usable version that would prove the idea works?"
        )
    if not draft.out_of_scope:
        questions.append(
            "Que veux-tu explicitement exclure de la première version pour éviter que le projet devienne trop large ?"
            if french
            else "What should be explicitly excluded from the first version to keep scope under control?"
        )
    audience_terms = ("public", "joueur", "player", "utilisateur", "audience", "âge", "age")
    if not any(term in lower for term in audience_terms):
        questions.append(
            "À qui s'adresse principalement ce projet ?"
            if french
            else "Who is the primary audience for this project?"
        )
    return questions[:4]


def _assistant_summary(draft: VisionDraft, questions: list[str], *, locale: str) -> str:
    french = locale.lower().startswith("fr")
    if questions:
        return (
            "J'ai structuré ce que tu m'as donné. Pour rendre la Vision exploitable, "
            "j'ai encore besoin de quelques précisions."
            if french
            else "I structured what you gave me. I still need a few clarifications to make the Vision actionable."
        )
    return (
        "La Vision est suffisamment structurée pour être relue et appliquée au projet."
        if french
        else "The Vision is structured enough to review and apply to the project."
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
