<template>
  <div class="app-shell" :class="{ 'is-collapsed': sidebarCollapsed }">
    <AppSidebar
      v-model:collapsed="sidebarCollapsed"
      v-model:mobile-open="mobileNavOpen"
      :brand-name="t('nav.companyName')"
      :brand-subtitle="t('nav.subtitle')"
      :translate="t"
    />

    <div class="app-main">
      <header class="app-topbar">
        <button
          type="button"
          class="topbar-menu"
          aria-label="Open navigation"
          :aria-expanded="mobileNavOpen"
          @click="mobileNavOpen = true"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16" /></svg>
        </button>
        <h1 class="topbar-title">{{ pageTitle }}</h1>
        <div class="topbar-actions">
          <LanguageSwitcher />
          <ProfileMenu
            :pending-task-count="pendingTaskCount"
            @show-profile-details="showProfileDetails = true"
            @show-tasks="showTasks = true"
          />
        </div>
      </header>

      <!-- Four selects + reset do not fit in the topbar, so filters sit in a sub-bar beneath it -->
      <FilterBar />

      <main class="app-content">
        <router-view />
      </main>
    </div>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      :saving="savingTask"
      :error="taskError"
      @close="closeTasks"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'
import AppSidebar from './components/AppSidebar.vue'
import { navItems } from './navigation'

export default {
  name: 'App',
  components: {
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher,
    AppSidebar
  },
  setup() {
    const { currentUser, isMockTask, toggleMockTask, deleteMockTask } = useAuth()
    const { t } = useI18n()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])
    // Task modal feedback: savingTask disables the Add button while a create is in flight;
    // taskError is shown inline in the modal for any failed load/add/toggle/delete
    const savingTask = ref(false)
    const taskError = ref(null)

    // Shell layout state (sidebar rail collapse on desktop, off-canvas drawer below 1024px)
    const route = useRoute()
    const sidebarCollapsed = ref(false)
    const mobileNavOpen = ref(false)

    // Topbar title = label of the nav item matching the current route; t() keeps it locale-reactive
    const pageTitle = computed(() => {
      const item = navItems.find(navItem => navItem.to === route.path)
      return item ? t(item.labelKey) : ''
    })

    // Close the drawer on any navigation (e.g. browser back), not only on sidebar link clicks
    watch(() => route.path, () => {
      mobileNavOpen.value = false
    })

    // Merge API tasks (newest first) ahead of the built-in demo tasks, so a newly
    // added task shows at the top of the modal
    const tasks = computed(() => {
      return [...apiTasks.value, ...currentUser.value.tasks]
    })

    // Badge count in the profile menu covers every pending task shown in the modal
    const pendingTaskCount = computed(() => {
      return tasks.value.filter(task => task.status === 'pending').length
    })

    // Localized message, plus the server's `detail` when it is a plain string
    // (FastAPI 400/404 responses); validation arrays and network errors get the generic text
    const describeTaskError = (err, key) => {
      const detail = err?.response?.data?.detail
      return typeof detail === 'string' ? `${t(key)}: ${detail}` : t(key)
    }

    const closeTasks = () => {
      showTasks.value = false
      taskError.value = null
    }

    const loadTasks = async () => {
      try {
        // Server ids increase with creation, so sorting by id desc gives newest first,
        // matching the unshift order used by addTask
        const loaded = await api.getTasks()
        apiTasks.value = [...loaded].sort((a, b) => b.id - a.id)
      } catch (err) {
        console.error('Failed to load tasks:', err)
        taskError.value = describeTaskError(err, 'tasks.errors.load')
      }
    }

    const addTask = async (taskData) => {
      savingTask.value = true
      taskError.value = null
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
        taskError.value = describeTaskError(err, 'tasks.errors.add')
      } finally {
        // TasksModal watches this flip back to false and only clears its form when taskError is null
        savingTask.value = false
      }
    }

    const deleteTask = async (taskId) => {
      taskError.value = null
      // Built-in demo tasks are client-side only; everything else lives on the server
      if (isMockTask(taskId)) {
        deleteMockTask(taskId)
        return
      }
      try {
        await api.deleteTask(taskId)
        apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
      } catch (err) {
        console.error('Failed to delete task:', err)
        taskError.value = describeTaskError(err, 'tasks.errors.delete')
      }
    }

    const toggleTask = async (taskId) => {
      taskError.value = null
      if (isMockTask(taskId)) {
        toggleMockTask(taskId)
        return
      }
      try {
        const updatedTask = await api.toggleTask(taskId)
        const index = apiTasks.value.findIndex(t => t.id === taskId)
        if (index !== -1) {
          apiTasks.value[index] = updatedTask
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
        taskError.value = describeTaskError(err, 'tasks.errors.toggle')
      }
    }

    onMounted(loadTasks)

    return {
      t,
      sidebarCollapsed,
      mobileNavOpen,
      pageTitle,
      showProfileDetails,
      showTasks,
      tasks,
      pendingTaskCount,
      savingTask,
      taskError,
      closeTasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>


<style>
/*
 * Global styles. Colors, spacing, radii and type come from src/styles/tokens.css
 * (box-sizing and body base styles are set there too).
 */
* {
  margin: 0;
  padding: 0;
}

/* ---------- App shell ---------- */
.app-shell {
  display: grid;
  grid-template-columns: var(--sidebar-width) 1fr;
  min-height: 100vh;
  background: var(--color-bg);
}

.app-shell.is-collapsed {
  grid-template-columns: var(--sidebar-width-collapsed) 1fr;
}

.app-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

/* The topbar is its own stacking context (sticky + z-index), so the language/profile
   dropdowns inside it layer above the filter sub-bar (z-topbar - 1) and page content. */
.app-topbar {
  position: sticky;
  top: 0;
  z-index: var(--z-topbar);
  display: flex;
  align-items: center;
  gap: var(--space-4);
  height: var(--topbar-height);
  padding: 0 var(--space-8);
  background: color-mix(in srgb, var(--color-surface) 85%, transparent);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid var(--color-border);
}

.topbar-title {
  flex: 1;
  min-width: 0;
  font-size: var(--text-lg);
  font-weight: 600;
  line-height: var(--leading-tight);
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-shrink: 0;
}

.topbar-menu {
  display: none;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  cursor: pointer;
}

.topbar-menu:hover {
  background: var(--color-surface-hover);
}

.topbar-menu svg {
  width: 18px;
  height: 18px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.75;
  stroke-linecap: round;
}

.app-content {
  flex: 1;
  width: 100%;
  max-width: var(--content-max);
  margin: 0 auto;
  padding: var(--space-8);
}

@media (max-width: 1023px) {
  .app-shell,
  .app-shell.is-collapsed {
    grid-template-columns: 1fr;
  }

  .topbar-menu {
    display: inline-flex;
  }

  .app-topbar,
  .app-content {
    padding-inline: var(--space-4);
  }

  .app-content {
    padding-block: var(--space-6);
  }
}

@media (max-width: 639px) {
  .app-topbar {
    gap: var(--space-2);
  }

  .topbar-actions {
    gap: var(--space-2);
  }
}

/* ---------- Page header ---------- */
/* Title + subtitle stack in column 1; an optional .page-header-actions block sits right-aligned in column 2 */
.page-header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  column-gap: var(--space-4);
  align-items: end;
  margin-bottom: var(--space-6);
}

.page-header > :not(.page-header-actions) {
  grid-column: 1;
}

.page-header-actions {
  grid-column: 2;
  grid-row: 1 / span 2;
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.page-header h2 {
  font-size: var(--text-2xl);
  font-weight: 600;
  line-height: var(--leading-tight);
  color: var(--color-text);
  letter-spacing: -0.01em;
}

.page-header p {
  margin-top: var(--space-1);
  color: var(--color-text-muted);
  font-size: var(--text-base);
}

/* ---------- KPI / stat cards ---------- */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--space-6);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--color-surface);
  padding: var(--space-5) var(--space-6);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
}

