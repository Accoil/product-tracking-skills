<!-- Last verified: 2026-10-01 against Sentry docs (SDK v11.1.0) -->
# Sentry Implementation Reference

## Overview

Sentry is an error and performance monitoring platform. It is NOT a product analytics tool. Sentry captures exceptions, unhandled rejections, and performance traces in production applications. It appears on the Forge approved domain list because apps use it for operational monitoring, not for user behavior analytics.

**Category:** Error / Performance Monitoring
**B2B Fit:** None -- Sentry has no concept of accounts, groups, event funnels, or retention analysis. It tracks errors and performance, not product usage.

> **Version note:** The Sentry JavaScript SDK is currently at **v11.1.0** (September 2026). All core APIs documented here (`setUser`, `addBreadcrumb`, `captureException`, `captureMessage`, `startSpan`, `init`) remain stable across v8-v11. Key v11 changes: `sendDefaultPii` is deprecated and replaced by `dataCollection` (per-category control; **unset `dataCollection` now collects user info, cookies, headers and bodies by default**); `enableLogs` removed -- logs are sent whenever you call `Sentry.logger.*` (on by default since v10.71.0); spans are streamed by default (`traceLifecycle: 'stream'`, no transactions -- use `traceLifecycle: 'static'` for the old behavior); scope `tags`/`extra` are no longer applied to spans; `captureMessage()` attaches stack traces by default; Node.js 20.19.0+ required; Safari 14 dropped.

## SDK Options

| Environment | Integration | Install |
|---|---|---|
| Browser | `@sentry/browser` | `npm install @sentry/browser` |
| React | `@sentry/react` | `npm install @sentry/react` |
| Node.js | `@sentry/node` | `npm install @sentry/node` |
| HTTP API | Envelope endpoint | No SDK -- raw `fetch()` calls to `https://{org}.ingest.sentry.io` |

## Initialization

### Browser

```typescript
import * as Sentry from '@sentry/browser';

Sentry.init({
  dsn: 'https://examplePublicKey@o0.ingest.sentry.io/0',
  environment: process.env.NODE_ENV,
  release: 'my-app@1.2.3',
  dataCollection: { userInfo: true }, // Replaces deprecated sendDefaultPii (v11); controls IP inference

  // Performance monitoring -- sample rate for transactions
  tracesSampleRate: 0.1,             // 10% of transactions
  tracePropagationTargets: ['localhost', /^https:\/\/yourserver\.io\/api/],

  // Session replay (optional)
  replaysSessionSampleRate: 0.1,     // 10% of sessions
  replaysOnErrorSampleRate: 1.0,     // 100% of sessions with errors

  // Structured logging: no flag needed in v11 -- logs are sent when you call Sentry.logger.*
});
```

### React

The React SDK now recommends a separate `instrument.ts` file imported before all other modules:

**instrument.ts:**
```typescript
import * as Sentry from '@sentry/react';

Sentry.init({
  dsn: 'https://examplePublicKey@o0.ingest.sentry.io/0',
  environment: process.env.NODE_ENV,
  release: 'my-app@1.2.3',
  dataCollection: { userInfo: true },
  integrations: [
    Sentry.browserTracingIntegration(),
    Sentry.replayIntegration(),
  ],
  tracesSampleRate: 0.1,
  tracePropagationTargets: ['localhost', /^https:\/\/yourserver\.io\/api/],
});
```

**main.tsx:**
```typescript
import './instrument';  // Must be first import
import App from './App';
import { createRoot } from 'react-dom/client';

const root = createRoot(document.getElementById('app')!);
root.render(<App />);
```

### Node.js

**Important:** Node.js 20.19.0+ is required (v11). Create a dedicated `instrument.ts` file and load it before all other modules.

**instrument.ts:**
```typescript
import * as Sentry from '@sentry/node';

Sentry.init({
  dsn: 'https://examplePublicKey@o0.ingest.sentry.io/0',
  environment: process.env.NODE_ENV,
  release: 'my-app@1.2.3',
  dataCollection: { userInfo: true },
  tracesSampleRate: 0.1,
});
```

