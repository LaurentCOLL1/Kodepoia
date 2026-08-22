# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R6 sont COMPLETE. Le planning R7 est ACCEPTED. R7.1–R7.7 sont COMPLETE ; R7.8 est NOT STARTED.** R7.7 a été accepté sur le head exact `04cef94c82fdacafe7313d27c8cf516e8e765295` avec R0 #997 / `32594549119`, Python Core #971 / `32594549136` cinq jobs SUCCESS, suite Ubuntu `443 passed / 4 skipped / 46 warnings`, et UI Smoke #938 / `32594549125` SUCCESS; PR #72 merge `8f296c383a28be0055a72a67587422318257aefc`; manual R7.7 = REQUIRED SATISFIED sur Windows réel avec doctor READY, media acceptance PASS et pytest autoritaire PASS. **La prochaine implémentation autorisée est R7.8 — Version-awareness + provenance/conflict model**, uniquement après fusion de la normalisation R7.7. R7.8 manual = NONE.

## Source de vérité et état

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 : gelée le 21 août 2026.
- `main` : source de vérité après chaque fusion acceptée.
- R1–R6 : COMPLETE.
- R7 planning : ACCEPTED — head `f86825ffd84c1c814afb5865be95b278c4291314`; PR #58 merge `9315d801f3a2d13a5441bd87babd2abeb9305995`; normalization #59 `7279412ae751bce739317763462c4a48d7832122`.
- R7.1 : COMPLETE — head `a6e9cf9f6db717155c311f4ded1ad5fb744b70ca`; PR #60 merge `86a5453b2fd8ce414e73277199fdd55bd210aeba`; manual NONE.
- R7.2 : COMPLETE — head `9101e686a32b24bb33a23d7ac578bf25570e115e`; PR #62 merge `25741ab9c39300483b62eb2cc07b9d2c9fcfb20c`; manual NONE.
- R7.3 : COMPLETE — head `4efd2cb016e774fa3ef06590ffda377606d875e9`; R0 #968, Python #942 5/5, UI #909; PR #64 merge `cde4f7fd727c6940c6a434f85fabc2ced27f04c5`; manual NONE.
- R7.4 : COMPLETE — head `be6f1d5d2f7d9a16c1c295a51905fcd22e9835be`; R0 #972, Python #946 5/5 (`388 passed / 3 skipped / 46 warnings` Ubuntu), UI #913; PR #66 merge `d17746b03fe4a8db47ec2c55ef11715fdd820f73`; manual CONDITIONAL NOT TRIGGERED.
- R7.5 : COMPLETE — head `12d5580ff3f8c6d9d0fb211e1688e3ba37dcdce5`; R0 #976, Python #950 5/5 (`400 passed / 3 skipped / 46 warnings` Ubuntu), UI #917; PR #68 merge `b02dfba4b6a6a4c0a6ec19d552e569b56845a4ea`; manual NONE.
- R7.6 : COMPLETE — head `b623836b8f5bd39fce101eca7fe4653a996a9562`; R0 #980 / `32590863193`; Python #954 / `32590863199` 5/5 (`432 passed / 3 skipped / 46 warnings` Ubuntu); UI #921 / `32590863191`; PR #70 merge `15216b59e14d692ff1e850812d572632bad5a88b`; manual CONDITIONAL NOT TRIGGERED.
- R7.7 : COMPLETE — head `04cef94c82fdacafe7313d27c8cf516e8e765295`; R0 #997 / `32594549119`; Python #971 / `32594549136` 5/5 (`443 passed / 4 skipped / 46 warnings` Ubuntu); UI #938 / `32594549125`; PR #72 merge `8f296c383a28be0055a72a67587422318257aefc`; manual REQUIRED SATISFIED.
- R7.8–R7.11 : NOT STARTED; next = R7.8.
- R8–R16 : PENDING / NOT STARTED.

## R7 frozen structure

