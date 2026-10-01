<!-- Last verified: 2026-10-01 against Userpilot docs (docs.userpilot.com), npm userpilot v1.4.3 -->
# Userpilot Implementation Reference

## Overview

Userpilot is a product growth platform. It combines in-app engagement (flows, checklists, tooltips, banners, surveys/NPS, resource centers) with product analytics: trends, funnels, paths, retention, product-usage dashboards, session replay, and user and company profiles. It has a first-class **Company** entity. Funnel reports can be run at user or company level, and every event carries the user's `company_id`. It is proprietary and cloud-only. Pricing is based on monthly active users (MAU).

**Category:** Product Adoption / Digital Adoption
**B2B Fit:** Full. It has native users, companies (accounts), and custom events with properties. The main constraint is that the account model is **flat**: each user belongs to exactly one company, and there are no parent/child hierarchies or multiple group types. See [Group Context on Track Calls](#group-context-on-track-calls).

Userpilot can be the primary analytics destination for a product-led B2B team that also wants in-app guidance. Teams that need multi-level account hierarchies, users who belong to several workspaces, or warehouse-grade event querying should pair it with a CDP or product analytics tool (Segment, Amplitude, Mixpanel, PostHog) and send the same identify, group and track calls to both.

## SDK Options

| Environment | Integration | Install |
|---|---|---|
| Browser (script) | `https://js.userpilot.io/sdk/latest.js` | Script tag in `<head>` |
| Browser (npm) | `userpilot` | `npm install userpilot` |
| Server (any language) | HTTP API (`https://analytex.userpilot.io`) | No SDK. Use raw `fetch()` calls with an API Key |
| Segment | "Userpilot Web (Actions)" (device mode), "Userpilot Cloud (Actions)" (cloud mode) | Add a destination in the Segment catalog |
| RudderStack | Userpilot destination (Beta; device and cloud mode) | Add a destination in RudderStack |
| Mobile | iOS, Android, React Native, Flutter, Capacitor, Cordova, MAUI SDKs | See the Userpilot mobile docs |

There is no official Node.js SDK. Server-side calls go directly to the HTTP API.

## Integration

### Script Tag

Add the Userpilot snippet at the beginning of the `<head>` on every page. The App Token is under Settings > Environment. Use the staging token in staging environments; the two environments are fully separate.

```html
<script>window.userpilotSettings = {token: "YOUR_APP_TOKEN"};</script>
<script src="https://js.userpilot.io/sdk/latest.js"></script>
```

### npm Package

```bash
npm install userpilot
```

```typescript
import { Userpilot } from 'userpilot';

// Second argument (userpilotSettings) is optional
Userpilot.initialize('YOUR_APP_TOKEN');
```

When you use the npm package, call methods on the imported `Userpilot` object (`Userpilot.identify(...)`, `Userpilot.reload()`). With the script tag, call them on the global `window.userpilot`.

### userpilotSettings Options

| Key | Purpose |
|---|---|
| `token` | App Token (required) |
| `version` | Pin a specific SDK version |
| `endpoint` / `domain` | Proxy endpoint or CNAME domain (custom domain hosting, helps with ad blockers) |
| `pageview` | What to collect from URLs: `pathonly`, `withhash`, `fullurl` |
| `auto_props` | Toggle automatic property collection |
| `auto_capture` | Auto-capture privacy settings (exclude or mask elements) |
| `sri` | Subresource Integrity hash |

## Initialization

Loading the script or npm package does not activate Userpilot. Nothing is displayed or tracked until `identify()` (or `anonymous()` on public pages) is called. `reload()` has no effect before the user is identified.

## User Identification

User identification is the core requirement. Guides, checklists, NPS surveys, analytics and company roll-ups all depend on a stable user ID.

**Browser (script tag):**

```javascript
userpilot.identify('usr_123', {
  name: 'Jane Smith',
  email: 'jane@example.com',
  role: 'admin',
  created_at: '2024-01-15T00:00:00Z',   // ISO 8601
  company: {
    id: 'acc_456',                        // Required whenever company is passed
    name: 'Acme Corp',
    plan: 'enterprise',
    created_at: '2023-06-01T00:00:00Z',
    monthly_spend: 5000
  }
});
```

**Browser (npm):**

```typescript
import { Userpilot } from 'userpilot';

Userpilot.identify('usr_123', {
  name: 'Jane Smith',
  email: 'jane@example.com',
  role: 'admin',
  created_at: '2024-01-15T00:00:00Z',
  company: {
    id: 'acc_456',
    name: 'Acme Corp',
    plan: 'enterprise',
    created_at: '2023-06-01T00:00:00Z'
  }
});
```

**Server (HTTP API):**

```typescript
await fetch('https://analytex.userpilot.io/v1/identify', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Token ${process.env.USERPILOT_API_KEY}`,
    'X-API-Version': '2020-09-22'
  },
  body: JSON.stringify({
    user_id: 'usr_123',
    metadata: {
      name: 'Jane Smith',
      email: 'jane@example.com',
      created_at: '2024-01-15T00:00:00Z'
    },
    company: { id: 'acc_456' }   // Optional; if present, id is required
  })
});
// 202 Accepted on success
```

**Key points about identify:**

| Aspect | Detail |
|---|---|
| First argument | Unique, stable user ID (string, required). Must be unique per environment. |
| Second argument | User properties, plus an optional nested `company` object |
| Reserved user fields | `name`, `email`, `created_at` (alias `signed_up_at`). `first_seen_at` and `last_seen_at` are set automatically. |
| Property types | String, number, boolean, date (ISO 8601). Arrays are not supported; use comma-separated strings. |
| Merge behavior | Properties merge with existing values. Set a property to `null` to remove it. |
| Repeat calls | Safe. Call again whenever user properties change. |

**When to call:** In multi-page apps, call on every page load. In SPAs, call once after successful authentication (and again when properties change), then call `reload()` on every route change.

### SPA Route Change Handling

```typescript
// Call on every route change, and only after identify()
userpilot.reload();