**CommonJS:** Require the instrument file first in your entry point.
**ESM:** Use Node's `--import` flag: `node --import ./instrument.mjs app.mjs`

The SDK instruments modules at import time and must be initialized before importing other modules.

## User Context (identify equivalent)

Sentry's `setUser()` is NOT a full identify call. It tags errors and performance events with user information so you can search for issues affecting a specific user. It does not create user profiles, track user properties over time, or feed into behavioral analytics.

**Browser:**

```typescript
import * as Sentry from '@sentry/browser';

Sentry.setUser({
  id: 'usr_123',
  email: 'jane@example.com',
  username: 'jane_smith',
});
```

**Node.js:**

```typescript
import * as Sentry from '@sentry/node';

// In a request handler or middleware
Sentry.setUser({
  id: 'usr_123',
  email: 'jane@example.com',
  username: 'jane_smith',
});
```

**Supported fields:**

| Field | Type | Purpose |
|---|---|---|
| `id` | `string \| number` | Primary user identifier |
| `email` | string | User email -- visible in Sentry issue detail |
| `username` | string | Display name |
| `ip_address` | string | Set to `"{{auto}}"` to use the client IP, or omit. In v11, `{{auto}}` is set automatically when `dataCollection.userInfo` is `true` (the default) |

You can also pass arbitrary key-value pairs:

```typescript
Sentry.setUser({
  id: 'usr_123',
  email: 'jane@example.com',
  account_id: 'acc_456',
  plan: 'enterprise',
  role: 'admin',
});
```

**Clear user context on logout:**

```typescript
Sentry.setUser(null);
```

**When to call:**
- After login, once user identity is known
- After signup completes
- On app initialization if the user is already authenticated
- On logout, call `Sentry.setUser(null)` to clear context

## Custom Events and Breadcrumbs

### Structured Logging (`Sentry.logger`) -- Recommended

Since v9.41.0, Sentry offers `Sentry.logger` as a structured logging API. Logs are enabled by default from v10.71.0, and the `enableLogs` option was removed in v11 -- logs are captured whenever you call `Sentry.logger.*` or add a logging integration. Sentry docs now recommend structured logging over `addBreadcrumb()` for new implementations -- logs are searchable, trace-connected, and viewable alongside errors.

**Enable in init:** No option needed in v11 (on SDK versions below 10.71.0, set `enableLogs: true`).

```typescript
Sentry.init({
  dsn: 'https://examplePublicKey@o0.ingest.sentry.io/0',
});
```

**Available log levels:**

| Method | Purpose |
|---|---|
| `Sentry.logger.trace()` | Fine-grained debugging |
| `Sentry.logger.debug()` | Development diagnostics |
| `Sentry.logger.info()` | Normal operations, milestones |
| `Sentry.logger.warn()` | Potential issues, degraded state |
| `Sentry.logger.error()` | Failures that need attention |
| `Sentry.logger.fatal()` | Critical failures, system down |

**Basic usage:**

```typescript
Sentry.logger.info('Order created', { orderId: 'order_456', plan: 'pro' });
Sentry.logger.warn('Rate limit approaching', { current: 95, max: 100 });
Sentry.logger.error('Payment failed', { reason: 'card_declined' });
```

The second parameter accepts an object with `string`, `number`, and `boolean` values as searchable attributes.

**Parameterized messages with `fmt`:**

Use `Sentry.logger.fmt` as a template literal tag to send the template and parameters separately, making them independently searchable in Sentry:

```typescript
const userId = 'user_123';
const productName = 'Widget Pro';
Sentry.logger.info(Sentry.logger.fmt`User ${userId} purchased ${productName}`);
```

**Filtering logs with `beforeSendLog`:**

