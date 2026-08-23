from __future__ import annotations


class ComfyError(RuntimeError):
    """Base error for the governed ComfyUI integration."""


class ComfyBoundaryError(ComfyError):
    """Raised when an endpoint or transport boundary would be crossed."""


class ComfyUnavailableError(ComfyError):
    """Raised when the accepted local ComfyUI service is unavailable."""


class ComfySubmissionAmbiguousError(ComfyUnavailableError):
    """Raised when a prompt POST may have reached ComfyUI but no response was obtained."""


class ComfyProtocolError(ComfyError):
    """Raised when ComfyUI protocol evidence is malformed or contradictory."""


class ComfyVersionError(ComfyError):
    """Raised when a persisted R9 contract version is unsupported."""


class ComfyResourceError(ComfyError):
    """Raised when a bounded local resource requirement cannot be satisfied."""


class ComfyGovernanceError(ComfyError):
    """Raised when an R9 operation is blocked by governance policy."""
