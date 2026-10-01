<!-- Last verified: 2026-10-01 against LaunchDarkly docs (js-client-sdk v4.10.4, react-sdk v4.1.21, node-server-sdk v9.13.8; v3 notes vs launchdarkly-js-client-sdk v3.9.5) -->
# LaunchDarkly Implementation Reference

## SDK Version Note

Browser and React examples target the **v4** SDKs: JavaScript Client SDK `@launchdarkly/js-client-sdk` and React Web SDK `@launchdarkly/react-sdk`. Node.js examples target the Node Server SDK v9 (`@launchdarkly/node-server-sdk`), which is unaffected by the client v4 changes.

**Recognizing v3 code during audits** (`launchdarkly-js-client-sdk`, `launchdarkly-react-client-sdk` -- v3 still receives releases, so existing codebases often use it):
- v3 `LDClient.initialize(id, context, options)` connects immediately; v4 uses `createClient(id, context, options)` and nothing connects until `client.start()`. In v4, `identify()` before `start()` returns an error result.
- v3 `waitForInitialization(timeout)` and `identify()` **reject** on failure; in v4 both always **resolve** with a result object (`waitForInitialization` → `status: 'complete' | 'failed' | 'timeout'`; `identify` → `status: 'completed' | 'error' | 'timeout' | 'shed'`), so try/catch around them no longer catches failures.
- v3 `on('change', (changes) => …)` received `{ flagKey: { current, previous } }` and `change:key` received `(newValue, oldValue)`; v4 listeners receive `(context, changedKeys)` / `(context)` with no values -- call a variation method to read the new value.
- v4 adds typed evaluation methods (`boolVariation`, `stringVariation`, `numberVariation`, `jsonVariation`, and `*Detail` forms); `bootstrap` moved from init options to `start({ bootstrap })`; `allFlags()` no longer sends analytics events.
- React v3 `withLDProvider` / `asyncWithLDProvider` / `useFlags` / `withLDConsumer` → v4 `createLDReactProvider()`, typed hooks (`useBoolVariation`, etc.), `useLDClient()`, `useInitializationStatus()`. The v4 provider renders immediately instead of blocking on initialization; `useFlags` is deprecated.

## Overview

LaunchDarkly is a feature flag and experimentation platform. It is not a product analytics tool, but it manages user and group targeting context for flag evaluation and tracks flag exposure events. Typically paired with a product analytics tool (Amplitude, Mixpanel, Segment, etc.) for experiment analysis and behavioral metrics. Proprietary, cloud-only.

## SDK Options

| Environment | Integration | Install |
|---|---|---|
| Browser | JS Client SDK v4 (`@launchdarkly/js-client-sdk`) | `npm install @launchdarkly/js-client-sdk` |
| Node.js | Node Server SDK v9 (`@launchdarkly/node-server-sdk`) | `npm install @launchdarkly/node-server-sdk` |
| React | React Web SDK v4 (`@launchdarkly/react-sdk`) | `npm install @launchdarkly/react-sdk` |
| Browser / React (legacy v3) | `launchdarkly-js-client-sdk`, `launchdarkly-react-client-sdk` | See SDK Version Note |

**Important:** The browser SDK uses a **client-side ID** (safe to expose). The Node.js server SDK uses an **SDK key** (secret, never expose client-side).

## Initialization

### Browser

```typescript
import { createClient } from '@launchdarkly/js-client-sdk';

// Client-side ID from LaunchDarkly dashboard → Environments
const client = createClient('YOUR_CLIENT_SIDE_ID', {
  kind: 'user',
  key: 'usr_123',
  name: 'Jane Smith',
  email: 'jane@example.com',
  role: 'admin',
  plan: 'pro'
});

// Register listeners first, then start -- nothing connects until start()
client.on('ready', () => {
  console.log('LaunchDarkly initialization finished (check status before relying on flags)');
});
client.start();

// Wait for flags to load before evaluating. Never rejects -- check status.
const result = await client.waitForInitialization({ timeout: 5 });
if (result.status === 'failed') {
  console.error('LaunchDarkly init failed:', result.error);
} else if (result.status === 'timeout') {
  console.warn('LaunchDarkly init timed out; using default flag values');
}
```

