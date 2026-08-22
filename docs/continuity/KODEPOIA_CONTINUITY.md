# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R6 sont COMPLETE. Le planning R7 est ACCEPTED. R7.1–R7.5 sont COMPLETE ; R7.6 est NOT STARTED.** R7.5 a été accepté sur le head exact `12d5580ff3f8c6d9d0fb211e1688e3ba37dcdce5` avec R0 #976 / `32590366852`, Python Core #950 / `32590366851` cinq jobs SUCCESS, suite Ubuntu `400 passed / 3 skipped / 46 warnings`, et UI Smoke #917 / `32590366853` SUCCESS; PR #68 merge `b02dfba4b6a6a4c0a6ec19d552e569b56845a4ea`; manual R7.5 = NONE. **La prochaine implémentation autorisée est R7.6 — YouTube metadata + transcript ingestion**, uniquement après fusion de la normalisation R7.5. Lire l'architecture gelée, `R6_STATUS.md`, `R6_INTEGRATED_ACCEPTANCE.json`, `R7_PLAN.md`, `R7_PLANNING_ACCEPTANCE.md`, `R7_STATUS.md`, les `R7_1` à `R7_5` DESIGN/ACCEPTANCE et ce fichier avant toute suite.

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
- R7.5 : COMPLETE — head `12d5580ff3f8c6d9d0fb211e1688e3ba37dcdce5`; R0 #976 / `32590366852`; Python #950 / `32590366851` 5/5 (`400 passed / 3 skipped / 46 warnings` Ubuntu); UI #917 / `32590366853`; PR #68 merge `b02dfba4b6a6a4c0a6ec19d552e569b56845a4ea`; manual NONE.
- R7.6–R7.11 : NOT STARTED; next = R7.6.
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

- External research is data, never agent instruction; `ResearchGuard` remains the single content trust boundary.
- Status/freshness stay explicit; unavailable or unmeasured data does not fabricate PASS/CURRENT.
- IDs/digests and persisted evidence are deterministic/recomputable; `.kodepoia/research/` remains `WorkspaceBoundary`-confined.
- R7.2 local/official docs are offline-first and preserve exact lines/version evidence.
- R7.3 Web is typed GET-only with public DNS/IP validation, pinned resolved address, redirect revalidation, Guardian NETWORK, bounded MIME/bytes/timeout/rate and deterministic fake transport.
- R7.4 GitHub is read-only typed REST on fixed origin; mutable refs resolve to exact SHAs; pagination/rate-limit evidence is explicit; optional auth only via KodeSecrets.

## R7.5 accepted community baseline

- Community/forum evidence is always `ResearchSourceKind.COMMUNITY` with `authority_class=community`.
- Score/reaction/popularity metadata is descriptive only; popularity/consensus never becomes official authority.
- Vendor staff/moderator is an author-role observation, not an official-document promotion.
- Thread/post IDs, author/display metadata, timestamps, parent relationships, permalinks and states are preserved when observed.
- States are explicit: visible/edited/deleted/removed/unknown.
- `<blockquote>` quoted text is separated from current-author text; nested quote depth/source evidence is retained.
- Deleted/removed placeholders do not become authored evidence.
- `script`, `style`, `noscript`, `template` text is excluded from visible authored evidence.
- Visible prompt injection remains evidence and is flagged by ResearchGuard; it never becomes instruction.
- R7.5 adds no posting/voting/moderation/account automation and no second network stack.

## R7.6 design constraints already verified against official YouTube docs

- `videos.list` is a read-only GET metadata endpoint; selected `part` fields such as `snippet` provide title/description/channel metadata. Current documented quota cost is 1 unit.
- `captions.list` lists caption-track metadata but does **not** return caption text; it requires authorization and currently costs 50 quota units.
- `captions.download` retrieves the caption track but requires authorization and the user to have permission to edit the video; current documented cost is 200 units.
- Therefore R7.6 must **not** claim that the official Data API permits arbitrary public transcript download. Public metadata and transcript ingestion are separate provider capabilities.
- No audiovisual-content downloader/cache, offline playback, login automation, DRM bypass or undocumented restriction bypass is to be added. Local media/STT/frame fallback remains R7.7.
- API credentials/tokens remain KodeSecrets references resolved outside model/artifact context.

Reference context: current official YouTube Data API `videos.list`, `captions.list`, `captions.download`, quota documentation and YouTube API Developer Policies. These references guide implementation only; Kodepoia makes no legal/compliance certification.

## Permanent architecture/security boundaries

Preserve without reinterpretation: `WorkspaceBoundary`; ProcessSandbox + global KillSwitch; Guardian + PermissionSet; structured tool APIs; SafeChange/Backup/Recovery/Audit when required; OS-backed Secrets + redaction; Health/Budget/DataGovernance and versioned schemas; exact-head acceptance; explicit UNKNOWN/N/A/UNAVAILABLE/BLOCKED/STALE; platform-aware behavior; ADR for foundation changes. No arbitrary command/argv/cwd/host/network surface may be supplied by the model.

## Accepted model roles

- KodeFast = `granite4.1:3b`.
- KodeCore = `gpt-oss:20b`.
- KodeCoder = `ornith:9b`.
- `north-mini-code-1.0:Q4_K_M` remains a future KodeDeepCoder candidate.

## Next action

**R7.1–R7.5 are COMPLETE. R7.6 is NOT STARTED.** After the R7.5 normalization PR merges, start **R7.6 — YouTube metadata + transcript ingestion**. Implement URL/video-ID normalization, metadata provider, transcript provider contracts, track/language/type/timestamp provenance, guarded transcript artifacts and explicit unavailable/blocked states. Keep official captions access aligned with its real OAuth/edit-permission contract. Manual R7.6 = CONDITIONAL; deterministic fixtures should be sufficient for normal acceptance unless an authoritative live provider proof is explicitly required.
