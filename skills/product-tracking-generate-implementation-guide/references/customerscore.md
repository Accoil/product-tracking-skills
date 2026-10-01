<!-- Last verified: 2026-10-01 against CustomerScore docs (docs.customerscore.io: Tracker, API Reference v1, Integrations) -->
# CustomerScore.io Implementation Reference

## Overview

CustomerScore.io (styled "Customerscore.io" in its docs) is a B2B customer health and engagement scoring platform for SaaS. It combines product usage, CRM, billing, and conversation data into a Fit Score, Health (engagement) Score, and churn risk per customer, and drives Smart Alerts, Playbooks, and worklists from them. Cloud-only, proprietary SaaS, hosted on AWS in Frankfurt, Germany (GDPR).

**Category:** B2B Engagement — **B2B Fit:** Full (native Customer = account, Contact = user, custom events, parent/child company hierarchy).

**Terminology:**

| Standard concept | CustomerScore term | Identifier |
|---|---|---|
| Account / group | **Customer** | `external_id` (your ID, e.g. `acc_456`) |
| User | **Contact** | contact external ID (your ID, e.g. `usr_123`) |
| Event | Tracker event | `name`, matched to a metric **codename** |
| Trait / property | **Attribute** (current value) or **Metric** (time series) | codename |

**Key model difference:** CustomerScore does not store events as an explorable event stream with per-event properties. Tracked events are **counted** — aggregated once a day into a 30-day rolling sum — and only events whose name matches a configured metric codename are kept. Data sent alongside events updates **attributes** on the contact or customer, not properties on the event.

## Integration Paths

| Path | Best For | Account Context |
|---|---|---|
| **Tracker JS snippet** | Browser usage events and page views | `identify({ customer, contact })` |
| **Tracker server-side events** (`POST /api/tracker/track`) | Backend actions, batch event sends | `identification.customer` on every event |
| **REST API v1** (`/api/v1`) | Creating/updating customers and contacts, attributes, time-series metrics | Customer endpoints + `customer_external_id` on contacts |
| **PostHog / Mixpanel integration** | Already tracking in PostHog or Mixpanel | A Person/User property holding the customer ID |

**No Segment or RudderStack destination.** CustomerScore's integrations list (Stripe, Chargebee, ChartMogul, HubSpot, Salesforce, Raynet, PostHog, Mixpanel, Intercom, Gmail, meeting tools, email senders) has no CDP destination, and no CustomerScore destination was found in the Segment or RudderStack catalogs as of 2026-10-01. Segment `group()` calls do not reach CustomerScore. Use the Tracker or REST API directly, or route through PostHog/Mixpanel.

**No npm packages.** There is no published browser or Node.js SDK package. The browser Tracker is a CDN script; server-side calls are raw HTTPS requests.

## SDK Options

| Environment | Integration | Install |
|---|---|---|
| Browser | Tracker loader snippet (`https://cdn.customerscore.io/tracker/tracker.min.js`) | No install — paste snippet in `<head>` (or via Google Tag Manager) |
| Node.js / any backend | Tracker HTTP endpoint + REST API | No SDK — raw `fetch()` calls |
| HTTP API | REST, JSON | `https://api.customerscore.io/api/v1` (Swagger: `https://api.customerscore.io/api-docs`) |

## Authentication

| Credential | Format | Used by | Where to find |
|---|---|---|---|
| **Tracker key** (public) | `CS-XXXXXX` | Browser `init()` and the `trackerKey` body field of server-side events | App settings / Tracker settings page |
| **API token** (`customerscore-key`, secret) | Opaque string | REST API and server-side Tracker endpoint, sent as the `customerscore-key` header | App → API settings |

Never expose the `customerscore-key` in browser code. The browser Tracker uses only the public tracker key. Your domain must be set on the Tracker settings page before the Tracker (browser or server-side) will accept data.

## Initialization

### Browser

Place the loader in `<head>`. It defines a `window.CustomerScoreTracker` stub that queues calls until the hosted library loads:

