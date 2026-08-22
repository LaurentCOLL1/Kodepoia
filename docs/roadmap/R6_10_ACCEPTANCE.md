# R6.10 — KodePrivacy baseline — Acceptance

**Status:** IN PROGRESS  
**Parent plan:** `docs/roadmap/R6_PLAN.md`  
**Starting normalized main:** `4df229e431d2d54e4268607f38bac4045ac590d1`  
**Manual intervention:** NONE

R6.10 is COMPLETE only after the exact final implementation head passes required hosted gates, the implementation PR merges, and post-merge plan/status/continuity normalization is CI-green and merged.

## Acceptance matrix

| Gate | Required | Current |
| --- | --- | --- |
| stable privacy data-category IDs | yes | IMPLEMENTED |
| explicit `collected` / `none` / `not_applicable` | yes | IMPLEMENTED |
| collected source/purpose/storage/retention/deletion required | yes | IMPLEMENTED |
| `none/not_applicable` rationale required | yes | IMPLEMENTED |
| collection lifecycle forbidden on none/N/A | yes | IMPLEMENTED |
| sensitivity explicit, unknown preserved | yes | IMPLEMENTED |
| legal/consent basis remains declared/unspecified/N/A | yes | IMPLEMENTED |
| no legal basis inferred from silence | yes | IMPLEMENTED |
| declared basis requires provenance | yes | IMPLEMENTED |
| explicit inventory-completeness evidence | yes | IMPLEMENTED |
| complete inventory requires review provenance | yes | IMPLEMENTED |
| incomplete inventory cannot PASS | yes | IMPLEMENTED |
| privacy issue applicability/status/severity | yes | IMPLEMENTED |
| privacy N/A never PASS | yes | IMPLEMENTED |
| N/A neutral in aggregate score | yes | IMPLEMENTED |
| all-N/A evidence remains UNKNOWN | yes | IMPLEMENTED |
| measured privacy issue requires evidence provenance | yes | IMPLEMENTED |
| only FAIL can block | yes | IMPLEMENTED |
| Apple declaration preparation fields | yes | IMPLEMENTED |
| Google Play Data safety preparation fields | yes | IMPLEMENTED |
| explicit declaration yes/no/unknown/N/A | yes | IMPLEMENTED |
| store/platform mismatch fails closed | yes | IMPLEMENTED |
| declaration cannot contradict inventory | yes | IMPLEMENTED |
| declaration readiness derived and tamper checked | yes | IMPLEMENTED |
| N/A declaration is R6.3 SKIP even when structurally ready | yes | IMPLEMENTED |
| recursive secret/personal evidence redaction | yes | IMPLEMENTED |
| canonical report SHA-256 | yes | IMPLEMENTED |
| counts/blockers/status/readiness/hash tamper rejection | yes | IMPLEMENTED |
| `privacy-report-v1` JSON Schema | yes | IMPLEMENTED |
| `.kodepoia/diagnostics/privacy/` confinement | yes | IMPLEMENTED |
| Health `privacy` adapter | yes | IMPLEMENTED |
| stable R6.3 privacy cases | yes | IMPLEMENTED |
| unknown/N/A/pending evidence never manufactures PASS | yes | IMPLEMENTED |
| no scanner/network/store-submission execution path | yes | IMPLEMENTED |
| R0 exact final head Windows+Ubuntu | yes | PENDING FINAL HEAD |
| Python Core exact final head, all jobs | yes | PENDING FINAL HEAD |
| KodeStudio UI Smoke exact final head | yes | PENDING FINAL HEAD |
| implementation PR merge | yes | PENDING |
| post-merge normalization | yes | PENDING |

## Required behavioral acceptance

The final suite must demonstrate at minimum:

