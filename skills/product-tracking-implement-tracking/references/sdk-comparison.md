# SDK Comparison Reference

Practical reference for implementing product telemetry across analytics platforms.

---

## Segment

The most common choice for multi-destination routing. Acts as a data layer between your app and analytics tools.

### Browser SDK

```bash
npm install @segment/analytics-next
```

```typescript
import { AnalyticsBrowser } from '@segment/analytics-next';

const analytics = AnalyticsBrowser.load({
  writeKey: 'YOUR_WRITE_KEY'
});

// Track event
analytics.track('Button Clicked', {
  buttonColor: 'primary',
  buttonLocation: 'header'
});

// Identify user
analytics.identify('user-123', {
  email: 'user@example.com',
  plan: 'pro',
  company: 'Acme Inc'
});

// Group (associate user with account)
analytics.group('account-456', {
  name: 'Acme Inc',
  plan: 'enterprise',
  employees: 50
});

// Page view
analytics.page('Dashboard', {
  title: 'Main Dashboard',
  url: window.location.href
});
```

### Node.js SDK

```bash
npm install @segment/analytics-node
```

```typescript
import { Analytics } from '@segment/analytics-node';

const analytics = new Analytics({
  writeKey: 'YOUR_WRITE_KEY',
  flushAt: 20,        // Batch size before sending
  flushInterval: 10000 // Flush every 10 seconds
});

// Track with explicit userId (required server-side)
analytics.track({
  userId: 'user-123',
  event: 'Order Completed',
  properties: {
    orderId: 'order-789',
    revenue: 99.99,
    products: ['SKU-001', 'SKU-002']
  }
});

// Identify
analytics.identify({
  userId: 'user-123',
  traits: {
    email: 'user@example.com',
    plan: 'pro'
  }
});

// Group
analytics.group({
  userId: 'user-123',
  groupId: 'account-456',
  traits: {
    name: 'Acme Inc',
    plan: 'enterprise'
  }
});

// Flush before shutdown
await analytics.closeAndFlush();
```

### Key Segment Concepts
- **Write Key**: Project-specific API key (safe for client-side)
- **Destinations**: Analytics tools that receive your data
- **Protocols**: Schema validation for event tracking
- **Sources**: Where data originates (web, mobile, server)

---

## Amplitude

Popular for product analytics with strong behavioral analysis features.

### Browser SDK

```bash
npm install @amplitude/analytics-browser
```

```typescript
import * as amplitude from '@amplitude/analytics-browser';

// Initialize
amplitude.init('AMPLITUDE_API_KEY', 'user@example.com', {
  serverZone: 'US',  // or 'EU'
  flushIntervalMillis: 1000,
  flushQueueSize: 30,
  minIdLength: 5,
  logLevel: amplitude.Types.LogLevel.Warn
});

// Track event
amplitude.track('Button Clicked', {
  buttonColor: 'primary',
  buttonLocation: 'header'
});

// Identify user properties
const identifyObj = new amplitude.Identify();
identifyObj.set('plan', 'pro');
identifyObj.setOnce('initial_signup_date', '2024-01-15');
identifyObj.add('login_count', 1);
amplitude.identify(identifyObj);

// Set user ID
amplitude.setUserId('user-123');

// Groups (for account-level analytics)
amplitude.setGroup('company', 'Acme Inc');
```

### Node.js SDK

```bash
npm install @amplitude/analytics-node
```

```typescript
import { init, track, identify, Identify, setGroup } from '@amplitude/analytics-node';

// Initialize
init('AMPLITUDE_API_KEY', {
  flushIntervalMillis: 10000,
  flushQueueSize: 300,
  serverZone: 'US'
});

// Track with explicit user_id (required server-side)
track('Button Clicked', { buttonColor: 'primary' }, {
  user_id: 'user@example.com'
});

// Identify
const identifyObj = new Identify();
identifyObj.set('plan', 'pro');
identifyObj.setOnce('initial_signup_date', '2024-01-15');
identify(identifyObj, { user_id: 'user@example.com' });

// Groups
setGroup('company', 'Acme Inc', { user_id: 'user@example.com' });

// Event-level groups (only for this event)
track({
  event_type: 'Feature Used',
  event_properties: { feature: 'export' },
  groups: { company: 'Acme Inc' }
}, undefined, { user_id: 'user@example.com' });
```

