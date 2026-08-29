from pathlib import Path

PATH = Path("src/kodepoia/backend/liveops.py")
text = PATH.read_text(encoding="utf-8")


def replace_once(old: str, new: str, label: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected exactly one occurrence, found {count}")
    text = text.replace(old, new, 1)


replace_once(
    "from typing import Any, Callable, Iterable\n",
    "from typing import Any, Callable\n",
    "typing imports",
)
replace_once(
    "from .entitlements import CatalogProductDefinition\n",
    "from .entitlements import BillingEnvironment, CatalogProductDefinition\n",
    "billing import",
)

start = text.index("@dataclass(frozen=True, slots=True)\nclass CatalogProductReference:")
end = text.index("@dataclass(frozen=True, slots=True)\nclass EventContractReference:", start)
text = text[:start] + '''@dataclass(frozen=True, slots=True)
class CatalogProductReference:
    product_id: str
    version: int
    entitlement_id: str
    digest: str
    billing_environment: BillingEnvironment

    def __post_init__(self) -> None:
        object.__setattr__(self, "product_id", _stable_id(self.product_id, field="product_id"))
        _positive_int(self.version, field="product_version")
        object.__setattr__(self, "entitlement_id", _stable_id(self.entitlement_id, field="entitlement_id"))
        object.__setattr__(self, "digest", _sha256(self.digest, field="product_digest"))
        if not isinstance(self.billing_environment, BillingEnvironment):
            raise LiveOpsPolicyError("invalid_billing_environment")

    @classmethod
    def from_product(cls, product: CatalogProductDefinition) -> CatalogProductReference:
        if not isinstance(product, CatalogProductDefinition):
            raise LiveOpsPolicyError("invalid_catalog_product")
        return cls(
            product.product_id,
            product.version,
            product.entitlement_id,
            product.digest(),
            product.environment,
        )

    def canonical(self) -> dict[str, Any]:
        return {
            "product_id": self.product_id,
            "version": self.version,
            "entitlement_id": self.entitlement_id,
            "digest": self.digest,
            "billing_environment": self.billing_environment.value,
        }


''' + text[end:]

replace_once(
'''        refs: Iterable[Any] = (self.config_snapshot, self.content_manifest, *products, *events)
        if any(item.environment is not environment for item in refs):
            raise LiveOpsPolicyError("campaign_environment_mismatch")
''',
'''        backend_refs = (self.config_snapshot, self.content_manifest, *events)
        if any(item.environment is not environment for item in backend_refs):
            raise LiveOpsPolicyError("campaign_environment_mismatch")
        if environment is BackendEnvironmentKind.PRODUCTION:
            if any(item.billing_environment is not BillingEnvironment.PRODUCTION for item in products):
                raise LiveOpsPolicyError("production_campaign_requires_production_billing")
        elif any(item.billing_environment is BillingEnvironment.PRODUCTION for item in products):
            raise LiveOpsPolicyError("nonproduction_campaign_rejects_production_billing")
''',
    "campaign environment boundary",
)
replace_once(
    "self._catalog_dependencies: dict[tuple[BackendEnvironmentKind, str, int], tuple[str, str]] = {}",
    "self._catalog_dependencies: dict[tuple[BillingEnvironment, str, int], tuple[str, str]] = {}",
    "catalog registry key type",
)
replace_once(
    "key = (ref.environment, ref.product_id, ref.version)\n        value = (ref.entitlement_id, ref.digest)",
    "key = (ref.billing_environment, ref.product_id, ref.version)\n        value = (ref.entitlement_id, ref.digest)",
    "catalog registration key",
)
replace_once(
    "key = (campaign.environment, product.product_id, product.version)\n            if self._catalog_dependencies.get(key) != (product.entitlement_id, product.digest):",
    "key = (product.billing_environment, product.product_id, product.version)\n            if self._catalog_dependencies.get(key) != (product.entitlement_id, product.digest):",
    "catalog dependency validation key",
)

preview_start = text.index("@dataclass(frozen=True, slots=True)\nclass LiveOpsPreview:")
preview_end = text.index("@dataclass(frozen=True, slots=True)\nclass LiveOpsApproval:", preview_start)
text = text[:preview_start] + '''@dataclass(frozen=True, slots=True)
class LiveOpsPreview:
    preview_id: str
    campaign_id: str
    campaign_version: int
    campaign_digest: str
    environment: BackendEnvironmentKind
    dependency_digest: str
    expected_state: LiveOpsCampaignState
    current_state: LiveOpsCampaignState
    evaluated_at_ms: int
    mutation_count: int = 0

    def binding_canonical(self) -> dict[str, Any]:
        return {
            "preview_id": self.preview_id,
            "campaign_id": self.campaign_id,
            "campaign_version": self.campaign_version,
            "campaign_digest": self.campaign_digest,
            "environment": self.environment.value,
            "dependency_digest": self.dependency_digest,
            "expected_state": self.expected_state.value,
            "current_state": self.current_state.value,
            "mutation_count": self.mutation_count,
        }

    def canonical(self) -> dict[str, Any]:
        payload = self.binding_canonical()
        payload["evaluated_at_ms"] = self.evaluated_at_ms
        return payload

    def digest(self) -> str:
        return canonical_sha256(self.binding_canonical())


''' + text[preview_end:]

preview_method_start = text.index("    def preview_campaign(")
approve_method_start = text.index("    def approve_campaign(", preview_method_start)
text = text[:preview_method_start] + '''    def _build_preview(self, campaign: LiveOpsCampaignDefinition) -> LiveOpsPreview:
        dependency_digest = self._validate_dependencies(campaign)
        now_ms = _server_now_ms(self.clock_ms)
        current_state = self._current_state(campaign)
        expected_state = self._expected_state(campaign, now_ms)
        binding_seed = {
            "campaign_digest": campaign.digest(),
            "dependency_digest": dependency_digest,
            "expected_state": expected_state.value,
            "current_state": current_state.value,
        }
        return LiveOpsPreview(
            preview_id=f"liveops.preview.{canonical_sha256(binding_seed)[:24]}",
            campaign_id=campaign.campaign_id,
            campaign_version=campaign.version,
            campaign_digest=campaign.digest(),
            environment=campaign.environment,
            dependency_digest=dependency_digest,
            expected_state=expected_state,
            current_state=current_state,
            evaluated_at_ms=now_ms,
            mutation_count=0,
        )

    def preview_campaign(self, actor: AuthorityActorContext, *, campaign_id: str, version: int) -> LiveOpsPreview:
        campaign_id = _stable_id(campaign_id, field="campaign_id")
        self._authorize(actor, "liveops.campaign.preview", campaign_id)
        return self._build_preview(self.campaign(campaign_id, version))

''' + text[approve_method_start:]

approve_start = text.index("    def approve_campaign(")
approve_end = text.index("    def _validated_approval(", approve_start)
text = text[:approve_start] + '''    def approve_campaign(
        self,
        actor: AuthorityActorContext,
        *,
        preview: LiveOpsPreview,
        approval_id: str,
        safe_change_digest: str,
    ) -> LiveOpsApproval:
        if not isinstance(preview, LiveOpsPreview):
            raise LiveOpsPolicyError("invalid_preview")
        approval_id = _stable_id(approval_id, field="approval_id")
        safe_change_digest = _sha256(safe_change_digest, field="safe_change_digest")
        self._authorize(actor, "liveops.campaign.approve", preview.campaign_id)
        campaign = self.campaign(preview.campaign_id, preview.campaign_version)
        current = self._build_preview(campaign)
        if current.digest() != preview.digest():
            raise LiveOpsStateError("stale_preview")
        with self._lock:
            existing = self._approvals.get(approval_id)
            if existing is not None:
                if (
                    existing.preview_digest != preview.digest()
                    or existing.campaign_digest != preview.campaign_digest
                    or existing.safe_change_digest != safe_change_digest
                    or existing.approver_account_id != actor.account_id
                ):
                    raise LiveOpsStateError("approval_id_rebind")
                return existing
            if len(self._audit) >= self.max_audit_records:
                raise LiveOpsCapacityError("audit_capacity")
            approval = LiveOpsApproval(
                approval_id=approval_id,
                preview_digest=preview.digest(),
                campaign_digest=preview.campaign_digest,
                safe_change_digest=safe_change_digest,
                approver_account_id=actor.account_id,
                approved_at_ms=_server_now_ms(self.clock_ms),
            )
            self._approvals[approval.approval_id] = approval
            self._append_audit(
                actor=actor,
                action="campaign_approved",
                campaign=campaign,
                state=LiveOpsCampaignState.APPROVED,
                safe_change_digest=approval.safe_change_digest,
            )
            return approval

''' + text[approve_end:]

replace_once(
'''        preview = self.preview_campaign(actor, campaign_id=campaign.campaign_id, version=campaign.version)
        if approval.preview_digest != preview.digest() or approval.campaign_digest != campaign.digest():
''',
'''        preview = self._build_preview(campaign)
        if approval.preview_digest != preview.digest() or approval.campaign_digest != campaign.digest():
''',
    "approval internal preview",
)

activation_start = text.index("    def activate_campaign(")
activation_end = text.index("    def runtime(", activation_start)
text = text[:activation_start] + '''    def activate_campaign(
        self,
        actor: AuthorityActorContext,
        *,
        campaign_id: str,
        version: int,
        activation_id: str,
        approval: LiveOpsApproval,
    ) -> LiveOpsActivationRecord:
        campaign_id = _stable_id(campaign_id, field="campaign_id")
        activation_id = _stable_id(activation_id, field="activation_id")
        self._authorize(actor, "liveops.campaign.activate", campaign_id)
        campaign = self.campaign(campaign_id, version)
        with self._lock:
            existing = self._activations.get(activation_id)
            if existing is not None:
                if (
                    not isinstance(approval, LiveOpsApproval)
                    or self._approvals.get(approval.approval_id) != approval
                    or existing.campaign_id != campaign.campaign_id
                    or existing.campaign_version != campaign.version
                    or existing.campaign_digest != campaign.digest()
                    or existing.approval_digest != approval.digest()
                    or existing.safe_change_digest != approval.safe_change_digest
                ):
                    raise LiveOpsStateError("activation_id_rebind")
                return existing
        self._validate_dependencies(campaign)
        checked, _preview = self._validated_approval(actor=actor, campaign=campaign, approval=approval)
        now_ms = _server_now_ms(self.clock_ms)
        if now_ms >= campaign.schedule.end_at_utc_ms:
            raise LiveOpsStateError("campaign_window_expired")
        state = LiveOpsCampaignState.SCHEDULED if now_ms < campaign.schedule.start_at_utc_ms else LiveOpsCampaignState.ACTIVE
        record = LiveOpsActivationRecord(
            activation_id=activation_id,
            campaign_id=campaign.campaign_id,
            campaign_version=campaign.version,
            campaign_digest=campaign.digest(),
            approval_digest=checked.digest(),
            state=state,
            activated_at_ms=now_ms,
            safe_change_digest=checked.safe_change_digest,
        )
        with self._lock:
            if len(self._activations) >= self.max_activations:
                raise LiveOpsCapacityError("activation_capacity")
            if len(self._audit) >= self.max_audit_records:
                raise LiveOpsCapacityError("audit_capacity")
            if len(self._trace) >= self.max_trace_records:
                raise LiveOpsCapacityError("trace_capacity")
            key = (campaign.campaign_id, campaign.version)
            runtime = self._runtime.get(key)
            if runtime is not None and runtime.activation_id != activation_id and runtime.state not in {
                LiveOpsCampaignState.EXPIRED,
                LiveOpsCampaignState.ROLLED_BACK,
                LiveOpsCampaignState.KILLED,
            }:
                raise LiveOpsStateError("campaign_already_activated")
            self._activations[activation_id] = record
            self._runtime[key] = LiveOpsRuntimeRecord(
                campaign_id=campaign.campaign_id,
                campaign_version=campaign.version,
                activation_id=activation_id,
                state=state,
                updated_at_ms=now_ms,
                transition_sequence=1,
            )
            self._append_audit(
                actor=actor,
                action="campaign_scheduled" if state is LiveOpsCampaignState.SCHEDULED else "campaign_activated",
                campaign=campaign,
                state=state,
                activation_id=activation_id,
                safe_change_digest=checked.safe_change_digest,
            )
            self._append_trace(
                {
                    "event": "campaign_activation",
                    "campaign_id": campaign.campaign_id,
                    "campaign_version": campaign.version,
                    "activation_id": activation_id,
                    "state": state.value,
                    "campaign_digest": campaign.digest(),
                    "approval_digest": checked.digest(),
                    "safe_change_digest": checked.safe_change_digest,
                }
            )
            return record

''' + text[activation_end:]

replace_once(
'''        key = (campaign.campaign_id, campaign.version)
        current = self.runtime(campaign.campaign_id, campaign.version)
        now_ms = _server_now_ms(self.clock_ms)
        next_record = replace(
''',
'''        key = (campaign.campaign_id, campaign.version)
        current = self.runtime(campaign.campaign_id, campaign.version)
        now_ms = _server_now_ms(self.clock_ms)
        if len(self._audit) >= self.max_audit_records:
            raise LiveOpsCapacityError("audit_capacity")
        if len(self._trace) >= self.max_trace_records:
            raise LiveOpsCapacityError("trace_capacity")
        next_record = replace(
''',
    "transition capacity preflight",
)

advance_start = text.index("    def advance_campaign(")
pause_start = text.index("    def pause_campaign(", advance_start)
text = text[:advance_start] + '''    def _advance_campaign(
        self,
        actor: AuthorityActorContext,
        campaign: LiveOpsCampaignDefinition,
    ) -> LiveOpsRuntimeRecord:
        current = self.runtime(campaign.campaign_id, campaign.version)
        now_ms = _server_now_ms(self.clock_ms)
        if current.state in {LiveOpsCampaignState.ROLLED_BACK, LiveOpsCampaignState.KILLED, LiveOpsCampaignState.EXPIRED}:
            return current
        if now_ms >= campaign.schedule.end_at_utc_ms:
            return self._transition(actor=actor, campaign=campaign, state=LiveOpsCampaignState.EXPIRED, action="campaign_expired")
        if current.state is LiveOpsCampaignState.SCHEDULED and now_ms >= campaign.schedule.start_at_utc_ms:
            return self._transition(actor=actor, campaign=campaign, state=LiveOpsCampaignState.ACTIVE, action="campaign_activated")
        return current

    def advance_campaign(self, actor: AuthorityActorContext, *, campaign_id: str, version: int) -> LiveOpsRuntimeRecord:
        campaign_id = _stable_id(campaign_id, field="campaign_id")
        self._authorize(actor, "liveops.campaign.advance", campaign_id)
        return self._advance_campaign(actor, self.campaign(campaign_id, version))

''' + text[pause_start:]
replace_once(
    "current = self.advance_campaign(actor, campaign_id=campaign_id, version=version)",
    "current = self._advance_campaign(actor, campaign)",
    "pause internal advance",
)

replace_once(
'''            self._campaigns[key] = campaign
            self._append_trace(
''',
'''            if len(self._trace) >= self.max_trace_records:
                raise LiveOpsCapacityError("trace_capacity")
            self._campaigns[key] = campaign
            self._append_trace(
''',
    "campaign trace capacity preflight",
)

replace_once(
'''                "catalog": sorted((env.value, identity, version, entitlement, digest) for (env, identity, version), (entitlement, digest) in self._catalog_dependencies.items()),
''',
'''                "catalog": sorted((billing_env.value, identity, version, entitlement, digest) for (billing_env, identity, version), (entitlement, digest) in self._catalog_dependencies.items()),
''',
    "catalog snapshot environment label",
)

PATH.write_text(text, encoding="utf-8", newline="\n")
