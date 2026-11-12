# Audit Action Plan

Three parallel audits of the inventory management app (security, performance, UX), with each auditor challenging the others' severity ratings. Findings are merged where they share a root cause and ordered by **user impact ÷ effort**. IDs refer to the individual audit findings (SEC-n, PERF-n, UX-n).

Context: this is a workshop demo (no auth, in-memory data). "Severity" below is for the app as it is used today; production-only concerns are listed separately.

## Already fixed on this branch

| Item | Findings | Fix |
|---|---|---|
| Any website could read data / create POs via CORS | SEC-1 | Origins restricted to the frontend (`ALLOWED_ORIGINS` env), no credentials, explicit methods/headers |
| API reachable from the whole network | SEC-3 | Binds `127.0.0.1` by default (`HOST` env to override) |
| PO endpoint accepted NaN/Infinity, unbounded strings, any date | SEC-4, SEC-5 | Finite non-negative cost, size limits, ISO date not in the past, trimmed inputs |
| Concurrent requests could create duplicate POs | SEC-6 | Check-and-append under a lock (tested with 8 concurrent requests) |
| Invalid PO body reported as 409 instead of 400 | SEC-12 | Validation runs before existence/conflict checks |
| `/api/tasks` missing: console error on every page, adding tasks failed silently | PERF-13, UX-12 (part) | Tasks API (GET/POST/PATCH/DELETE) with tests; frontend error handling |
| No response compression | PERF-7 | `GZipMiddleware` (orders 110 KB → ~13 KB) |
| Reports page: no i18n, ignored filters, 90 console logs, index keys, Options API, stale responses | Bug bounty | Rewritten to app patterns; backend reports accept filters |

## P1: Correctness bugs (users see wrong numbers)

1. **Wrong data after quick filter changes + full-page blanking + sticky errors.** PERF-4, PERF-15, UX-14, error-not-cleared.
   Measured: filter says "May", table shows April's 19 orders. Every filter change replaces the page with "Loading…"; a failed request leaves the error banner up forever.
   **Fix (one change, all views):** a `useFetch` composable with a request token (or `AbortController`), keeping previous data visible while refreshing (`aria-busy`), clearing `error` on success. `Reports.vue` and `PurchaseOrderModal.vue` already use the token pattern.
   Effort: M. Fixes 3 findings across 6 views.

2. **Japanese prices off by 150×.** UX-4.
   Inventory, Orders and Finance charts concatenate `¥` with unconverted USD while the stat cards convert.
   **Fix:** route every money value through `formatCurrency` / `formatCurrencyWithDecimals`. Effort: S.

3. **Finance "Monthly Cost Flow" chart is meaningless.** UX-5.
   Divides by a hardcoded `maxValue = 25000` with hardcoded axis labels; real values are ~$555K, so every bar is pinned to the top.
   **Fix:** derive max and ticks from the data (as the revenue chart does). Effort: S.

4. **Finance ignores warehouse/category filters; quarter periods never match.** PERF challenge #3.
   `Spending.vue:266-276` compares `toISOString().slice(0,7)` to the period value.
   **Fix:** filter server-side via `/api/reports/monthly-trends?...` (already filter-aware). Effort: S.

## P2: Accessibility blockers (keyboard users cannot complete tasks)

5. **Language switcher and profile menu are mouse-only.** UX-1. Items use `@mousedown.prevent` and close on blur, so keyboard users can't change language, open tasks or log out.
   **Fix:** `@click` items, `focusout` with `relatedTarget` check, `aria-haspopup`/`aria-expanded`, Escape/arrow keys. Effort: S.
6. **Modals don't move/trap/restore focus or close on Escape.** UX-2. 7 modals.
   **Fix:** one `BaseModal` / `useModal` (focus first control, trap Tab, Escape closes, restore focus, `inert` on `.app-shell`). Effort: M; also removes duplicated modal shell markup.
7. **Clickable rows and chart bars unreachable by keyboard.** UX-3.
   **Fix:** a `<button>` in the first cell (SKU / order no.) and `<button>` bars with descriptive `aria-label`. Effort: S.