```html
<script type="text/javascript">
  (function (t) {
    typeof define == "function" && define.amd ? define(t) : t();
  })(function () {
    "use strict";
    (function () {
      var t = "CustomerScoreTracker",
        i = window,
        n = [],
        s = i[t] || {};
      s.__stub__ = !0;
      function d(e) {
        s[e] = function () {
          n.push({ name: e, args: Array.prototype.slice.call(arguments) });
        };
      }
      for (
        var f = [
            "init",
            "identify",
            "resetIdentity",
            "track",
            "pageView",
            "group",
            "set",
            "unset",
            "setOnce",
            "config",
            "eventStart",
          ],
          o = 0;
        o < f.length;
        o++
      )
        d(f[o]);
      i[t] = s;
      function l() {
        var e = i[t];
        if (e && !e.__stub__) {
          for (var u = 0; u < n.length; u++) {
            var c = n[u];
            typeof e[c.name] == "function" && e[c.name].apply(e, c.args);
          }
          n = [];
        }
      }
      var h = document.createElement("script");
      h.src = "https://cdn.customerscore.io/tracker/tracker.min.js";
      h.async = !0;
      h.onload = l;
      document.head.appendChild(h);
    })();
  });
</script>
```

Then initialize once per page/app load, before any `identify` or `track`:

```javascript
CustomerScoreTracker.init('CS-123456', {
  autocapture: {
    pageview: 'soft-navigation', // SPAs; use 'hard-navigation' for full-reload sites, or true
  },
});
```

<!-- UNVERIFIED: The loader stub also queues `group`, `set`, `unset`, `setOnce`, `config`, and `eventStart`, but none of these are documented as of 2026-10-01. Do not use them in generated code until documented. -->

### Node.js / Server

No SDK. Use `fetch()` with the secret API token:

```typescript
const CS_API = 'https://api.customerscore.io';
const headers = {
  'Content-Type': 'application/json',
  'customerscore-key': process.env.CUSTOMERSCORE_API_KEY!,
};
const TRACKER_KEY = process.env.CUSTOMERSCORE_TRACKER_KEY!; // e.g. 'CS-123456'
```

## Core Methods

### identify()

**Browser:** `identify()` requires the customer (account) ID; the contact (user) is optional. The docs' examples use an email as the contact ID — prefer your stable user ID.

```javascript
CustomerScoreTracker.identify({
  customer: { id: 'acc_456' },          // required — your external customer ID
  contact: {
    id: 'usr_123',                      // optional — your external contact ID
    contact_name: 'Jane Doe',           // reserved property
    email: 'jane@example.com',
    role: 'admin',                      // stored only if a contact attribute with codename "role" exists
  },
});
```

Extra keys on `contact` are stored on the contact attribute with the matching codename. Each `identify` call is also counted as an `identify` event (the docs show it mapped to a "Login" system metric).

**When to call:** Right after login or when the user context becomes available; again if the logged-in user changes. Call `CustomerScoreTracker.resetIdentity()` on logout.

**Node.js — bulk contact upsert** (`POST /api/v1/contacts`, upserts by external ID, max 100 per request):

```typescript
await fetch(`${CS_API}/api/v1/contacts`, {
  method: 'POST',
  headers,
  body: JSON.stringify({
    contacts: [
      {
        customer_external_id: 'acc_456',  // customer must already exist
        contact_external_id: 'usr_123',
        contact_name: 'Jane Doe',          // required
        attributes: {
          email: 'jane@example.com',
          role: 'admin',
        },
      },
    ],
  }),
});
```

**Single-contact endpoints:**
- `POST /api/v1/customer/{customerExternalId}/contact` — body `{ "external_id": "usr_123", "name": "Jane Doe" }` (both required)
- `PUT /api/v1/customer/{customerExternalId}/contact/{contactExternalId}` — only `name` is documented as updatable; use the bulk upload or tracker `data.contact` for attributes
- `DELETE /api/v1/customer/{customerExternalId}/contact/{contactExternalId}`

The Tracker creates contacts automatically when it sees a new contact ID. It does **not** create customers.

### group() / Customer

Customers are the scored entity. They must exist **before** Tracker data for them is processed, and the browser Tracker cannot create them. Create/update customers from your backend.

**Create one customer** (`POST /api/v1/customer`) — e.g. at account signup:

