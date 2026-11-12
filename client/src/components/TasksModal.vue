<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen" class="modal-overlay" @click="close">
        <div class="modal modal-lg" role="dialog" aria-modal="true" aria-labelledby="tasks-modal-title" @click.stop>
          <div class="modal-header">
            <h3 id="tasks-modal-title" class="modal-title">{{ t('tasks.title') }}</h3>
            <button class="modal-close" type="button" :aria-label="t('profileDetails.close')" @click="close">
              <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <!-- Server/network failures for add, toggle and delete; uses the global .error block -->
            <div v-if="error" class="error" role="alert">{{ error }}</div>

            <!-- Add Task Form -->
            <div class="task-form">
              <div class="form-row">
                <div class="form-group form-group-wide">
                  <label for="task-title" class="form-label">{{ t('tasks.taskTitle') }}</label>
                  <input
                    id="task-title"
                    v-model="newTask.title"
                    type="text"
                    :placeholder="t('tasks.taskTitlePlaceholder')"
                    class="form-control"
                    @keyup.enter="handleAddTask"
                  />
                </div>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label for="task-priority" class="form-label">{{ t('tasks.priority') }}</label>
                  <select
                    id="task-priority"
                    v-model="newTask.priority"
                    class="form-control"
                  >
                    <option value="high">{{ t('priority.high') }}</option>
                    <option value="medium">{{ t('priority.medium') }}</option>
                    <option value="low">{{ t('priority.low') }}</option>
                  </select>
                </div>

                <div class="form-group">
                  <label for="task-due-date" class="form-label">{{ t('tasks.dueDate') }}</label>
                  <input
                    id="task-due-date"
                    v-model="newTask.dueDate"
                    type="date"
                    class="form-control"
                  />
                </div>

                <div class="form-group-btn">
                  <button @click="handleAddTask" type="button" class="btn btn-primary" :disabled="saving || !newTask.title.trim() || !newTask.dueDate">
                    {{ saving ? t('tasks.adding') : t('tasks.addTask') }}
                  </button>
                </div>
              </div>
            </div>

            <!-- Tasks List -->
            <div v-if="sortedTasks.length === 0" class="no-tasks">
              {{ t('tasks.noTasks') }}
            </div>

            <div v-else class="tasks-list">
              <div
                v-for="task in sortedTasks"
                :key="task.id"
                class="task-item"
                :class="[`priority-${task.priority}`, { completed: task.status === 'completed' }]"
              >
                <div class="task-header">
                  <div class="task-check-title">
                    <input
                      type="checkbox"
                      :checked="task.status === 'completed'"
                      @change="$emit('toggle-task', task.id)"
                      class="task-checkbox"
                    />
                    <span class="task-title" @click="$emit('toggle-task', task.id)">{{ task.title }}</span>
                  </div>
                  <button @click="$emit('delete-task', task.id)" type="button" class="task-delete-btn" title="Delete task" aria-label="Delete task">
                    <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
                      <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                  </button>
                </div>

                <div class="task-footer">
                  <!-- task.priority is high|medium|low, matching the global .badge variants -->
                  <span class="badge" :class="task.priority">
                    {{ translatePriority(task.priority) }}
                  </span>
                  <div class="task-due-date">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                      <rect x="2" y="3" width="10" height="9" rx="1" stroke="currentColor" stroke-width="1.2"/>
                      <path d="M4.5 1.5V4.5M9.5 1.5V4.5M2 6H12" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                    </svg>
                    {{ formatDueDate(task.dueDate) }}
                  </div>
                  <span class="badge status-badge" :class="getStatusClass(task.dueDate, task.status)">
                    {{ getStatusText(task.dueDate, task.status) }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn btn-secondary" type="button" @click="close">{{ t('profileDetails.close') }}</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'TasksModal',
  props: {
    isOpen: {
      type: Boolean,
      required: true
    },
    tasks: {
      type: Array,
      default: () => []
    },
    // True while the parent is creating a task on the server
    saving: {
      type: Boolean,
      default: false
    },
    // Localized error message from the parent, or null
    error: {
      type: String,
      default: null
    }
  },
  emits: ['close', 'add-task', 'delete-task', 'toggle-task'],
  setup(props, { emit }) {
    const { t, currentLocale } = useI18n()
    const newTask = ref({
      title: '',
      priority: 'medium',
      dueDate: ''
    })

    const sortedTasks = computed(() => {
      // Don't sort - just return tasks in their current order (newest first)
      return [...props.tasks]
    })

    const close = () => {
      emit('close')
    }

    const handleAddTask = () => {
      // Guard here too: Enter in the title field bypasses the disabled button
      if (props.saving) return
      if (newTask.value.title.trim() && newTask.value.dueDate) {
        emit('add-task', {
          title: newTask.value.title.trim(),
          priority: newTask.value.priority,
          dueDate: newTask.value.dueDate
        })
      }
    }

    // The parent owns the request, so the form is only cleared once it reports the
    // outcome: saving flips back to false with no error = success. On failure the
    // values stay so the user can correct and resubmit.
    watch(() => props.saving, (isSaving, wasSaving) => {
      if (wasSaving && !isSaving && !props.error) {
        newTask.value = {
          title: '',
          priority: 'medium',
          dueDate: ''
        }
      }
    })

    const formatDueDate = (dateString) => {
      const date = new Date(dateString)
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const dueDate = new Date(date)
      dueDate.setHours(0, 0, 0, 0)

      const diffTime = dueDate - today
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

      const isJapanese = currentLocale.value === 'ja'

      if (diffDays === 0) return isJapanese ? '今日' : 'today'
      if (diffDays === 1) return isJapanese ? '明日' : 'tomorrow'
      if (diffDays === -1) return isJapanese ? '昨日' : 'yesterday'
      if (diffDays < 0) return isJapanese ? `${Math.abs(diffDays)}日前` : `${Math.abs(diffDays)} days ago`
      if (diffDays < 7) return isJapanese ? `${diffDays}日後` : `in ${diffDays} days`

      const locale = isJapanese ? 'ja-JP' : 'en-US'
      return date.toLocaleDateString(locale, {
        month: 'short',
        day: 'numeric',
        year: date.getFullYear() !== today.getFullYear() ? 'numeric' : undefined
      })
    }

    const getStatusClass = (dueDate, status) => {
      if (status === 'completed') return 'completed'

      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const due = new Date(dueDate)
      due.setHours(0, 0, 0, 0)

      const diffTime = due - today
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

      if (diffDays < 0) return 'overdue'
      if (diffDays <= 1) return 'urgent'
      return 'upcoming'
    }

    const getStatusText = (dueDate, status) => {
      const isJapanese = currentLocale.value === 'ja'

      if (status === 'completed') return isJapanese ? '完了' : 'Completed'

      const statusClass = getStatusClass(dueDate, status)
      if (statusClass === 'overdue') return isJapanese ? '期限超過' : 'Overdue'
      if (statusClass === 'urgent') return isJapanese ? 'もうすぐ期限' : 'Due Soon'
      return isJapanese ? '予定' : 'Upcoming'
    }

    const translatePriority = (priority) => {
      const priorityMap = {
        'high': t('priority.high'),
        'medium': t('priority.medium'),
        'low': t('priority.low')
      }
      return priorityMap[priority] || priority
    }

    return {
      t,
      newTask,
      sortedTasks,
      close,
      handleAddTask,
      formatDueDate,
      getStatusClass,
      getStatusText,
      translatePriority
    }
  }
}
</script>