| ID | Title | Manual |
| --- | --- | --- |
| R7.1 | KodeResearch contracts + ResearchGuard hardening | NONE |
| R7.2 | Local + official documentation research | NONE |
| R7.3 | Governed Web fetch + extraction | NONE |
| R7.4 | GitHub research adapter | CONDITIONAL |
| R7.5 | Community/forums research normalization | NONE |
| R7.6 | YouTube metadata + transcript ingestion | CONDITIONAL |
| R7.7 | Local STT + frame extraction/analysis hooks | REQUIRED |
| R7.8 | Version-awareness + provenance/conflict model | NONE |
| R7.9 | Research cache + Context/Memory orchestration | NONE |
| R7.10 | CLI + KodeStudio Research UX | NONE |
| R7.11 | Adversarial hardening + R7 integrated acceptance | CONDITIONAL |

Aucune subdivision ne peut être ajoutée, supprimée, fusionnée, scindée ou renumérotée silencieusement. Toute modification de structure doit synchroniser `R7_PLAN.md` + continuité; tout changement de fondation exige un ADR.

## Accepted R7 trust baseline

- Toute donnée externe reste une donnée, jamais une instruction agentique; `ResearchGuard` reste l'unique frontière de confiance contenu.
- Status/freshness restent explicites; indisponible/non mesuré ne fabrique jamais PASS/CURRENT.
- IDs/digests et preuves persistées sont déterministes/recalculables; `.kodepoia/research/` reste confiné par `WorkspaceBoundary`.
- R7.2 local/official docs est offline-first avec lignes/version/provenance explicites.
- R7.3 Web est GET-only typé avec DNS/IP publics, IP épinglée, redirects revalidés, Guardian NETWORK et bornes MIME/octets/timeout/rate.
- R7.4 GitHub est REST read-only typé sur origine fixe, refs mutables résolues vers SHA exact, pagination/rate-limit explicites, auth optionnelle via KodeSecrets.
- R7.5 Community préserve auteur/thread/parent/timestamps/états/quotes; `authority_class=community`; popularité n'est jamais autorité.

## R7.6 accepted YouTube baseline

- `YouTubeLocator` accepte uniquement ID vidéo exact ou formes URL vidéo YouTube connues et normalise vers un watch URL canonique.
- Metadata et transcript sont deux capacités indépendantes; existence vidéo n'implique jamais existence transcript.
- `videos.list` provider exige l'identité exacte retournée pour le video ID demandé.
- Les timestamp markers de description sont conservés comme observations de description, jamais comme chapitres certifiés par le provider.
- Le transcript provider est explicite. Fixtures déterministes prouvent l'ingestion sans inventer une API publique universelle.
- Le chemin officiel captions est uniquement `captions.list` puis `captions.download?tfmt=vtt` dans un contexte OAuth autorisé.
- Absence OAuth et 401/403 provider restent `BLOCKED`; absence piste reste `UNAVAILABLE`; transcript non demandé = `NOT_APPLICABLE`.
- Caption track provenance : video ID, language, human/automatic/forced/unknown kind, provider, caption ID, name/lastUpdated si observés.
- WebVTT conserve les bornes temporelles en millisecondes; les citations utilisent URL timestamp + `ms:start` / `ms:end`.
- Metadata/transcript deviennent des `ResearchArtifact` distincts de `ResearchSourceKind.YOUTUBE` et repassent par ResearchGuard.
- Production provider : origine fixe `www.googleapis.com:443`, GET-only, Guardian NETWORK avant DNS/socket, public-address validation et TLS sur IP épinglée, KodeSecrets pour API key/OAuth.
- Aucun secret n'est persisté dans artifacts/evidence ou exposé dans les targets Guardian.
- R7.6 n'ajoute aucun stream audio/vidéo, cache audiovisuel, offline playback, browser/login automation, scraping d'endpoint caption non documenté, DRM bypass, yt-dlp, ffmpeg ou subprocess helper.
- STT/frame/media local reste strictement R7.7.

## R7.7 accepted local-media baseline

