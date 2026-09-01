from __future__ import annotations

import base64
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from kodepoia.core.sandbox import ProcessSandbox, SandboxResult
from kodepoia.core.secrets import KodeSecrets, SecretRef
from kodepoia.exceptions import PolicyDenied

_REDACTED = "<redacted-secret>"
_SECRET_KEY_RE = re.compile(
    r"(?:^|[_-])(?:api[_-]?key|access[_-]?token|auth(?:orization)?|credential|password|passwd|private[_-]?key|secret|session[_-]?id|token)(?:$|[_-])",
    re.IGNORECASE,
)
_GENERIC_SECRET_PATTERNS = (
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{12,}\b", re.IGNORECASE),
)


def _variants(value: str) -> tuple[str, ...]:
    raw = value.encode("utf-8")
    b64 = base64.b64encode(raw).decode("ascii")
    b64url = base64.urlsafe_b64encode(raw).decode("ascii")
    double_b64 = base64.b64encode(b64.encode("ascii")).decode("ascii")
    return tuple(
        sorted(
            {
                value,
                b64,
                b64.rstrip("="),
                b64url,
                b64url.rstrip("="),
                double_b64,
                raw.hex(),
            },
            key=len,
            reverse=True,
        )
    )


def _is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


@dataclass(frozen=True, slots=True)
class SecretLeak:
    surface: str
    location: str
    encoding: str

    def to_dict(self) -> dict[str, str]:
        return {
            "surface": self.surface,
            "location": self.location,
            "encoding": self.encoding,
        }


@dataclass(frozen=True, slots=True)
class ArtifactLeakReport:
    scanned_files: int
    scanned_bytes: int
    leaks: tuple[SecretLeak, ...]
    bounded: bool

    @property
    def clean(self) -> bool:
        return not self.leaks and self.bounded

    def to_dict(self) -> dict[str, Any]:
        return {
            "scanned_files": self.scanned_files,
            "scanned_bytes": self.scanned_bytes,
            "bounded": self.bounded,
            "clean": self.clean,
            "leaks": [item.to_dict() for item in self.leaks],
        }


class SecretTaintGuard:
    """In-memory taint/redaction guard for secret values and common encodings.

    Durable reports contain surfaces/locations only. Raw values and transformed
    secret material are never returned by the reporting API.
    """

    def __init__(self, secrets: KodeSecrets, *, extra_values: Sequence[str] = ()) -> None:
        self.secrets = secrets
        self._extra_values = {value for value in extra_values if value}

    def register(self, value: str) -> None:
        if not value:
            raise ValueError("secret taint value cannot be empty")
        self._extra_values.add(value)

    def _known_values(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                set(self.secrets.known_values()) | self._extra_values,
                key=len,
                reverse=True,
            )
        )

    def _variant_map(self) -> dict[str, str]:
        result: dict[str, str] = {}
        for value in self._known_values():
            variants = _variants(value)
            for index, variant in enumerate(variants):
                if variant:
                    result.setdefault(variant, "raw" if variant == value else f"encoded-{index}")
        return result

    def redact_text(self, text: str) -> str:
        result = str(text)
        for variant in sorted(self._variant_map(), key=len, reverse=True):
            result = result.replace(variant, _REDACTED)
        for pattern in _GENERIC_SECRET_PATTERNS:
            result = pattern.sub(_REDACTED, result)
        return result

    def contains_taint(self, value: Any) -> bool:
        return bool(self.find_leaks(value))

    def find_leaks(self, value: Any, *, surface: str = "payload") -> tuple[SecretLeak, ...]:
        leaks: list[SecretLeak] = []
        variants = self._variant_map()

        def walk(item: Any, location: str, key: str = "") -> None:
            if isinstance(item, SecretRef):
                return
            if key and _SECRET_KEY_RE.search(key) and item not in (None, "", [], {}, ()):
                leaks.append(SecretLeak(surface, location, "sensitive-field"))
            if isinstance(item, Mapping):
                for child_key, child in item.items():
                    name = str(child_key)
                    walk(child, f"{location}.{name}", name)
                return
            if isinstance(item, (list, tuple, set, frozenset)):
                for index, child in enumerate(item):
                    walk(child, f"{location}[{index}]")
                return
            if _is_scalar(item):
                text = "" if item is None else str(item)
                for variant, encoding in variants.items():
                    if variant and variant in text:
                        leaks.append(SecretLeak(surface, location, encoding))
                        break
                else:
                    if any(pattern.search(text) for pattern in _GENERIC_SECRET_PATTERNS):
                        leaks.append(SecretLeak(surface, location, "generic-signature"))
                return
            walk(repr(item), location)

        walk(value, "$")
        return tuple(leaks)

    def sanitize_payload(self, value: Any, *, key: str = "") -> Any:
        if isinstance(value, SecretRef):
            return value.to_dict()
        if key and _SECRET_KEY_RE.search(key) and value not in (None, "", [], {}, ()):
            return _REDACTED
        if isinstance(value, Mapping):
            return {
                str(child_key): self.sanitize_payload(child, key=str(child_key))
                for child_key, child in value.items()
            }
        if isinstance(value, (list, tuple, set, frozenset)):
            return [self.sanitize_payload(child, key=key) for child in value]
        if isinstance(value, str):
            return self.redact_text(value)
        if _is_scalar(value):
            return value
        return self.redact_text(repr(value))

    def sanitize_json(self, value: Any) -> str:
        return json.dumps(self.sanitize_payload(value), ensure_ascii=False, sort_keys=True)

    def assert_no_taint(self, value: Any, *, surface: str = "payload") -> None:
        leaks = self.find_leaks(value, surface=surface)
        if leaks:
            raise PolicyDenied(
                f"Secret-tainted material denied on {surface}: "
                + ", ".join(sorted({item.location for item in leaks}))
            )

    def assert_safe_argv(self, argv: Sequence[str]) -> None:
        self.assert_no_taint(list(argv), surface="argv")

    def assert_safe_environment(self, env: Mapping[str, str]) -> None:
        self.assert_no_taint(dict(env), surface="environment")

    def sanitize_exception(self, exc: BaseException) -> str:
        return self.redact_text(f"{type(exc).__name__}: {exc}")


