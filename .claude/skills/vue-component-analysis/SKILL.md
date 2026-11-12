---
name: vue-component-analysis
description: Analyze Vue 3 component structure and suggest optimizations for performance and code reuse. Use when asked to review, audit, optimize, refactor or find duplication across Vue components, or "why is this page slow / hard to maintain". Produces a prioritized report; does not change code unless the user asks.
---

# Vue Component Analysis

Analyze the Vue 3 single-file components in a project and produce a prioritized list of **performance** and **reuse** improvements, each backed by evidence (file:line) and a concrete change.

Default mode is **report only**. Apply changes only if the user asks; then follow the project's rules (in this repo: `.vue` edits go through the `vue-expert` agent, Composition API, no emojis, comment non-obvious logic).

## 1. Run the analyzer

```bash
node .claude/skills/vue-component-analysis/scripts/analyze.mjs client          # human-readable
node .claude/skills/vue-component-analysis/scripts/analyze.mjs client --json   # for further processing
```

Argument = the directory containing `package.json` and `src/`. It loads `@vue/compiler-sfc` from that project's `node_modules` (run `npm install` there first if it fails), parses every `.vue` file under `src/`, and is read-only.

What it detects:

| Rule | Category | Why it matters |
|---|---|---|
| `index-key`, `missing-key` | perf/correctness | Index or missing `:key` in `v-for` makes Vue reuse the wrong DOM on reorder/filter |
| `v-if-with-v-for` | perf | `v-if` is evaluated per item; filter in a computed |
| `template-method-calls` | perf | Functions in `{{ }}` / `:bind` re-run on every render; derived data belongs in `computed` |
| `listener-leak`, `interval-leak` | perf/memory | Listeners/intervals not cleaned up in `onBeforeUnmount` |
| `double-load`, `deep-watch` | perf | Duplicate fetches; expensive deep watchers |
| `no-route-splitting` | perf | Statically imported views all land in the main bundle |
| `large-template` (>100 lines), `large-script` (>150) | reuse | Thresholds from `client/CLAUDE.md` for extracting components/composables |
| `duplicate-helper` | reuse | Same helper (`formatDate`, `get*Class`, `translate*`) defined in several components |
| `duplicate-css` | reuse | Identical CSS blocks across files → shared stylesheet |
| `direct-http`, `hardcoded-url` | reuse | HTTP outside `src/api.js` |
| `options-api` | consistency | Project standard is Composition API |
| `no-loading-state`, `no-error-state` | UX | Fetching components must show both states |
| `console-log`, `inline-styles`, `hardcoded-colors` | hygiene | Debug output, styles that bypass classes/tokens |

## 2. Verify before reporting

The analyzer is heuristic. For every finding you report, **open the file at that line and confirm it**. Drop false positives (e.g. a helper that is called once in a click handler, an index key on a static list that never reorders — say so if you keep it as low). Look for what static rules miss:

- **Reactivity cost**: large arrays in `ref` that are never mutated → `shallowRef`; computed chains that rebuild big arrays on every filter change; `watch` on objects that fire too often.
- **Repeated work across pages**: several views fetching the same endpoint (e.g. inventory) on every visit → shared composable with a cache.
- **Charts**: per-render geometry math in the template (`getCircleSegment(...)`, `getBarHeight(...)`) → precompute in one computed array.
- **Component boundaries**: repeated markup blocks (stat cards, tables with the same columns, modal shells) → extract a component with props/slots.
- **Bundle**: run `npx vite build` and note the largest chunks; recommend `() => import()` for rarely visited routes and heavy modals.

Measure where you can (bundle sizes from the build, request counts in the browser devtools/CDP, item counts) instead of asserting.

## 3. Report

```
## Vue component analysis — <project>

Summary: <N components, biggest risks in one or two sentences>

### Performance
1. [High] <title> — <file:line>
   Evidence: <what you saw / measured>
   Change: <specific refactor, short code sketch>
   Impact: <what improves, roughly how much>

### Reuse
1. [Medium] <title> — <files>
   ...

### Quick wins (≤ 15 min each)
- ...

### Not worth changing now
- <finding> — <why>
```

Order by impact ÷ effort. Group duplicates into one item (e.g. "`formatDate` in 7 components → `src/utils/date.js`") rather than listing each file. Finish with the 3 changes you would make first.

## 4. If asked to apply

Make the changes in small, separately testable steps (shared util/composable first, then call sites), run `npm run build`, re-run the analyzer to show the findings are gone, and check affected pages in the browser.
