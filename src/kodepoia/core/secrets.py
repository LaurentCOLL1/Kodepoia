from __future__ import annotations

import ctypes
import os
from ctypes import wintypes
from dataclasses import dataclass
from typing import Protocol

from .guardian import KodeGuardian
from .types import ActionKind, ActionRequest


class SecretStore(Protocol):
    def get(self, name: str) -> str | None: ...
    def set(self, name: str, value: str) -> None: ...
    def delete(self, name: str) -> None: ...


class MemorySecretStore:
    """Test-only volatile store."""

    def __init__(self) -> None:
        self._values: dict[str, str] = {}

    def get(self, name: str) -> str | None:
        return self._values.get(name)

    def set(self, name: str, value: str) -> None:
        self._values[name] = value

    def delete(self, name: str) -> None:
        self._values.pop(name, None)


if os.name == "nt":
    CRED_TYPE_GENERIC = 1
    CRED_PERSIST_LOCAL_MACHINE = 2
    ERROR_NOT_FOUND = 1168

    class CREDENTIALW(ctypes.Structure):
        _fields_ = [
            ("Flags", wintypes.DWORD), ("Type", wintypes.DWORD), ("TargetName", wintypes.LPWSTR),
            ("Comment", wintypes.LPWSTR), ("LastWritten", wintypes.FILETIME),
            ("CredentialBlobSize", wintypes.DWORD), ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
            ("Persist", wintypes.DWORD), ("AttributeCount", wintypes.DWORD), ("Attributes", ctypes.c_void_p),
            ("TargetAlias", wintypes.LPWSTR), ("UserName", wintypes.LPWSTR),
        ]


class WindowsCredentialManagerStore:
    """Windows Credential Manager backend using Win32 Cred* APIs."""

    def __init__(self, namespace: str = "Kodepoia") -> None:
        if os.name != "nt":
            raise OSError("Windows Credential Manager is only available on Windows")
        self.namespace = namespace
        self._advapi32 = ctypes.WinDLL("Advapi32.dll", use_last_error=True)
        self._advapi32.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(CREDENTIALW))]
        self._advapi32.CredReadW.restype = wintypes.BOOL
        self._advapi32.CredWriteW.argtypes = [ctypes.POINTER(CREDENTIALW), wintypes.DWORD]
        self._advapi32.CredWriteW.restype = wintypes.BOOL
        self._advapi32.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
        self._advapi32.CredDeleteW.restype = wintypes.BOOL
        self._advapi32.CredFree.argtypes = [ctypes.c_void_p]

    def _target(self, name: str) -> str:
        return f"{self.namespace}/{name}"

    def get(self, name: str) -> str | None:
        credential = ctypes.POINTER(CREDENTIALW)()
        if not self._advapi32.CredReadW(self._target(name), CRED_TYPE_GENERIC, 0, ctypes.byref(credential)):
            error = ctypes.get_last_error()
            if error == ERROR_NOT_FOUND:
                return None
            raise ctypes.WinError(error)
        try:
            size = credential.contents.CredentialBlobSize
            return ctypes.string_at(credential.contents.CredentialBlob, size).decode("utf-16-le")
        finally:
            self._advapi32.CredFree(credential)

    def set(self, name: str, value: str) -> None:
        blob = value.encode("utf-16-le")
        buffer = (ctypes.c_ubyte * len(blob)).from_buffer_copy(blob)
        credential = CREDENTIALW()
        credential.Type = CRED_TYPE_GENERIC
        credential.TargetName = self._target(name)
        credential.CredentialBlobSize = len(blob)
        credential.CredentialBlob = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))
        credential.Persist = CRED_PERSIST_LOCAL_MACHINE
        credential.UserName = "Kodepoia"
        if not self._advapi32.CredWriteW(ctypes.byref(credential), 0):
            raise ctypes.WinError(ctypes.get_last_error())

    def delete(self, name: str) -> None:
        if not self._advapi32.CredDeleteW(self._target(name), CRED_TYPE_GENERIC, 0):
            error = ctypes.get_last_error()
            if error != ERROR_NOT_FOUND:
                raise ctypes.WinError(error)


@dataclass(slots=True)
class SecretBroker:
    guardian: KodeGuardian
    store: SecretStore
    actor: str = "kodepoia.secret-broker"

    def get(self, name: str, *, confirmed: bool = False) -> str | None:
        self.guardian.require_allowed(ActionRequest(ActionKind.SECRET_READ, self.actor, target=name), confirmed=confirmed)
        return self.store.get(name)

    def set(self, name: str, value: str, *, confirmed: bool = False) -> None:
        self.guardian.require_allowed(ActionRequest(ActionKind.SECRET_WRITE, self.actor, target=name), confirmed=confirmed)
        self.store.set(name, value)

    def delete(self, name: str, *, confirmed: bool = False) -> None:
        self.guardian.require_allowed(ActionRequest(ActionKind.SECRET_WRITE, self.actor, target=name), confirmed=confirmed)
        self.store.delete(name)

    @staticmethod
    def redact(text: str, values: list[str]) -> str:
        redacted = text
        for value in sorted((v for v in values if v), key=len, reverse=True):
            redacted = redacted.replace(value, "[REDACTED]")
        return redacted
