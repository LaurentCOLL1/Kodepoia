"""Kodepoia domain exceptions."""

class KodepoiaError(Exception):
    """Base exception."""


class PolicyDenied(KodepoiaError):
    """Raised when KodeGuardian denies an action."""


class PermissionDenied(KodepoiaError):
    """Raised when a permission is not granted."""


class SchemaError(KodepoiaError):
    """Raised when a schema or migration is invalid."""


class BrainUnavailable(KodepoiaError):
    """Raised when the configured local model runtime is unavailable."""