```typescript
await fetch(`${CS_API}/api/v1/customer`, {
  method: 'POST',
  headers,
  body: JSON.stringify({
    external_id: 'acc_456',
    name: 'Acme Corp',
    // parent_external_id: 'acc_100', // optional; parent must already exist
  }),
});
```

**Update traits** (`PUT /api/v1/customer/{customerExternalId}`) — on plan change, renewal, churn:

```typescript
await fetch(`${CS_API}/api/v1/customer/acc_456`, {
  method: 'PUT',
  headers,
  body: JSON.stringify({
    name: 'Acme Corp',
    owner_email: 'csm@example.com',   // links to an existing CustomerScore user
    attributes: {
      plan: 'enterprise',
      renewal_date: '2027-03-31',     // DATE: YYYY-MM-DD
      seats: 250,                     // NUMBER: real number, not a numeric string
    },
  }),
});
```

Churn has core fields: `is_churned` (boolean), `churned_date` (`YYYY-MM-DD`), plus `is_unsubscribed`.

**Bulk upsert** (`POST /api/v1/customers`, max 100 per request, upserts by `external_id`) — best for recurring syncs, and the only way to write time-series **metrics**:

```typescript
await fetch(`${CS_API}/api/v1/customers`, {
  method: 'POST',
  headers,
  body: JSON.stringify({
    customers: [
      {
        external_id: 'acc_456',
        name: 'Acme Corp',
        attributes: { plan: 'enterprise', renewal_date: '2027-03-31' },
        metrics: [
          { date: '2026-09-30', reports_created: 42, active_seats: 37 },
        ],
      },
    ],
  }),
});
```

Other documented customer endpoints: `GET /api/v1/customer/{customerExternalId}` (returns `fitscore`, `engagementscore`, `churn_risk`, properties), `DELETE /api/v1/customer/{customerExternalId}`, `POST /api/v1/customers/search`.

**When to call:** Create on account signup (before the first Tracker event for that account). Update whenever account traits change.

### track()

**Browser:** event name only, or name plus attribute data for the identified contact:

```javascript
CustomerScoreTracker.track('report_created');

CustomerScoreTracker.track('report_created', {
  contact: {
    last_report_type: 'standard', // updates the contact attribute "last_report_type"
  },
});
```

Any string is accepted as the event name, but only names matching a configured metric codename (case-sensitive) are counted. The second argument does **not** become event properties — it updates contact attributes.

<!-- UNVERIFIED: Whether the browser track() data object accepts a `customer` key (the server-side endpoint does). Only `contact` is documented for the browser as of 2026-10-01. -->

**Node.js / HTTP** (`POST https://api.customerscore.io/api/tracker/track`). Note this path is `/api/tracker/track`, not under `/api/v1`. Up to 100 events per request:

```typescript
await fetch(`${CS_API}/api/tracker/track`, {
  method: 'POST',
  headers,
  body: JSON.stringify({
    trackerKey: TRACKER_KEY,
    events: [
      {
        name: 'report_created',
        timestamp: Date.now(),              // required, Unix milliseconds
        identification: {
          customer: 'acc_456',              // required
          contact: 'usr_123',               // optional
        },
        data: {                             // optional — updates attributes, not event properties
          customer: { last_report_at: '2026-10-01' },
          contact: { email: 'jane@example.com' },
        },
      },
    ],
  }),
});
```

**When to call:** After the action succeeds. Server-side tracking requires the Tracker to already be set up for your domain.

### page()

```javascript
CustomerScoreTracker.pageView();
```

Use `autocapture: { pageview: 'soft-navigation' }` in `init()` for SPAs, or call `pageView()` on each route change. Page views are not captured unless `autocapture` is set. Page views are counted by URL — a metric codename like `example.com/settings` counts views of that page.

## Group Context on Track Calls

- **Browser:** The customer comes from the last `identify({ customer, contact })` call and applies to later `track()` and `pageView()` calls. There is no separate group call (see the UNVERIFIED note on `group` above).
- **Server-side:** `identification.customer` is required on every event. There is no sticky context.
- **Contact vs customer metrics:** Metrics are configured as Contact metrics or Customer metrics. A **Grouped metric** on the customer counts all events of a given name for that customer, including events with no contact. Use grouped metrics for account-level scoring.