// Optionally pass a URL to override the detected page URL
userpilot.reload({ url: 'https://app.example.com/dashboard' });
```

For React Router:

```typescript
import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

function App() {
  const location = useLocation();

  useEffect(() => {
    if (isAuthenticated) {
      userpilot.reload();
    }
  }, [location]);

  return <Routes>...</Routes>;
}
```

In the Segment Web (Actions) destination, `analytics.page()` maps to `userpilot.reload()`.

### Anonymous Users

`anonymous()` generates a session-based unique ID so content can be shown on public or pre-login pages without user data.

```javascript
// For public/pre-login pages. No parameters.
userpilot.anonymous();
```

Anonymous users count toward MAU. To target content only at anonymous users, set the audience condition to "User Data" => "user id" => doesn't exist. Content set to "All users" also shows to anonymous visitors.

## Group / Company Identification

Userpilot has a first-class Company entity with its own profile, properties, dashboard, segments and company-level reporting (funnels can be run at company level; the Companies dashboard shows activity, events, sessions and NPS per company). There is no separate `group()` method in the JavaScript SDK. The user's company is set through the nested `company` object in `identify()`, and company properties can also be written server-side with the Identify Company API.

**Rules (from the Userpilot data model):**
- `company.id` is required whenever a `company` object is sent.
- **A user belongs to one company at a time.** Sending a different `company.id` moves the user to the new company.
- Company properties merge, as user properties do.
- A company appears in the Companies dashboard only after at least one user is associated with it.

**Browser (associate the user and set company traits):**

```javascript
userpilot.identify('usr_123', {
  company: {
    id: 'acc_456',
    name: 'Acme Corp',
    plan: 'enterprise',
    created_at: '2023-06-01T00:00:00Z',
    employee_count: 50,
    monthly_spend: 5000
  }
});
```

**Server (update company traits, e.g. from billing or CRM):**

```typescript
await fetch('https://analytex.userpilot.io/v1/companies/identify', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json, text/plain, */*',
    'Authorization': `Token ${process.env.USERPILOT_API_KEY}`
  },
  body: JSON.stringify({
    company_id: 'acc_456',
    metadata: {
      name: 'Acme Corp',
      plan: 'enterprise',
      monthly_spend: 5000
    }
  })
});
// 200 OK on success. Metadata values must be primitives.
```

**Server (associate a user with a company):** send `company: { id: 'acc_456' }` on the HTTP Identify User call (see above). The Identify Company endpoint updates company traits only; it does not attach users.

**Via a CDP:** Segment and RudderStack `group()` calls map to Userpilot companies (Segment Cloud (Actions) "Identify Company" mapping is triggered by `type = "group"`; Userpilot's docs state Segment group properties appear under Companies). This is the common path for B2B teams that already have a CDP.

## Custom Events

Custom events serve two purposes:
1. **Trigger and target experiences.** Show a flow, checklist or survey when an event fires, or segment users by event history.
2. **Product analytics.** Events feed trends, funnels, paths, retention and the product-usage dashboards.

### Track Events

**Browser:**

```javascript
userpilot.track('report_created', {
  report_id: 'rpt_789',
  report_type: 'standard'
});

// Without properties
userpilot.track('onboarding_completed');
```

**Server (HTTP API):**

```typescript
await fetch('https://analytex.userpilot.io/v1/track', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Token ${process.env.USERPILOT_API_KEY}`,
    'X-API-Version': '2020-09-22'
  },
  body: JSON.stringify({
    user_id: 'usr_123',
    event_name: 'subscription_upgraded',
    metadata: { from_plan: 'pro', to_plan: 'enterprise' }
  })
});
// 202 Accepted. The user must already exist in Userpilot.
```

Property values must be primitives (string, number, boolean or null). Nested objects and arrays are not supported. Event metadata is limited to 10 KB. Server-tracked events can take up to 15 minutes to appear in the dashboard. Use browser `track()` when an event must trigger content immediately.

### Auto-captured Events

When auto-capture is enabled, the SDK also records `$pageview`, `$click`, `$change` and `$submit`. These power "labeled events" and "tagged pages" that can be defined in the dashboard without code. Coded `track()` calls remain the reliable way to capture product events that match your tracking plan.

### Trigger Experiences Programmatically

```javascript
// Force a specific flow or other content to show, bypassing targeting rules
userpilot.triggerById(17);
```

The content ID is in the experience settings in the Userpilot dashboard.

## Group Context on Track Calls

- **Automatic attribution:** every event automatically carries the `company_id` of the user's current company. There is no per-event group parameter, and you do not need to add `account_id` as an event property for company-level reporting.
- **Single level only:** Userpilot has one group type (Company). It has no workspace, team or project level and no parent/child roll-ups.
- **Multi-workspace products:** because a user belongs to one company at a time, switching `company.id` in `identify()` moves the user. If users work across several accounts at once, decide which level maps to Userpilot's Company, typically the billing account. Send finer levels (workspace, project) as event properties, and send the full hierarchy to a tool that supports it (Segment, Amplitude, Mixpanel, PostHog, Accoil).

## Guides and Checklists

Guides, checklists, tooltips and resource centers are configured in the Userpilot dashboard (using the Chrome extension), not in code. The SDK's role is to:

1. **Identify the user and company** so targeting rules can be evaluated
2. **Track events** that trigger experiences and complete checklist items
3. **Reload on navigation** so page-based targeting works
4. **Programmatically trigger** specific experiences when needed

### Checklist Example (Dashboard-Configured, Code-Triggered)

```javascript
// 1. User logs in: identify user and company
userpilot.identify('usr_123', {
  name: 'Jane Smith',
  email: 'jane@example.com',
  created_at: '2024-01-15T00:00:00Z',
  company: { id: 'acc_456', name: 'Acme Corp' }
});

// 2. User completes onboarding steps: track events
userpilot.track('profile_completed');
userpilot.track('first_report_created');
userpilot.track('team_member_invited');

// 3. On route change: reload to show context-appropriate guides
userpilot.reload();
```

### Listening to Experience Events

```javascript
// Supported events: 'started', 'completed', 'dismissed', 'step'
userpilot.on('completed', (event) => {
  console.log('User completed experience:', event);
});

// One-time listener
userpilot.once('started', (event) => {
  console.log('First experience started:', event);
});

// Remove a listener
userpilot.off('completed');
```

## Bulk Updates (Server)

For CRM or warehouse syncs, use the bulk endpoints instead of looping over real-time calls.

```typescript
// Users (company_id per record associates users with companies)
await fetch('https://analytex.userpilot.io/v1/users/bulk_identify', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json, text/plain, */*',
    'Authorization': `Token ${process.env.USERPILOT_API_KEY}`
  },
  body: JSON.stringify({
    users: [
      { user_id: 'usr_123', company_id: 'acc_456', metadata: { role: 'admin' } }
    ]
  })
});

