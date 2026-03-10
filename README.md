This is a fork and I want to change things

# Product Tracking Skills

**Your product isn't data-ready. These skills fix that.**

You're paying for Amplitude, Mixpanel, or PostHog — but you can't answer three basic questions: Which features do your customers actually use? Where do users drop off? Which accounts are at risk?

The problem isn't your analytics tool. It's your instrumentation.

Product Tracking Skills is a set of open-source AI agent skills that scan your codebase, design an opinionated tracking plan, and generate real instrumentation code — for any analytics SDK, in any AI agent tool.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/accoilhq/product-tracking-skills)](https://github.com/accoilhq/product-tracking-skills)

**Works in:** Claude Code &middot; Codex &middot; VS Code &middot; any tool with AI agent support

---

## See It In Action

Open your codebase in any AI agent tool and start talking:

```
You: audit tracking
AI:  [Finds every tracking call, identifies gaps and issues]
     Found 14 events across 8 files. Saved to .telemetry/current-state.yaml

You: design tracking plan
AI:  [Designs best-practice tracking plan, produces delta from current state]
     22 events. Delta: add 10, rename 3, change 4, remove 1. Review and adjust.

You: implement tracking
AI:  [Generates typed wrapper functions, delivery infrastructure, event constants]
     Tracking code ready in tracking/
```

Seven skills. One session. Data-ready.

---

## The Problem

Most B2B products have one of these situations:

**No tracking.** You know you need it. It's been on the backlog for six months. It never happens.

**Broken tracking.** 14 events across 23 files. Some camelCase, some snake_case. No account context. Three events that do the same thing. Five that nobody uses.

**Decayed tracking.** Someone set it up 18 months ago. Twelve features have shipped since. None were instrumented. The tracking plan — if one exists — is a lie.

In all three cases, your CS team can't see which accounts are healthy. Your product team can't measure feature adoption. You can't give investors real usage numbers. And the analytics tool you're paying for? It works fine. It's just being fed garbage.

---

## What These Skills Do

They make your product **data-ready** — properly instrumented so any analytics tool downstream can answer real questions about how customers use your product.

The focus is **users, accounts, features, and lifecycle events**. The raw signals your product emits. Not vanity pageviews. Not generic clicks. Semantic events with meaning, properties, and account attribution.

### What They Don't Do

- Define KPIs or success metrics
- Build dashboards or reports
- Interpret what the data means
- Replace any analytics tool

The boundary is deliberate. This produces instrumentation. What happens downstream — scoring, dashboards, alerts — belongs to tools like [Amplitude](https://amplitude.com), [PostHog](https://posthog.com), [Mixpanel](https://mixpanel.com), or [Accoil](https://accoil.com).

---

## What's Inside

These aren't thin prompts. Each skill includes a built-in reference library:

- **19 common instrumentation mistakes** and how to detect them
- **Anti-pattern detection** — PII in event properties, noise events, redundant tracking, blocking calls
- **Naming conventions** — dot.notation for event names (`report.created`), snake_case for properties and traits (`signup_source`)
- **B2B entity modeling** — two-entity model, group hierarchies, instance vs user-level tracking
- **7 category templates** — opinionated starting points for B2B SaaS, AI/ML, dev tools, and more
- **SDK guides** for 6 analytics platforms — correct identify, group, and track call patterns for each (and more coming)

The skills encode the kind of knowledge that usually lives in a senior analytics engineer's head — except it doesn't walk out the door when they leave.

---

## How It Works

Seven skills. Each produces artifacts that feed the next. Everything version-controlled in your repo.

```
Business Case ──▶ Model ──▶ Audit ──▶ Design ──▶ Instrument ──▶ Implement ──▶ Maintain
```

| Phase | What Happens | You Get |
|-------|-------------|---------|
| **Business Case** | Builds a stakeholder-ready case for why product telemetry matters — blind spots, business value, effort involved | `.telemetry/business-case.md` |
| **Model** | Scans your codebase to understand the product — entities, features, value flow | `.telemetry/product.md` |
| **Audit** | Reverse-engineers current tracking. Every event, property, identity call. No judgment. | `.telemetry/current-state.yaml` |
| **Design** | Designs an opinionated tracking plan + explicit delta from current state | `.telemetry/tracking-plan.yaml` + `delta.md` |
| **Instrument** | Translates the plan into SDK-specific guidance with template code | `.telemetry/instrument.md` |
| **Implement** | Generates real typed wrapper functions, identity management, delivery infrastructure | `tracking/` directory |
| **Maintain** | Updates tracking when features ship. Versioned with changelog. | Updated plan + `changelog.md` |

---

## Who Is This For?

**Founders** who know they need product analytics but it's been on the backlog for six months. You can go from zero to a complete tracking plan with working code in a single session.

**Product engineers** who inherited tracking that's scattered, inconsistent, and undocumented. You get a structured system: audit what exists, design what should exist, generate typed code to close the gap.

**CS and product teams** who need feature adoption data and account health signals. You can't run the skills yourself, but you can hand engineering a clear process: "Run these skills. Get us the data we need."

If you're a B2B SaaS team and you can't answer *"which features does account X actually use?"* — start here.

---

## Supported Analytics SDKs

Code generation is SDK-specific. Not generic wrappers — real call patterns, identity management, and group handling for each platform. More will be added over time.

| Platform | Browser | Node.js |
|----------|---------|---------|
| **Segment** | `@segment/analytics-next` | `@segment/analytics-node` |
| **Amplitude** | `@amplitude/analytics-browser` | `@amplitude/analytics-node` |
| **Mixpanel** | `mixpanel-browser` | `mixpanel` |
| **PostHog** | `posthog-js` | `posthog-node` |
| **Accoil** | `tracker.js` (CDN) | Direct API |
| **RudderStack** | `rudder-sdk-js` | `@rudderstack/rudder-sdk-node` |

---

## Category Templates

The design phase picks the best starting template for your product type. All extend `b2b-saas-core`.

| Template | Best For |
|----------|----------|
| `b2b-saas-core` | Generic B2B SaaS baseline |
| `ai-ml-tools` | AI/ML products, generation, models |
| `developer-tools` | APIs, SDKs, CLI tools |
| `collaboration-tools` | Team workspaces, real-time collab |
| `form-builders` | Form creation, submissions |
| `security-products` | Security events, alerts, compliance |
| `analytics-platforms` | Analytics products tracking their own usage |

---

## Design Principles

**Opinionated defaults.** dot.notation for event names (`user.signed_up`). snake_case for properties and traits (`signup_source`). Properties over events. Minimalist coverage. We take positions so you don't have to debate them.

**Audit before design.** Capture reality first, then decide intent. The audit describes what exists. Design is where opinions live.

**Delta-driven.** The diff between current state and tracking plan is the implementation backlog. "Add 10, rename 3, change 4, remove 1." No ambiguity.

**B2B-first.** Users and accounts are first-class. Group hierarchy (account → workspace → project) is built in. Every event attributed to the correct level.

**Maintainable.** Tracking decays when features ship without instrumentation. The maintain phase prevents that. Versioning, deprecation, and changelogs are built in.

---

## What You Get

Everything lives in `.telemetry/` in your repo. Version-controlled. Survives across sessions and engineers. Nothing in someone's head. Nothing in a third-party tool.

```
.telemetry/
├── business-case.md        # Why add telemetry — stakeholder-ready
├── product.md              # What your product does, entities, value flow
├── current-state.yaml      # What's tracked today (from audit)
├── tracking-plan.yaml      # What should be tracked
├── delta.md                # Current → target diff (the backlog)
├── instrument.md           # SDK-specific instrumentation guide
├── changelog.md            # How the plan evolved over time
└── audits/
    └── 2026-02-13.md       # Timestamped audit snapshots
```

---

## Skills Reference

Each skill is self-contained with its own `references/` directory. Trigger them with natural language.

| Skill | Try saying... |
|-------|---------------|
| `product-tracking-business-case` | *"write a business case for analytics"* or *"why add tracking?"* |
| `product-tracking-model-product` | *"model this product"* or *"understand this codebase"* |
| `product-tracking-audit-current-tracking` | *"audit tracking"* or *"what's currently tracked?"* |
| `product-tracking-design-tracking-plan` | *"design tracking plan"* or *"what should we track?"* |
| `product-tracking-generate-implementation-guide` | *"create instrumentation guide"* |
| `product-tracking-implement-tracking` | *"implement tracking"* or *"generate code"* |
| `product-tracking-instrument-new-feature` | *"instrument this feature"* |

---

## Installation

### Option 1: CLI Install (Recommended)

Use `npx skills` to install skills directly:

```bash
# Install all skills
npx skills add accoilhq/product-tracking-skills

# Install specific skills
npx skills add accoilhq/product-tracking-skills --skill audit design

# List available skills
npx skills add accoilhq/product-tracking-skills --list
```

This automatically installs to your `.claude/skills/` directory.

### Option 2: Claude Code Plugin

Install via Claude Code's built-in plugin system:

```bash
# Add the marketplace
/plugin marketplace add accoilhq/product-tracking-skills

# Install all skills
/plugin install product-tracking-skills
```

### Option 3: Clone and Copy

Clone the repo and copy the skills folder:

```bash
git clone https://github.com/accoilhq/product-tracking-skills.git
cp -r product-tracking-skills/skills/* .claude/skills/
```

Once installed, open your codebase in any AI agent tool and start with a prompt like this:

### Example Prompt

```
Use the product-tracking skills to model this product, audit the current tracking,
and design a complete tracking plan. Our tracking destination is Segment — use the
Segment library. Track at the account and user level. Give me a complete, product 
analytics tracking plan.
```

This runs the full skill chain — model, audit, design — and produces a tracking plan in `.telemetry/` ready for implementation.

---

## Feedback

Found a bug? Have a suggestion? [Open an issue](https://github.com/accoilhq/product-tracking-skills/issues).

---

## License

MIT — free for any use. Built by [Accoil](https://accoil.com).
