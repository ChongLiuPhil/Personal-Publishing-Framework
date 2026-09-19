# Provider Integration Semantic Migration — 2026-09-19

**Status:** HUMAN-APPROVED / NORMATIVE MIGRATION AUDIT  
**Scope:** PPF provider-neutral semantics only

## Human authorization

On 2026-09-19 the human project owner explicitly requested that stable, provider-neutral lessons from the recent real provider pilot be migrated into durable PPF norms, while requiring that:

- provider-specific UI / token / command details stay out of the normative core;
- AI/MCP remain optional rather than a PPF conformance requirement;
- provider build success not be treated as formal production approval;
- publication permission remain separate from deployment state;
- later upstream PPF changes not be silently treated as adopted downstream.

## Promoted in this migration

This normative migration promotes only the following provider-neutral invariants:

1. Repository Integration Intent, Provider Actual State, and Human Authorization State remain distinct;
2. a provider production branch is not canonical publication production;
3. the common readiness vocabulary is a set of mappable milestones, not a rigid single-path state machine;
4. runtime verification is a first-class gate before cutover;
5. provider actions should be followed by actual-state verification and durable repository write-back;
6. canonical production cutover is an explicit gate;
7. an existing public production URL requires an explicit legacy URL policy during migration;
8. downstream adoption should record upstream version/tag/immutable commit, and later upstream changes are not automatically adopted.

## Not promoted

The following remain reference-implementation detail, dated observation, or research:

- Cloudflare UI fields and menu structure;
- Workers Builds token product constraints;
- Cloudflare-specific Profile A/B/C implementation;
- concrete Wrangler / Quarto / Node versions;
- concrete build/deploy commands;
- Cloudflare MCP/OAuth paths;
- the full Provider Integration Reconciliation Loop as a standalone formal specification.

The broader architecture research remains in `docs/PROVIDER_INTEGRATION_PATTERN_RESEARCH.md` with status `AI-PROPOSED / NON-NORMATIVE / RESEARCH NOTE` until its promotion criteria are satisfied.

## Validation requirements

This migration requires:

- synchronized Chinese canonical and English mirror;
- formal recognition of adoption metadata and generic provider-state fields in `schema/publishing.schema.json`;
- real JSON Schema validation of the reference `publishing.yaml` in Reference Template CI;
- continued compatibility of the current reference template after the schema extension.
