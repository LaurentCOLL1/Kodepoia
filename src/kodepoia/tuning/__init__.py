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
from .topology import (
    AcceleratorDevice,
    AcceleratorTopologyReport,
    ObservedAcceleratorTopology,
    ProviderAcceleratorRequest,
    SingleGpuSelection,
    TopologyDisposition,
    evaluate_single_gpu_selection,
)
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
    "AcceleratorDevice",
    "AcceleratorTopologyReport",
    "CapabilityReport",
    "CapabilityState",
    "CheckpointRecord",
    "DTypeName",
    "DatasetBinding",
    "HostResourceProbe",
    "LoraTrainingConfig",
    "ModelBinding",
    "ObservedAcceleratorTopology",
    "ProviderAcceleratorRequest",
    "QuantizationMode",
    "ResourceRequest",
    "RuntimeDisposition",
    "RuntimeRequest",
    "SFTTrainingConfig",
    "SeedConfig",
    "SingleGpuSelection",
    "TopologyDisposition",
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
    "evaluate_single_gpu_selection",
    "redact_runtime_text",
]
