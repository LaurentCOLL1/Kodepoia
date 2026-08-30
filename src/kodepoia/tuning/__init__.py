"""R15.8 optional training-runtime capability boundary.

Heavy ML packages are intentionally not imported here. They are capability-probed
only inside the isolated probe worker launched by :class:`TrainingRuntime`.
"""

from .contracts import (
    CapabilityReport,
    CapabilityState,
    DTypeName,
    QuantizationMode,
    ResourceRequest,
    RuntimeDisposition,
    RuntimeRequest,
    SeedConfig,
    TrainingBackend,
    TuningRuntimeError,
)
from .runtime import HostResourceProbe, TrainingRuntime, redact_runtime_text

__all__ = [
    "CapabilityReport",
    "CapabilityState",
    "DTypeName",
    "HostResourceProbe",
    "QuantizationMode",
    "ResourceRequest",
    "RuntimeDisposition",
    "RuntimeRequest",
    "SeedConfig",
    "TrainingBackend",
    "TrainingRuntime",
    "TuningRuntimeError",
    "redact_runtime_text",
]