1. collected inventory items fail closed when purpose/storage/retention/deletion is missing;
2. `none` and `not_applicable` are explicit, require rationale, and cannot carry collection lifecycle fields;
3. legal/consent-basis state is never inferred; `UNSPECIFIED` remains distinct from declared/N/A;
4. declared basis placeholders require provenance;
5. inventory completeness is an explicit evidence field and `inventory_complete=true` requires review provenance;
6. incomplete inventory evidence remains WARN rather than PASS;
7. an all-N/A report remains UNKNOWN and contributes no numeric Health score;
8. N/A inventory/issues/declarations are neutral in aggregate score and N/A declarations stay SKIP in R6.3;
9. privacy issue N/A is distinct from PASS, and measured outcomes require evidence source;
10. obvious raw personal samples and secrets are absent from serialized detail evidence;
11. Apple and Google declaration readiness follows their relevant preparation fields;
12. Apple/Google platform mismatches fail closed;
13. declaration collection state cannot contradict the inventory;
14. declarations cannot reference unknown data categories or platforms outside category scope;
15. UNKNOWN, WARN, PASS and FAIL aggregate states are distinguishable;
16. unknown sensitivity, unspecified basis and pending store declaration remain WARN rather than PASS;
17. evidence-backed `none` can be represented without pretending data is collected;
18. derived counts, blockers, declaration readiness and canonical hash reject tampering;
19. duplicate inventory/declaration identities fail closed;
20. Health PRIVACY preserves UNKNOWN/WARN/PASS/FAIL and blocking semantics;
21. stable R6.3 IDs preserve N/A/UNKNOWN/pending as SKIP rather than fake PASS;
22. persistence requires initialized `.kodepoia` and remains project-confined;
23. JSON Schema accepts canonical output;
24. malformed platform scope fails closed.

## Development diagnostic / design review

The first implementation head `935d6b4fc7a29ad832df501f605c3648cde05988` was already CI-green (R0 #830, Python Core #804, UI Smoke #771). Independent contract review nevertheless found a potential false-green path: N/A values could contribute 100 points and a non-empty/all-N/A inventory did not require explicit completeness evidence.

This was hardened rather than accepted as-is:

- added `inventory_complete` and `inventory_review_source` to the canonical report/schema;
- PASS now requires explicit inventory-completeness evidence;
- N/A inventory/issues/declarations are score-neutral;
- all-N/A evidence is UNKNOWN;
- N/A store declarations are SKIP in R6.3 even when structurally `ready`;
- incomplete inventory remains WARN and receives a deterministic score completeness factor.

Hardened diagnostic head `48daa4f82194e1875211f205b99ba19089f42d92` passed R0 #836, Python Core #810 with all five jobs and UI Smoke #777. No architecture boundary or legal/compliance claim was weakened.

## External-reference interpretation

R6.10 uses the following as reference context, not as legal certification:

- EU/GDPR principles: explicit purpose, data minimisation, storage limitation, integrity/confidentiality and accountability;
- Google Play Data safety: collected/shared data, purposes and optionality declaration preparation;
- Apple App Privacy/privacy manifests: collected data categories, purposes, whether data is linked to the user, and tracking declaration preparation.

No lawful basis, consent requirement, GDPR/CCPA compliance, App Store approval or Google Play approval is inferred by Kodepoia.

## Manual intervention

**NONE.**

R6.10 does not require local GPU/Godot/hardware evidence. Hosted Windows + Ubuntu Python/CI are authoritative for this foundation. No user-side privacy data or personal information is required for acceptance.

## Failure recovery / anti-regression

- Do not invent legal/consent basis to turn WARN into PASS.
- Do not mark inventory complete without provenance.
- Do not count N/A as PASS or use it to inflate Health score.
- Do not convert unknown sensitivity or pending declaration fields into known values without evidence.
- Do not copy raw personal data into fixtures/evidence.
- Do not loosen declaration/inventory cross-validation.
- Do not weaken secret/personal-value redaction.
- Do not loosen `WorkspaceBoundary` confinement.
- Do not add remote privacy SaaS, scanner commands or store-submission side effects.
- Do not remove/narrow R0, Python Core, UI Smoke or R6.8 package-build gates.

## Completion record

PENDING exact-final-head CI, implementation merge and post-merge normalization.
