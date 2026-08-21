from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Iterable

from .guardian import KodeGuardian
from .types import ActionKind, ActionRequest


_INJECTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("ignore-instructions", re.compile(r"\b(ignore|disregard|forget)\b.{0,40}\b(instruction|system|developer|user)\b", re.I | re.S)),
    ("tool-coercion", re.compile(r"\b(run|execute|download|install|delete|upload|send)\b.{0,40}\b(command|script|file|secret|token|password|tool)\b", re.I | re.S)),
    ("role-spoof", re.compile(r"\b(system|developer)\s*(message|prompt|instruction)\b", re.I)),
    ("secret-request", re.compile(r"\b(api\s*key|token|password|private\s*key|credential)\b", re.I)),
)


@dataclass(frozen=True, slots=True)
class ResearchEnvelope:
    source: str
    content: str
    sha256: str
    flags: tuple[str, ...]
    trusted: bool = False
    instruction_authority: str = "none"

    def prompt_fragment(self) -> str:
        return '<external_untrusted_data instruction_authority="none">\n' + self.content + "\n</external_untrusted_data>"


class KodeResearchGuard:
    """Makes external material permanently non-authoritative and surfaces injection indicators."""

    def __init__(self, guardian: KodeGuardian) -> None:
        self.guardian = guardian

    def ingest(self, source: str, content: str, *, actor: str = "kodepoia.research") -> ResearchEnvelope:
        self.guardian.require_allowed(ActionRequest(ActionKind.RESEARCH_INGEST, actor, target=source))
        flags = tuple(name for name, pattern in _INJECTION_PATTERNS if pattern.search(content))
        digest = hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()
        return ResearchEnvelope(source, content, digest, flags)

    @staticmethod
    def has_high_risk_flags(envelope: ResearchEnvelope) -> bool:
        return any(flag in {"ignore-instructions", "tool-coercion", "secret-request"} for flag in envelope.flags)

    @staticmethod
    def combine(envelopes: Iterable[ResearchEnvelope]) -> str:
        return "\n\n".join(item.prompt_fragment() for item in envelopes)
