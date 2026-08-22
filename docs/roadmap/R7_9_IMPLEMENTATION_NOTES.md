# R7.9 implementation notes — cache semantics references

These notes are non-normative implementation context. Kodepoia R7.9 is not an HTTP cache, but it deliberately borrows conservative cache-selection and revalidation principles from RFC 9111 without importing HTTP semantics that do not apply.

- A stored response and a fresh response are distinct concepts; reuse eligibility and source freshness are not equivalent.
- Cache selection depends on the dimensions that can change the selected representation. R7.9 therefore keys normalized query/scope/source/target-version/version-evidence/policy dimensions, while keeping one invocation's `request_id` as provenance rather than selection identity.
- Stale mutable evidence requires explicit revalidation before its cache age can be advanced.
- Revalidation must not silently replace source/version/content identity; changed identity invalidates the derived cache entry.

R7.9 additionally applies Kodepoia-specific trust boundaries that are stricter than generic HTTP caching: guarded external research remains external/untrusted in Context and project-scoped Memory, and cache reuse never promotes it to validated global Experience.
