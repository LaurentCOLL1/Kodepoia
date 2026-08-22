# Kodepoia — R7 status

**Phase:** R7 — Research sécurisé  
**Overall status:** IN PROGRESS  
**Planning:** ACCEPTED  
**Current subdivision:** R7.4 NOT STARTED  
**Manual blocker:** NONE

## Subdivision status

| ID | Title | Status | Accepted head | Manual |
| --- | --- | --- | --- | --- |
| R7.1 | KodeResearch contracts + ResearchGuard hardening | COMPLETE | `a6e9cf9f6db717155c311f4ded1ad5fb744b70ca` | NONE |
| R7.2 | Local + official documentation research | COMPLETE | `9101e686a32b24bb33a23d7ac578bf25570e115e` | NONE |
| R7.3 | Governed Web fetch + extraction | COMPLETE | `4efd2cb016e774fa3ef06590ffda377606d875e9` | NONE |
| R7.4 | GitHub research adapter | NOT STARTED | — | CONDITIONAL |
| R7.5 | Community/forums research normalization | NOT STARTED | — | NONE |
| R7.6 | YouTube metadata + transcript ingestion | NOT STARTED | — | CONDITIONAL |
| R7.7 | Local STT + frame extraction/analysis hooks | NOT STARTED | — | REQUIRED |
| R7.8 | Version-awareness + provenance/conflict model | NOT STARTED | — | NONE |
| R7.9 | Research cache + Context/Memory orchestration | NOT STARTED | — | NONE |
| R7.10 | CLI + KodeStudio Research UX | NOT STARTED | — | NONE |
| R7.11 | Adversarial hardening + R7 integrated acceptance | NOT STARTED | — | CONDITIONAL |

## Planning acceptance

- planning head `f86825ffd84c1c814afb5865be95b278c4291314`;
- planning PR #58 merge `9315d801f3a2d13a5441bd87babd2abeb9305995`;
- planning normalization PR #59 merge `7279412ae751bce739317763462c4a48d7832122`;
- R0 #955, Python Core #929 5/5, UI Smoke #896 SUCCESS on the accepted planning head.

## R7.1 acceptance

- implementation head `a6e9cf9f6db717155c311f4ded1ad5fb744b70ca`;
- implementation PR #60 merge `86a5453b2fd8ce414e73277199fdd55bd210aeba`;
- R0 #959 / `32584754313` SUCCESS;
- Python Core #933 / `32584754311` SUCCESS, 5/5 jobs; Ubuntu authoritative suite: 310 passed / 3 skipped / 46 warnings;
- KodeStudio UI Smoke #900 / `32584754325` SUCCESS;
- manual NONE;
- acceptance source: `docs/roadmap/R7_1_ACCEPTANCE.md`.

## R7.2 acceptance

- implementation head `9101e686a32b24bb33a23d7ac578bf25570e115e`;
- implementation PR #62 merge `25741ab9c39300483b62eb2cc07b9d2c9fcfb20c`;
- R0 #964 / `32585721455` SUCCESS;
- Python Core #938 / `32585721645` SUCCESS, 5/5 jobs;
- KodeStudio UI Smoke #905 / `32585721536` SUCCESS;
- manual NONE;
- preceding head `61eb6fbaf73066274249b3e490695bb0d4ff122c` was rejected after Python Core #937 exposed one Windows-only POSIX-root path-validation regression; final head fixes it with native + POSIX + Windows path semantics;
- acceptance source: `docs/roadmap/R7_2_ACCEPTANCE.md`.

## R7.3 acceptance

- implementation head `4efd2cb016e774fa3ef06590ffda377606d875e9`;
- implementation PR #64 merge `cde4f7fd727c6940c6a434f85fabc2ced27f04c5`;
- R0 #968 / `32586392901` SUCCESS;
- Python Core #942 / `32586392898` SUCCESS, 5/5 jobs; Ubuntu authoritative suite: 369 passed / 3 skipped / 46 warnings;
- KodeStudio UI Smoke #909 / `32586392883` SUCCESS;
- manual NONE;
- acceptance source: `docs/roadmap/R7_3_ACCEPTANCE.md`.

## Next authorized action

Start **R7.4 — GitHub research adapter** only after this R7.3 normalization PR is accepted and merged. R7.4 must remain read-only, typed and provenance-preserving; prefer immutable commit-SHA locators, pass README/issue/PR/comment content through `ResearchGuard`, preserve pagination/rate-limit evidence, expose no GitHub write operation or arbitrary GraphQL, and resolve optional credentials only outside model context through the existing secret boundary.