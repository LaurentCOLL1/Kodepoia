# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R6 COMPLETE. Planning R7 ACCEPTED. R7.1–R7.10 COMPLETE ; R7.11 NOT STARTED.** R7.10 a été accepté sur le head exact `cfd0f7ba02af04b456993f686827f10810b3a61a` avec R0 #1025 / `32598029034`, Python Core #999 / `32598029045` cinq jobs SUCCESS, suite Ubuntu `494 passed / 5 skipped / 46 warnings`, UI Smoke #966 / `32598029037` SUCCESS; PR #78 merge `963799042ee30723fd2856f54dad9dedde6ed225`; manual R7.10 = NONE. **La prochaine et dernière subdivision R7 autorisée est R7.11 — Adversarial hardening + R7 integrated acceptance**, uniquement après fusion de la normalisation R7.10. R7.11 manual = CONDITIONAL.

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
- R7.6 : COMPLETE — head `b623836b8f5bd39fce101eca7fe4653a996a9562`; R0 #980, Python #954 5/5 (`432 passed / 3 skipped / 46 warnings` Ubuntu), UI #921; PR #70 merge `15216b59e14d692ff1e850812d572632bad5a88b`; manual CONDITIONAL NOT TRIGGERED.
- R7.7 : COMPLETE — head `04cef94c82fdacafe7313d27c8cf516e8e765295`; R0 #997, Python #971 5/5 (`443 passed / 4 skipped / 46 warnings` Ubuntu), UI #938; PR #72 merge `8f296c383a28be0055a72a67587422318257aefc`; manual REQUIRED SATISFIED.
- R7.8 : COMPLETE — head `deb5de415541004fb07bfbc6d955e9d76d717533`; R0 #1001, Python #975 5/5 (`460 passed / 4 skipped / 46 warnings` Ubuntu), UI #942; PR #74 merge `f0de53379d6a8eb1883137946db4f2731cb9830a`; manual NONE.
- R7.9 : COMPLETE — head `80390f95a11e5b3d4353b16eada26f10204bb4fa`; R0 #1018, Python #992 5/5 (`483 passed / 4 skipped / 46 warnings` Ubuntu), UI #959; PR #76 merge `5406887055117e7fea5cdd27579fb27b41051ed1`; manual NONE.
- R7.10 : COMPLETE — head `cfd0f7ba02af04b456993f686827f10810b3a61a`; R0 #1025 / `32598029034`; Python #999 / `32598029045` 5/5 (`494 passed / 5 skipped / 46 warnings` Ubuntu); UI #966 / `32598029037`; PR #78 merge `963799042ee30723fd2856f54dad9dedde6ed225`; manual NONE.
- R7.11 : NOT STARTED; next = R7.11 after R7.10 normalization.
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

## Accepted R7 trust/security baseline

- Toute donnée externe reste une donnée, jamais une instruction agentique; `ResearchGuard` reste l'unique frontière de confiance contenu.
- Status/freshness restent explicites; indisponible/non mesuré ne fabrique jamais PASS/CURRENT.
- IDs/digests et preuves persistées sont déterministes/recalculables; `.kodepoia/research/` reste confiné par `WorkspaceBoundary`.
- R7.2 local/official docs est offline-first avec lignes/version/provenance explicites.
- R7.3 Web est GET-only typé avec DNS/IP publics, IP épinglée, redirects revalidés, Guardian NETWORK et bornes MIME/octets/timeout/rate.
- R7.4 GitHub est REST read-only typé sur origine fixe, refs mutables résolues vers SHA exact, pagination/rate-limit explicites, auth optionnelle via KodeSecrets.
- R7.5 Community conserve auteur/thread/parent/timestamps/états/quotes et ne transforme jamais popularité en autorité.
- R7.6 YouTube sépare metadata/transcript, préserve timing/provenance et n'ajoute aucun contournement d'auth/DRM.
- R7.7 local-media réutilise WorkspaceBoundary/Guardian/ProcessSandbox/KillSwitch; FFmpeg/whisper.cpp/model sont hashés; REQUIRED Windows gate est satisfait; vision reste UNAVAILABLE sans provider réel.
- R7.8 distingue exact/range/inferred/unknown, version relation/freshness, mutability et conflits sans supprimer les contradictions.
- R7.9 cache et orchestre les preuves sans transformer cache hit, résumé ou Memory en nouvelle autorité; global/training promotion est désactivée.
- R7.10 expose CLI + KodeStudio via un seul `ResearchService`; Web est BLOCKED sans opt-in NETWORK; Qt ne manipule ni secret/socket/process arbitraire; cancel précède persistence/READY; copy/export reste cité et redacted.

## R7.7 local-media accepted evidence

