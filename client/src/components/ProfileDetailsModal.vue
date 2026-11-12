<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen" class="modal-overlay" @click="close">
        <div class="modal" role="dialog" aria-modal="true" aria-labelledby="profile-modal-title" @click.stop>
          <div class="modal-header">
            <h3 id="profile-modal-title" class="modal-title">{{ t('profileDetails.title') }}</h3>
            <button class="modal-close" type="button" :aria-label="t('profileDetails.close')" @click="close">
              <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="profile-section">
              <div class="avatar-section">
                <div class="avatar-xl" aria-hidden="true">
                  {{ getInitials(currentUser.name) }}
                </div>
                <div class="profile-heading">
                  <h4 class="profile-name">{{ currentUser.name }}</h4>
                  <p class="profile-job-title">{{ currentUser.jobTitle }}</p>
                </div>
              </div>

              <div class="info-grid">
                <div class="info-item">
                  <div class="info-label">{{ t('profileDetails.email') }}</div>
                  <div class="info-value">{{ currentUser.email }}</div>
                </div>

                <div class="info-item">
                  <div class="info-label">{{ t('profileDetails.department') }}</div>
                  <div class="info-value">{{ currentUser.department }}</div>
                </div>

                <div class="info-item">
                  <div class="info-label">{{ t('profileDetails.location') }}</div>
                  <div class="info-value">{{ currentUser.location }}</div>
                </div>

                <div class="info-item">
                  <div class="info-label">{{ t('profileDetails.phone') }}</div>
                  <div class="info-value">{{ currentUser.phone }}</div>
                </div>

                <div class="info-item">
                  <div class="info-label">{{ t('profileDetails.joinDate') }}</div>
                  <div class="info-value">{{ formatDate(currentUser.joinDate) }}</div>
                </div>

                <div class="info-item">
                  <div class="info-label">{{ t('profileDetails.employeeId') }}</div>
                  <div class="info-value mono">CC-{{ currentUser.id.toString().padStart(5, '0') }}</div>
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

<script setup>
import { useAuth } from '../composables/useAuth'
import { useI18n } from '../composables/useI18n'

const { currentUser, getInitials } = useAuth()
const { t, currentLocale } = useI18n()

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close'])

const close = () => {
  emit('close')
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
  return date.toLocaleDateString(locale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}
</script>

<style scoped>
/* Layout, buttons and info grid come from src/styles/modal.css */
.modal {
  max-width: 560px;
}

/* Identity row: avatar beside name/title, separated from the details below */
.avatar-section {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding-bottom: var(--space-6);
  margin-bottom: var(--space-6);
  border-bottom: 1px solid var(--color-border-subtle);
}

.avatar-xl {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  flex-shrink: 0;
  border-radius: var(--radius-full);
  background: var(--color-primary);
  color: var(--color-primary-contrast);
  font-size: var(--text-xl);
  font-weight: 600;
  letter-spacing: 0.02em;
}

.profile-heading {
  min-width: 0;
}

.profile-name {
  font-size: var(--text-xl);
  font-weight: 600;
  line-height: var(--leading-tight);
  color: var(--color-text);
}

.profile-job-title {
  margin-top: var(--space-1);
  font-size: var(--text-base);
  color: var(--color-text-muted);
}

@media (max-width: 639px) {
  .avatar-section {
    padding-bottom: var(--space-4);
    margin-bottom: var(--space-4);
  }

  .avatar-xl {
    width: 48px;
    height: 48px;
    font-size: var(--text-md);
  }

  /* Emails are long; one column keeps them readable at 375px */
  .modal .info-grid {
    grid-template-columns: 1fr;
  }
}
</style>