`start()` itself also returns a promise resolving to the same result object, so `const result = await client.start();` works too. The default `waitForInitialization` timeout is 5 seconds.

### React

```tsx
import { createLDReactProvider, useBoolVariation, useInitializationStatus } from '@launchdarkly/react-sdk';

const LDProvider = createLDReactProvider('YOUR_CLIENT_SIDE_ID', {
  kind: 'user',
  key: 'usr_123',
  name: 'Jane Smith'
});

root.render(
  <LDProvider>
    <App />
  </LDProvider>
);

function Checkout() {
  const { status } = useInitializationStatus(); // 'initializing' | 'complete' | 'failed' | 'timeout'
  const showNewCheckout = useBoolVariation('new-checkout', false);
  if (status === 'initializing') return <Spinner />;
  return showNewCheckout ? <NewCheckout /> : <OldCheckout />;
}
```

The provider creates and starts the client and renders immediately. Use `useLDClient()` to get the client for `identify()` and `track()` calls.

### Node.js

```typescript
import * as LaunchDarkly from '@launchdarkly/node-server-sdk';

const client = LaunchDarkly.init('YOUR_SDK_KEY');

// Wait for initialization before evaluating flags (timeout in seconds)
await client.waitForInitialization({ timeout: 10 });
```

## User Context (identify equivalent)

LaunchDarkly uses a **context** object for flag evaluation. The context determines which flags and variations a user sees. This is the equivalent of `identify()` in product analytics tools.

**Browser:**

The initial context is passed to `createClient()`. To change the user (e.g., on login or user switch), call `identify()` -- only after `start()` has been called:

```typescript
// Initial context set during createClient (see Initialization above)

// Switch user context (e.g., after login). Never rejects -- check status.
const identifyResult = await client.identify({
  kind: 'user',
  key: 'usr_123',
  name: 'Jane Smith',
  email: 'jane@example.com',
  role: 'admin',
  plan: 'pro',
  created_at: '2024-01-15T10:30:00Z'
});
if (identifyResult.status !== 'completed') {
  // 'error' | 'timeout' | 'shed' -- flags may still reflect the previous context
  console.warn('LaunchDarkly identify did not complete:', identifyResult.status);
}
```

In React, get the client with `const ldClient = useLDClient();` and call `ldClient.identify(...)` the same way.

**Node.js:**

Server-side, context is passed per flag evaluation — there is no persistent user state:

```typescript
const context = {
  kind: 'user',
  key: 'usr_123',
  name: 'Jane Smith',
  email: 'jane@example.com',
  role: 'admin',
  plan: 'pro'
};

// Context is passed to each variation call
const showFeature = await client.variation('new-checkout', context, false);
```

**When to call (browser):**
- On login — switch from anonymous to identified user
- On user switch — when a different user takes over the session
- When user attributes change that affect targeting rules

## Group / Organization Context

LaunchDarkly supports **multi-kind contexts** for targeting by both user and organization. This enables flag rules like "enable for all users in enterprise accounts."

**Browser:**

```typescript
const identifyResult = await client.identify({
  kind: 'multi',
  user: {
    key: 'usr_123',
    name: 'Jane Smith',
    email: 'jane@example.com',
    role: 'admin'
  },
  organization: {
    key: 'acc_456',
    name: 'Acme Corp',
    plan: 'enterprise',
    industry: 'technology',
    employee_count: 150
  }
});
```

**Node.js:**