```typescript
Sentry.init({
  dsn: 'https://examplePublicKey@o0.ingest.sentry.io/0',
  beforeSendLog: (log) => {
    if (log.level === 'debug') return null;  // Drop debug logs
    if (log.attributes?.password) delete log.attributes.password;
    return log;
  },
});
```

**Console integration -- capture `console.log` calls as Sentry logs:**

```typescript
Sentry.init({
  dsn: 'https://examplePublicKey@o0.ingest.sentry.io/0',
  integrations: [
    Sentry.consoleLoggingIntegration({ levels: ['log', 'warn', 'error'] }),
  ],
});
```

### Breadcrumbs (Legacy)

Breadcrumbs provide a trail of events leading up to an error. Sentry automatically captures breadcrumbs for console logs, DOM events, XHR/fetch requests, and navigation. You can add custom breadcrumbs for product context. The `addBreadcrumb()` API remains fully functional but Sentry docs now recommend structured logging (above) for new implementations.

```typescript
Sentry.addBreadcrumb({
  category: 'product',
  message: 'User created a report',
  level: 'info',
  data: {
    report_id: 'rpt_789',
    report_type: 'standard',
    account_id: 'acc_456',
  },
});
```

Custom breadcrumbs are useful for debugging -- when an error occurs, the breadcrumb trail shows what product actions the user took before the crash. This is operational context, not analytics data.

### Custom Messages

Capture non-exception events when you want to flag something in Sentry without throwing:

```typescript
Sentry.captureMessage('Payment retry limit reached', {
  level: 'warning',
  tags: {
    account_id: 'acc_456',
    payment_provider: 'stripe',
  },
  extra: {
    retry_count: 3,
    last_attempt: '2025-01-15T10:30:00Z',
  },
});
```

### Tags vs Extra Data

- **Tags** are indexed and searchable in Sentry. Use for low-cardinality values you want to filter by (e.g., `plan`, `environment`, `region`). Keys and values are limited to 200 characters each. In v11, scope tags/extra are no longer applied to spans -- use `span.setAttribute()` for span-searchable data.
- **Extra data** is not indexed. Use for high-cardinality debugging context (e.g., request payloads, specific IDs).

```typescript
// Set tags globally -- applied to all subsequent events
Sentry.setTag('account_id', 'acc_456');
Sentry.setTag('plan', 'enterprise');

// Set multiple tags at once
Sentry.setTags({
  account_id: 'acc_456',
  plan: 'enterprise',
  region: 'us-east-1',
});

// Set extra context globally
Sentry.setExtra('deployment_id', 'deploy_abc');

// Set structured context (not searchable, but viewable on issue detail)
Sentry.setContext('deployment', {
  id: 'deploy_abc',
  environment: 'production',
  timestamp: '2026-03-10T12:00:00Z',
});
```

### Capturing Exceptions

```typescript
try {
  await riskyOperation();
} catch (error) {
  Sentry.captureException(error, {
    tags: { operation: 'report_generation' },
    extra: { report_id: 'rpt_789' },
  });
}
```

## Performance Monitoring

Sentry's performance monitoring tracks transaction timing and spans. This is operational performance data (response times, database query duration), not product analytics.

```typescript
// Automatic instrumentation handles most cases.
// Manual spans for custom operations:
Sentry.startSpan(
  {
    name: 'generate-report',
    op: 'task',
    attributes: {
      report_type: 'standard',
    },
  },
  async (span) => {
    await generateReport();
    // Span ends automatically when the callback returns
  }
);
```

**Additional span APIs:**

```typescript
// startSpanManual -- for cases where automatic closure isn't suitable
Sentry.startSpanManual({ name: 'middleware', op: 'http' }, (span) => {
  res.once('finish', () => {
    Sentry.setHttpStatus(span, res.statusCode);
    span.end();  // Must call end() manually
  });
  return next();
});

// startInactiveSpan -- for independent span tracking
const span = Sentry.startInactiveSpan({ name: 'background-task' });
await doWork();
span.end();
```

