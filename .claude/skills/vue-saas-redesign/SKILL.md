---
name: vue-saas-redesign
description: Redesign a Vue 3 application's UI into a modern SaaS-style interface - left vertical sidebar navigation instead of a top nav bar, a design-token system, consistent 4/8px spacing, and polished cards, tables, badges and page headers. Use when asked to modernize, restyle, or "make professional" a Vue 3 app's layout, or to replace a top nav with a sidebar. Visual/layout only - never changes business logic, API calls, routes or data.
---

# Vue 3 SaaS Redesign

Turn an existing Vue 3 app into a clean SaaS dashboard layout:

```
+------------+------------------------------------------+
|  Brand     |  Topbar: page title · filters · actions  |
|            +------------------------------------------+
|  Nav item  |                                          |
|  Nav item  |   Page header                            |
|  Nav item  |   Content (cards, tables, charts)        |
|            |                                          |
|  ────────  |                                          |
|  User/menu |                                          |
+------------+------------------------------------------+
   240px (64px collapsed, off-canvas drawer < 1024px)
```

Supporting files in this skill directory:
- `references/tokens.css` - design tokens (color, spacing, radius, shadow, type). Copy into the app.
- `templates/AppSidebar.vue` - sidebar component: collapse, mobile drawer, active state, a11y.

## Ground rules

1. **Visual and layout changes only.** Do not change API calls, data loading, computed logic, router paths, props/emits contracts, i18n keys or filter state. If a component's markup must change, keep every binding, event handler and `v-if`/`v-for` intact.
2. **No new dependencies** unless the user asks. Icons are inline SVG; no UI kit, no icon package, no Tailwind.
3. **Follow the project's own instructions first.** Read `CLAUDE.md` files (root and `client/`). If they require delegating `.vue` edits to a subagent (e.g. `vue-expert`), do that and pass it this skill's rules and the token file path. Honor rules like "no emojis in UI" and existing colour palettes.
4. **Match the codebase's component style.** If components use `export default { setup() }`, write new ones the same way; if they use `<script setup>`, use that. Adapt the template accordingly.
5. **Work on a branch** and keep the diff reviewable: tokens and shell first, then pages.

## Workflow

### 1. Audit (read before writing)