- Accepted exact head: `04cef94c82fdacafe7313d27c8cf516e8e765295`.
- Local doctor: READY on the exact head with FFmpeg 4.2.3, whisper.cpp 1.9.1 and project-local `ggml-base.en.bin`.
- FFmpeg executable SHA-256: `b6bd38a97c5f118f30c93a97b5739b5f33dd2616c735f841c2a56074a9f0a9f0`.
- whisper.cpp executable SHA-256: `58245314fb73b30fbd0cf0542c5c172e23f02b6eb7cad7b51e792439cf5e1755`.
- STT model SHA-256: `a03779c86df3323075f5e796cb2ce5029f00ec8869eee3fdfb897afe36c6d002`.
- Accepted fixture SHA-256: `8b3ed015526fd4584309a3c661b9e267ac464315e2d1c9aeed5bea19f28bdcf7`, 12,112 bytes.
- Actual transcript was `1, 2, 3, 4.` with timestamps and passed bounded semantic normalization; no exact lexical rendering is assumed.
- Frames at 500/1500/2500 ms were extracted as 320x180 with three distinct SHA-256 hashes.
- Local acceptance `status=PASS`, cleanup true, temporary disk budget PASS; CPU/RAM remain explicit UNKNOWN because not measured.
- `tests/test_r7_7_media_local_acceptance.py` passed locally and was not skipped.
- Returned local evidence SHA-256: doctor `463c0de4ad477baabc711a2b89fc1c7ad0b7735c6bdfc2ecfdde457a9f8f86e1`; acceptance `33e52eb43ed448dd02766b823c3b22bfb08301a9f4dc3f24f336269f1ab76283`.
- No visual interpretation is fabricated: default frame-analysis state is `UNAVAILABLE` until a real accepted provider exists.
- No automatic binary/model/driver install; no model-provided arbitrary executable/argv/cwd/env; media processing reuses WorkspaceBoundary, Guardian, ProcessSandbox and KillSwitch.
- Rejected candidates and their reasons remain recorded in `R7_7_ACCEPTANCE.md` and PR #72 rather than being rewritten as PASS.

## R7.8 execution contract

R7.8 is now the next authorized subdivision after normalization. Preserve these frozen requirements:

- represent exact, range, inferred and unknown version relationships distinctly;
- exact version must never be inferred without direct evidence;
- consume Project DNA target-version constraints without silently rewriting them;
- expose freshness/current/stale/unknown independently from version match;
- distinguish mutable source identity from immutable identity (for example a Git ref vs exact commit SHA);
- record conflict, agreement, supersession and unresolved evidence across sources;
- keep source facts distinct from inference;
- do not let source popularity or source count manufacture authority;
- manual intervention = NONE.

For Python-package style versions, PEP 440/version-specifier semantics are useful reference context; for SemVer sources, SemVer 2.0.0 precedence/range semantics are reference context. Kodepoia must record the version scheme/evidence used rather than assuming every ecosystem follows one universal scheme.

## Permanent architecture/security boundaries

Preserve without reinterpretation: `WorkspaceBoundary`; ProcessSandbox + global KillSwitch; Guardian + PermissionSet; structured tool APIs; SafeChange/Backup/Recovery/Audit when required; OS-backed Secrets + redaction; Health/Budget/DataGovernance and versioned schemas; exact-head acceptance; explicit UNKNOWN/N/A/UNAVAILABLE/BLOCKED/STALE; platform-aware behavior; ADR for foundation changes. No arbitrary command/argv/cwd/host/network surface may be supplied by the model.

## Accepted model roles

- KodeFast = `granite4.1:3b`.
- KodeCore = `gpt-oss:20b`.
- KodeCoder = `ornith:9b`.
- `north-mini-code-1.0:Q4_K_M` remains a future KodeDeepCoder candidate.

## Next action

**R7.1–R7.7 are COMPLETE. R7.8 is NOT STARTED.** After the R7.7 normalization PR merges, start **R7.8 — Version-awareness + provenance/conflict model**. Manual gate = NONE. Implement exact/range/inferred/unknown version evidence, Project DNA target constraints, freshness/staleness, mutable/immutable identity, conflict/agreement/supersession and deterministic provenance without fabricating exact version matches.
