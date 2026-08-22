# Kodepoia — R7 status

**Phase:** R7 — Research sécurisé  
**Overall status:** IN PROGRESS  
**Planning:** ACCEPTED  
**Current subdivision:** R7.11 NOT STARTED  
**Manual blocker:** CONDITIONAL for R7.11; not triggered unless deterministic evidence cannot establish a required live-provider behavior

## Subdivision status

| ID | Title | Status | Accepted head | Manual |
| --- | --- | --- | --- | --- |
| R7.1 | KodeResearch contracts + ResearchGuard hardening | COMPLETE | `a6e9cf9f6db717155c311f4ded1ad5fb744b70ca` | NONE |
| R7.2 | Local + official documentation research | COMPLETE | `9101e686a32b24bb33a23d7ac578bf25570e115e` | NONE |
| R7.3 | Governed Web fetch + extraction | COMPLETE | `4efd2cb016e774fa3ef06590ffda377606d875e9` | NONE |
| R7.4 | GitHub research adapter | COMPLETE | `be6f1d5d2f7d9a16c1c295a51905fcd22e9835be` | CONDITIONAL NOT TRIGGERED |
| R7.5 | Community/forums research normalization | COMPLETE | `12d5580ff3f8c6d9d0fb211e1688e3ba37dcdce5` | NONE |
| R7.6 | YouTube metadata + transcript ingestion | COMPLETE | `b623836b8f5bd39fce101eca7fe4653a996a9562` | CONDITIONAL NOT TRIGGERED |
| R7.7 | Local STT + frame extraction/analysis hooks | COMPLETE | `04cef94c82fdacafe7313d27c8cf516e8e765295` | REQUIRED SATISFIED |
| R7.8 | Version-awareness + provenance/conflict model | COMPLETE | `deb5de415541004fb07bfbc6d955e9d76d717533` | NONE |
| R7.9 | Research cache + Context/Memory orchestration | COMPLETE | `80390f95a11e5b3d4353b16eada26f10204bb4fa` | NONE |
| R7.10 | CLI + KodeStudio Research UX | COMPLETE | `cfd0f7ba02af04b456993f686827f10810b3a61a` | NONE |
| R7.11 | Adversarial hardening + R7 integrated acceptance | NOT STARTED | — | CONDITIONAL |

## Accepted evidence summary

- R7 planning: head `f86825ffd84c1c814afb5865be95b278c4291314`; PR #58 merge `9315d801f3a2d13a5441bd87babd2abeb9305995`; normalization #59 `7279412ae751bce739317763462c4a48d7832122`.
- R7.1: head `a6e9cf9f6db717155c311f4ded1ad5fb744b70ca`; R0 #959, Python #933 5/5, UI #900; PR #60 merge `86a5453b2fd8ce414e73277199fdd55bd210aeba`; manual NONE.
- R7.2: head `9101e686a32b24bb33a23d7ac578bf25570e115e`; R0 #964, Python #938 5/5, UI #905; PR #62 merge `25741ab9c39300483b62eb2cc07b9d2c9fcfb20c`; manual NONE.
- R7.3: head `4efd2cb016e774fa3ef06590ffda377606d875e9`; R0 #968, Python #942 5/5 (`369 passed / 3 skipped / 46 warnings` Ubuntu), UI #909; PR #64 merge `cde4f7fd727c6940c6a434f85fabc2ced27f04c5`; manual NONE.
- R7.4: head `be6f1d5d2f7d9a16c1c295a51905fcd22e9835be`; R0 #972, Python #946 5/5 (`388 passed / 3 skipped / 46 warnings` Ubuntu), UI #913; PR #66 merge `d17746b03fe4a8db47ec2c55ef11715fdd820f73`; manual CONDITIONAL NOT TRIGGERED.
- R7.5: head `12d5580ff3f8c6d9d0fb211e1688e3ba37dcdce5`; R0 #976 / `32590366852`; Python #950 / `32590366851` 5/5 (`400 passed / 3 skipped / 46 warnings` Ubuntu); UI #917 / `32590366853`; PR #68 merge `b02dfba4b6a6a4c0a6ec19d552e569b56845a4ea`; manual NONE.
- R7.6: head `b623836b8f5bd39fce101eca7fe4653a996a9562`; R0 #980 / `32590863193`; Python #954 / `32590863199` 5/5 (`432 passed / 3 skipped / 46 warnings` Ubuntu); UI #921 / `32590863191`; PR #70 merge `15216b59e14d692ff1e850812d572632bad5a88b`; manual CONDITIONAL NOT TRIGGERED.
- R7.7: head `04cef94c82fdacafe7313d27c8cf516e8e765295`; R0 #997 / `32594549119`; Python #971 / `32594549136` 5/5 (`443 passed / 4 skipped / 46 warnings` Ubuntu); UI #938 / `32594549125`; PR #72 merge `8f296c383a28be0055a72a67587422318257aefc`; manual REQUIRED SATISFIED.
- R7.8: head `deb5de415541004fb07bfbc6d955e9d76d717533`; R0 #1001 / `32595358745`; Python #975 / `32595358772` 5/5 (`460 passed / 4 skipped / 46 warnings` Ubuntu); UI #942 / `32595358734`; PR #74 merge `f0de53379d6a8eb1883137946db4f2731cb9830a`; manual NONE.
- R7.9: head `80390f95a11e5b3d4353b16eada26f10204bb4fa`; R0 #1018 / `32596697106`; Python #992 / `32596697107` 5/5 (`483 passed / 4 skipped / 46 warnings` Ubuntu); UI #959 / `32596697121`; PR #76 merge `5406887055117e7fea5cdd27579fb27b41051ed1`; manual NONE.
- R7.10: head `cfd0f7ba02af04b456993f686827f10810b3a61a`; R0 #1025 / `32598029034`; Python #999 / `32598029045` 5/5 (`494 passed / 5 skipped / 46 warnings` Ubuntu); UI #966 / `32598029037`; PR #78 merge `963799042ee30723fd2856f54dad9dedde6ed225`; manual NONE.