<style scoped>
/* Overlay, panel, buttons and .form-control come from src/styles/modal.css */

/* Global .error block; drop its top margin so it sits flush with the modal body padding */
.error {
  margin-top: 0;
}

/* ---------- Add task form ---------- */
.task-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-5);
  margin-bottom: var(--space-6);
  background: var(--color-surface-muted);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
}

.form-row {
  display: flex;
  gap: var(--space-4);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  flex: 1;
  min-width: 0;
}

.form-group-btn {
  display: flex;
  align-items: flex-end;
}

/* ---------- Task list ---------- */
.no-tasks {
  padding: var(--space-10) var(--space-4);
  text-align: center;
  font-size: var(--text-base);
  color: var(--color-text-muted);
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

/* Priority shows as a 3px left accent; the rest of the border stays neutral */
.task-item {
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-left-width: 3px;
  border-radius: var(--radius-lg);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.task-item:hover {
  box-shadow: var(--shadow-sm);
}

.task-item.priority-high {
  border-left-color: var(--color-danger);
}

.task-item.priority-medium {
  border-left-color: var(--color-warning);
}

.task-item.priority-low {
  border-left-color: var(--color-info);
}

.task-item.completed {
  border-left-color: var(--color-border);
  background: var(--color-surface-muted);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-2);
}

.task-check-title {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex: 1;
  min-width: 0;
}

.task-checkbox {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  cursor: pointer;
  accent-color: var(--color-primary);
}

.task-title {
  flex: 1;
  min-width: 0;
  font-size: var(--text-base);
  font-weight: 500;
  line-height: var(--leading-tight);
  color: var(--color-text);
  cursor: pointer;
  user-select: none;
  overflow-wrap: anywhere;
}

.task-item.completed .task-title {
  text-decoration: line-through;
  color: var(--color-text-faint);
}

/* Quiet icon button; turns danger-coloured on hover so delete is never the loudest thing on screen */
.task-delete-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  padding: 0;
  background: none;
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-text-faint);
  cursor: pointer;
  transition: background-color var(--transition-fast), color var(--transition-fast);
}

.task-delete-btn svg {
  width: 14px;
  height: 14px;
}

.task-delete-btn:hover {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.task-footer {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-2) var(--space-3);
  /* Indent under the title, past the 16px checkbox + 12px gap */
  padding-left: calc(16px + var(--space-3));
}

.task-due-date {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.task-due-date svg {
  color: var(--color-text-faint);
}

/* getStatusClass() returns overdue|urgent|upcoming|completed; map to status tokens */
.status-badge {
  margin-left: auto;
}

.status-badge.overdue {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.status-badge.urgent {
  background: var(--color-warning-soft);
  color: var(--color-warning);
}

.status-badge.upcoming {
  background: var(--color-info-soft);
  color: var(--color-info);
}

.status-badge.completed {
  background: var(--color-success-soft);
  color: var(--color-success);
}

@media (max-width: 639px) {
  .task-form {
    padding: var(--space-4);
  }

  /* Priority + date side by side, add button full width beneath */
  .form-row {
    flex-wrap: wrap;
    gap: var(--space-3);
  }

  .form-group {
    flex: 1 1 calc(50% - var(--space-3));
  }

  .form-group-btn {
    flex: 1 1 100%;
  }

  .form-group-btn .btn {
    width: 100%;
  }
}
</style>
