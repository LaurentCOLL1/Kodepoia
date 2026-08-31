# R16.2 — Prompt-injection and untrusted-content hardening

## Authority

This document implements the frozen R16.2 scope from `docs/roadmap/R16_PLAN.md`. The repository plan and deterministic security boundaries remain authoritative; natural-language content from repositories, research, documents, web pages, tools, models or durable memory does not become policy merely because it contains instruction-like text.

## Trust contract

R16.2 represents content trust as four separate facts:

- `origin`: where the material came from;
- `level`: trusted, explicit user-authorized, untrusted or unknown;
- `authority`: policy, user intent or data-only;
- `provenance_id`: a deterministic SHA-256 binding for the content/source contract.

External origins (`repository`, `research`, `document`, `web`, `tool_output`, `model_output`, `memory`) are structurally restricted to `untrusted + data_only`. Attempts to deserialize contradictory provenance fail closed. Missing provenance at a content-driven privileged boundary also fails closed.

## Instruction/data separation

External context is rendered with explicit security metadata and an `<UNTRUSTED_DATA>` envelope. The original text remains inspectable and auditable, including suspicious directives, but the envelope is not itself the authorization control. Authorization is enforced independently by `TrustBoundary` and `KodeGuardian`.

A benign README or document may therefore contain ordinary phrases such as “Build Instructions” or `python -m build` and remain usable as data. The same source cannot grant permissions, suppress confirmation, widen filesystem/network scope, rewrite roadmap/policy authority, trigger a privileged tool/process, or gain secret access.

## Consumer boundary

`KodeGuardian` applies the trust boundary before its normal permission and confirmation policy whenever an action is marked `content_driven=true`.

- read/inspection remains possible as data;
- missing or contradictory trust metadata denies privileged effects;
- untrusted/data-only content denies privileged effects even when the caller sets `confirmed=true`;
- explicit user/system authority still passes through the existing `PermissionSet` and Guardian policy, so R16.2 does not replace least-privilege checks.

This prevents model/tool/research text from laundering itself into a permission grant or approval signal.

## Detection is defense-in-depth, not authorization

`ResearchGuard` continues to surface deterministic indicators for audit and now carries explicit provenance. R16.2 adds bounded handling for encoded/nested variants (Base64, URL encoding, HTML normalization, role spoofing and authority-spoof phrases). Detection is deliberately not treated as a complete security boundary: a source remains data-only even if no indicator matches.

This design aligns with current OWASP/NCSC guidance: external content should be segregated, privileged actions should be least-privilege and independently controlled, and authorization must not be delegated to model compliance.

## Acceptance

R16.2 reuses the immutable R16.1 corpus rather than replacing it. The acceptance policy exercises all ten benign/adversarial cases owned by these five R16.1 boundaries:

- prompt/context assembly;
- research/web ingestion;
- repository/workspace ingestion;
- memory/context;
- tool/plugin/MCP capability.

It adds eight immutable synthetic R16.2 controls covering encoded/nested attacks, model/tool outputs, roadmap authority, permission/network/process escalation, and benign README/document instructions.

The exact-source acceptance report binds:

- Git source SHA;
- canonical R16.1 corpus digest and full case-set digest;
- R16.2 targeted case-set digest;
- R16.2 supplemental case-set digest;
- deterministic policy digest;
- per-case payload digests and decisions;
- critical veto and final security-claim status.

No live secret, live malware, destructive host action or production target is used. Manual state is **NONE**.
