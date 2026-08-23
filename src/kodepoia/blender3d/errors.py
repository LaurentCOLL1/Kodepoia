from __future__ import annotations


class BlenderError(RuntimeError):
    """Base error for the governed R10 Blender boundary."""


class BlenderBoundaryError(BlenderError):
    """Raised when an executable, path, recipe or process policy is rejected."""


class BlenderProtocolError(BlenderError):
    """Raised when persisted R10 data is malformed or non-canonical."""


class BlenderVersionError(BlenderError):
    """Raised when a Blender runtime/version is unsupported by the active profile."""
