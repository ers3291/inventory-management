<!--
  AppSidebar - SaaS-style vertical navigation (from the vue-saas-redesign skill template).
  Nav items live in src/navigation.js so App.vue can derive the topbar page title from the same list.
  Requires src/styles/tokens.css to be loaded.
-->
<template>
  <!-- Mobile overlay: only rendered while the drawer is open below the breakpoint -->
  <div v-if="mobileOpen" class="sidebar-overlay" aria-hidden="true" @click="closeMobile" />

  <aside
    class="sidebar"
    :class="{ 'is-collapsed': collapsed, 'is-mobile-open': mobileOpen }"
    :aria-label="tr('nav.primaryNav', 'Primary')"
  >
    <div class="sidebar-brand">
      <span class="brand-mark" aria-hidden="true">{{ brandInitial }}</span>
      <span class="brand-text">
        <span class="brand-name">{{ brandName }}</span>
        <span v-if="brandSubtitle" class="brand-subtitle">{{ brandSubtitle }}</span>
      </span>
    </div>

    <nav class="sidebar-nav">
      <div v-for="section in navSections" :key="section.id" class="nav-section">
        <p v-if="section.title" class="nav-section-title">{{ section.title }}</p>
        <ul>
          <li v-for="item in section.items" :key="item.to">
            <!-- exact-active for "/" so the home link is not active on every page -->
            <router-link
              :to="item.to"
              class="nav-link"
              :active-class="item.to === '/' ? '' : 'is-active'"
              exact-active-class="is-active"
              :title="collapsed ? label(item) : undefined"
              @click="closeMobile"
            >
              <svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true">
                <path :d="icons[item.icon] || icons.dot" />
              </svg>
              <span class="nav-label">{{ label(item) }}</span>
            </router-link>
          </li>
        </ul>
      </div>
    </nav>

    <div class="sidebar-footer">
      <slot name="footer" :collapsed="collapsed" />
      <button
        type="button"
        class="collapse-toggle"
        :aria-expanded="!collapsed"
        :aria-label="collapsed ? tr('nav.expandSidebar', 'Expand sidebar') : tr('nav.collapseSidebar', 'Collapse sidebar')"
        @click="toggleCollapsed"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true"><path :d="collapsed ? icons.chevronRight : icons.chevronLeft" /></svg>
        <span class="nav-label">{{ tr('nav.collapse', 'Collapse') }}</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount } from 'vue'
import { navSections } from '../navigation'

const props = defineProps({
  collapsed: { type: Boolean, default: false },
  mobileOpen: { type: Boolean, default: false },
  brandName: { type: String, default: 'App' },
  brandSubtitle: { type: String, default: '' },
  // Optional translate function, e.g. pass `t` from useI18n
  translate: { type: Function, default: null }
})
const emit = defineEmits(['update:collapsed', 'update:mobileOpen'])

// Computed (not a one-off const) so the mark updates when brandName changes on a language switch
const brandInitial = computed(() => props.brandName.charAt(0).toUpperCase())

const label = (item) => (props.translate && item.labelKey ? props.translate(item.labelKey) : item.label)

// UI strings: use the translation when a translate fn is given, else the English fallback
const tr = (key, fallback) => (props.translate ? props.translate(key) : fallback)

// 24x24 stroke icon paths (no icon library dependency)
const icons = {
  home: 'M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z',
  box: 'M21 8 12 3 3 8v8l9 5 9-5zM3 8l9 5 9-5M12 13v8',
  cart: 'M3 4h2l2.4 11.2a1 1 0 0 0 1 .8h8.9a1 1 0 0 0 1-.8L20 8H6M9 20h.01M17 20h.01',
  wallet: 'M3 7a2 2 0 0 1 2-2h13v4M3 7v10a2 2 0 0 0 2 2h15V9H5a2 2 0 0 1-2-2zM16 14h.01',
  trend: 'M3 17l6-6 4 4 8-8M15 7h6v6',
  chart: 'M4 20V10M10 20V4M16 20v-7M22 20H2',
  list: 'M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01',
  settings: 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z',
  dot: 'M12 12h.01',
  chevronLeft: 'M15 18l-6-6 6-6',
  chevronRight: 'M9 18l6-6-6-6'
}

const STORAGE_KEY = 'sidebar-collapsed'

