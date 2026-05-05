# RIVR Data Loading & API Resilience Audit
**Date:** April 7, 2026

---

## Purpose

Audit how RIVR fetches, orchestrates, and displays forecast data from the NOAA National Water Prediction Service (NWPS) API. Identify bottlenecks in perceived performance, gaps in error transparency, and opportunities for progressive loading that reduces user wait time.

---

## Current Architecture

### Data Flow

```
User taps river
  │
  ▼
Phase 1 — loadOverviewData()              ← blocks until BOTH complete
  ├── fetchReachInfo()                     15s timeout
  └── fetchCurrentFlowOnly()              15s timeout (?series=short_range)
  │
  ▼  UI shows overview page
  │
Phase 2 — loadSupplementaryData()         ← blocks until BOTH complete
  ├── fetchReturnPeriods()                20s timeout (NWM API)
  └── fetchForecast('medium_range')       20s timeout (?series=medium_range)
  │
  ▼  UI updates with return periods + medium range
  │
Phase 3 — loadCompleteReachData()         ← blocks until ALL 3 complete
  ├── fetchForecast('short_range')        30s timeout
  ├── fetchForecast('medium_range')       30s timeout
  └── fetchForecast('long_range')         30s timeout
  │
  ▼  UI updates with all forecast types
```

### Key Files

| File | Role |
|------|------|
| `services/4_infrastructure/api/noaa_api_service.dart` | All NOAA HTTP calls, retry logic, unit conversion |
| `services/4_infrastructure/forecast/forecast_service.dart` | Phased loading orchestration, caching, computed values |
| `ui/1_state/features/forecast/reach_data_provider.dart` | Provider that calls ForecastService, notifies UI |
| `services/0_config/shared/config.dart` | API URLs and keys |

---

## Findings

### 1. NOAA API `?series=` Filter Is Unreliable (Server-Side)

**Severity:** High (data missing for users)
**Type:** External dependency issue

Live testing on April 7, 2026 revealed that the NWPS API's `?series=` query parameter is broken for medium and long range forecasts:

| Request | HTTP Status | Data? |
|---------|-------------|-------|
| `?series=short_range` | 200 | 18 data points, real flow values |
| `?series=medium_range` | 200 | Correct structure (7 members), **all data arrays empty**, `referenceTime: null` |
| `?series=long_range` | 200 | Partial — only 2 of 5 members have data, rest empty |
| No `?series=` filter | 200 | **All data populated** — short, medium (7 members, 204-240 pts each), long (5 members, 120 pts each), blend |

The unfiltered endpoint returns the exact same JSON structure with the same keys (`shortRange`, `mediumRange`, `longRange`, `mediumRangeBlend`, `analysisAssimilation`). The only difference is that all sections are populated.

**Impact:** Phase 2 medium range always returns empty. Phase 3 medium and long range return empty. Users see "No Data" for medium and long range forecasts.

**Note:** This may be a temporary server issue. The fix should handle both the broken and working states gracefully.

**Edge case — short range could fail too:** During testing, `?series=short_range` happened to work, but there is no guarantee. Short range is the most critical series — it powers the overview page's current flow display, the flow category badge, and the short-range chart. If short range returns empty:

- **Phase 1 breaks silently:** `loadOverviewData` would return a `ForecastResponse` with a null/empty `shortRange`, and `getCurrentFlow()` would fall through to medium/long range — which are also empty if the filter is broken for those too.
- **User sees a blank overview:** No current flow, no chart, no flow category. The page loads but shows nothing useful.
- **Favorites list shows no flow values:** `loadCurrentFlowOnly` depends entirely on short range.