```typescript
const context = {
  kind: 'multi',
  user: {
    key: 'usr_123',
    name: 'Jane Smith',
    role: 'admin'
  },
  organization: {
    key: 'acc_456',
    name: 'Acme Corp',
    plan: 'enterprise',
    employee_count: 150
  }
};

const showFeature = await client.variation('enterprise-dashboard', context, false);
```

You can define any context kind names — `organization`, `workspace`, `project`, etc. These map to your product's group hierarchy. Multi-kind contexts allow targeting rules that combine user attributes with group attributes.

## Flag Evaluation

### Boolean Flags

**Browser:**
```typescript
// Browser flags are evaluated locally (cached from server)
const showNewCheckout = client.boolVariation('new-checkout', false);
// React: const showNewCheckout = useBoolVariation('new-checkout', false);

if (showNewCheckout) {
  renderNewCheckout();
} else {
  renderOldCheckout();
}
```

**Node.js:**
```typescript
const context = { kind: 'user', key: 'usr_123' };

const showNewCheckout = await client.variation('new-checkout', context, false);
// Third argument is the default value if flag is not found
```

### Multivariate Flags

```typescript
// Browser
const pricingTier = client.stringVariation('pricing-experiment', 'control');
// React: const pricingTier = useStringVariation('pricing-experiment', 'control');
// Returns: 'control' | 'variant-a' | 'variant-b'

// Node.js
const pricingTier = await client.variation('pricing-experiment', context, 'control');
```

### Variation Detail (with reason)

```typescript
// Browser (variationDetail() also works for untyped values)
const detail = client.boolVariationDetail('new-checkout', false);
// detail.value — the flag value
// detail.variationIndex — which variation was served
// detail.reason — why this variation was chosen (e.g., rule match, fallthrough)

// Node.js
const detail = await client.variationDetail('new-checkout', context, false);
```

## Tracking Flag Exposures as Events

LaunchDarkly automatically tracks flag evaluations internally. To pipe these exposure events to external analytics tools for experiment analysis, use **Data Export** or **integrations**.

### Data Export Destinations

LaunchDarkly can export flag evaluation events to:
- **Segment** — sends `$ld:flag` events as Segment track calls
- **mParticle** — forwards evaluation data
- **Kinesis, Pub/Sub, Azure Event Hubs** — raw event streams for data warehouses
- **Warehouse destinations** — BigQuery, ClickHouse, Databricks, Redshift, Snowflake

Configure these in LaunchDarkly dashboard → Integrations → Data Export. Data Export is a paid **add-on** (contact LaunchDarkly Sales).

### Listening to Flag Changes (Browser)

```typescript
// React to flag value changes in real-time.
// v4 listeners receive the context, not values -- read the new value yourself.
client.on('change:new-checkout', (context) => {
  // Forward to your analytics tool
  analytics.track('experiment.exposure', {
    flag_key: 'new-checkout',
    variation: client.boolVariation('new-checkout', false)
  });
});

// Listen to all flag changes
client.on('change', (context, changedKeys) => {
  // changedKeys is an array of flag keys
  changedKeys.forEach((flagKey) => {
    analytics.track('experiment.exposure', {
      flag_key: flagKey,
      variation: client.variation(flagKey)
    });
  });
});
```

### Manual Exposure Tracking Pattern

For experiment analysis, manually forward flag evaluations to your product analytics tool:

```typescript
// Helper: evaluate flag and track exposure
function evaluateAndTrack(flagKey: string, defaultValue: any) {
  const detail = client.variationDetail(flagKey, defaultValue);

  // Send exposure event to product analytics (e.g., Segment, Amplitude)
  analytics.track('experiment.exposure', {
    flag_key: flagKey,
    variation_value: detail.value,
    variation_index: detail.variationIndex,
    reason: detail.reason?.kind
  });

  return detail.value;
}

// Usage
const variant = evaluateAndTrack('pricing-experiment', 'control');
```

## Custom Events / Metrics

LaunchDarkly supports custom events for experiment goal metrics. These events are used within LaunchDarkly to measure experiment outcomes — they do NOT replace product analytics events.

