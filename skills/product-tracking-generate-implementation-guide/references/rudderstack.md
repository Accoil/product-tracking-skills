<!-- Last verified: 2026-10-01 against RudderStack docs (@rudderstack/analytics-js v3.34.x, @rudderstack/rudder-sdk-node v3.0.x) -->
# RudderStack Implementation Guide

## Overview

RudderStack is an open-source customer data platform (CDP) that routes events to downstream destinations. Its API is Segment-compatible — the same identify/group/track model — so switching between them requires minimal code changes.

## Installation

**npm (recommended for SPAs):**
```bash
npm install @rudderstack/analytics-js
```

**CDN snippet (traditional websites):**

Add to `<head>`. Replace `WRITE_KEY` and `DATA_PLANE_URL` from your RudderStack source dashboard. The recommended approach is to copy the snippet directly from your RudderStack dashboard (Sources > JavaScript > Setup), which includes your write key and data plane URL pre-filled.

> **Note:** SDK v3 uses a new CDN URL pattern (`cdn.rudderlabs.com/v3/[modern|legacy]/rsa.min.js`) and a substantially different snippet than v1.1. The snippet below is the current v3 pattern. The SDK auto-detects browser capabilities and loads the appropriate modern or legacy bundle.

```html
<script type="text/javascript">
!function(){"use strict";
  var e,n,s,o,i,a,r,c,l,d,t="rudderanalytics";
  if(window[t]||(window[t]=[]),e=window[t],!Array.isArray(e))return;
  if(e.snippetExecuted===!0){window.console&&console.error("RudderStack JavaScript SDK snippet included more than once.");return}
  e.snippetExecuted=!0;
  window.rudderAnalyticsBuildType="legacy";
  c="https://cdn.rudderlabs.com/v3";
  l="rsa.min.js";
  i=["setDefaultInstanceKey","load","ready","page","track","identify","alias","group","reset",
     "setAnonymousId","startSession","endSession","consent"];
  for(n=0;n<i.length;n++)a=i[n],e[a]=function(n){return function(){
    if(Array.isArray(window[t]))e.push([n].concat(Array.prototype.slice.call(arguments)));
    else{var s;(s=window[t][n])===null||s===void 0||s.apply(window[t],arguments)}
  }}(a);
  try{new Function('class Test{field=()=>{};test({prop=[]}={}){return prop?(prop?.property??[...prop]):import("");}}');
    window.rudderAnalyticsBuildType="modern"}catch(x){}
  s=document.head||document.getElementsByTagName("head")[0];
  r=document.body||document.getElementsByTagName("body")[0];
  window.rudderAnalyticsAddScript=function(e,t,n){
    var i=document.createElement("script");i.src=e;i.setAttribute("data-loader","RS_JS_SDK");
    t&&n&&i.setAttribute(t,n);i.async=!0;
    s?s.insertBefore(i,s.firstChild):r.insertBefore(i,r.firstChild);
  };
  window.rudderAnalyticsMount=function(){
    window.rudderAnalyticsAddScript("".concat(c,"/").concat(window.rudderAnalyticsBuildType,"/").concat(l),"data-rsa-write-key","WRITE_KEY");
  };
  typeof Promise=="undefined"||typeof globalThis=="undefined"
    ?window.rudderAnalyticsAddScript("https://polyfill-fastly.io/v3/polyfill.min.js?version=3.111.0&features=Symbol%2CPromise&callback=rudderAnalyticsMount")
    :window.rudderAnalyticsMount();
  e.load("WRITE_KEY","DATA_PLANE_URL");
}();
</script>
```

> **Important (v3 change):** The implicit `page()` call at the end of the snippet (present in v1.1) has been removed in SDK v3. Call `rudderanalytics.page()` explicitly (and on every route change in SPAs). Note: `autoTrack.pageLifecycle` in the load options does **not** fire `page()` calls — it only adds a `pageViewId` to event context and, with Beacon enabled, sends a `Page Unloaded` track event with time on page.

## Initialization (npm)

```typescript
import { RudderAnalytics } from '@rudderstack/analytics-js';

const analytics = new RudderAnalytics();
analytics.load('WRITE_KEY', 'DATA_PLANE_URL');
```

## Core Flow: Identify, Group, Track

### 1. Identify the User

Call on login or signup, once the user ID is known.

```typescript
analytics.identify('usr_123', {
  email: 'jane@example.com',
  name: 'Jane Smith',
  role: 'admin',
  plan: 'pro'
});
```

This ties all future events from this browser to the identified user.

### 2. Associate User with a Group

