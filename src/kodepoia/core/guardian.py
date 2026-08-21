from __future__ import annotations

from .audit import AuditEvent, AuditLog
from .permissions import PermissionPolicy
from .types import ActionRequest, DecisionStatus, GuardianDecision, RiskLevel


class GuardianError(RuntimeError):
    pass


class KodeGuardian:
    """Non-bypassable decision point. It decides; it never executes actions."""

    def __init__(self, policy: PermissionPolicy, audit: AuditLog | None = None) -> None:
        self._policy = policy
        self._audit = audit
        self._stopped = False

    @property
    def stopped(self) -> bool:
        return self._stopped

    def kill_switch(self, actor: str = "user") -> None:
        self._stopped = True
        self._record("guardian.kill_switch", actor, "stopped", None, {})

    def reset_kill_switch(self, actor: str = "user") -> None:
        self._stopped = False
        self._record("guardian.kill_switch", actor, "reset", None, {})

    def evaluate(self, request: ActionRequest) -> GuardianDecision:
        if self._stopped:
            decision = GuardianDecision(DecisionStatus.DENY, RiskLevel.CRITICAL, "global kill switch is active", request.request_id, "global-kill-switch")
            self._audit_decision(request, decision)
            return decision
        rule = self._policy.find_rule(request)
        if rule is None:
            decision = GuardianDecision(DecisionStatus.DENY, RiskLevel.CRITICAL, "no matching capability rule; KodeGuardian is default-deny", request.request_id, "default-deny")
        else:
            decision = GuardianDecision(rule.status, rule.risk, rule.reason, request.request_id, rule.rule_id, requires_snapshot=rule.requires_snapshot)
        self._audit_decision(request, decision)
        return decision

    def require_allowed(self, request: ActionRequest, *, confirmed: bool = False) -> GuardianDecision:
        decision = self.evaluate(request)
        if decision.status is DecisionStatus.DENY:
            raise GuardianError(decision.reason)
        if decision.status is DecisionStatus.CONFIRM and not confirmed:
            raise GuardianError("explicit confirmation is required: " + decision.reason)
        return decision

    def _audit_decision(self, request: ActionRequest, decision: GuardianDecision) -> None:
        self._record("guardian.decision", request.actor, decision.status.value, request.request_id, {"kind": request.kind.value, "target": request.target, "risk": decision.risk.value, "rule_id": decision.rule_id, "requires_snapshot": decision.requires_snapshot, "reason": decision.reason})

    def _record(self, event_type: str, actor: str, outcome: str, request_id: str | None, details: dict) -> None:
        if self._audit is not None:
            self._audit.append(AuditEvent(event_type, actor, outcome, request_id, details))