The fallback strategy (Finding #6) must apply to **all** series, not just medium and long range. If any filtered request returns 200-with-empty-data, the unfiltered endpoint should be tried as a fallback.

### 2. Phase Gates Block on Slowest Request

**Severity:** Medium (perceived performance)
**Type:** Architecture

Each phase uses `Future.wait()` or sequential `await` calls, meaning the entire phase blocks until the slowest request completes:

- **Phase 1:** `Future.wait([fetchReachInfo, fetchCurrentFlowOnly])` — if reach info takes 3s and short range takes 8s, user waits 8s before seeing anything.
- **Phase 2:** Sequential `await` on return periods then medium range — these could run in parallel but don't.
- **Phase 3:** `Future.wait()` on 3 forecast types — one slow response holds up all data.

The phased approach is correct in principle, but within each phase, requests should resolve independently rather than gating on each other.

### 3. Single Global Loading State

**Severity:** Medium (UX)
**Type:** UI pattern

The UI uses a single loading indicator for the entire page. When Phase 1 completes, the page appears all at once. Medium range, long range, and return period sections don't have independent loading states — they either show data or show nothing.

**Impact:** User perceives a longer wait because they see nothing until the slowest Phase 1 request finishes. Sections that could display data earlier are held back.

### 4. No User Transparency on Data Sources

**Severity:** Low-Medium (user trust)
**Type:** UX

When a forecast section has no data, the UI shows no explanation of why. Users don't know:
- Where the data comes from (NOAA National Water Model)
- Why it might be unavailable (server issue vs. no coverage for this reach)
- Whether it's likely to resolve itself

For an app that democratizes access to government hydrological data, transparency about data provenance and availability builds user trust.

### 5. Empty Data Indistinguishable from No Coverage

**Severity:** Medium (correctness)
**Type:** Data handling

The API returns HTTP 503 with `"Data unavailable"` for reaches not covered by the NWPS endpoint. But it returns HTTP 200 with empty data arrays when the `?series=` filter is broken. The app treats both as "no data" — but they mean very different things:

- **503:** This reach isn't served by the NWPS API (permanent, for that reach)
- **200 with empty arrays:** Server glitch, data exists but filter is broken (transient)

The app should differentiate these cases to give users accurate messaging.

### 6. Retry Logic Is Solid but Missing Fallback

**Severity:** Medium (resilience)
**Type:** API layer

`_httpGetWithRetry` correctly handles timeouts and 5xx errors with exponential backoff (2 retries). However, there's no fallback strategy when the filtered endpoint returns 200-with-empty-data. The app accepts the empty response as valid because the HTTP status is 200.

A fallback to the unfiltered endpoint when the filtered response has empty data arrays would provide resilience against the current server behavior.

### 7. Short Range Is a Single Point of Failure for the Entire Overview

**Severity:** High (UX)
**Type:** Resilience

The overview page, favorites list, and flow category badge all depend on short range data via `getCurrentFlow()`. If short range is unavailable, the entire overview appears empty — even if medium or long range data could provide a reasonable current flow estimate.

`getCurrentFlow()` already has a fallback priority chain (`short_range → medium_range → long_range`), but that only works if those other series were loaded. In the current phased architecture:
- Phase 1 only loads short range
- Medium range isn't loaded until Phase 2
- Long range isn't loaded until Phase 3

So if short range fails in Phase 1, the fallback series aren't available yet. The user sees an empty page and has to wait for Phase 2/3 to potentially recover — but Phase 2/3 are only triggered after Phase 1 "succeeds."

**Impact:** A short range outage (even temporary) makes the app appear completely broken. The user has no indication that data might be available from other forecast types.

**Fix:** When short range returns empty, the overview should still render (show reach name/location from reach info) and immediately attempt to load medium range as a fallback source for current flow. The per-section loading states (Finding #3) would make this transition transparent.

### 8. Phase 3 Re-Fetches Short Range Unnecessarily

**Severity:** Low (efficiency)
**Type:** Redundancy

`fetchAllForecasts()` fetches `short_range`, `medium_range`, and `long_range` in parallel — but short range was already loaded in Phase 1. The re-fetch is wasted bandwidth and server load.

---

## Positive Findings

These aspects of the current architecture are well-designed:

1. **Unit conversion at the API layer** — all forecast data is converted to user's preferred unit before reaching the UI. Clean separation.
2. **ServiceResult pattern** — structured error handling prevents crashes from propagating.
3. **Cache-first for reach data** — static reach info (name, coordinates, return periods) is cached, only forecasts are fetched fresh.
4. **Graceful degradation** — Phase 2 and 3 failures don't crash the app; it continues with available data.
5. **Response cache for re-taps** — 5-minute TTL prevents hammering the API on rapid navigation.

---

## Summary

| # | Finding | Severity | Type |
|---|---------|----------|------|
| 1 | `?series=` filter returns empty data for medium/long range (any series could be affected) | High | External |
| 2 | Phase gates block on slowest request within each phase | Medium | Architecture |
| 3 | Single global loading state instead of per-section | Medium | UX |
| 4 | No transparency about data source or why data is missing | Low-Medium | UX |
| 5 | Empty API response indistinguishable from no coverage | Medium | Data handling |
| 6 | No fallback when filtered endpoint returns empty data | Medium | Resilience |
| 7 | Short range is a single point of failure for the entire overview | High | Resilience |
| 8 | Phase 3 re-fetches short range unnecessarily | Low | Efficiency |