### Key Amplitude Concepts
- **Device ID**: Auto-generated client-side identifier
- **User ID**: Your explicit user identifier (min 5 chars by default)
- **User Properties**: Persistent traits set via `identify()`
- **Groups**: Account/org-level groupings for B2B analytics
- **Autocapture**: Optional auto-tracking of clicks, page views, sessions

---

## Mixpanel

Strong behavioral analytics with focus on user journey analysis.

### Browser SDK

```html
<!-- CDN installation -->
<script src="https://cdn.mxpnl.com/libs/mixpanel-2-latest.min.js"></script>
<script>
  mixpanel.init('YOUR_PROJECT_TOKEN', {
    track_pageview: true,
    persistence: 'localStorage'
  });
</script>
```

```typescript
// NPM installation
import mixpanel from 'mixpanel-browser';

mixpanel.init('YOUR_PROJECT_TOKEN', {
  track_pageview: true,
  persistence: 'localStorage',
  api_host: 'https://api.mixpanel.com'  // or 'https://api-eu.mixpanel.com'
});

// Track event
mixpanel.track('Button Clicked', {
  buttonColor: 'primary',
  buttonLocation: 'header'
});

// Identify user
mixpanel.identify('user-123');

// Set user profile properties
mixpanel.people.set({
  $email: 'user@example.com',
  $name: 'John Doe',
  plan: 'pro'
});

// Set properties only if not already set
mixpanel.people.set_once({
  'First Login Date': new Date().toISOString()
});

// Super properties (added to all subsequent events)
mixpanel.register({
  'User Type': 'Pro'
});

// Groups (paid add-on)
mixpanel.set_group('company', 'Acme Inc');

// Time an event (records duration)
mixpanel.time_event('Checkout');
// ... later ...
mixpanel.track('Checkout');  // Includes 'Duration' property
```

### Node.js SDK

```bash
npm install mixpanel
```

```typescript
import Mixpanel from 'mixpanel';

const mixpanel = Mixpanel.init('YOUR_PROJECT_TOKEN', {
  host: 'api.mixpanel.com',  // or 'api-eu.mixpanel.com'
  debug: process.env.NODE_ENV !== 'production',
  geolocate: false  // Disable to avoid server IP geolocation
});

// Track event (distinct_id required)
mixpanel.track('Button Clicked', {
  distinct_id: 'user-123',
  buttonColor: 'primary',
  buttonLocation: 'header'
});

// Set user profile properties
mixpanel.people.set('user-123', {
  $email: 'user@example.com',
  $name: 'John Doe',
  plan: 'pro'
});

// Set once (won't overwrite)
mixpanel.people.set_once('user-123', {
  'First Login Date': new Date().toISOString()
});

// Import historical events (>5 days old)
mixpanel.import('Historical Event', new Date('2023-01-15'), {
  distinct_id: 'user-123',
  property: 'value'
});

// Group analytics
mixpanel.groups.set('company', 'Acme Inc', {
  employees: 50,
  plan: 'enterprise'
});
```

### Key Mixpanel Concepts
- **distinct_id**: Primary user identifier
- **Super Properties**: Persist across all events via `register()`
- **People Properties**: User profile traits (prefix with `$` for reserved)
- **Time Events**: Measure duration between start and completion
- **Group Analytics**: Paid add-on for B2B account analysis

---

## PostHog

Open-source product analytics with session replay and feature flags.

### Browser SDK

```bash
npm install posthog-js
```

