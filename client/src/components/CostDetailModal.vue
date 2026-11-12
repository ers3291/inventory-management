<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && costData" class="modal-overlay" @click="close">
        <div class="modal" role="dialog" aria-modal="true" aria-labelledby="cost-modal-title" @click.stop>
          <div class="modal-header">
            <h3 id="cost-modal-title" class="modal-title">{{ costData.month }} cost breakdown</h3>
            <button class="modal-close" type="button" aria-label="Close" @click="close">
              <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="summary-card total">
              <div class="summary-label">Total costs</div>
              <div class="summary-value">{{ currencySymbol }}{{ totalCosts.toLocaleString() }}</div>
            </div>

            <div class="cost-breakdown">
              <div class="cost-item procurement">
                <div class="cost-icon">
                  <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <rect x="4" y="6" width="16" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
                    <path d="M8 6V4M16 6V4M4 10H20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  </svg>
                </div>
                <div class="cost-info">
                  <div class="cost-name">Procurement</div>
                  <div class="cost-percentage">{{ getProcurementPercentage() }}% of total</div>
                </div>
                <div class="cost-amount">{{ currencySymbol }}{{ costData.procurement.toLocaleString() }}</div>
              </div>

              <div class="cost-item operational">
                <div class="cost-icon">
                  <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <circle cx="12" cy="12" r="8" stroke="currentColor" stroke-width="2"/>
                    <path d="M12 8V12L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  </svg>
                </div>
                <div class="cost-info">
                  <div class="cost-name">Operational</div>
                  <div class="cost-percentage">{{ getOperationalPercentage() }}% of total</div>
                </div>
                <div class="cost-amount">{{ currencySymbol }}{{ costData.operational.toLocaleString() }}</div>
              </div>

              <div class="cost-item labor">
                <div class="cost-icon">
                  <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <circle cx="12" cy="8" r="4" stroke="currentColor" stroke-width="2"/>
                    <path d="M6 20C6 16.6863 8.68629 14 12 14C15.3137 14 18 16.6863 18 20" stroke="currentColor" stroke-width="2"/>
                  </svg>
                </div>
                <div class="cost-info">
                  <div class="cost-name">Labor</div>
                  <div class="cost-percentage">{{ getLaborPercentage() }}% of total</div>
                </div>
                <div class="cost-amount">{{ currencySymbol }}{{ costData.labor.toLocaleString() }}</div>
              </div>

              <div class="cost-item overhead">
                <div class="cost-icon">
                  <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path d="M3 12L5 10M5 10L12 3L19 10M5 10V20C5 20.5523 5.44772 21 6 21H9M19 10L21 12M19 10V20C19 20.5523 18.5523 21 18 21H15M9 21C9 21 9 18 9 16C9 14 10 14 12 14C14 14 15 14 15 16C15 18 15 21 15 21M9 21H15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  </svg>
                </div>
                <div class="cost-info">
                  <div class="cost-name">Overhead</div>
                  <div class="cost-percentage">{{ getOverheadPercentage() }}% of total</div>
                </div>
                <div class="cost-amount">{{ currencySymbol }}{{ costData.overhead.toLocaleString() }}</div>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn btn-secondary" type="button" @click="close">Close</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from '../composables/useI18n'

const { currentCurrency } = useI18n()

const currencySymbol = computed(() => {
  return currentCurrency.value === 'JPY' ? '¥' : '$'
})

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  costData: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close'])

const totalCosts = computed(() => {
  if (!props.costData) return 0
  return props.costData.procurement + props.costData.operational +
         props.costData.labor + props.costData.overhead
})

const getProcurementPercentage = () => {
  if (!props.costData || totalCosts.value === 0) return 0
  return ((props.costData.procurement / totalCosts.value) * 100).toFixed(1)
}

const getOperationalPercentage = () => {
  if (!props.costData || totalCosts.value === 0) return 0
  return ((props.costData.operational / totalCosts.value) * 100).toFixed(1)
}

const getLaborPercentage = () => {
  if (!props.costData || totalCosts.value === 0) return 0
  return ((props.costData.labor / totalCosts.value) * 100).toFixed(1)
}

const getOverheadPercentage = () => {
  if (!props.costData || totalCosts.value === 0) return 0
  return ((props.costData.overhead / totalCosts.value) * 100).toFixed(1)
}

const close = () => {
  emit('close')
}
</script>

<style scoped>
/* Layout, buttons and summary tiles come from src/styles/modal.css */
.modal {
  max-width: 560px;
}

.summary-card.total {
  margin-bottom: var(--space-6);
  background: var(--color-primary-soft);
  border-color: color-mix(in srgb, var(--color-primary) 20%, transparent);
}

.summary-card.total .summary-value {
  font-size: var(--text-3xl);
  color: var(--color-primary);
}

.cost-breakdown {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

/* Row: tinted icon tile | name + share | amount (right-aligned) */
.cost-item {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.cost-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  border-radius: var(--radius-md);
}

.cost-icon svg {
  width: 20px;
  height: 20px;
}

/* One status hue per cost type; operational uses neutral as there is no fifth hue in the palette */
.cost-item.procurement .cost-icon {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.cost-item.operational .cost-icon {
  background: var(--color-surface-hover);
  color: var(--color-text-secondary);
}

.cost-item.labor .cost-icon {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.cost-item.overhead .cost-icon {
  background: var(--color-warning-soft);
  color: var(--color-warning);
}

.cost-info {
  flex: 1;
  min-width: 0;
}

.cost-name {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text);
}

.cost-percentage {
  margin-top: 0;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  font-variant-numeric: tabular-nums;
}

.cost-amount {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
  text-align: right;
}
</style>