class EphemeralSecretResolver:
    """Resolve a SecretRef at the narrow use boundary without durable caching."""

    def __init__(self, secrets: KodeSecrets, guard: SecretTaintGuard) -> None:
        self.secrets = secrets
        self.guard = guard

    def resolve(self, ref: SecretRef) -> str:
        value = self.secrets.resolve(ref)
        if value is None:
            raise PolicyDenied(f"Secret reference is unavailable: {ref.namespace}/{ref.key}")
        self.guard.register(value)
        return value

    def materialize_environment(self, refs: Mapping[str, SecretRef]) -> dict[str, str]:
        result: dict[str, str] = {}
        for name, ref in refs.items():
            normalized = str(name).strip()
            if not normalized or any(char in normalized for char in "\r\n=\x00"):
                raise ValueError("invalid environment variable name for secret reference")
            result[normalized] = self.resolve(ref)
        return result


class SecretDestinationPolicy:
    """Block secret-tainted egress unless the destination and use are explicit."""

    def __init__(self, *, approved_hosts: Sequence[str] = (), allow_loopback: bool = True) -> None:
        self.approved_hosts = {host.strip().lower() for host in approved_hosts if host.strip()}
        self.allow_loopback = allow_loopback

    def authorize(
        self,
        destination: str,
        payload: Any,
        guard: SecretTaintGuard,
        *,
        allow_secret_payload: bool = False,
    ) -> None:
        parsed = urlsplit(destination)
        host = (parsed.hostname or "").lower()
        if not host or parsed.scheme.lower() not in {"http", "https"}:
            raise PolicyDenied("Unsupported or ambiguous exfiltration destination")
        if guard.contains_taint(destination):
            raise PolicyDenied("Secret material is forbidden in destination URLs")

        tainted = guard.contains_taint(payload)
        if not tainted:
            return

        approved = host in self.approved_hosts
        if self.allow_loopback and host in {"localhost", "127.0.0.1", "::1"}:
            approved = True
        if not approved or not allow_secret_payload:
            raise PolicyDenied(
                f"Secret-tainted egress denied for destination host: {host or '<unknown>'}"
            )


class SecretAwareProcessSandbox:
    """Resolve secret refs only for process launch and redact captured output."""

    def __init__(
        self,
        sandbox: ProcessSandbox,
        secrets: KodeSecrets,
        guard: SecretTaintGuard | None = None,
    ) -> None:
        self.sandbox = sandbox
        self.secrets = secrets
        self.guard = guard or SecretTaintGuard(secrets)
        self.resolver = EphemeralSecretResolver(secrets, self.guard)

    def run(
        self,
        argv: Sequence[str],
        *,
        cwd: Path | None = None,
        timeout: float = 60.0,
        env: Mapping[str, str] | None = None,
        secret_env: Mapping[str, SecretRef] | None = None,
    ) -> SandboxResult:
        self.guard.assert_safe_argv(argv)
        ordinary_env = dict(env or {})
        self.guard.assert_safe_environment(ordinary_env)
        narrow_secret_env = self.resolver.materialize_environment(secret_env or {})
        combined_env = ordinary_env | narrow_secret_env
        result = self.sandbox.run(argv, cwd=cwd, timeout=timeout, env=combined_env)
        return SandboxResult(
            result.returncode,
            self.guard.redact_text(result.stdout),
            self.guard.redact_text(result.stderr),
            timed_out=result.timed_out,
            cancelled=result.cancelled,
        )


class ArtifactLeakScanner:
    def __init__(
        self,
        guard: SecretTaintGuard,
        *,
        max_files: int = 20_000,
        max_bytes: int = 128 * 1024 * 1024,
    ) -> None:
        if max_files < 1 or max_bytes < 1:
            raise ValueError("artifact scan bounds must be positive")
        self.guard = guard
        self.max_files = max_files
        self.max_bytes = max_bytes

    def scan(self, root: Path) -> ArtifactLeakReport:
        base = root.resolve(strict=False)
        leaks: list[SecretLeak] = []
        scanned_files = 0
        scanned_bytes = 0
        bounded = True

        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            scanned_files += 1
            if scanned_files > self.max_files:
                bounded = False
                break
            size = path.stat().st_size
            if scanned_bytes + size > self.max_bytes:
                bounded = False
                break
            scanned_bytes += size
            data = path.read_bytes()
            text = data.decode("utf-8", errors="ignore")
            relative = path.relative_to(base).as_posix()
            for item in self.guard.find_leaks(text, surface="artifact"):
                leaks.append(SecretLeak("artifact", relative, item.encoding))

        return ArtifactLeakReport(
            scanned_files=scanned_files,
            scanned_bytes=scanned_bytes,
            leaks=tuple(leaks),
            bounded=bounded,
        )

    def require_clean(self, root: Path) -> ArtifactLeakReport:
        report = self.scan(root)
        if not report.bounded:
            raise PolicyDenied("Artifact secret scan exceeded configured bounds")
        if report.leaks:
            raise PolicyDenied(
                "Secret-tainted artifact content detected: "
                + ", ".join(sorted({item.location for item in report.leaks}))
            )
        return report
