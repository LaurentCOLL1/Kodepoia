from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Mapping, Protocol, Sequence


class SecretBackend(Protocol):
    def set(self, namespace: str, key: str, value: str) -> None: ...
    def get(self, namespace: str, key: str) -> str | None: ...
    def delete(self, namespace: str, key: str) -> None: ...


@dataclass(frozen=True, slots=True)
class SecretRef:
    namespace: str
    key: str

    def __post_init__(self) -> None:
        if not self.namespace.strip() or not self.key.strip():
            raise ValueError("Secret references require non-empty namespace and key")
        if any(ch in self.namespace + self.key for ch in "\r\n\x00"):
            raise ValueError("Secret references cannot contain control delimiters")

    def to_dict(self) -> dict[str, str]:
        return {"namespace": self.namespace, "key": self.key}


class KeyringSecretBackend:
    """OS keyring adapter; Windows uses the available Windows keyring backend."""

    @staticmethod
    def _keyring():
        try:
            import keyring
        except ImportError as exc:
            raise RuntimeError("keyring is required for OS-backed secret storage") from exc
        return keyring

    def set(self, namespace: str, key: str, value: str) -> None:
        self._keyring().set_password(namespace, key, value)

    def get(self, namespace: str, key: str) -> str | None:
        return self._keyring().get_password(namespace, key)

    def delete(self, namespace: str, key: str) -> None:
        self._keyring().delete_password(namespace, key)


@dataclass(slots=True)
class MemorySecretBackend:
    values: dict[tuple[str, str], str] = field(default_factory=dict)

    def set(self, namespace: str, key: str, value: str) -> None:
        self.values[(namespace, key)] = value

    def get(self, namespace: str, key: str) -> str | None:
        return self.values.get((namespace, key))

    def delete(self, namespace: str, key: str) -> None:
        self.values.pop((namespace, key), None)


class KodeSecrets:
    def __init__(self, backend: SecretBackend | None = None) -> None:
        self.backend = backend or KeyringSecretBackend()
        self._known_values: set[str] = set()

    def store(self, namespace: str, key: str, value: str) -> None:
        if not value:
            raise ValueError("Secret value cannot be empty")
        self.backend.set(namespace, key, value)
        self._known_values.add(value)

    def ref(self, namespace: str, key: str) -> SecretRef:
        return SecretRef(namespace=namespace, key=key)

    def resolve(self, ref: SecretRef) -> str | None:
        return self.delegated_get(ref.namespace, ref.key)

    def delegated_get(self, namespace: str, key: str) -> str | None:
        value = self.backend.get(namespace, key)
        if value:
            self._known_values.add(value)
        return value

    def redact(self, text: str) -> str:
        result = text
        for value in sorted(self._known_values, key=len, reverse=True):
            if value:
                result = result.replace(value, "***REDACTED***")
        return result

    def known_values(self) -> tuple[str, ...]:
        return tuple(sorted(self._known_values, key=len, reverse=True))


def find_secret_leaks(payload: object, known_values: Sequence[str]) -> tuple[str, ...]:
    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return tuple(value for value in known_values if value and value in serialized)


def assert_secret_refs_only(
    payload: Mapping[str, object],
    refs: Sequence[SecretRef],
    known_values: Sequence[str],
) -> None:
    leaks = find_secret_leaks(payload, known_values)
    if leaks:
        raise ValueError("raw secret material leaked into durable payload")
    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    for ref in refs:
        if ref.namespace not in serialized or ref.key not in serialized:
            raise ValueError("durable payload lost a required KodeSecrets reference")