.stat-label {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  font-weight: 500;
  margin-bottom: var(--space-2);
}

/* Sentence case: labels may come from data/i18n in any case, so only lift the first letter */
.stat-label::first-letter {
  text-transform: uppercase;
}

.stat-value {
  font-size: var(--text-3xl);
  font-weight: 600;
  line-height: var(--leading-tight);
  color: var(--color-text);
  letter-spacing: -0.01em;
  font-variant-numeric: tabular-nums;
}

.stat-card.warning .stat-value {
  color: var(--color-warning);
}

.stat-card.success .stat-value {
  color: var(--color-success);
}

.stat-card.danger .stat-value {
  color: var(--color-danger);
}

.stat-card.info .stat-value {
  color: var(--color-info);
}

/* ---------- Cards ---------- */
.card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  margin-bottom: var(--space-6);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}

.card-title {
  font-size: var(--text-md);
  font-weight: 600;
  line-height: var(--leading-tight);
  color: var(--color-text);
}

/* ---------- Tables ---------- */
.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-variant-numeric: tabular-nums;
}

thead {
  background: var(--color-surface-muted);
  border-bottom: 1px solid var(--color-border);
}

th {
  text-align: left;
  padding: var(--space-2) var(--space-4);
  height: 36px;
  font-weight: 500;
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

/* ~45px rows: 21px line + 2 x 12px padding */
td {
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid var(--color-border-subtle);
  color: var(--color-text-secondary);
  font-size: var(--text-base);
}

tbody tr {
  transition: background-color var(--transition-fast);
}

tbody tr:hover {
  background: var(--color-surface-hover);
}

/* Numeric columns: add to th and td */
th.num,
td.num {
  text-align: right;
}

/* ---------- Badges ---------- */
.badge {
  display: inline-flex;
  align-items: center;
  padding: 2px var(--space-2);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 500;
  line-height: var(--leading-normal);
  white-space: nowrap;
  background: var(--color-surface-hover);
  color: var(--color-text-secondary);
}

/* Sentence case for lower-case data values (e.g. "increasing" -> "Increasing") */
.badge::first-letter {
  text-transform: uppercase;
}

.badge.success,
.badge.increasing {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.badge.warning,
.badge.medium {
  background: var(--color-warning-soft);
  color: var(--color-warning);
}

.badge.danger,
.badge.decreasing,
.badge.high {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.badge.info,
.badge.low {
  background: var(--color-info-soft);
  color: var(--color-info);
}

/* Neutral: no change in trend */
.badge.stable,
.badge.neutral {
  background: var(--color-surface-hover);
  color: var(--color-text-secondary);
}

/* ---------- Loading / error states ---------- */
.loading {
  text-align: center;
  padding: var(--space-12) var(--space-4);
  color: var(--color-text-muted);
  font-size: var(--text-base);
}

.error {
  background: var(--color-danger-soft);
  border: 1px solid color-mix(in srgb, var(--color-danger) 20%, transparent);
  color: var(--color-danger);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  margin: var(--space-4) 0;
  font-size: var(--text-base);
}
</style>
