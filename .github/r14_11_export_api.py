from pathlib import Path

path = Path("src/kodepoia/backend/__init__.py")
text = path.read_text(encoding="utf-8")
import_anchor = "from .postgres import (\n"
import_block = '''from .remote_config import (
    ActivationApproval,
    ActivationPreview,
    ConfigAuditRecord,
    ConfigSnapshot,
    EvaluationContext,
    EvaluationErrorCode,
    EvaluationReason,
    EvaluationResult,
    FeatureFlagDefinition,
    FlagPrerequisite,
    FlagValueType,
    FlagVariant,
    InMemoryRemoteConfigService,
    OpenFeatureRemoteConfigAdapter,
    RemoteConfigAuthorizationError,
    RemoteConfigCapacityError,
    RemoteConfigPolicyError,
    RemoteConfigStateError,
    RemoteConfigStateSnapshot,
    RolloutAllocation,
    RolloutPlan,
    TargetingOperator,
    TargetingRule,
)
'''
assert text.count(import_anchor) == 1, text.count(import_anchor)
assert "from .remote_config import (" not in text
text = text.replace(import_anchor, import_block + import_anchor)

all_anchor = '    "BillingEnvironment",\n'
all_block = '''    "ActivationApproval",
    "ActivationPreview",
    "ConfigAuditRecord",
    "ConfigSnapshot",
    "EvaluationContext",
    "EvaluationErrorCode",
    "EvaluationReason",
    "EvaluationResult",
    "FeatureFlagDefinition",
    "FlagPrerequisite",
    "FlagValueType",
    "FlagVariant",
    "InMemoryRemoteConfigService",
    "OpenFeatureRemoteConfigAdapter",
    "RemoteConfigAuthorizationError",
    "RemoteConfigCapacityError",
    "RemoteConfigPolicyError",
    "RemoteConfigStateError",
    "RemoteConfigStateSnapshot",
    "RolloutAllocation",
    "RolloutPlan",
    "TargetingOperator",
    "TargetingRule",
'''
assert text.count(all_anchor) == 1, text.count(all_anchor)
assert '    "InMemoryRemoteConfigService",\n' not in text
text = text.replace(all_anchor, all_block + all_anchor)
path.write_text(text, encoding="utf-8")
