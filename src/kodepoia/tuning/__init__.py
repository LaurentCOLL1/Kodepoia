"""R15.8/R15.9 optional training capability and governed adapter-training boundary.

Heavy ML packages are intentionally not imported here. They are capability-probed or
loaded only inside isolated workers launched by :class:`TrainingRuntime` or
:class:`TrainingRunner`.
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
from .training import (
    CheckpointRecord,
    DatasetBinding,
    LoraTrainingConfig,
    ModelBinding,
    SFTTrainingConfig,
    TrainingAuthorization,
    TrainingError,
    TrainingMode,
    TrainingPlan,
    TrainingReport,
    TrainingRunner,
    TrainingRunState,
)

__all__ = [
    "CapabilityReport",
    "CapabilityState",
    "CheckpointRecord",
    "DTypeName",
    "DatasetBinding",
    "HostResourceProbe",
    "LoraTrainingConfig",
    "ModelBinding",
    "QuantizationMode",
    "ResourceRequest",
    "RuntimeDisposition",
    "RuntimeRequest",
    "SFTTrainingConfig",
    "SeedConfig",
    "TrainingAuthorization",
    "TrainingBackend",
    "TrainingError",
    "TrainingMode",
    "TrainingPlan",
    "TrainingReport",
    "TrainingRunState",
    "TrainingRunner",
    "TrainingRuntime",
    "TuningRuntimeError",
    "redact_runtime_text",
]