- Accepted head `04cef94c82fdacafe7313d27c8cf516e8e765295`.
- FFmpeg 4.2.3 SHA-256 `b6bd38a97c5f118f30c93a97b5739b5f33dd2616c735f841c2a56074a9f0a9f0`.
- whisper.cpp 1.9.1 SHA-256 `58245314fb73b30fbd0cf0542c5c172e23f02b6eb7cad7b51e792439cf5e1755`.
- STT model SHA-256 `a03779c86df3323075f5e796cb2ce5029f00ec8869eee3fdfb897afe36c6d002`.
- Fixture SHA-256 `8b3ed015526fd4584309a3c661b9e267ac464315e2d1c9aeed5bea19f28bdcf7`, 12,112 bytes.
- Doctor SHA-256 `463c0de4ad477baabc711a2b89fc1c7ad0b7735c6bdfc2ecfdde457a9f8f86e1`; acceptance SHA-256 `33e52eb43ed448dd02766b823c3b22bfb08301a9f4dc3f24f336269f1ab76283`.

## R7.10 accepted UX baseline

- Accepted head `cfd0f7ba02af04b456993f686827f10810b3a61a`.
- Shared service: query/fetch/show/cache/status/media capability; same typed/redacted records for CLI and UI.
- Web opt-in grants only NETWORK and still uses Guardian/R7.3 public-target, pinned-IP, redirect/MIME/size/timeout/rate protections.
- Persisted GitHub/Community/YouTube evidence is queryable; absent live interactive provider setup remains explicit rather than fabricated.
- Cancellation is checked before dispatch and before persistence/result promotion.
- KodeStudio Research uses worker/QThreadPool, textual READY/BLOCKED/UNAVAILABLE/UNKNOWN/STALE/CANCELLED semantics, citations, version/freshness/trust, suspicious warning, copy/export.
- Exports are WorkspaceBoundary-confined and redacted.
- Accessibility/pseudo-locale accepts legitimate layout expansion while enforcing keyboard reachability and no navigation truncation.
- Rejected candidate heads and their test-only contract defects remain documented in `R7_10_ACCEPTANCE.md`; no failed run is reused as acceptance.

## R7.11 execution contract

R7.11 est la prochaine subdivision autorisée uniquement après fusion de la normalisation R7.10. Exigences gelées :

- adversarial fixtures cross-source : local/official/Web/GitHub/Community/YouTube hostile text doit rester `ResearchGuard` data et ne jamais obtenir d'autorité/tool instruction;
- SSRF : private/loopback/link-local/credential URLs, malicious redirects, mixed public/private DNS answers et DNS rebinding regression doivent rester bloqués avant action dangereuse;
- paths : traversal/absolute/symlink escapes pour local docs, official snapshots, research cache/context/export et chemins media doivent fail closed via `WorkspaceBoundary`;
- process/tool surface : aucun arbitrary command/argv/cwd/executable/host injecté depuis Research; seuls les adapters structurés acceptés R7.3–R7.7/R7.10 restent utilisables;
- secrets : valeurs d'auth/token ne doivent jamais apparaître dans artifact/report/cache/context/view/copy/export/log-like evidence; delegated secrets seulement;
- cancel : aucune opération annulée ne peut persister/promouvoir un résultat partiel comme READY;
- version conflicts : contradictions et supersession restent visibles; popularité/source count ne devient jamais authority;
- créer une preuve machine R7 intégrée versionnée contenant accepted heads/manual states, acceptance-doc path, SHA-256 et byte length, plus les preuves phase-closing pertinentes;
- créer un validator repository qui recharge les documents, recalcule bytes/SHA-256/identités et fail closed sur missing/tamper/mismatch;
- effectuer la revue finale R6 quality/security/BOM et les gates exact-head R0/Python/UI;
- R7.7 REQUIRED manual est déjà SATISFIED et reste un prerequisite explicite;
- manual R7.11 = CONDITIONAL : déclencher un live-provider gate seulement si le comportement requis ne peut pas être établi de façon déterministe. Sinon enregistrer `CONDITIONAL NOT TRIGGERED`.

R7 ne peut être marqué **COMPLETE** qu'après acceptation exacte de R7.11 et normalisation de l'acceptance intégrée.

## Permanent architecture/security boundaries

Preserve without reinterpretation: `WorkspaceBoundary`; ProcessSandbox + global KillSwitch; Guardian + PermissionSet; structured tool APIs; SafeChange/Backup/Recovery/Audit when required; OS-backed Secrets + redaction; Health/Budget/DataGovernance and versioned schemas; exact-head acceptance; explicit UNKNOWN/N/A/UNAVAILABLE/BLOCKED/STALE; platform-aware behavior; ADR for foundation changes. No arbitrary command/argv/cwd/host/network surface may be supplied by the model.

## Accepted model roles

- KodeFast = `granite4.1:3b`.
- KodeCore = `gpt-oss:20b`.
- KodeCoder = `ornith:9b`.
- `north-mini-code-1.0:Q4_K_M` remains a future KodeDeepCoder candidate.

## Next action

**R7.1–R7.10 COMPLETE. R7.11 NOT STARTED.** Après fusion de la normalisation R7.10, commencer **R7.11 — Adversarial hardening + R7 integrated acceptance**. Manual gate = CONDITIONAL.
