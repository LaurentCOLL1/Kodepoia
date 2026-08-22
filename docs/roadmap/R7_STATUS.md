# Kodepoia — R7 status

**Phase:** R7 — Research sécurisé  
**Overall status:** IN PROGRESS  
**Planning:** ACCEPTED  
**Current subdivision:** R7.6 NOT STARTED  
**Manual blocker:** NONE

## Subdivision status

| ID | Title | Status | Accepted head | Manual |
| --- | --- | --- | --- | --- |
| R7.1 | KodeResearch contracts + ResearchGuard hardening | COMPLETE | `a6e9cf9f6db717155c311f4ded1ad5fb744b70ca` | NONE |
| R7.2 | Local + official documentation research | COMPLETE | `9101e686a32b24bb33a23d7ac578bf25570e115e` | NONE |
| R7.3 | Governed Web fetch + extraction | COMPLETE | `4efd2cb016e774fa3ef06590ffda377606d875e9` | NONE |
| R7.4 | GitHub research adapter | COMPLETE | `be6f1d5d2f7d9a16c1c295a51905fcd22e9835be` | CONDITIONAL NOT TRIGGERED |
| R7.5 | Community/forums research normalization | COMPLETE | `12d5580ff3f8c6d9d0fb211e1688e3ba37dcdce5` | NONE |
| R7.6 | YouTube metadata + transcript ingestion | NOT STARTED | — | CONDITIONAL |
| R7.7 | Local STT + frame extraction/analysis hooks | NOT STARTED | — | REQUIRED |
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
- R7.5: head `12d5580ff3f8c6d9d0fb211e1688e3ba37dcdce5`; R0 #976 / `32590366852`; Python Core #950 / `32590366851` 5/5 (`400 passed / 3 skipped / 46 warnings` Ubuntu); UI Smoke #917 / `32590366853`; PR #68 merge `b02dfba4b6a6a4c0a6ec19d552e569b56845a4ea`; manual NONE.

Detailed evidence remains in the corresponding `R7_X_ACCEPTANCE.md` files.

## R7.5 accepted invariants

- community/forum evidence remains `ResearchSourceKind.COMMUNITY` and `authority_class=community`;
- score/reaction/popularity metadata is descriptive only and never authority;
- vendor-staff/moderator is an author-role observation, not automatic official evidence;
- post/thread/parent/timestamps/permalinks/states remain explicit;
- quoted material is separated from current-author text; nested quotes preserve depth/source evidence;
- deleted/removed placeholders do not become authored evidence;
- hidden script/style/noscript/template text is excluded;
- visible hostile instructions remain evidence but are guarded by the existing ResearchGuard;
- no posting/voting/moderation/account automation or second network stack exists.

## Next authorized action

Start **R7.6 — YouTube metadata + transcript ingestion** only after this R7.5 normalization PR is accepted and merged. R7.6 must validate video IDs/URLs, preserve video/track/language/timestamp provenance, route transcript text through ResearchGuard, represent unavailable/blocked transcript access explicitly, and expose no media download, playback, login automation, DRM bypass or arbitrary helper arguments. Official YouTube caption access must follow the provider's actual authorization contract rather than assuming arbitrary public caption download is available.