**Hierarchy:** CustomerScore supports a parent/subsidiary **company** tree through `parent_external_id` (up to 10 levels; no cycles; contacts can't be parents). This is meant for corporate hierarchies (e.g. `Acme Group` → `Acme Czechia`), not product sub-entities. If your account syncs hierarchy from HubSpot, that sync overwrites API-set parents.

For product sub-groups (workspace `ws_789`, project `proj_123`), attribute events to the billing account (`acc_456`) and encode sub-group detail only where it is useful as an attribute. There is no per-event property to carry `workspace_id`. Do not create a CustomerScore customer per workspace unless each workspace is a separately managed customer relationship.

## Account Traits That Matter

Attributes must already be defined in Settings → Attributes with a matching codename. Unknown codenames are dropped (bulk upload) or reject the whole request (`PUT`).

| Trait | Codename / field | Type | Why |
|---|---|---|---|
| Name | `name` (core) | string | Required on create |
| Owner / CSM | `owner_email` (core) | email | Assigns the customer to a CustomerScore user |
| Renewal date | `renewal_date` (system attribute) | DATE `YYYY-MM-DD` | Renewal alerts and worklists |
| CRM link | `crm_link` (system attribute) | URL | Link-out from the customer record |
| Churn status | `is_churned`, `churned_date` (core, `PUT` only) | boolean / date | Excludes churned customers from active scoring |
| Plan | `plan` (custom) | string | Segmentation, fit scoring |
| MRR | `mrr` (custom) | number | Revenue-weighted views (often supplied by the Stripe/Chargebee integration instead) |
| Seats | `seats` (custom) | number | Expansion and utilization signals |

If billing (Stripe, Chargebee, ChartMogul) or CRM (HubSpot, Salesforce) integrations feed an attribute, the API cannot update it. `PUT` rejects attributes whose data source is not API.

## Required Fields

| Call | Required | Notes |
|---|---|---|
| Browser `init` | tracker key | Once per page load, before other calls |
| Browser `identify` | `customer.id` | `contact.id` optional |
| Browser `track` | event name | Data object optional (`contact` only documented) |
| Server track request | `trackerKey`, `events[]` | Max 100 events |
| Server track event | `name`, `timestamp` (ms), `identification.customer` | `identification.contact`, `data` optional |
| Customer create | `external_id`, `name` | Parent must already exist |
| Customer bulk upload | `customers[].external_id`, `customers[].name` | Max 100; `metrics[].date` unique per array |
| Contact bulk upload | `customer_external_id`, `contact_external_id`, `contact_name` | Customer must exist, or the contact is ignored |
| Contact create | `external_id`, `name` | Customer in path must exist |

## Limits

| Constraint | Value |
|---|---|
| REST API rate limit (`/api/v1`) | 500 requests/minute |
| Tracker server-side rate limit (`/api/tracker/track`) | 200 requests/minute |
| Rate-limit response | `429` with `Retry-After` (seconds) |
| Max request body | 5 MB |
| Events per server-side request | 100 |
| Customers / contacts per bulk request | 100 (more → `400`, nothing imported) |
| Metrics per customer/contact object | 200 items |
| `external_id` / `name` length | 255 characters |
| Tracker data types | number and string |
| Attribute value types (API) | string, number, boolean, date `YYYY-MM-DD`; TIMESTAMP = Unix seconds |
| Hierarchy depth | 10 levels |
| Tracker aggregation latency | Daily; allow up to 24 h for first data |
| Bulk upload scoring | Up to 30 minutes after import |
| Data residency | AWS Frankfurt, Germany (single region documented) |

## Common Pitfalls

1. **Tracking before the customer exists.** The Tracker auto-creates contacts but never customers. Events for an `acc_456` that hasn't been created via the API (or a CRM/billing sync) are not processed. Create the customer at account signup, server-side.

2. **Expecting event properties.** `track('report_created', { contact: { ... } })` updates contact attributes; it does not store properties on the event. Events become counts (30-day rolling sums). Don't design a plan that depends on per-event properties reaching CustomerScore, and don't put property values into event names to get around this.

3. **Unmapped or mis-cased event names are silently dropped.** Only events whose name matches a metric codename exactly (case-sensitive) are merged. `Report_Created` ≠ `report_created`. Create the metric codenames in Settings → Metrics (or from Settings → Tracker after first data arrives) using the same snake_case names as the tracking plan.

4. **Unregistered attribute codenames.** Bulk uploads keep only keys that match a configured attribute codename. `PUT /customer/{id}` rejects the **whole** request with `400` if any codename is unknown, has the wrong type (e.g. `"250"` for a NUMBER, `"true"` for a BOOL), or belongs to a non-API data source.

5. **Two keys, two hosts.** Browser `init` takes the public tracker key (`CS-…`). Server calls need the secret `customerscore-key` header. Server-side events also need `trackerKey` in the body, and their path is `/api/tracker/track`, not `/api/v1/...`. Mixing these up gives `401`/`403`.

6. **Wrong timestamp unit.** Server-side event `timestamp` is Unix **milliseconds**, but TIMESTAMP-type attributes on `PUT /customer` are Unix **seconds**.

7. **Expecting a Segment/RudderStack destination.** There isn't one. An existing Segment `group()` call won't populate CustomerScore. Integrate directly, or connect PostHog/Mixpanel with a Person/User property that holds the account ID (only Persons/Users with that property set are synced).

8. **Expecting real-time data.** Tracker data is aggregated daily and scores refresh on the next snapshot. A `PUT` attribute change doesn't recalculate health/fit scores immediately. Don't use CustomerScore to verify instrumentation in real time.

## Debugging

**Browser:** In DevTools console, check that the library loaded (`true` once loaded, not the stub):

```javascript
window.CustomerScoreTracker && typeof CustomerScoreTracker.init === 'function';
CustomerScoreTracker.track('test_event');
```

Filter the Network tab for `customerscore.io` to inspect outgoing requests.

**Dashboard:** Settings → Tracker (Metrics and Attributes section) lists events and data keys received so far, and lets you create metrics/attributes from them. Settings → Imports shows bulk-upload warnings (e.g. skipped parent links).

**HTTP response codes:**

| Code | Meaning |
|---|---|
| `200` | Accepted for processing (bulk/tracker) or applied (single-resource) |
| `400` | Malformed body, over-limit batch, unknown/ineligible attribute codename, wrong value type, unusable `parent_external_id` |
| `401` | Missing/invalid `customerscore-key` |
| `403` | Key invalid or lacks permission |
| `404` | Customer or contact not found |
| `405` | Wrong HTTP method |
| `406` | Not Acceptable |
| `429` | Rate limit exceeded — honor `Retry-After` |
| `490` | Unconfigured scoring — set up a scoring profile in the app first |
| `491` | Account blocked (customer update) |

## Further Documentation

This reference covers the essentials for product tracking implementation. For advanced topics, consult CustomerScore.io's official documentation:

- **Docs home:** https://docs.customerscore.io/
- **Tracker overview:** https://docs.customerscore.io/tracker/
- **Tracking Code Setup (browser):** https://docs.customerscore.io/tracker/tracking-code-setup/
- **Server-side Events:** https://docs.customerscore.io/tracker/server-side-events/
- **Metrics & Attributes:** https://docs.customerscore.io/tracker/metrics-and-attributes/
- **API Introduction:** https://docs.customerscore.io/api-reference/introduction/
- **API Endpoints Overview:** https://docs.customerscore.io/api-reference/endpoints/
- **Customer upload:** https://docs.customerscore.io/api-reference/endpoints/customer/
- **Update Customer:** https://docs.customerscore.io/api-reference/endpoints/customer/update/
- **Contact upload:** https://docs.customerscore.io/api-reference/endpoints/contact/
- **Integrations (PostHog, Mixpanel, CRM, billing):** https://docs.customerscore.io/integrations/
- **Swagger:** https://api.customerscore.io/api-docs

**Documentation note:** CustomerScore's docs cover the Tracker and REST API publicly, with cURL examples. No official SDK packages exist. Code samples here use raw `fetch()` built from the documented endpoints and fields. The docs give no browser `group()`/`set()` behavior, browser `track()` customer-level data, or event-name length limits.