For B2B, always call `group()` after `identify()` to establish account context.

```typescript
analytics.group('acc_456', {
  name: 'Acme Corp',
  plan: 'enterprise',
  employee_count: 50
});
```

For hierarchical products, issue a `group()` call for **every level** in the hierarchy, with `parent_group_id` to establish relationships:

```typescript
// Account (top level)
analytics.group('acc_456', {
  name: 'Acme Corp',
  group_type: 'account',
  plan: 'enterprise'
});

// Workspace (child of account)
analytics.group('ws_789', {
  name: 'Engineering',
  group_type: 'workspace',
  parent_group_id: 'acc_456'
});

// Project (child of workspace)
analytics.group('proj_123', {
  name: 'Q1 Release',
  group_type: 'project',
  parent_group_id: 'ws_789'
});
```

### 3. Track Events

```typescript
analytics.track('report.created', {
  report_id: 'rpt_789',
  report_type: 'standard'
});
```

The SDK automatically attaches the identified user. You do not need to pass `userId` in the browser.

### 4. Reset on Logout

```typescript
analytics.reset();  // By default clears userId, user traits, groupId, and group traits (selectively via reset({ entries: {...} }))
```

## Group Attribution

Group association comes from `group()` calls -- send one per group (per hierarchy level) the user belongs to. Track calls stay plain (event name + properties); RudderStack's common-fields spec defines no `context.groupId`, so don't add it to track calls expecting downstream attribution.

Per-event group attribution, where it exists, is destination-specific -- check the destination's RudderStack docs. For example, the Amplitude and Mixpanel cloud-mode docs document groups only through `group()` calls (Amplitude: Group name/value trait settings, one group per call; Mixpanel: Group Key settings, looked up from `message.groupId` / `message.traits`).

**Critical limitation:** RudderStack has no native group hierarchy support. Hierarchical rollups depend on the downstream tool supporting `parent_group_id` traits on group calls.

## Node.js (Server-Side)

```typescript
import Analytics from '@rudderstack/rudder-sdk-node';

const analytics = new Analytics('WRITE_KEY', {
  dataPlaneUrl: 'DATA_PLANE_URL'
});

// Server-side requires userId on every call
analytics.identify({
  userId: 'usr_123',
  traits: {
    email: 'jane@example.com',
    plan: 'pro'
  }
});

analytics.group({
  userId: 'usr_123',
  groupId: 'acc_456',
  traits: {
    name: 'Acme Corp',
    plan: 'enterprise'
  }
});

analytics.track({
  userId: 'usr_123',
  event: 'report.created',
  properties: {
    report_id: 'rpt_789',
    report_type: 'standard'
  }
});
```

## HTTP API Limits

Base URL is your data plane URL; auth is Basic with the source write key as username and an empty password. Max 32 KB per call; `/v1/batch` accepts up to 4 MB per request (32 KB per event). Oversized requests return `400`.

## Verifying Events

1. Go to your Source in the RudderStack dashboard
2. Open the **Live Events** debugger
3. Trigger actions in your app and confirm `identify`, `group`, and `track` events appear with correct payloads

## Common Pitfalls

1. **Calling track before identify** -- Events are anonymous until identify is called
2. **Forgetting reset on logout** -- Previous user context persists for the next user
3. **Missing group() calls** -- Downstream B2B tools lose account-level attribution
4. **Server-side without userId** -- Unlike the browser SDK, there is no implicit user context
5. **Expecting `context.groupId` on track calls to attribute events** -- It isn't part of RudderStack's spec; use `group()` calls, plus any destination-specific per-event mechanism

## Further Documentation

This reference covers the essentials for product tracking implementation. For advanced topics, consult RudderStack's official documentation:

- **Getting Started:** https://www.rudderstack.com/docs/get-started/introduction/
- **JavaScript SDK:** https://www.rudderstack.com/docs/sources/event-streams/sdks/rudderstack-javascript-sdk/
- **Node.js SDK:** https://www.rudderstack.com/docs/sources/event-streams/sdks/rudderstack-node-sdk/
- **Identify:** https://www.rudderstack.com/docs/event-spec/standard-events/identify/
- **Group:** https://www.rudderstack.com/docs/event-spec/standard-events/group/
- **Track:** https://www.rudderstack.com/docs/event-spec/standard-events/track/
- **Destinations:** https://www.rudderstack.com/docs/destinations/overview/
- **HTTP API:** https://www.rudderstack.com/docs/api/http-api/
- **Transformations:** https://www.rudderstack.com/docs/transformations/overview/