// Companies
await fetch('https://analytex.userpilot.io/v1/companies/bulk_identify', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json, text/plain, */*',
    'Authorization': `Token ${process.env.USERPILOT_API_KEY}`
  },
  body: JSON.stringify({
    companies: [
      { company_id: 'acc_456', metadata: { plan: 'enterprise', mrr: 5000 } }
    ]
  })
});
// Both return a queued job object. Only one bulk job (user or company) runs at a time.
```

Both endpoints also accept NDJSON file uploads (`multipart/form-data`, field `file`, max 50 MB).

## Required Fields

| Method | Required Fields | Notes |
|---|---|---|
| `identify()` (SDK) | user ID | `company.id` required if `company` is passed |
| `POST /v1/identify` | `user_id` | Optional `metadata`, `company: { id }`. Headers: `Authorization`, `X-API-Version: 2020-09-22` |
| `POST /v1/companies/identify` | `company_id` | Optional `metadata`. Headers: `Authorization`, `Accept` |
| `track()` (SDK) | event name | Optional properties |
| `POST /v1/track` | `user_id`, `event_name` | Optional `metadata`. Headers: `Authorization`, `X-API-Version: 2020-09-22`. User must already exist. |
| `POST /v1/users/bulk_identify` | `users[].user_id` | Optional `company_id`, `metadata` |
| `POST /v1/companies/bulk_identify` | `companies[].company_id` | Optional `metadata` |

## Limits

| Constraint | Value |
|---|---|
| Real-time Identify API | 600 requests/minute per application token (429 when exceeded) |
| Real-time Track API | 600 requests/minute per application token (429 when exceeded) |
| Bulk jobs | One job at a time (409 Conflict otherwise); processed at 1,800 records/minute |
| Bulk payload | 10,000 records per request (JSON or NDJSON); 50 MB per file upload (413 when exceeded) |
| Properties per user / company | 500 |
| Property name / value length | 255 / 65,535 characters |
| Event metadata size | 10 KB |
| Property value types | Primitives only (string, number, boolean, null, ISO 8601 dates); no arrays or nested objects |
| Data residency | Default `analytex.userpilot.io`; EU uses `analytex-eu.userpilot.io`; Enterprise may have a dedicated endpoint. Check Settings > Environment. |

## Authentication

| Credential | Used by | Where |
|---|---|---|
| App Token | Browser SDK, Segment Web (Actions), RudderStack device mode | Settings > Environment |
| API Key | HTTP API, Segment Cloud (Actions), RudderStack cloud mode | Settings > Environment |

HTTP header format: `Authorization: Token {API_KEY}`. All requests must use HTTPS. Never expose the API Key in client-side code.

## Via Segment or RudderStack

| CDP | Destination | Mapping |
|---|---|---|
| Segment | **Userpilot Web (Actions)**, device mode, App Token | `identify` → `userpilot.identify`, `track` → `userpilot.track`, `page` → `userpilot.reload`; also accepts `group` and `alias` |
| Segment | **Userpilot Cloud (Actions)**, cloud mode, API Key + API Endpoint | Identify User (`type = "identify"`), Track Event (`type = "track"`), Identify Company (`type = "group"`); max 5 mappings per instance |
| RudderStack | **Userpilot** (Beta, built by Userpilot) | Identify, Track, Group supported; Page in device mode only. Device mode uses the App Token; cloud mode uses API Key + HTTP API endpoint. |

Userpilot's separate outbound **Segment integration** (Configure > Integrations) sends Userpilot's own content events (flow/checklist/survey seen, completed, dismissed; NPS; form submissions) back to Segment. Tracked events, labeled events and tagged pages are not sent outbound.

## Privacy Controls

### Consent

```javascript
// Do not identify users who have not consented. Userpilot stays inactive.
if (userHasConsentedToAnalytics()) {
  userpilot.identify('usr_123', { ... });
}
```

### Clear User Data / Session Management

```javascript
userpilot.clean();       // Clear Userpilot storage and session data (e.g. on logout)
userpilot.destroy();     // Fully clear storage and remove all active content
userpilot.suppress();    // Stop all SDK operations (e.g. consent withdrawn)
userpilot.unsuppress();  // Resume SDK operations
userpilot.end();         // End the currently running flow
```

### Auto-capture and Session Replay Masking

Userpilot auto-captures clicks, inputs and page views, and offers session replay. Configure what is collected with `auto_capture` in `userpilotSettings`, and review the dashboard's Data Capture & Privacy settings.

```javascript
window.userpilotSettings = {
  token: 'YOUR_APP_TOKEN',
  auto_capture: {
    enabled: true,
    excluded_elements: ['#billing-widget', "[data-up-ignore='true']"],
    masked_elements: ["input[name='email']", '[data-up-mask]'],
    excluded_attributes: ['data-secret']
  }
};
```

Deletion of users and companies (GDPR/CCPA) is available through the Delete API.

### Data Sent to Userpilot

- User ID and properties passed to `identify()`
- Company ID and properties
- Events passed to `track()`, plus auto-captured interactions (if enabled)
- Current page URL (for page-based targeting)
- Session replay recordings (if enabled)
- Browser metadata

## What Userpilot Is NOT

- **Not a multi-level account model.** It has one Company per user and no hierarchy or multiple group types (use Segment, Amplitude, Mixpanel, PostHog or Accoil for hierarchies).
- **Not server-side content delivery.** Experiences render in the browser or mobile app only. Server-side calls only feed data.
- **Not a raw-SQL warehouse.** Use the Bulk Data Export API or a CDP to get events into your warehouse.
- **Not a feature-flag or code-experimentation tool.** Use LaunchDarkly, PostHog or Statsig.

## Forge Compatibility

**Approved domains:**
- `*.userpilot.io`

```yaml
permissions:
  external:
    fetch:
      backend:
        - address: "*.userpilot.io"
          category: analytics
          inScopeEUD: false
```

**Considerations for Forge apps:** Userpilot runs in the browser and injects DOM elements (tooltips, modals, guides) into the page. In Forge Custom UI (sandboxed iframe), the Userpilot script would need to run inside the iframe. This means:

1. Userpilot guides will appear inside the Forge app iframe, not in the parent Atlassian page
2. The current page URL visible to Userpilot is the iframe URL, not the Atlassian page URL. Configure targeting rules accordingly.
3. Ensure no in-scope End User Data (issue titles, page content) is passed to Userpilot via `identify()` or `track()` properties
4. Auto-capture and session replay can collect on-screen content. Disable them (`auto_capture: { enabled: false }`) or mask aggressively in Forge apps.

## Common Pitfalls

1. **Not calling identify before anything else.** Userpilot does nothing until `identify()` (or `anonymous()`) is called. `reload()` before `identify()` has no effect.

2. **Forgetting to call reload() on SPA route changes.** Userpilot evaluates targeting rules against the current URL. Call `userpilot.reload()` on every route change.

3. **Passing company data outside the company object.** Company properties must be nested inside `company: { id, ... }`. Flat properties like `company_name: 'Acme'` become user properties. A `company` object without `id` is rejected (400 on the HTTP API).

4. **Assuming users can belong to multiple companies.** Sending a different `company.id` moves the user. For multi-workspace products, map one level (usually the billing account) to Company and carry the others as properties.

5. **Using the App Token for the HTTP API, or omitting headers.** Server calls need the API Key (`Authorization: Token ...`), and `/v1/identify` and `/v1/track` also require `X-API-Version: 2020-09-22`. A 401 usually means the App Token was used by mistake.

6. **Tracking server events for users that don't exist yet.** `/v1/track` requires the user to already be identified. Call `/v1/identify` first, for example at signup.

7. **Sending nested objects or arrays as properties.** Only primitives are supported. Flatten objects and join arrays into strings.

8. **Wrong regional endpoint.** EU and Enterprise accounts may not use `analytex.userpilot.io`. Copy the endpoint from Settings > Environment.

9. **Not sending created_at.** Without `created_at` on users and companies, time-based targeting (e.g. "created in the last 7 days") and lifecycle analysis do not work.

## Debugging

### Verify Userpilot Is Loaded

```javascript
typeof window.userpilot !== 'undefined'  // Should be true
```

<!-- UNVERIFIED: isIdentified() and a ?userpilot_debug=true URL flag were previously documented here but are not in current SDK docs (checked 2026-10-01). -->

### Common Issues

| Symptom | Cause | Fix |
|---|---|---|
| `userpilot is not defined` | SDK not loaded | Check script is in `<head>`; check CSP |
| Content not showing | User not identified | Call `identify()` before content triggers |
| Wrong content in SPA | Missing `reload()` | Call `reload()` on every route change |
| Requests blocked | Ad blocker or CSP | Allow `*.userpilot.io` (including `wss:`) in CSP, or use custom domain hosting |
| Server user not appearing | Wrong regional endpoint | Match the endpoint on Settings > Environment |

### Network Tab

- `js.userpilot.io`: SDK script
- `analytex*.userpilot.io`: identify, events and analytics (the SDK uses a WebSocket connection by default)

### Dashboard Verification

1. **Users / Companies:** confirm identified users and their company association appear. HTTP-only identifications show in Overview but not in "active" stats until a real session occurs.
2. **Events:** confirm tracked events and properties (server events can lag up to 15 minutes).
3. **Preview:** use the Chrome extension's preview to test targeting.

## Further Documentation

- **Getting Started:** https://docs.userpilot.com/
- **Web Installation (script, npm, Segment, GTM):** https://docs.userpilot.com/developer/installation/web
- **JavaScript SDK API:** https://docs.userpilot.com/developer/installation/SDK-APIs
- **Identify vs Reload:** https://docs.userpilot.com/developer/identify-vs-reload
- **Anonymous Users:** https://docs.userpilot.com/developer/installation/anonymous-user
- **Data Model (users, companies, events, limits):** https://docs.userpilot.com/reference/data-model
- **Auto-capture Privacy Settings:** https://docs.userpilot.com/developer/installation/sdk/settings/privacy
- **API Authentication:** https://docs.userpilot.com/api-references/authentication
- **API Environment / Endpoints:** https://docs.userpilot.com/api-references/environment
- **Real-Time API Overview (rate limits):** https://docs.userpilot.com/api-references/real-time/overview
- **Identify User API:** https://docs.userpilot.com/api-references/real-time/identify-user
- **Identify Company API:** https://docs.userpilot.com/api-references/real-time/identify-company
- **Track Event API:** https://docs.userpilot.com/api-references/real-time/track-event
- **Bulk User Updates:** https://docs.userpilot.com/api-references/bulk-updates/users
- **Bulk Company Updates:** https://docs.userpilot.com/api-references/bulk-updates/companies
- **Funnels (user/company level):** https://docs.userpilot.com/product-analytics/reports/funnels
- **Session Replay:** https://docs.userpilot.com/sessions/session-replay
- **Content Security Policy:** https://docs.userpilot.com/developer/security/csp
- **Segment Web (Actions) destination:** https://segment.com/docs/connections/destinations/catalog/actions-userpilot-web/
- **Segment Cloud (Actions) destination:** https://segment.com/docs/connections/destinations/catalog/actions-userpilot-cloud/
- **RudderStack destination:** https://www.rudderstack.com/docs/destinations/streaming-destinations/userpilot/