**Span options:**

| Parameter | Type | Required | Purpose |
|---|---|---|---|
| `name` | string | Yes | Identifies the span |
| `op` | string | No | Categorizes span operation type |
| `attributes` | Record | No | Attaches custom data pairs |
| `parentSpan` | Span | No | Designates parent relationship |
| `onlyIfParent` | boolean | No | Ignores span if no active parent exists |
| `forceTransaction` | boolean | No | Forces span visibility as transaction in UI |

**Key configuration:**
- `tracesSampleRate: 1.0` -- 100% of transactions (use in development only)
- `tracesSampleRate: 0.1` -- 10% of transactions (typical production setting)
- `tracesSampleRate: 0` -- disable performance monitoring
- `tracePropagationTargets` -- array of strings/regexes controlling which URLs receive trace headers for distributed tracing

## What Sentry Is NOT

Sentry does not replace product analytics. Specifically:

- **No group/account concept** -- `setUser()` tags individual errors with user info. There is no `group()` or account-level aggregation.
- **No event funnels** -- Sentry tracks errors and transactions, not user journeys through product flows.
- **No retention analysis** -- No DAU/WAU/MAU metrics, no cohort analysis, no engagement scoring.
- **No behavioral segmentation** -- You cannot segment users by product actions or feature usage.
- **No user property persistence** -- `setUser()` sets context for the current session/scope. It does not build a persistent user profile.

**Use Sentry alongside a product analytics tool.** A typical B2B SaaS app might use:
- **Amplitude / Mixpanel / PostHog** for product analytics (identify, group, track)
- **Sentry** for error monitoring and performance visibility

Both can share the same user ID (`usr_123`), allowing you to cross-reference a user's error history with their product usage.

## Forge Compatibility

### Approved Domains

Sentry is on the Forge approved analytics domain list:

| Domain Pattern | Purpose |
|---|---|
| `*.ingest.sentry.io` | Event ingestion (primary) |
| `*.ingest.us.sentry.io` | US region ingestion |
| `*.sentry-cdn.com` | SDK loader (CDN) |

### Manifest Configuration

```yaml
permissions:
  external:
    fetch:
      backend:
        - address: "*.ingest.sentry.io"
          category: analytics
          inScopeEUD: false
```

**Important:** Sentry error payloads can contain stack traces, request URLs, and other data that may include end user content. When using Sentry in a Forge app, configure `beforeSend` to strip any in-scope End User Data before transmission:

```typescript
Sentry.init({
  dsn: 'https://examplePublicKey@o0.ingest.sentry.io/0',
  beforeSend(event) {
    // Strip request data that might contain EUD
    if (event.request) {
      delete event.request.data;
      delete event.request.query_string;
    }
    // Strip breadcrumb messages that might contain user content
    if (event.breadcrumbs) {
      event.breadcrumbs = event.breadcrumbs.map((breadcrumb) => {
        if (breadcrumb.category === 'console') {
          return { ...breadcrumb, message: '[redacted]' };
        }
        return breadcrumb;
      });
    }
    return event;
  },
});
```

## Common Pitfalls

1. **Treating Sentry as product analytics** -- Sentry tracks errors, not user behavior. Do not use `captureMessage()` as a substitute for `analytics.track()`. Error monitoring and product analytics serve different purposes and should use separate tools.

2. **Forgetting to call `setUser(null)` on logout** -- If the user logs out and another user logs in, Sentry will attribute the new user's errors to the old user. Always clear user context on logout.

3. **Sending PII in stack traces and breadcrumbs** -- Sentry captures full stack traces, console logs, and HTTP request data by default. In a Forge app or any privacy-sensitive context, use `beforeSend` and `beforeBreadcrumb` hooks to strip sensitive data before it leaves the client. In v11 the default (no `dataCollection`) collects user info, cookies, headers and request bodies -- set `dataCollection: { userInfo: false, cookies: false, httpBodies: [] }` (etc.) to opt out; `sendDefaultPii: false` is deprecated.

