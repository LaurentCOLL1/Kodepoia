# Kodepoia — R7.5 design

**Subdivision:** R7.5 — Community/forums research normalization  
**Architecture:** v1.0 frozen  
**Manual gate:** NONE  
**Foundation change:** NONE

## Objective

Normalize forum/community evidence without conflating anecdote, reaction count, score, recency or apparent consensus with official documentation. R7.5 is a normalization layer over already governed R7.3 Web evidence; it does not introduce a second network transport or any community write action.

## Trust boundary

- Community text is external untrusted data and always becomes a `ResearchArtifact` through the existing R7.1 `ResearchGuard`.
- `ResearchSourceKind.COMMUNITY` is mandatory for normalized thread artifacts.
- `authority_class` is fixed to `community`; no author role or popularity metric can promote the source to `official_docs`.
- `score` and `reaction_count` are preserved only as descriptive observed metadata.
- Vendor staff or moderator identity is an author-role observation, not a change in source class or an automatic correctness claim.

## Input model

R7.5 consumes a `RawWebResponse` that has already been produced under the R7.3 governed Web boundary. `normalize_community_html()` re-validates the raw response against `WebPolicy` before parsing and only accepts HTML/XHTML. This deliberately avoids adding a community-specific fetcher, login flow, cookie jar, proxy, POST, voting, moderation or account-automation surface.

A generic semantic HTML contract is used for deterministic normalization:

- each post/comment is represented by `<article>`;
- stable provider identifiers may use `data-post-id` or `id`;
- author/display name, parent ID, state, author role, permalink, score and reaction count are explicit data attributes when the provider can supply them;
- `<time datetime>` records creation time; `data-kind="updated"` distinguishes an observed edit time;
- `<blockquote>` represents quoted material and is never merged into the current author's body;
- optional `cite`, `data-source-post-id` and `data-source-author` preserve quote attribution evidence.

This contract is an internal normalized extraction target; provider-specific adapters may map provider HTML/API fields into it later if justified. No heuristic is allowed to invent missing author/timestamp/state data.

## Quote semantics

HTML's `<blockquote>` element represents extended quoted content and its `cite` attribute may identify the source. R7.5 uses that semantic boundary to keep quoted material separate from the current author's authored text. Nested blockquotes become distinct `CommunityQuote` objects with explicit depth; inner quote text is not duplicated into the parent quote.

Reference context used during implementation:

- MDN `<blockquote>` reference: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/blockquote
- HTML/WHATWG quotation semantics: https://html.spec.whatwg.org/

These references are parser-design context only, not an authority or compliance claim.

## Normalized contracts

`CommunityQuote` preserves text, cite locator, optional source post/author and nesting depth with a canonical `quote_id`.

`CommunityPost` preserves:

- stable post ID and canonical `evidence_id`;
- author/display metadata;
- author body with quotations removed;
- explicit state: `visible`, `edited`, `deleted`, `removed`, `unknown`;
- author role: `community`, `moderator`, `vendor_staff`, `unknown`;
- observed creation/update timestamps;
- parent-post relationship;
- permalink when supplied;
- separated quotations;
- optional score/reaction count as non-authoritative observations.

Deleted/removed posts keep their state but never treat provider placeholder text as authored evidence.

`CommunityThread` validates unique post IDs and parent references, records source URL/retrieval time/title/platform, fixes `authority_class=community`, and derives a canonical thread digest from source + normalized post evidence.

## Hidden content and prompt injection

`script`, `style`, `noscript` and `template` text is excluded from authored evidence. Visible post and quote content is not silently stripped for instruction-like text: it is retained as evidence and the final artifact is passed through `ResearchGuard`, allowing prompt-injection indicators to remain auditable while never becoming agent instructions.

## Persistence

The normalized thread JSON is deterministic and stored through the existing `ResearchStore` under `.kodepoia/research/`. Cache reuse is content-addressed and does not convert community evidence into fresh or official evidence. R7.5 sets freshness to `UNKNOWN`; richer cross-source/version reasoning remains R7.8.

## Schema

`schemas/community-thread-v1.schema.json` fixes the machine shape, permitted states/roles, digest fields, quote nesting and `authority_class=community`. A schema violation cannot silently promote a community thread to official evidence.

## Tests

Deterministic tests cover:

- author/timestamp/parent/permalink preservation;
- nested quote separation and attribution;
- deleted/removed semantics;
- vendor-staff + high popularity remaining community evidence;
- prompt injection in authored and quoted material;
- hidden script/style/template exclusion;
- missing parent and missing semantic posts as explicit unavailable states;
- HTML-only policy;
- duplicate IDs/invalid parent invariants;
- schema validation and anti-promotion constraint;
- content-addressed cache round-trip.

## Deliverables

- `src/kodepoia/intelligence/research/community.py`;
- exports in `src/kodepoia/intelligence/research/__init__.py`;
- `schemas/community-thread-v1.schema.json`;
- `tests/test_r7_5_community.py`;
- this design document;
- after exact-head acceptance: `R7_5_ACCEPTANCE.md`, `R7_STATUS.md` and continuity synchronization.

## Acceptance

R7.5 is COMPLETE only when R0 Repository Guard, Python Core all jobs and KodeStudio UI Smoke are SUCCESS on the exact final implementation head. Manual intervention is **NONE**.

## Rollback

Remove/disable the R7.5 normalizer, exports, schema and fixtures, and optionally purge community cache artifacts. No external community state has been mutated, so there is no remote rollback action.