8. **Closed mobile drawer is still in the tab order.** UX-6.
   **Fix:** `inert` when closed below 1024px; focus first link on open; restore to the menu button. Effort: S.
9. **Focus ring fails 3:1 contrast** (1.4:1). UX-7. **Fix:** `outline: 2px solid var(--color-primary); outline-offset: 2px`. Effort: XS.
10. **Unlabeled filters/search, unnamed icon buttons, no skip link, `<html lang>` never changes.** UX-8, UX-9, UX-18, UX-11 (part). Effort: S.

## P3: Scale and efficiency (fine at 1×, breaks at 100×)

| # | Item | Findings | 100× measurement | Fix | Effort |
|---|---|---|---|---|---|
| 11 | Orders list has no pagination; renders every row and every item list | PERF-2, SEC challenge (unbounded responses) | 11 MB response, 489k DOM nodes, 4 s render, 174 MB heap | `limit`/`offset` + `total` (max limit), lazy item lists, virtual scroll or paging | M |
| 12 | Dashboard/Finance download all orders to aggregate | PERF-3, PERF-6 | 10.7 MB per page | Extend `/dashboard/summary` with the aggregates; Finance uses `/reports/monthly-trends` | M |
| 13 | Dashboard top-products is O(items × inventory) on deep proxies | PERF-1 | 9.7 s | `Map` by SKU + `shallowRef` for API arrays (or server-side, #12) | XS |
| 14 | Filter changes refetch filter-independent endpoints | PERF-5 | 4 requests where 2 needed | Split watchers by dependency | S |
| 15 | Per-call `useI18n()` and `toLocaleDateString` in row helpers | PERF-10 | 33× slower formatting | Cached `Intl.DateTimeFormat`, `useI18n()` once in setup | XS |
| 16 | Template helpers recomputed per render; search not debounced | PERF-11, PERF-12 | 115 ms keystrokes | Single-pass computeds; 150 ms debounce | S |
| 17 | Routes not lazy-loaded | PERF-14 | entry 92.6 → 77.6 KB gz | `() => import()` routes, async modals | XS |
| 18 | Server re-filters/aggregates per request; backlog×PO scan | PERF-8, PERF-9 | 10–18 ms; 142 ms at 4,000 POs | Precomputed month buckets; dict index for POs | S |

Severity dispute resolved: the backlog × PO lookup (PERF-9) is **Info** today (0.01 ms) and was deprioritized below PERF-1/PERF-2, which dominate at scale.

## P4: Polish

- Missing translations: Dashboard "Actions/Create PO/View PO", Demand product names, error messages, `document.title` per route, `alert()` in Finance (UX-11). Replace `alert()` with the existing cost modal.
- Empty states for zero results on Inventory/Orders/Demand (UX-13).
- Filter bar shows filters a page ignores; show only supported filters (UX-15).
- Mobile: 44px targets, no-wrap IDs, frozen first column / card rows (UX-16).
- Faint chart axis labels 2.56:1 → `--color-text-muted` (UX-17); plurals ("1 days"), consistent money decimals.
- Chart text alternatives (`role="img"` + data summary) (UX-10).

## Before any production use

| Item | Findings |
|---|---|
| Authentication and authorization on every route; `created_by` on POs | SEC-2 |
| Security headers / CSP / `frame-ancestors`, hide `server` header, disable or protect `/docs` | SEC-7 |
| API base URL from env, HTTPS, same-origin `/api` behind a proxy | SEC-8 |
| Commit lockfiles; pin MCP server versions (`server-github` is unpinned and receives a GitHub token); `npm audit` + `pip-audit` in CI | SEC-10 |
| Validate filter values against allowed lists; rate limiting; request body size limit | SEC-5, PERF challenge |
| Encode path params in `api.js` | SEC-9 |
| Redact the tool-usage logging hook output | SEC-11 |

## Suggested order

1. #1 `useFetch` composable (biggest correctness win, touches every view once).
2. #2–#4 money/chart/filter correctness (small, high trust impact).
3. #5–#9 keyboard and focus (shared `BaseModal` + menu fixes).
4. #13, #15, #17 (XS performance wins), then #11–#12 when data grows.
