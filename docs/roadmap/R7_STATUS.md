# Kodepoia — R7 status

**Phase:** R7 — Research sécurisé  
**Overall status:** IN PROGRESS  
**Planning:** ACCEPTED  
**Current subdivision:** R7.10 NOT STARTED  
**Manual blocker:** NONE for R7.10

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
| R7.10 | CLI + KodeStudio Research UX | NOT STARTED | — | NONE |
| R7.11 | Adversarial hardening + R7 integrated acceptance | NOT STARTED | — | CONDITIONAL |

## Accepted evidence summary

- R7 planning: head `f86825ffd84c1c814afb5865be95b278c4291314`; PR #58 merge `9315d801f3a2d13a5441bd87babd2abeb9305995`; normalization #59 `7279412ae751bce739317763462c4a48d7832122`.
- R7.1: head `a6e9cf9f6db717155c311f4ded1ad5fb744b70ca`; R0 #959, Python #933 5/5, UI #900; PR #60 merge `86a5453b2fd8ce414e73277199fdd55bd210aeba`; manual NONE.
- R7.2: head `9101e686a32b24bb33a23d7ac578bf25570e115e`; R0 #964, Python #938 5/5, UI #905; PR #62 merge `25741ab9c39300483b62eb2cc07b9d2c9fcfb20c`; manual NONE.
- R7.3: head `4efd2cb016e774fa3ef06590ffda377606d875e9`; R0 #968, Python #942 5/5 (`369 passed / 3 skipped / 46 warnings` Ubuntu), UI #909; PR #64 merge `cde4f7fd727c6940c6a434f85fabc2ced27f04c5`; manual NONE.
- R7.4: head `be6f1d5d2f7d9a16c1c295a51905fcd22e9835be`; R0 #972, Python #946 5/5 (`388 passed / 3 skipped / 46 warnings` Ubuntu), UI #913; PR #66 merge `d17746b03fe4a8db47ec2c55ef11715fdd820f73`; manual CONDITIONAL NOT TRIGGERED.
- R7.5: head `12d5580ff3f8c6d9d0fb211e1688e3ba37dcdce5`; R0 #976 / `32590366852`; Python #950 / `32590366851` 5/5 (`400 passed / 3 skipped / 46 warnings` Ubuntu); UI #917 / `32590366853`; PR #68 merge `b02dfba4b6a6a4c0a6ec19d552e569b56845a4ea`; manual NONE.
- R7.6: head `b623836b8f5bd39fce101eca7fe4653a996a9562`; R0 #980 / `32590863193`; Python Core #954 / `32590863199` 5/5 (`432 passed / 3 skipped / 46 warnings` Ubuntu); UI Smoke #921 / `32590863191`; PR #70 merge `15216b59e14d692ff1e850812d572632bad5a88b`; manual CONDITIONAL NOT TRIGGERED.
- R7.7: head `04cef94c82fdacafe7313d27c8cf516e8e765295`; R0 #997 / `32594549119`; Python Core #971 / `32594549136` 5/5 (`443 passed / 4 skipped / 46 warnings` Ubuntu); UI Smoke #938 / `32594549125`; PR #72 merge `8f296c383a28be0055a72a67587422318257aefc`; manual REQUIRED SATISFIED.
- R7.8: head `deb5de415541004fb07bfbc6d955e9d76d717533`; R0 #1001 / `32595358745`; Python Core #975 / `32595358772` 5/5 (`460 passed / 4 skipped / 46 warnings` Ubuntu); UI Smoke #942 / `32595358734`; PR #74 merge `f0de53379d6a8eb1883137946db4f2731cb9830a`; manual NONE.
- R7.9: head `80390f95a11e5b3d4353b16eada26f10204bb4fa`; R0 #1018 / `32596697106`; Python Core #992 / `32596697107` 5/5 (`483 passed / 4 skipped / 46 warnings` Ubuntu); UI Smoke #959 / `32596697121`; PR #76 merge `5406887055117e7fea5cdd27579fb27b41051ed1`; manual NONE.