```typescript
import posthog from 'posthog-js';

// Initialize
posthog.init('YOUR_API_KEY', {
  api_host: 'https://us.i.posthog.com',  // EU: 'https://eu.i.posthog.com', or your self-hosted URL
  autocapture: true,
  capture_pageview: true,
  capture_pageleave: true,
  disable_session_recording: false
});

// Track event
posthog.capture('Button Clicked', {
  buttonColor: 'primary',
  buttonLocation: 'header',
  $set: { lastAction: 'button_click' },  // Also set person property
  $set_once: { firstAction: 'button_click' }  // Set if not exists
});

// Identify user
posthog.identify('user-123', {
  email: 'user@example.com',
  plan: 'pro'
});

// Groups (for B2B account analytics)
posthog.group('company', 'account-456', {
  name: 'Acme Inc',
  plan: 'enterprise',
  employees: 50
});

// Reset on logout
posthog.reset();

// Feature flags
if (posthog.isFeatureEnabled('new-checkout')) {
  // Show new checkout
}

// Check flag with payload
const variant = posthog.getFeatureFlag('pricing-experiment');
```

### Node.js SDK

```bash
npm install posthog-node
```

```typescript
import { PostHog } from 'posthog-node';

const posthog = new PostHog('YOUR_API_KEY', {
  host: 'https://us.i.posthog.com',  // EU: 'https://eu.i.posthog.com', or your self-hosted URL
  flushAt: 20,
  flushInterval: 10000
});

// Capture event (distinctId required)
posthog.capture({
  distinctId: 'user-123',
  event: 'Button Clicked',
  properties: {
    buttonColor: 'primary',
    buttonLocation: 'header'
  }
});

// Identify with properties
posthog.identify({
  distinctId: 'user-123',
  properties: {
    email: 'user@example.com',
    plan: 'pro'
  }
});

// Groups
posthog.groupIdentify({
  groupType: 'company',
  groupKey: 'account-456',
  properties: {
    name: 'Acme Inc',
    plan: 'enterprise'
  }
});

// Feature flags (async)
const isEnabled = await posthog.isFeatureEnabled('new-checkout', 'user-123');

// Alias (link anonymous to known user)
posthog.alias({
  distinctId: 'user-123',
  alias: 'anonymous-abc'
});

// Flush on shutdown
await posthog.shutdown();
```

### Key PostHog Concepts
- **distinctId**: Primary user identifier
- **$set / $set_once**: Set person properties inline with events
- **Groups**: Account-level analytics (company, team, etc.)
- **Feature Flags**: Built-in experimentation
- **Session Recording**: Automatic user session capture (browser)
- **Autocapture**: Auto-track clicks, inputs, page views

---

## Accoil

B2B-first engagement analytics with account-level insights. Three integration methods: tracker.js (browser), Direct API v2 (server), or as a Segment destination.

### Browser SDK (tracker.js)

Zero-dependency library loaded from CDN (no npm package). Add to your top-level template:

```html
<script type="text/javascript">
(function() {
  var accoil = window.accoil = window.accoil || {q: []};
  var calls = ['load', 'identify', 'group', 'track'];
  for (var i = 0; i < calls.length; i++) (function(call) {
    accoil[call] = function() { accoil.q.push([call, arguments]); };
  })(calls[i]);
  var s = document.createElement('script'); s.src = 'https://cdn.accoil.com/tracker.js'; s.async = true;
  var f = document.getElementsByTagName('script')[0]; f.parentNode.insertBefore(s, f);
})();
</script>
<script type="text/javascript">
  accoil.load("YOUR_API_KEY");
</script>
```

```javascript
// Identify user (call on every page load, before tracking)
accoil.identify("usr_123", {
  email: "jane@example.com",
  name: "Jane Doe",
  created_at: "2024-01-15T00:00:00Z",
  role: "admin"
});

// Group (account) — call when accounts are created or traits change
accoil.group("acc_456", {
  name: "Acme Corp",
  status: "active",
  mrr: 500000, // $5,000 in cents — MRR is specified in cents, not dollars
  created_at: "2023-06-01T00:00:00Z"
});

// Track event — event name only, no properties and no group context.
// Account attribution comes from the user's membership (identify/group).
// Don't encode variants in the name (e.g. not 'Report_Exported_PDF').
accoil.track("Report_Exported");
```

### Server-Side (Direct API v2)

REST API at `https://in.accoil.com`, authenticated with `Authorization: Basic YOUR_API_KEY`. Returns 202 and processes asynchronously — including key validation, so an invalid key still returns 202.