4. **Setting `tracesSampleRate: 1.0` in production** -- Full transaction sampling generates massive volume and can exceed your Sentry quota. Use `0.1` (10%) or lower in production. Adjust based on traffic volume and Sentry plan limits.

5. **Assuming user context persists across requests in Node.js** -- In the browser, `setUser()` persists for the session. In Node.js, Sentry uses async-context isolation. You must call `setUser()` within the scope of each request (typically in middleware), not once at startup.

6. **Mismatched user IDs between Sentry and product analytics** -- If your product analytics tool identifies users as `usr_123` but Sentry uses a different ID format, you lose the ability to cross-reference errors with product usage. Use the same user ID in both `Sentry.setUser({ id: 'usr_123' })` and `analytics.identify('usr_123')`.

7. **Carrying v10 options into v11** -- `enableLogs` was removed in v11 (logs are sent whenever `Sentry.logger.*` is called), and `sendDefaultPii` is deprecated in favor of `dataCollection`. Note the default flipped: v10 with no `sendDefaultPii` was restrictive, v11 with no `dataCollection` collects everything. `beforeSendLog` remains a top-level option.

## Debugging

### Verify SDK Is Sending Events

Enable debug mode to see Sentry SDK activity in the console:

```typescript
Sentry.init({
  dsn: 'https://examplePublicKey@o0.ingest.sentry.io/0',
  debug: true,  // Logs SDK activity to console
});
```

### Trigger a Test Error

```typescript
// Browser -- throw a test exception
Sentry.captureException(new Error('Sentry test error'));

// Or use the built-in test method
throw new Error('Sentry connection test');
```

### Browser DevTools

Check the Network tab for requests to `*.ingest.sentry.io`. Successful submissions return HTTP `200`. The request body uses Sentry's envelope format (not plain JSON).

### Sentry Dashboard

1. Open your Sentry project in the Sentry web UI
2. Navigate to **Issues** to see captured errors
3. Use the search bar to filter by user: `user.id:usr_123`
4. Check **Performance** tab for transaction traces
5. Check **Logs** tab for structured log entries

### Common Response Codes

| Code | Meaning |
|---|---|
| `200` | Event accepted |
| `401` | Invalid or missing DSN |
| `429` | Rate limited -- too many events |
| `403` | Project disabled or DSN revoked |

## Further Documentation

This reference covers the essentials for using Sentry alongside product analytics in a B2B application. For advanced topics, consult Sentry's official documentation:

- **Getting Started (Browser):** https://docs.sentry.io/platforms/javascript/
- **React SDK:** https://docs.sentry.io/platforms/javascript/guides/react/
- **Node.js SDK:** https://docs.sentry.io/platforms/javascript/guides/node/
- **Configuration Options:** https://docs.sentry.io/platforms/javascript/configuration/options/
- **SDK APIs (setUser, setContext, setTag):** https://docs.sentry.io/platforms/javascript/configuration/apis/
- **Set User:** https://docs.sentry.io/platforms/javascript/configuration/apis/#setUser
- **Breadcrumbs:** https://docs.sentry.io/platforms/javascript/enriching-events/breadcrumbs/
- **Structured Logging:** https://docs.sentry.io/platforms/javascript/logs/
- **Performance Monitoring:** https://docs.sentry.io/platforms/javascript/tracing/
- **Custom Instrumentation:** https://docs.sentry.io/platforms/javascript/tracing/instrumentation/
- **Data Scrubbing & Privacy:** https://docs.sentry.io/security-legal-pii/scrubbing/
- **Envelope API:** https://develop.sentry.dev/sdk/foundations/envelopes/
- **v10 to v11 Migration:** https://docs.sentry.io/platforms/javascript/migration/v10-to-v11/
- **v9 to v10 Migration:** https://docs.sentry.io/platforms/javascript/migration/v9-to-v10/