**Browser:**
```typescript
// Simple event (for conversion metrics)
client.track('checkout-completed');

// Event with numeric value (for numeric metrics)
client.track('cart-total', undefined, 149.99);

// Event with custom data
client.track('feature-used', { feature_name: 'export', format: 'csv' });
```

**Node.js:**
```typescript
const context = { kind: 'user', key: 'usr_123' };

// Simple event
client.track('checkout-completed', context);

// Event with numeric value
client.track('cart-total', context, undefined, 149.99);

// Event with custom data
client.track('feature-used', context, { feature_name: 'export' });
```

These metric events are used in LaunchDarkly's Experimentation to calculate statistical significance of experiment outcomes. They do not flow to external analytics tools automatically.

## Analytics Integration Pattern

LaunchDarkly is a flag/experimentation tool that works **alongside** product analytics, not as a replacement. The typical integration pattern:

```
┌─────────────────────────────────────────────────────────┐
│                     Your Application                    │
│                                                         │
│   1. Evaluate flag → LaunchDarkly SDK                   │
│   2. Track exposure → Product Analytics (Segment, etc.) │
│   3. Track behavior → Product Analytics                 │
│   4. Track metric → LaunchDarkly SDK (for experiments)  │
│                                                         │
└──────────┬──────────────────┬──────────────────┬────────┘
           │                  │                  │
    ┌──────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐
    │ LaunchDarkly │   │   Segment   │   │  Amplitude  │
    │  (flags +    │   │  (routing)  │   │ (analysis)  │
    │  experiments)│   │             │   │             │
    └─────────────┘   └─────────────┘   └─────────────┘
```

**Two-way data flow:**
1. **Flag exposure → Analytics tool** — Send which variation the user saw so you can segment behavior by experiment group
2. **Product events → LaunchDarkly metrics** — Track conversion events via `client.track()` so LaunchDarkly can calculate experiment results

### Combined Example

```typescript
// 1. Evaluate the flag
const checkoutVariant = client.stringVariation('new-checkout-flow', 'control');

// 2. Track exposure in product analytics
analytics.track('experiment.exposure', {
  experiment_key: 'new-checkout-flow',
  variation: checkoutVariant,
  user_id: 'usr_123'
});

// 3. User completes the action — track in both systems
analytics.track('checkout.completed', {
  order_value: 149.99,
  checkout_variant: checkoutVariant  // Include variant for segmentation
});

// 4. Track metric in LaunchDarkly for experiment analysis
client.track('checkout-completed', undefined, 149.99);
```

## Forge Compatibility

LaunchDarkly is on the Atlassian Forge approved analytics domain list.

**Approved domains:**
- `*.launchdarkly.com`

**Manifest configuration:**
```yaml
permissions:
  external:
    fetch:
      backend:
        - address: "*.launchdarkly.com"
          category: analytics
          inScopeEUD: false
```

**Note:** In Forge apps, use the Node.js server SDK in backend resolvers. The browser client SDK cannot be used in Forge Custom UI iframes because direct external network calls are blocked. Flag evaluations should happen server-side, with results passed to the frontend via `invoke()`.

## Common Pitfalls

1. **Using the SDK key client-side** — The server SDK key is secret. Browser apps must use the client-side ID. Exposing the SDK key allows anyone to read all flag configurations and targeting rules.

2. **Evaluating flags before initialization** — Both browser and server SDKs require initialization before flag values are available. Browser (v4): call `client.start()` (the React provider does this for you), then `await client.waitForInitialization({ timeout: 5 })` and check `result.status` -- it never rejects, so a `try/catch` will not detect failure. Server: `await client.waitForInitialization({ timeout: 10 })`, which rejects on failure. Evaluating early returns the default value silently.

3. **Not passing context on server-side evaluations** — The Node.js SDK has no persistent user context. Every `variation()` call requires an explicit context object. Forgetting this returns the default value for all users.

