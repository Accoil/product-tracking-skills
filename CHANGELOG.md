# Changelog

All notable changes to Product Tracking Skills. Releases: https://github.com/Accoil/product-tracking-skills/releases

## v1.2.3 — 2026-10-09

Security fixes in the example code, prompted by OpenAI's plugin skill scan.

- **No API key in debug logs.** The generic dispatcher example in `implementation-architecture.md` (implement and audit skills) logged the request body, which included the API key. Debug mode now logs only the event name; how the key is sent is unchanged.
- **No PII in debug logs.** Debug examples log event names and property keys, not payload values (including the Forge example).
- **Verification is for the user to run.** `implement-tracking` now puts its verification checklist in `tracking/README.md` and doesn't run tracking calls, send events or use API keys itself.

## v1.2.2 — 2026-10-08

OpenAI plugin directory submission prep.

- **Neutral destination suggestions** — `model-product` no longer steers users toward Accoil; it starts from what the codebase already uses and otherwise lists common options without favoring one

## v1.2.1 — 2026-10-01

Template fixes reported in issues #12–#15.

- **`tracking-plan-schema.yaml` now parses** — `snapshot_sync` entries moved under a `traits:` key, matching the design skill (#12)
- **Example event `group_level`** — `report.created` uses `account`, the only group the template defines; added a note that every `group_level` must match a `groups[].type` (#13)
- **`meta.version` is a semver string** (`"1.0.0"`) in the schema and the design skill, matching `instrument-new-feature`'s major/minor/patch rules (#14)
- **No PII in the core template** — `user.invited` replaces required `invitee_email` with `invitation_id` and `invitee_email_domain` (also in the walkthrough and B2B spec) (#15)

## v1.2.0 — 2026-10-01

- **OpenAI support** alongside Claude Code: portable `plugin.json` (`product-tracking`), assets, and per-skill Codex metadata (`skills/*/agents/openai.yaml`)
- **New integrations** (25 destinations): CustomerScore.io (new); Userpilot rebuilt as Product Adoption with full B2B support
- **Updated**: every destination reference re-verified against vendor docs; Accoil name-only track calls; `context.groupId` advice dropped for Segment/RudderStack; Intercom JWT; LaunchDarkly v4; Sentry v11
- **Removed**: Beam Analytics (shut down), empty `hooks/hooks.json`

## v1.1.0 — 2026-03-11

- Tracking watchdog background agent
- Intercom destination

## v1.0.2 — 2026-03-10

- 18 new analytics destination references

## v0.5.0 — 2026-02-13

- Initial release