Detailed evidence remains in the corresponding `R7_X_ACCEPTANCE.md` files.

## R7.5 accepted community invariants

- community evidence remains community evidence; popularity is not authority;
- author/timestamp/parent/permalink/state/quotes stay explicit;
- deleted/removed placeholders do not become authored evidence;
- hostile visible text remains guarded data;
- no posting/voting/account automation exists.

## R7.6 accepted YouTube invariants

- video identity is exact and canonicalized;
- metadata and transcript availability remain independent;
- official caption paths preserve actual OAuth/permission restrictions;
- WebVTT timing and transcript provenance stay explicit;
- no audiovisual download, browser login automation, undocumented caption scraping, DRM bypass, yt-dlp or subprocess helper exists in R7.6.

## R7.7 accepted local-media invariants

- FFmpeg/whisper.cpp/model capability is explicit and hash-bound;
- fixed governed process arguments, WorkspaceBoundary/Guardian/ProcessSandbox/KillSwitch reused;
- exact fixture hash, STT timestamp evidence, frame timestamp/hash/dimensions and cleanup are accepted;
- equivalent word/digit rendering is normalized only for the bounded fixture semantic check;
- no vision interpretation is fabricated without a real accepted provider;
- REQUIRED local Windows acceptance passed on the exact accepted head.

## R7.8 accepted version/provenance invariants

- exact/range/inferred/unknown version evidence are distinct and survive round-trip;
- inferred observations require evidence/reason and never become exact matches;
- Project DNA target engine/version is consumed without mutation and version scheme is supplied explicitly;
- SemVer exact identity is distinct from precedence; build metadata does not affect range ordering but remains part of an exact stated identifier;
- PEP 440 support is deliberately conservative for simple numeric releases with zero-padding; unsupported rich shapes become UNKNOWN rather than guessed;
- opaque versions support exact identity but gain no fabricated ordering;
- version relation and freshness remain independent axes;
- mutable sources require explicit revalidation timestamp evidence before CURRENT/STALE assessment;
- immutable identities require revision or snapshot evidence;
- contradictory claims remain visible even when explicit supersession evidence exists;
- agreement/conflict/unresolved groups are deterministic and recalculated on load;
- ranking is presentation ordering only and retains all claims; source count/popularity is not authority;
- canonical IDs/report digest fail closed on tampering or missing references;
- R7.8 adds no network/process/UI surface and does not mutate R7.1–R7.7 artifacts.

## R7.9 accepted cache/context/memory invariants

- cache selection uses normalized query/scope/source/target/version/policy dimensions; invocation `request_id` is provenance, not a cache-key dimension;
- raw query/scope text is absent from query manifests;
- cache freshness is distinct from source freshness and never fabricates `CURRENT`;
- mutable sources use the shorter TTL; stale cache requires explicit revalidation;
- revalidation is rejected when source/version/content identity changes;
- declared source version is retained alongside normalized R7.8 version evidence so historical artifact-ID collisions cannot silently collapse distinct versions;
- deduplication preserves source/version/content provenance;
- cached reports re-enter through typed `ResearchStore` validation and tampering fails closed;
- context summaries are extractive, bounded, cited, secret-redacted and remain external/untrusted/guarded;
- oversized findings are deterministically trimmed to their actual rendered budget instead of being dropped because of a guessed overhead;
- Research Memory write is explicit, project-scoped, `allow_global_memory=false`, `allow_training_dataset=false`;
- no summary automatically becomes validated global Experience;
- R7.9 adds no network/process/tool surface.

## Next authorized action

After this R7.9 normalization PR is accepted and merged, the next authorized subdivision is **R7.10 — CLI + KodeStudio Research UX**. Manual intervention is **NONE**. R7.10 must expose the already accepted research APIs through structured CLI commands and the frozen KodeStudio Research surface, while preserving permissions, cancellation, provenance, uncertainty, accessibility/localization and secret non-disclosure.