const toggleCollapsed = () => {
  const next = !props.collapsed
  emit('update:collapsed', next)
  // Persisting is a convenience only; storage can be unavailable (private mode), so never let it throw
  try { localStorage.setItem(STORAGE_KEY, next ? '1' : '0') } catch { /* ignore */ }
}

const closeMobile = () => {
  if (props.mobileOpen) emit('update:mobileOpen', false)
}

const onKeydown = (e) => {
  if (e.key === 'Escape') closeMobile()
}

onMounted(() => {
  try {
    if (localStorage.getItem(STORAGE_KEY) === '1') emit('update:collapsed', true)
  } catch { /* ignore */ }
  window.addEventListener('keydown', onKeydown)
})
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
</script>

<style scoped>
.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--sidebar-bg);
  color: var(--sidebar-text);
  overflow: hidden;
  z-index: var(--z-sidebar);
  transition: width var(--transition);
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: var(--topbar-height);
  padding: 0 var(--space-4);
  border-bottom: 1px solid var(--sidebar-divider);
  flex-shrink: 0;
}
.brand-mark {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  border-radius: var(--radius-md);
  background: var(--color-primary);
  color: var(--color-primary-contrast);
  font-weight: 700;
  font-size: var(--text-base);
}
.brand-text { display: flex; flex-direction: column; min-width: 0; }
.brand-name {
  color: var(--sidebar-text-strong);
  font-weight: 600;
  font-size: var(--text-base);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.brand-subtitle { font-size: var(--text-xs); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.sidebar-nav { flex: 1; overflow-y: auto; padding: var(--space-4) var(--space-3); }
.nav-section + .nav-section { margin-top: var(--space-6); }
.nav-section-title {
  margin: 0 0 var(--space-2);
  padding: 0 var(--space-3);
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-text-faint);
}
.nav-section ul { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--space-1); }

.nav-link,
.collapse-toggle {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  height: 36px;
  padding: 0 var(--space-3);
  border-radius: var(--radius-md);
  color: var(--sidebar-text);
  font: inherit;
  font-size: var(--text-base);
  font-weight: 500;
  text-decoration: none;
  background: none;
  border: 0;
  cursor: pointer;
  transition: background var(--transition-fast), color var(--transition-fast);
}
.nav-link:hover,
.collapse-toggle:hover { background: var(--sidebar-hover); color: var(--sidebar-text-strong); }
.nav-link.is-active { background: var(--sidebar-active-bg); color: var(--sidebar-active-text); }
.nav-link.is-active::before {
  content: '';
  position: absolute;
  left: calc(-1 * var(--space-3));
  top: 8px;
  bottom: 8px;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: var(--sidebar-active-indicator);
}

.nav-icon,
.collapse-toggle svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.75;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.nav-label { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.sidebar-footer {
  display: grid;
  gap: var(--space-2);
  padding: var(--space-3);
  border-top: 1px solid var(--sidebar-divider);
}

/* Collapsed rail: icons only */
.sidebar.is-collapsed .brand-text,
.sidebar.is-collapsed .nav-label,
.sidebar.is-collapsed .nav-section-title { display: none; }
.sidebar.is-collapsed .nav-link,
.sidebar.is-collapsed .collapse-toggle { justify-content: center; padding: 0; }
.sidebar.is-collapsed .sidebar-brand { justify-content: center; padding: 0; }

/* Below 1024px the sidebar becomes an off-canvas drawer */
.sidebar-overlay { display: none; }
@media (max-width: 1023px) {
  .sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    width: var(--sidebar-width);
    transform: translateX(-100%);
    transition: transform var(--transition);
  }
  .sidebar.is-mobile-open { transform: translateX(0); box-shadow: var(--shadow-lg); }
  /* Collapsing makes no sense in drawer mode: always show labels */
  .sidebar.is-collapsed .brand-text,
  .sidebar.is-collapsed .nav-label { display: initial; }
  .sidebar.is-collapsed .nav-link { justify-content: flex-start; padding: 0 var(--space-3); }
  .collapse-toggle { display: none; }
  .sidebar-overlay {
    display: block;
    position: fixed;
    inset: 0;
    background: rgb(15 23 42 / 0.45);
    z-index: var(--z-overlay);
  }
  .sidebar { z-index: calc(var(--z-overlay) + 1); }
}
</style>
