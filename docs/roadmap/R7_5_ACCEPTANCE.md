# Kodepoia — R7.5 acceptance

**Subdivision:** R7.5 — Community/forums research normalization  
**Status:** COMPLETE  
**Accepted implementation head:** `12d5580ff3f8c6d9d0fb211e1688e3ba37dcdce5`  
**Implementation PR:** #68  
**Implementation merge:** `b02dfba4b6a6a4c0a6ec19d552e569b56845a4ea`  
**Manual:** NONE

## Exact-head CI evidence

All required gates ran against exact implementation head `12d5580ff3f8c6d9d0fb211e1688e3ba37dcdce5`:

- R0 Repository Guard #976 / run `32590366852`: **SUCCESS**;
- Python Core #950 / run `32590366851`: **SUCCESS**, 5/5 jobs;
- authoritative Ubuntu suite: **400 passed / 3 skipped / 46 warnings**;
- Python Core Windows test job: **SUCCESS**;
- package-build Ubuntu: **SUCCESS**;
- package-build Windows: **SUCCESS**;
- embedded KodeStudio UI job: **SUCCESS**;
- KodeStudio UI Smoke #917 / run `32590366853`: **SUCCESS**.

Manual intervention was not required.

## Accepted capability

R7.5 provides deterministic community/forum normalization over already governed R7.3 raw Web evidence:

- thread/post/comment identity;
- author/display metadata;
- creation/update timestamps when observed;
- parent-post relationships;
- visible/edited/deleted/removed/unknown states;
- permalink preservation;
- nested quote separation and quote-source metadata;
- community/moderator/vendor-staff/unknown author roles;
- descriptive score/reaction observations;
- content-addressed normalized evidence;
- fixed community authority class;
- ResearchGuard coverage of visible authored/quoted content;
- versioned `community-thread-v1` schema.

## Accepted trust/provenance invariants

1. Community evidence always remains `ResearchSourceKind.COMMUNITY`.
2. `authority_class` is fixed to `community` by the normalized contract and JSON Schema.
3. High score/reaction counts do not promote a source to official authority; `popularity_is_authority=false` is explicit artifact metadata.
4. Vendor staff/moderator is an observed author role, not an automatic official-document classification or correctness claim.
5. `<blockquote>` content is separated from the current author's body; nested quotes are distinct and preserve nesting depth.
6. Deleted/removed provider placeholders are not treated as authored text.
7. Parent IDs must resolve inside the normalized thread; missing parents fail into explicit unavailable evidence rather than a guessed relationship.
8. `script`, `style`, `noscript` and `template` content does not become visible post evidence.
9. Prompt-like content is retained as evidence but routed through the existing R7.1 `ResearchGuard`; it never becomes agent instruction.
10. R7.5 does not introduce posting, voting, moderation, account automation, login bypass or a second network stack.

## External reference context

The quote-separation design was cross-checked against the HTML/MDN semantics for `<blockquote>` and its optional `cite` source reference. These references are parser-design context only and do not make a community post authoritative.

## Rollback

Rollback is repository-local: remove/disable the R7.5 normalizer, exports, schema and tests and optionally purge community artifacts under the governed research cache. R7.5 performs no remote community mutation.