Detailed evidence remains in the corresponding `R7_X_ACCEPTANCE.md` files.

## Accepted R7.8–R7.10 invariants

### R7.8 version/provenance

- exact/range/inferred/unknown evidence are distinct; inference never silently becomes exact;
- version relation and freshness are independent;
- mutable/immutable identity and revalidation evidence are explicit;
- contradictions remain visible; ranking never deletes claims or treats source count/popularity as authority;
- canonical IDs/report digest fail closed on tampering or missing references.

### R7.9 cache/context/memory

- cache selection uses normalized query/scope/source/target/version/policy dimensions; invocation `request_id` remains provenance only;
- cache reuse state never fabricates source `CURRENT`;
- source/version/content changes invalidate or prevent revalidation;
- dedupe preserves source/version/content provenance;
- cached reports re-enter through typed `ResearchStore` validation;
- context summaries are bounded, cited, secret-redacted and remain external/untrusted/guarded;
- Research Memory writes are explicit/project-scoped with global/training promotion disabled.

### R7.10 CLI/KodeStudio UX

- CLI and KodeStudio use one shared `ResearchService` and one trust/status/provenance model;
- Web is BLOCKED by default and explicit NETWORK opt-in still passes through Guardian + R7.3 controls;
- no Qt control directly handles sockets, secrets or arbitrary process execution;
- missing live provider setup stays explicit UNKNOWN/config-required rather than fabricated READY;
- cancellation occurs before persistence/result promotion;
- views/export preserve citations, source identity, status/freshness/version/trust and ResearchGuard indicators;
- exports stay below `.kodepoia/research/exports/` and use redaction;
- worker/thread-pool execution keeps long research work off the GUI event loop;
- keyboard/accessibility/pseudo-localization gates pass, including legitimate layout expansion under pseudo-locale;
- rejected candidate heads are retained in `R7_10_ACCEPTANCE.md`; no failed run is reused as accepted evidence.

## Next authorized action

After this R7.10 normalization PR is accepted and merged, the next and final R7 subdivision is **R7.11 — Adversarial hardening + R7 integrated acceptance**.

Frozen R7.11 scope:

- cross-source hostile/prompt-injection fixtures covering local/official/Web/GitHub/Community/YouTube evidence and proving content remains data rather than privileged instructions;
- SSRF/private-address/redirect/DNS-rebinding regression coverage for the accepted Web boundary;
- workspace/path escape and symlink boundary regression coverage for research reads, cache/context/export/media-related paths;
- process/tool-surface checks proving research cannot supply arbitrary command/argv/cwd/executable/host outside typed accepted APIs;
- secret non-disclosure tests across delegated auth, view/copy/export/cache/context paths;
- cancellation tests proving no post-cancel READY/persistence promotion;
- version conflict/supersession tests proving contradictory evidence remains visible and no popularity/source count becomes authority;
- integrated R7 acceptance evidence with accepted subdivision heads, manual states, acceptance-document path/SHA-256/byte length and exact phase-closing evidence;
- a repository validator that recalculates file bytes/hashes and fails closed on missing/tampered/mismatched evidence;
- final R6 quality/security/BOM regression review and exact-head R0/Python/UI gates;
- R7.7 REQUIRED local acceptance remains a prerequisite and is already SATISFIED;
- manual R7.11 = CONDITIONAL. A live provider probe is triggered only if deterministic evidence cannot establish a frozen required behavior; otherwise record `CONDITIONAL NOT TRIGGERED`.

R7 must remain **IN PROGRESS** until R7.11 itself is accepted, its integrated evidence is normalized, and every R7.1–R7.11 completion requirement is satisfied.