```typescript
const ACCOIL_API_KEY = process.env.ACCOIL_API_KEY!;
const ACCOIL_BASE = 'https://in.accoil.com';

async function accoilPost(path: string, body: object) {
  await fetch(`${ACCOIL_BASE}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Basic ${ACCOIL_API_KEY}`,
    },
    body: JSON.stringify(body),
  });
}

// Identify (userId required; groupId associates the user with an account)
await accoilPost('/v2/identify', {
  userId: 'usr_123',
  groupId: 'acc_456',
  traits: { email: 'jane@example.com', name: 'Jane Doe', created_at: '2024-01-15T00:00:00Z' }
});

// Group (groupId required; userId optional — omit for account-only trait updates)
await accoilPost('/v2/group', {
  groupId: 'acc_456',
  userId: 'usr_123',
  traits: { name: 'Acme Corp', created_at: '2023-06-01T00:00:00Z', status: 'paid', mrr: 500000 }
});

// Track (userId + event only — no properties accepted)
await accoilPost('/v2/track', { userId: 'usr_123', event: 'Report_Exported' });
```

### Via Segment

Add the **Accoil Analytics** destination in Segment; existing `identify`, `group`, and `track` calls flow through. Segment `page`/`screen` calls arrive as track events. Track properties are passed but Accoil stores only the event name.

### Key Accoil Concepts
- **API key**: Used by `accoil.load()` (browser) and as `Authorization: Basic` (Direct API)
- **userId**: Stable user identifier (database ID, not email)
- **groupId**: B2B account/organization identifier, set via `group()`
- **Name-only tracking**: Track calls store the event name only — no properties, no variants in names
- **MRR in cents**: `mrr` trait is an integer in cents (`500000` = $5,000)
- **Engagement Scoring**: Engagement scores calculated at the account level
- **Account-First**: Events attributed to accounts via user membership (`identify` with `groupId` / `group()`)

---

## Quick Comparison

| Feature | Segment | Amplitude | Mixpanel | PostHog | Accoil |
|---------|---------|-----------|----------|---------|--------|
| Primary Use | Data routing | Product analytics | User analytics | Open-source analytics | B2B engagement |
| Pricing Model | MTU-based | Event-based | Event-based | Event/Self-hosted | Account-based |
| Groups/Accounts | ✓ via `group()` | ✓ Groups | ✓ (paid add-on) | ✓ Groups | ✓ First-class |
| Session Replay | Via destinations | Paid add-on | ✓ | ✓ Built-in | - |
| Feature Flags | - | ✓ (Experiment) | - | ✓ Built-in | - |
| Self-Hosted | - | - | - | ✓ | - |
| Auto-capture | - | ✓ Autocapture | ✓ Autocapture | ✓ Autocapture | - |

---

## Implementation Patterns

### Wrapper Pattern (Recommended)
Abstract the analytics SDK behind your own interface:

```typescript
// analytics.ts
interface AnalyticsClient {
  track(event: string, properties?: Record<string, unknown>): void;
  identify(userId: string, traits?: Record<string, unknown>): void;
  group(accountId: string, traits?: Record<string, unknown>): void;
}

// Swap implementations without changing app code
export const analytics: AnalyticsClient = new SegmentClient();
// or: new AmplitudeClient();
// or: new MixpanelClient();
```

### Multi-Destination Pattern
Send to multiple analytics tools:

```typescript
class MultiAnalytics implements AnalyticsClient {
  private clients: AnalyticsClient[];

  constructor(clients: AnalyticsClient[]) {
    this.clients = clients;
  }

  track(event: string, properties?: Record<string, unknown>): void {
    this.clients.forEach(client => client.track(event, properties));
  }
}

export const analytics = new MultiAnalytics([
  new SegmentClient(),   // Routes to multiple destinations
  new PostHogClient()    // Direct for feature flags
]);
```

### Server-Side Considerations

```typescript
// Always include userId server-side (no anonymous tracking)
analytics.track({
  userId: req.user.id,  // Required!
  event: 'API Request',
  properties: {
    endpoint: req.path,
    method: req.method
  }
});

// Disable geolocation if server IP would be misleading
mixpanel.init(token, { geolocate: false });

// Flush before process exit
process.on('SIGTERM', async () => {
  await analytics.closeAndFlush();
  process.exit(0);
});
```

