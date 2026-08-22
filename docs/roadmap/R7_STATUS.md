# Kodepoia — R7 status

**Phase:** R7 — Research sécurisé  
**Overall status:** IN PROGRESS  
**Planning:** ACCEPTED  
**Current subdivision:** R7.8 NOT STARTED  
**Manual blocker:** NONE for R7.8

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
| R7.8 | Version-awareness + provenance/conflict model | NOT STARTED | — | NONE |
| R7.9 | Research cache + Context/Memory orchestration | NOT STARTED | — | NONE |
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
- R7.7: head `04cef94c82fdacafe7313d27c8cf516e8e765295`; R0 #997 / `32594549119`; Python Core #971 / `32594549136` 5/5 (`443 passed / 4 skipped / 46 warnings` Ubuntu); UI Smoke #938 / `32594549125`; PR #72 merge `8f296c383a28be0055a72a67587422318257aefc`; manual REQUIRED SATISFIED by exact-head Windows doctor + local media acceptance + authoritative pytest.

Detailed evidence remains in the corresponding `R7_X_ACCEPTANCE.md` files.

## R7.5 accepted community invariants

- community/forum evidence remains `ResearchSourceKind.COMMUNITY` and `authority_class=community`;
- score/reaction/popularity is descriptive only and never automatic authority;
- vendor-staff/moderator is an author-role observation, not official-document promotion;
- author/timestamp/parent/permalink/state provenance remains explicit;
- quoted material is separated from current-author text; nested quotes preserve depth/source evidence;
- deleted/removed placeholders do not become authored evidence;
- hidden script/style/noscript/template text is excluded;
- hostile visible instructions remain guarded evidence;
- no posting/voting/moderation/account automation or second network stack exists.

## R7.6 accepted YouTube invariants

- video IDs and known YouTube video URL shapes normalize to one canonical watch locator;
- Data API metadata must return the exact requested video identity;
- metadata and transcript availability are independent states;
- official caption metadata/text is not treated as arbitrary public transcript access;
- missing OAuth or provider 401/403 for official captions remains explicit BLOCKED evidence;
- authorized caption tracks preserve language, human/automatic/forced/unknown kind, caption ID, timestamps and provider evidence;
- WebVTT cue timing is preserved and transcript citations carry millisecond anchors;
- description timestamps remain description-observed markers, not provider-certified chapters;
- metadata/transcript content remains external and passes through ResearchGuard;
- production API access uses fixed provider endpoints, KodeSecrets references, Guardian NETWORK and R7.3 public-address/pinned-TLS protections;
- no audiovisual stream download/cache, offline playback, browser login automation, undocumented caption scraping, DRM bypass, yt-dlp, ffmpeg or subprocess helper is present;
- STT/frame/media fallback is reserved for R7.7.

## R7.7 accepted local-media invariants

- local helper discovery is deterministic and reports missing helpers/models as explicit UNAVAILABLE;
- FFmpeg and whisper.cpp execute only through the governed process layer with fixed structured arguments;
- acceptance STT uses CPU/no-GPU mode and does not require CUDA/Vulkan;
- project-local STT model provenance includes SHA-256 and size; no model/binary/driver auto-install exists;
- media fixture bytes are hash-bound and bounded before processing;
- transcript timing is preserved; the acceptance checks the exact intended numeric sequence while tolerating equivalent word/digit rendering from the decoder;
- frame extraction records timestamp, SHA-256 and dimensions and is compatible with the accepted FFmpeg 4.2.3 baseline;
- no visual interpretation is claimed without an accepted vision provider; state remains explicit UNAVAILABLE;
- temporary artifacts are size-bounded and cleaned on success/failure;
- CPU/RAM remain UNKNOWN where not measured, never fabricated;
- the REQUIRED local Windows gate passed on the exact accepted head and hosted evidence alone was not treated as sufficient.

## Next authorized action

After this R7.7 normalization PR is accepted and merged, the next authorized subdivision is **R7.8 — Version-awareness + provenance/conflict model**. Manual intervention is **NONE**. R7.8 must preserve exact/range/inferred/unknown version evidence, Project DNA target constraints, explicit freshness/staleness, mutable-vs-immutable source identity, conflict/supersession evidence and the rule that exact versions are never inferred without evidence.