Find and note:
- **App shell**: usually `src/App.vue` - where the top nav, `<router-view>`, global bars (filters, language switcher, profile menu) and modals live.
- **Routes**: `src/main.js` or `src/router/*` - every path the sidebar must link to, plus any view files that exist but are unrouted (report these; don't silently add routes).
- **Global styles**: unscoped `<style>` in `App.vue`, `src/assets/*.css`, `src/style.css`. List shared classes (`.card`, `.stat-card`, `.badge`, `.page-header`, tables) - restyling these is high leverage.
- **Hardcoded values**: `grep -rnE '#[0-9a-fA-F]{3,6}|[0-9.]+(px|rem)' src --include=*.vue` to gauge how many colours and spacings are inlined in scoped styles.
- **i18n**: if nav labels go through `t('nav.x')`, the sidebar must use the same keys.
- **Header-only widgets**: language switcher, profile menu, notifications - decide where each goes (sidebar footer or topbar).

Summarize the plan to the user in a few lines before large edits if the app has more than ~5 views.

### 2. Install the token layer

Copy `references/tokens.css` into the app (e.g. `src/styles/tokens.css`) and import it once in `main.js` *before* other styles. If the project already has a palette (e.g. in `CLAUDE.md`), map those values onto the token names instead of replacing them.

All new and edited CSS must use tokens - `var(--space-4)`, `var(--color-text-muted)` - not raw hex or arbitrary px.

**Spacing scale** (4px base): `--space-1` 4 · `--space-2` 8 · `--space-3` 12 · `--space-4` 16 · `--space-5` 20 · `--space-6` 24 · `--space-8` 32 · `--space-10` 40 · `--space-12` 48. Snap every padding/margin/gap to this scale.

### 3. Build the shell

1. Copy `templates/AppSidebar.vue` to `src/components/AppSidebar.vue`. Fill `navItems` from the router (path, label or i18n key, icon). Order items by importance, group into sections if there are more than ~6.
2. Rewrite the `App.vue` template to:

```html
<div class="app-shell" :class="{ 'is-collapsed': sidebarCollapsed }">
  <AppSidebar v-model:collapsed="sidebarCollapsed" v-model:mobile-open="mobileNavOpen">
    <template #footer><!-- ProfileMenu, LanguageSwitcher --></template>
  </AppSidebar>
  <div class="app-main">
    <header class="app-topbar">
      <button class="topbar-menu" @click="mobileNavOpen = true" aria-label="Open navigation">…</button>
      <!-- page title (from route meta or nav item), global filters, actions -->
    </header>
    <main class="app-content"><router-view /></main>
  </div>
  <!-- existing modals unchanged -->
</div>
```

3. Shell CSS (unscoped, in `App.vue` or `src/styles/layout.css`):

```css
.app-shell { display: grid; grid-template-columns: var(--sidebar-width) 1fr; min-height: 100vh; background: var(--color-bg); }
.app-shell.is-collapsed { grid-template-columns: var(--sidebar-width-collapsed) 1fr; }
.app-main { min-width: 0; display: flex; flex-direction: column; }
.app-topbar { position: sticky; top: 0; z-index: var(--z-topbar); display: flex; align-items: center; gap: var(--space-4);
  height: var(--topbar-height); padding: 0 var(--space-8); background: color-mix(in srgb, var(--color-surface) 85%, transparent);
  backdrop-filter: blur(8px); border-bottom: 1px solid var(--color-border); }
.app-content { padding: var(--space-8); max-width: var(--content-max); width: 100%; margin: 0 auto; }
.topbar-menu { display: none; }
@media (max-width: 1023px) {
  .app-shell, .app-shell.is-collapsed { grid-template-columns: 1fr; }
  .topbar-menu { display: inline-flex; }
  .app-topbar, .app-content { padding-inline: var(--space-4); }
}
```

4. Move global filter bars into the topbar (or directly under it as a sub-bar if they are wide). Keep the component; change only its container styles.
5. Delete the old top-nav markup and its CSS once the sidebar renders every route.

### 4. Polish shared components

Restyle the shared global classes first, then scoped styles per view. Targets:

| Element | Spec |
|---|---|
| Page header | Title `--text-2xl`/600, muted subtitle, actions right-aligned; `margin-bottom: var(--space-6)` |
| Card | `--color-surface`, 1px `--color-border`, `--radius-lg`, `--shadow-sm`, padding `--space-6`; header with title `--text-md`/600 and optional actions; no heavy hover effects |
| Stat / KPI card | Label `--text-sm` muted (sentence case, not uppercase-shouting), value `--text-3xl`/600 tabular-nums, optional delta badge |
| Grid | `display: grid; gap: var(--space-6)`; KPI rows `repeat(auto-fit, minmax(220px, 1fr))` |
| Table | Header row `--color-surface-muted`, `--text-xs` uppercase muted labels; rows 44-48px tall; `--color-border-subtle` dividers; numeric columns right-aligned + tabular-nums; row hover `--color-surface-hover` |
| Badge | Pill (`--radius-full`), `--text-xs`/500, soft background + strong text from the status tokens; sentence case |
| Buttons | Primary: `--color-primary` bg; secondary: surface + border; 36px tall; `--radius-md`; visible `:focus-visible` ring |
| Inputs/selects | 36px, `--radius-md`, border `--color-border`, focus ring `--shadow-focus` |
| Modals | `--radius-xl`, `--shadow-lg`, padding `--space-6`, overlay `rgb(15 23 42 / .45)` |
| Loading / empty / error | Centered muted text or skeleton blocks; error uses danger-soft background |

Remove one-off colours, double borders, and inconsistent radii as you go. Keep chart colours readable; update their hex values to status/primary tokens where it is a direct swap.

### 5. Verify

Do all of these before reporting done:
- `npm run build` passes with no new warnings.
- Run the dev server and visit **every** route: sidebar active state is correct on each, data still loads, filters still change data, modals still open and close.
- Check widths 1440, 1024, 768 and 375: no horizontal scroll, sidebar collapses to icons, becomes a drawer below 1024px, drawer closes on route change, overlay click and `Escape`.
- Keyboard: Tab reaches every nav item with a visible focus ring; `aria-current="page"` on the active link.
- If the app has i18n, switch languages and confirm long labels don't break the sidebar (truncate with ellipsis).
- If Playwright MCP is available, take before/after screenshots of the main views and show them to the user.
- `git diff --stat` - confirm no files outside the client/UI layer changed.

## Report

Tell the user: what changed (shell, tokens, which views), anything left inconsistent (views still using raw hex), unrouted views or other issues noticed during the audit, and how to tweak the look (edit `tokens.css`).
