<template>
  <!-- aria-pressed reports "dark mode on"; the label names the action so it stays accurate in both states -->
  <button
    type="button"
    class="theme-toggle"
    :aria-label="isDark ? t('theme.switchToLight') : t('theme.switchToDark')"
    :title="isDark ? t('theme.switchToLight') : t('theme.switchToDark')"
    :aria-pressed="isDark"
    @click="toggleTheme"
  >
    <!-- Shows the theme you will switch to: moon while light, sun while dark -->
    <svg v-if="isDark" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
    </svg>
    <svg v-else viewBox="0 0 24 24" aria-hidden="true">
      <path d="M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5a8.5 8.5 0 1 0 11 11Z" />
    </svg>
  </button>
</template>

<script setup>
import { useTheme } from '../composables/useTheme'
import { useI18n } from '../composables/useI18n'

const { isDark, toggleTheme } = useTheme()
const { t } = useI18n()
</script>

<style scoped>
/* Matches the LanguageSwitcher button height and border so the topbar controls align */
.theme-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  padding: 0;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: background var(--transition-fast), border-color var(--transition-fast);
}

.theme-toggle:hover {
  background: var(--color-surface-hover);
  border-color: var(--color-text-faint);
}

.theme-toggle:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus);
}

.theme-toggle svg {
  width: 18px;
  height: 18px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.75;
  stroke-linecap: round;
  stroke-linejoin: round;
}
</style>
