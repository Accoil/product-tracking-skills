<!-- Last verified: 2026-10-01 against developer.accoil.com (concepts/track-call, concepts/group-call) -->
# Accoil — Design Constraints

Design-time constraints for products targeting Accoil as an analytics destination. These affect how you design events, not how you implement them.

## Event Names Only — No Properties

Accoil stores **event names only**. No event properties are stored or queryable. This is the single most important constraint affecting event design.

**Impact on design:**
- `report.created` with `{ type: "template" }` — Accoil sees only `report.created`, and that is fine
- **Do not put variants in event names.** No dynamic values or property values in names — `Report_Exported`, not `Report_Exported_PDF`; no `template_report.created` splits. Encoding variants creates event sprawl and fragments engagement scoring.
- Track the action once; put descriptive context on user/account traits via identify/group

**When properties still matter:**
If the tracking plan targets multiple destinations (e.g., Segment + Accoil), design events with properties as normal. Other destinations will use them. Accoil ignores the properties and counts the action by name — don't rename or split events to carry variant context for Accoil.

## Group Calls Are Essential

Accoil is account-centric. It calculates engagement scores at the account level. Without `group()` calls, events cannot be attributed to accounts and scoring fails entirely.

**Design implication:** The tracking plan MUST include group hierarchy with account as a top-level group. Every event should be attributable to an account.

**Event attribution comes from membership, not event context.** Accoil track calls carry only `userId` and the event name — no `context.groupId` or other group context. Events are attributed to groups through the user's membership (identify with `groupId`, `group()` calls); hierarchy rollup comes from `parent_group_id` traits on `group()` calls. The plan should specify when users are associated with each group level, not a group ID per event.

