# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R6 sont COMPLETE. Le planning R7 est ACCEPTED. R7.1–R7.6 sont COMPLETE ; R7.7 est NOT STARTED.** R7.6 a été accepté sur le head exact `b623836b8f5bd39fce101eca7fe4653a996a9562` avec R0 #980 / `32590863193`, Python Core #954 / `32590863199` cinq jobs SUCCESS, suite Ubuntu `432 passed / 3 skipped / 46 warnings`, et UI Smoke #921 / `32590863191` SUCCESS; PR #70 merge `15216b59e14d692ff1e850812d572632bad5a88b`; manual R7.6 = CONDITIONAL NOT TRIGGERED. **La prochaine implémentation autorisée est R7.7 — Local STT + frame extraction/analysis hooks**, uniquement après fusion de la normalisation R7.6. R7.7 possède un gate manuel REQUIRED et ne peut pas être fermé avec de la preuve hosted/headless seule.

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
- R7.7–R7.11 : NOT STARTED; next = R7.7.
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

## YouTube official reference context used by R7.6

- `videos.list` : read-only metadata endpoint; selected `part` fields include `snippet`/`contentDetails`; current documented quota cost 1.
- `captions.list` : track metadata only, not caption text; authorization required; current documented quota cost 50.
- `captions.download` : caption text/file download; OAuth required and user must have permission to edit the video; current documented quota cost 200; WebVTT supported by `tfmt=vtt`.
- Caption resources expose `videoId`, `language`, `trackKind`, `lastUpdated`, `status`, `isDraft`; `trackKind` includes ASR/forced/standard.
- YouTube Developer Policies are treated as provider-policy context for keeping audiovisual stream download/storage outside R7.6; Kodepoia makes no legal conclusion or certification.

## Permanent architecture/security boundaries

Preserve without reinterpretation: `WorkspaceBoundary`; ProcessSandbox + global KillSwitch; Guardian + PermissionSet; structured tool APIs; SafeChange/Backup/Recovery/Audit when required; OS-backed Secrets + redaction; Health/Budget/DataGovernance and versioned schemas; exact-head acceptance; explicit UNKNOWN/N/A/UNAVAILABLE/BLOCKED/STALE; platform-aware behavior; ADR for foundation changes. No arbitrary command/argv/cwd/host/network surface may be supplied by the model.

## Accepted model roles

- KodeFast = `granite4.1:3b`.
- KodeCore = `gpt-oss:20b`.
- KodeCoder = `ornith:9b`.
- `north-mini-code-1.0:Q4_K_M` remains a future KodeDeepCoder candidate.

## Next action

**R7.1–R7.6 are COMPLETE. R7.7 is NOT STARTED.** After the R7.6 normalization PR merges, start **R7.7 — Local STT + frame extraction/analysis hooks**. The manual gate is REQUIRED: hosted/headless fixtures may validate deterministic contracts but cannot by themselves close R7.7. Any media helper must use structured fixed arguments and existing ProcessSandbox/KillSwitch governance; paths remain WorkspaceBoundary-confined; provenance and resource bounds remain explicit; real manual evidence must be recorded before COMPLETE.