---

## B2B-Specific Patterns
Product Tracking – Model Product
Product Tracking – Audit Current Tracking
Product Tracking – Design Tracking Plan
Product Tracking – Generate Implementation Guide
Product Tracking – Implement Tracking
Product Tracking – Instrument New Feature
### Account Context on Every Event
For B2B apps, always include account context:

```typescript
// Segment — group() associates the user with the account; there is no generic
// per-event group option. Use the destination's mechanism, e.g. Amplitude (Classic):
analytics.track('Feature Used', {
  feature: 'export'
}, {
  integrations: { Amplitude: { groups: { company: 'account-456' } } }
});

// Amplitude
track({
  event_type: 'Feature Used',
  event_properties: { feature: 'export' },
  groups: { company: 'account-456' }
}, undefined, { user_id: 'user-123' });

// PostHog
posthog.capture({
  distinctId: 'user-123',
  event: 'Feature Used',
  properties: { feature: 'export' },
  groups: { company: 'account-456' }
});
```

### Account Properties
Track account-level traits separately:

```typescript
// Segment
analytics.group('account-456', {
  name: 'Acme Inc',
  plan: 'enterprise',
  mrr: 999,
  employeeCount: 50
});

// Amplitude
groupIdentify('company', 'account-456', {
  name: 'Acme Inc',
  plan: 'enterprise',
  mrr: 999
});

// PostHog
posthog.groupIdentify({
  groupType: 'company',
  groupKey: 'account-456',
  properties: {
    name: 'Acme Inc',
    plan: 'enterprise'
  }
});
```

---

## Hierarchical Groups

Most B2B products have structure beyond "users and accounts." Support for nested groups varies by platform.

### Platform Support

| Platform | Event-Level Groups | Hierarchical Groups |
|----------|-------------------|---------------------|
| **Accoil** | ✓ via user membership (no group context on track) | ✓ Full via `parent_group_id` |
| **Amplitude** | ✓ `groups` property | ⚠️ Limited — no native hierarchy |
| **Mixpanel** | ✓ group key as event property | ⚠️ Limited — no native hierarchy |
| **Segment** | ✗ User-level only (`group()`); per-event via destination-specific options | ✗ Not supported |
| **PostHog** | ✓ `groups` property | ⚠️ Max 5 group types |

### Defining Hierarchical Groups

```typescript
// Define the hierarchy with parent_group_id

// Account (top level)
analytics.group('acc_456', {
  group_type: 'account',
  name: 'Acme Inc'
});

// Workspace (child of account)
analytics.group('ws_789', {
  group_type: 'workspace',
  name: 'Engineering',
  parent_group_id: 'acc_456'
});

// Project (child of workspace)
analytics.group('proj_123', {
  group_type: 'project',
  name: 'Q1 Release',
  parent_group_id: 'ws_789'
});
```

### Attributing Events to Groups

Track at the most specific group level:

```typescript
// Accoil — no group context on track calls; event name only.
// Attribution comes from user membership (identify with groupId / group()),
// rollup from parent_group_id traits.
accoil.track('Task_Completed');

// Amplitude — use groups in integrations
analytics.track('Task Completed', {
  task_id: 'task_456'
}, {
  integrations: {
    Amplitude: {
      groups: { project: 'proj_123' }
    }
  }
});

// Mixpanel — use $groups property
mixpanel.track('Task Completed', {
  task_id: 'task_456',
  $groups: { project: 'proj_123' }
});
```

### Rollup Behavior

Analytics tools that support hierarchical groups can automatically roll metrics up:

```
Event: Task Completed (groupId: proj_123)
  ↓ Rolls up to:
  - Project proj_123 ✓
  - Workspace ws_789 ✓ (via parent_group_id)
  - Account acc_456 ✓ (via parent chain)
```

This means you only need to track at the most specific level — don't duplicate events at each level.

See [Group Hierarchy](group-hierarchy.md) for comprehensive documentation.
