# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R6 COMPLETE. Planning R7 ACCEPTED. R7.1–R7.8 COMPLETE ; R7.9 NOT STARTED.** R7.8 a été accepté sur le head exact `deb5de415541004fb07bfbc6d955e9d76d717533` avec R0 #1001 / `32595358745`, Python Core #975 / `32595358772` cinq jobs SUCCESS, suite Ubuntu `460 passed / 4 skipped / 46 warnings`, UI Smoke #942 / `32595358734` SUCCESS; PR #74 merge `f0de53379d6a8eb1883137946db4f2731cb9830a`; manual R7.8 = NONE. **La prochaine implémentation autorisée est R7.9 — Research cache + Context/Memory orchestration**, uniquement après fusion de la normalisation R7.8. R7.9 manual = NONE.

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
- R7.8 : COMPLETE — head `deb5de415541004fb07bfbc6d955e9d76d717533`; R0 #1001 / `32595358745`; Python #975 / `32595358772` 5/5 (`460 passed / 4 skipped / 46 warnings` Ubuntu); UI #942 / `32595358734`; PR #74 merge `f0de53379d6a8eb1883137946db4f2731cb9830a`; manual NONE.
- R7.9–R7.11 : NOT STARTED; next = R7.9.
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
- R7.6 YouTube sépare metadata/transcript, respecte les restrictions OAuth captions, préserve timing/provenance et n'ajoute aucun téléchargement audiovisuel ou contournement.
- R7.7 local-media réutilise WorkspaceBoundary/Guardian/ProcessSandbox/KillSwitch; FFmpeg/whisper.cpp/model sont hashés; STT/frames/cleanup ont passé le gate Windows exact-head; vision reste UNAVAILABLE sans provider réel.

## R7.7 accepted local-media baseline

- Accepted head `04cef94c82fdacafe7313d27c8cf516e8e765295`.
- FFmpeg 4.2.3 SHA-256 `b6bd38a97c5f118f30c93a97b5739b5f33dd2616c735f841c2a56074a9f0a9f0`.
- whisper.cpp 1.9.1 SHA-256 `58245314fb73b30fbd0cf0542c5c172e23f02b6eb7cad7b51e792439cf5e1755`.
- STT model SHA-256 `a03779c86df3323075f5e796cb2ce5029f00ec8869eee3fdfb897afe36c6d002`.
- Fixture SHA-256 `8b3ed015526fd4584309a3c661b9e267ac464315e2d1c9aeed5bea19f28bdcf7`, 12,112 bytes.
- Transcript réel `1, 2, 3, 4.` avec timestamps; frames 500/1500/2500 ms, 320x180, trois hashes distincts; cleanup true.
- Preuves locales retournées : doctor SHA-256 `463c0de4ad477baabc711a2b89fc1c7ad0b7735c6bdfc2ecfdde457a9f8f86e1`; acceptance SHA-256 `33e52eb43ed448dd02766b823c3b22bfb08301a9f4dc3f24f336269f1ab76283`.

## R7.8 accepted version/provenance baseline

- `VersionEvidenceKind`: exact/range/inferred/unknown reste distinct en mémoire et après roundtrip.
- L'inférence exige preuve + raison et ne devient jamais une version exacte; relation = `INFERRED_MATCH` si elle correspond au target.
- Les contraintes target refusent l'inférence silencieuse.
- `VersionScheme` est explicite (`OPAQUE`, `SEMVER`, `PEP440`); aucun schéma n'est deviné depuis le nom du produit ou la ponctuation.
- SemVer : parsing strict, prerelease precedence, build metadata ignoré pour la précédence/ranges mais conservé dans l'identité exacte déclarée.
- PEP 440 : comparaison conservatrice seulement pour releases numériques simples avec zero-padding (`1.0 == 1.0.0`); formes riches non implémentées -> UNKNOWN plutôt qu'une pseudo-compatibilité.
- Opaque : égalité exacte seulement, pas d'ordre fabriqué.
- Project DNA : `engine` / `engine_version` sont consommés sans mutation; version absente -> UNKNOWN; caller fournit le scheme.
- Version relation et freshness sont indépendants.
- Source mutable : CURRENT/STALE nécessite `validated_at`; relecture cache/retrieved_at ne rafraîchit pas silencieusement la source.
- Missing/future freshness evidence -> UNKNOWN.
- Source immutable : révision ou snapshot hash obligatoire.
- `VersionedClaim` source_fact requiert citation; claim lie finding/version/source/citations/freshness/relation.
- Conflict groups : 1 claim UNRESOLVED, mêmes valeurs AGREEMENT, valeurs différentes CONFLICT.
- Supersession explicite exige preuve/raison mais ne supprime jamais l'ancienne contradiction.
- Ranking conserve toutes les claims; inputs explicites = relation version, authority rank, freshness, mutability, tie-break ID; popularité/source count absent.
- Report/schema : IDs/groupes/digest recalculés au load, tampering/missing refs fail closed.
- Aucun nouveau network/process/secret/UI surface; rollback supprime seulement la couche dérivée.

## R7.9 execution contract

R7.9 est la prochaine subdivision autorisée après fusion de cette normalisation. Exigences gelées :

- cache et manifests sous `.kodepoia/research/` via WorkspaceBoundary;
- query/result manifests déterministes, versionnés et hashés;
- TTL/revalidation explicites selon source/mutability/freshness; aucun cache hit ne fabrique CURRENT;
- déduplication par source/version/content hash avec provenance conservée;
- invalidation par source identity, version evidence, content hash et policy/version du cache;
- synthèses de contexte bornées avec citations et evidence IDs, sans perdre le statut untrusted/guarded;
- injection d'un résumé de recherche dans Context/Memory ne transforme jamais celui-ci en expérience globale validée;
- les artefacts/citations originaux restent la preuve autoritaire et peuvent être rechargés/recalculés;
- aucune donnée secrète ne doit entrer dans les manifests/context summaries;
- manual = NONE.

## Permanent architecture/security boundaries

Preserve without reinterpretation: `WorkspaceBoundary`; ProcessSandbox + global KillSwitch; Guardian + PermissionSet; structured tool APIs; SafeChange/Backup/Recovery/Audit when required; OS-backed Secrets + redaction; Health/Budget/DataGovernance and versioned schemas; exact-head acceptance; explicit UNKNOWN/N/A/UNAVAILABLE/BLOCKED/STALE; platform-aware behavior; ADR for foundation changes. No arbitrary command/argv/cwd/host/network surface may be supplied by the model.

## Accepted model roles

- KodeFast = `granite4.1:3b`.
- KodeCore = `gpt-oss:20b`.
- KodeCoder = `ornith:9b`.
- `north-mini-code-1.0:Q4_K_M` remains a future KodeDeepCoder candidate.

## Next action

**R7.1–R7.8 COMPLETE. R7.9 NOT STARTED.** Après fusion de la normalisation R7.8, commencer **R7.9 — Research cache + Context/Memory orchestration**. Manual gate = NONE.
