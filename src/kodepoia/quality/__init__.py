"""Quality, health, budget, test, regression, visual QA, accessibility, localization, debt, CI, build, security, privacy, license/BOM and patch-gate primitives."""

from kodepoia.quality.accessibility import (
    AccessibilityReport, AccessibilityReportStatus, AccessibilityResult, AccessibilitySeverity,
    AccessibilityStatus, AccessibilityStore, KodeAccessibility,
)
from kodepoia.quality.budget import (
    BudgetConstraint, BudgetDirection, BudgetMetric, BudgetMetricResult, BudgetObservation,
    BudgetReport, BudgetStatus, BudgetStore, KodeBudget, PlatformBudgetSpec,
)
from kodepoia.quality.build import (
    BuildArtifact, BuildArtifactKind, BuildManifest, BuildStatus, BuildStore, KodeBuild,
    collect_python_artifacts, dependency_input_digests, hash_source_inputs, redact_sensitive,
)
from kodepoia.quality.ci import CICheck, CICheckStatus, CIReport, CIReportStatus, CIStore, KodeCI
from kodepoia.quality.health import (
    HealthDimension, HealthMetric, HealthPolicy, HealthReport, HealthStatus, HealthStore, KodeHealth,
)
from kodepoia.quality.license_bom import (
    SPDX_BASELINE, SPDX_JSONLD_CONTEXT, SPDX_SERIALIZATION_VERSION, BomComponent, BomReport, BomStatus,
    BomStore, ComponentKind, ComponentResolution, DependencyRequirement, IntegrityEvidence,
    IntegrityStatus, KodeBOM, KodeLicense, LicenseAssertion, LicenseAssertionState, LicenseDecision,
    LicensePolicy, LicensePolicyAction, LicensePolicyRule, LicenseReport, LicenseReportStatus,
    LicenseStore, canonical_python_name, normalize_spdx_expression,
)
from kodepoia.quality.localization import (
    KodeLocalization, LocaleCatalog, LocalizationReport, LocalizationResult, LocalizationSeverity,
    LocalizationStatus, LocalizationStore, LocalizedMessage, pseudo_catalog, pseudo_localize_text,
)
from kodepoia.quality.patch_gate import (
    ClassificationResult, GateEvidence, GateEvidenceStatus, GateRequirement, IntegrationEvidenceStatus,
    KodePatchGate, PatchChange, PatchClassification, PatchDomain, PatchGateReport, PatchGateStatus,
    PatchGateStore, PatchOperation, PatchRisk, R6IntegrationReport, R6SubdivisionEvidence,
    RehearsalStatus, RollbackMethod, RollbackRehearsalEvidence, RollbackStrategy, ValidationGate,
    rehearse_fixture_rollback,
)
from kodepoia.quality.privacy import (
    DeclarationValue, KodePrivacy, PrivacyApplicability, PrivacyBasisState, PrivacyCheckStatus,
    PrivacyDataItem, PrivacyDisposition, PrivacyIssue, PrivacyReport, PrivacyReportStatus,
    PrivacySensitivity, PrivacySeverity, PrivacyStore, StoreKind, StorePrivacyDeclaration,
    redact_privacy_evidence,
)
from kodepoia.quality.regression import (
    KodeRegression, RegressionChange, RegressionEntry, RegressionReport, RegressionStatus, RegressionStore,
)
from kodepoia.quality.security import (
    DependencySecurityStatus, DependencyVulnerabilityEvidence, KodeAppSecurity, ResidualRisk,
    SecurityApplicability, SecurityCategory, SecurityCheckStatus, SecurityEntryPoint, SecurityReport,
    SecurityReportStatus, SecurityRequirement, SecuritySeverity, SecurityStore, Threat, ThreatAsset,
    ThreatModel, TrustBoundary, applicable_requirement, kodepoia_threat_model,
    not_applicable_requirement, secure_storage_requirement,
)
from kodepoia.quality.technical_debt import (
    DebtCategory, DebtReference, DebtReferenceKind, DebtSeverity, DebtState, KodeTechnicalDebt,
    TechnicalDebtItem, TechnicalDebtReport, TechnicalDebtStatus, TechnicalDebtStore,
)
from kodepoia.quality.tests import (
    KodeTests, TestCaseResult, TestCaseStatus, TestRunReport, TestRunStatus, TestRunStore,
)
from kodepoia.quality.visual import (
    KodeVisualQA, VisualBaselineApproval, VisualImage, VisualMask, VisualMetrics, VisualPolicy,
    VisualReport, VisualStatus, VisualStore,
)