4. **Forgetting to track exposures in analytics** — LaunchDarkly tracks flag evaluations internally, but your product analytics tool does not know about them unless you explicitly send exposure events. Without exposure tracking in your analytics, you cannot segment user behavior by experiment variation.

5. **Mixing up `track()` purposes** — LaunchDarkly's `client.track()` sends events to LaunchDarkly for experiment metrics. It does NOT send events to your product analytics tool. You need to call both `client.track()` (for LaunchDarkly experiments) and `analytics.track()` (for product analytics) when an event matters to both systems.

6. **Not shutting down the server SDK** — The Node.js SDK maintains a streaming connection, and it does **not** automatically send pending analytics events on shutdown. Call `flush()` then `close()` on process exit:
   ```typescript
   process.on('SIGTERM', async () => {
     await client.flush();
     client.close();
     process.exit(0);
   });
   ```

## Debugging

### Browser
```typescript
import { createClient, basicLogger } from '@launchdarkly/js-client-sdk';

// Enable debug logging
const client = createClient('YOUR_CLIENT_SIDE_ID', context, {
  logger: basicLogger({ level: 'debug' })
});
client.start();

// Inspect all flag values
const allFlags = client.allFlags();
console.log(allFlags);

// Inspect a specific flag with reason
const detail = client.variationDetail('new-checkout', false);
console.log(detail.reason);
// e.g., { kind: 'RULE_MATCH', ruleIndex: 0, ruleId: 'rule-123' }
```

### Node.js
```typescript
const client = LaunchDarkly.init('YOUR_SDK_KEY', {
  logger: LaunchDarkly.basicLogger({ level: 'debug' })
});

// Evaluate with reason
const detail = await client.variationDetail('new-checkout', context, false);
console.log(detail.reason);
```

### LaunchDarkly Dashboard
- **Flag Insights** — shows evaluation counts per variation, per environment
- **Live Events** — real-time stream of flag evaluations and custom events
- **Debugger** — filter events by user key, flag key, or context kind

### Flag Status Check
```typescript
// Browser: check initialization status and current context
const result = await client.waitForInitialization({ timeout: 5 });
console.log(result.status); // 'complete' | 'failed' | 'timeout'
console.log(client.getContext()); // current context
console.log(client.variation('flag-key', 'default')); // current value

// Node.js: verify client is initialized
client.waitForInitialization().then(() => {
  console.log('SDK initialized and connected');
}).catch((err) => {
  console.error('SDK failed to initialize:', err);
});
```

## Further Documentation

This reference covers the essentials for product tracking implementation. For advanced topics, consult LaunchDarkly's official documentation:

- **Getting Started:** https://launchdarkly.com/docs/home/getting-started
- **JavaScript Client SDK:** https://launchdarkly.com/docs/sdk/client-side/javascript
- **Node.js Server SDK:** https://launchdarkly.com/docs/sdk/server-side/node-js
- **React SDK:** https://launchdarkly.com/docs/sdk/client-side/react/react-web
- **JS Client SDK v3 → v4 Migration:** https://launchdarkly.com/docs/sdk/client-side/javascript/migration-3-to-4
- **React Web SDK v3 → v4 Migration:** https://launchdarkly.com/docs/sdk/client-side/react/web-migration-3-to-4
- **Contexts and Targeting:** https://launchdarkly.com/docs/home/flags/contexts/intro
- **Multi-Kind Contexts:** https://launchdarkly.com/docs/home/flags/multi-contexts
- **Experimentation:** https://launchdarkly.com/docs/home/experimentation
- **Custom Metrics:** https://launchdarkly.com/docs/home/metrics/create-metrics
- **Data Export:** https://launchdarkly.com/docs/integrations/data-export
- **Integrations (Segment, Amplitude, etc.):** https://launchdarkly.com/docs/integrations
