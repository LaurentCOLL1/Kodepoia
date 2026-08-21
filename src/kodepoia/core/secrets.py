from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


class SecretBackend(Protocol):
    def set(self, namespace: str, key: str, value: str) -> None: ...
    def get(self, namespace: str, key: str) -> str | None: ...
    def delete(self, namespace: str, key: str) -> None: ...


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