__all__ = [
    "AccessibilityReport", "AccessibilityReportStatus", "AccessibilityResult", "AccessibilitySeverity",
    "AccessibilityStatus", "AccessibilityStore", "BomComponent", "BomReport", "BomStatus", "BomStore",
    "BuildArtifact", "BuildArtifactKind", "BuildManifest", "BuildStatus", "BuildStore",
    "BudgetConstraint", "BudgetDirection", "BudgetMetric", "BudgetMetricResult", "BudgetObservation",
    "BudgetReport", "BudgetStatus", "BudgetStore", "CICheck", "CICheckStatus", "CIReport",
    "CIReportStatus", "CIStore", "ClassificationResult", "ComponentKind", "ComponentResolution",
    "DebtCategory", "DebtReference", "DebtReferenceKind", "DebtSeverity", "DebtState",
    "DeclarationValue", "DependencyRequirement", "DependencySecurityStatus",
    "DependencyVulnerabilityEvidence", "GateEvidence", "GateEvidenceStatus", "GateRequirement",
    "HealthDimension", "HealthMetric", "HealthPolicy", "HealthReport", "HealthStatus", "HealthStore",
    "IntegrationEvidenceStatus", "IntegrityEvidence", "IntegrityStatus", "KodeAccessibility",
    "KodeAppSecurity", "KodeBOM", "KodeBuild", "KodeBudget", "KodeCI", "KodeHealth", "KodeLicense",
    "KodeLocalization", "KodePatchGate", "KodePrivacy", "KodeRegression", "KodeTechnicalDebt",
    "KodeTests", "KodeVisualQA", "LicenseAssertion", "LicenseAssertionState", "LicenseDecision",
    "LicensePolicy", "LicensePolicyAction", "LicensePolicyRule", "LicenseReport", "LicenseReportStatus",
    "LicenseStore", "LocaleCatalog", "LocalizationReport", "LocalizationResult",
    "LocalizationSeverity", "LocalizationStatus", "LocalizationStore", "LocalizedMessage",
    "PatchChange", "PatchClassification", "PatchDomain", "PatchGateReport", "PatchGateStatus",
    "PatchGateStore", "PatchOperation", "PatchRisk", "PlatformBudgetSpec", "PrivacyApplicability",
    "PrivacyBasisState", "PrivacyCheckStatus", "PrivacyDataItem", "PrivacyDisposition", "PrivacyIssue",
    "PrivacyReport", "PrivacyReportStatus", "PrivacySensitivity", "PrivacySeverity", "PrivacyStore",
    "R6IntegrationReport", "R6SubdivisionEvidence", "RegressionChange", "RegressionEntry",
    "RegressionReport", "RegressionStatus", "RegressionStore", "RehearsalStatus", "ResidualRisk",
    "RollbackMethod", "RollbackRehearsalEvidence", "RollbackStrategy", "SPDX_BASELINE",
    "SPDX_JSONLD_CONTEXT", "SPDX_SERIALIZATION_VERSION", "SecurityApplicability", "SecurityCategory",
    "SecurityCheckStatus", "SecurityEntryPoint", "SecurityReport", "SecurityReportStatus",
    "SecurityRequirement", "SecuritySeverity", "SecurityStore", "StoreKind", "StorePrivacyDeclaration",
    "TechnicalDebtItem", "TechnicalDebtReport", "TechnicalDebtStatus", "TechnicalDebtStore",
    "TestCaseResult", "TestCaseStatus", "TestRunReport", "TestRunStatus", "TestRunStore", "Threat",
    "ThreatAsset", "ThreatModel", "TrustBoundary", "ValidationGate", "VisualBaselineApproval",
    "VisualImage", "VisualMask", "VisualMetrics", "VisualPolicy", "VisualReport", "VisualStatus",
    "VisualStore", "applicable_requirement", "canonical_python_name", "collect_python_artifacts",
    "dependency_input_digests", "hash_source_inputs", "kodepoia_threat_model",
    "normalize_spdx_expression", "not_applicable_requirement", "pseudo_catalog", "pseudo_localize_text",
    "redact_privacy_evidence", "redact_sensitive", "rehearse_fixture_rollback",
    "secure_storage_requirement",
]
