import { ref, computed } from 'vue'

// localStorage key for an explicit user choice; absent means "follow the OS"
const STORAGE_KEY = 'app-theme'
const DARK_QUERY = '(prefers-color-scheme: dark)'

// Storage can throw (private mode, blocked site data), so every access is guarded
// and the app falls back to following the OS preference.
const readStoredTheme = () => {
  try {
    const value = localStorage.getItem(STORAGE_KEY)
    return value === 'light' || value === 'dark' ? value : null
  } catch {
    return null
  }
}

const writeStoredTheme = (value) => {
  try {
    localStorage.setItem(STORAGE_KEY, value)
  } catch {
    // Not persisted; the choice still applies for this page session
  }
}

const getSystemTheme = () => {
  if (typeof window === 'undefined' || !window.matchMedia) return 'light'
  return window.matchMedia(DARK_QUERY).matches ? 'dark' : 'light'
}

// Module-level state so every caller shares one theme (same pattern as useFilters/useI18n)
const storedTheme = ref(readStoredTheme())
const systemTheme = ref(getSystemTheme())

// Effective theme: the explicit choice wins, otherwise the OS preference
const theme = computed(() => storedTheme.value || systemTheme.value)

const applyTheme = () => {
  document.documentElement.dataset.theme = theme.value
}

let initialized = false

/**
 * Apply the theme to <html> and start following OS changes.
 * Called from main.js before the app mounts so the first painted frame of the
 * app already uses the right tokens. Safe to call more than once.
 */
export function initTheme() {
  applyTheme()
  if (initialized || typeof window === 'undefined' || !window.matchMedia) return
  initialized = true

  // While the user has not picked a theme explicitly, track live OS switches
  window.matchMedia(DARK_QUERY).addEventListener('change', (event) => {
    systemTheme.value = event.matches ? 'dark' : 'light'
    if (!storedTheme.value) applyTheme()
  })
}

export function useTheme() {
  const isDark = computed(() => theme.value === 'dark')

  const setTheme = (value) => {
    storedTheme.value = value
    writeStoredTheme(value)
    applyTheme()
  }

  // A toggle always records an explicit choice, which then overrides the OS preference
  const toggleTheme = () => {
    setTheme(isDark.value ? 'light' : 'dark')
  }

  return {
    theme,
    isDark,
    setTheme,
    toggleTheme
  }
}
