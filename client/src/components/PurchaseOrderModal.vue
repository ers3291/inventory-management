<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div class="modal" role="dialog" aria-modal="true" aria-labelledby="po-modal-title" @click.stop>
          <div class="modal-header">
            <h3 id="po-modal-title" class="modal-title">
              {{ mode === 'view' ? 'Purchase order details' : 'Create purchase order' }}
            </h3>
            <button class="modal-close" type="button" aria-label="Close" @click="close">
              <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <!-- ---------- Create mode ---------- -->
          <template v-if="mode === 'create'">
            <div class="modal-body">
              <div class="detail-header">
                <div class="detail-icon">
                  <svg viewBox="0 0 48 48" fill="none" aria-hidden="true">
                    <rect x="10" y="8" width="28" height="32" rx="3" stroke="currentColor" stroke-width="3"/>
                    <path d="M17 18H31M17 25H31M17 32H25" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
                  </svg>
                </div>
                <div class="detail-title-section">
                  <h4 class="detail-name">{{ translateProductName(backlogItem.item_name) }}</h4>
                  <div class="detail-sku">SKU: {{ backlogItem.item_sku }} · Order {{ backlogItem.order_id }}</div>
                </div>
                <!-- priority is high|medium|low, which map to the global .badge colour variants -->
                <span class="badge" :class="backlogItem.priority">{{ backlogItem.priority }} priority</span>
              </div>

              <div class="info-grid po-summary">
                <div class="info-item">
                  <div class="info-label">Needed</div>
                  <div class="info-value">{{ backlogItem.quantity_needed }} units</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Available</div>
                  <div class="info-value">{{ backlogItem.quantity_available }} units</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Shortfall</div>
                  <div class="info-value danger-text">{{ shortfall }} units</div>
                </div>
              </div>

              <div v-if="submitError" class="error" role="alert">{{ submitError }}</div>

              <form id="po-form" class="po-form" novalidate @submit.prevent="submit">
                <div class="form-group form-group-wide">
                  <label class="form-label" for="po-supplier">Supplier name</label>
                  <input
                    id="po-supplier"
                    v-model="form.supplier_name"
                    class="form-control"
                    :class="{ invalid: errors.supplier_name }"
                    type="text"
                    placeholder="e.g. Acme Components"
                    :aria-invalid="!!errors.supplier_name"
                    aria-describedby="po-supplier-error"
                  />
                  <div v-if="errors.supplier_name" id="po-supplier-error" class="field-error">{{ errors.supplier_name }}</div>
                </div>

                <div class="form-group">
                  <label class="form-label" for="po-quantity">Quantity</label>
                  <input
                    id="po-quantity"
                    v-model="form.quantity"
                    class="form-control"
                    :class="{ invalid: errors.quantity }"
                    type="number"
                    min="1"
                    step="1"
                    inputmode="numeric"
                    :aria-invalid="!!errors.quantity"
                    aria-describedby="po-quantity-error"
                  />
                  <div v-if="errors.quantity" id="po-quantity-error" class="field-error">{{ errors.quantity }}</div>
                </div>

                <div class="form-group">
                  <label class="form-label" for="po-unit-cost">Unit cost (USD)</label>
                  <input
                    id="po-unit-cost"
                    v-model="form.unit_cost"
                    class="form-control"
                    :class="{ invalid: errors.unit_cost }"
                    type="number"
                    min="0"
                    step="0.01"
                    inputmode="decimal"
                    placeholder="0.00"
                    :aria-invalid="!!errors.unit_cost"
                    aria-describedby="po-unit-cost-error"
                  />
                  <div v-if="errors.unit_cost" id="po-unit-cost-error" class="field-error">{{ errors.unit_cost }}</div>
                </div>

                <div class="form-group">
                  <label class="form-label" for="po-delivery">Expected delivery</label>
                  <input
                    id="po-delivery"
                    v-model="form.expected_delivery_date"
                    class="form-control"
                    :class="{ invalid: errors.expected_delivery_date }"
                    type="date"
                    :min="todayIso"
                    :aria-invalid="!!errors.expected_delivery_date"
                    aria-describedby="po-delivery-error"
                  />
                  <div v-if="errors.expected_delivery_date" id="po-delivery-error" class="field-error">{{ errors.expected_delivery_date }}</div>
                </div>

                <div class="form-group">
                  <div class="form-label">Total</div>
                  <div class="po-total">{{ totalDisplay }}</div>
                </div>

                <div class="form-group form-group-wide">
                  <label class="form-label" for="po-notes">Notes <span class="optional">(optional)</span></label>
                  <textarea id="po-notes" v-model="form.notes" class="form-control po-notes" rows="3"></textarea>
                </div>
              </form>
            </div>

            <div class="modal-footer">
              <button class="btn btn-secondary" type="button" @click="close">Cancel</button>
              <!-- form attribute lets the footer button submit the form that lives in the body -->
              <button class="btn btn-primary" type="submit" form="po-form" :disabled="saving">
                {{ saving ? 'Creating…' : 'Create purchase order' }}
              </button>
            </div>
          </template>

          <!-- ---------- View mode ---------- -->
          <template v-else>
            <div class="modal-body">
              <div v-if="loading && !po" class="loading">Loading purchase order...</div>
              <div v-else-if="loadError && !po" class="error" role="alert">{{ loadError }}</div>
              <template v-else-if="po">
                <div class="detail-header">
                  <div class="detail-icon">
                    <svg viewBox="0 0 48 48" fill="none" aria-hidden="true">
                      <rect x="10" y="8" width="28" height="32" rx="3" stroke="currentColor" stroke-width="3"/>
                      <path d="M17 18H31M17 25H31M17 32H25" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
                    </svg>
                  </div>
                  <div class="detail-title-section">
                    <h4 class="detail-name">{{ po.id }}</h4>
                    <div class="detail-sku">{{ translateProductName(backlogItem.item_name) }} · {{ backlogItem.item_sku }}</div>
                  </div>
                  <span class="badge" :class="statusVariant(po.status)">{{ po.status }}</span>
                </div>

                <div class="info-grid">
                  <div class="info-item">
                    <div class="info-label">Supplier</div>
                    <div class="info-value">{{ po.supplier_name }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Quantity</div>
                    <div class="info-value">{{ po.quantity }} units</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Unit cost</div>
                    <div class="info-value">{{ formatCurrencyWithDecimals(po.unit_cost, currentCurrency, 2) }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Total</div>
                    <div class="info-value accent">{{ formatCurrency(po.quantity * po.unit_cost, currentCurrency) }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Expected delivery</div>
                    <div class="info-value">{{ formatDate(po.expected_delivery_date) }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Created</div>
                    <div class="info-value">{{ formatDate(po.created_date) }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Order ID</div>
                    <div class="info-value mono accent">{{ backlogItem.order_id }}</div>
                  </div>
                  <div class="info-item po-notes-item">
                    <div class="info-label">Notes</div>
                    <div class="info-value">{{ po.notes || 'None' }}</div>
                  </div>
                </div>
              </template>
            </div>

            <div class="modal-footer">
              <button class="btn btn-secondary" type="button" @click="close">Close</button>
            </div>
          </template>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
import { ref, reactive, computed, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

// Local-time YYYY-MM-DD. toISOString() would use UTC and can be a day off near midnight.
const toIsoDate = (date) => {
  const pad = n => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

const DEFAULT_LEAD_DAYS = 14

export default {
  name: 'PurchaseOrderModal',
  props: {
    isOpen: {
      type: Boolean,
      default: false
    },
    backlogItem: {
      type: Object,
      default: null
    },
    mode: {
      type: String,
      default: 'create',
      validator: value => ['create', 'view'].includes(value)
    }
  },
  emits: ['close', 'po-created'],
  setup(props, { emit }) {
    const { currentCurrency, translateProductName } = useI18n()

    const todayIso = ref(toIsoDate(new Date()))

    // ---- Create mode state ----
    const form = reactive({
      supplier_name: '',
      quantity: 1,
      unit_cost: '',
      expected_delivery_date: '',
      notes: ''
    })
    const errors = reactive({})
    const saving = ref(false)
    const submitError = ref(null)

    // ---- View mode state ----
    const po = ref(null)
    const loading = ref(false)
    const loadError = ref(null)
    // Guards against a slow response for a previously opened item overwriting the current one
    let fetchToken = 0

    const shortfall = computed(() => {
      if (!props.backlogItem) return 0
      return Math.max(props.backlogItem.quantity_needed - props.backlogItem.quantity_available, 0)
    })

    // Only show a total once both inputs parse; otherwise show a dash rather than "$NaN"
    const totalDisplay = computed(() => {
      const qty = Number(form.quantity)
      const cost = Number(form.unit_cost)
      if (form.unit_cost === '' || !Number.isFinite(qty) || !Number.isFinite(cost)) return '—'
      return formatCurrency(qty * cost, currentCurrency.value)
    })

    const clearErrors = () => {
      Object.keys(errors).forEach(key => delete errors[key])
    }

    const resetForm = () => {
      const today = new Date()
      todayIso.value = toIsoDate(today)
      const delivery = new Date(today)
      delivery.setDate(delivery.getDate() + DEFAULT_LEAD_DAYS)

      form.supplier_name = ''
      // Default to the shortfall, but never below 1 since the backend rejects quantity <= 0
      form.quantity = Math.max(shortfall.value, 1)
      form.unit_cost = ''
      form.expected_delivery_date = toIsoDate(delivery)
      form.notes = ''
      clearErrors()
      submitError.value = null
      saving.value = false
    }

    // Mirrors the backend rules (400 for blank supplier / quantity <= 0 / unit_cost < 0,
    // 422 for missing fields) so most mistakes are caught without a round trip.
    const validate = () => {
      clearErrors()
      if (!form.supplier_name.trim()) {
        errors.supplier_name = 'Supplier name is required'
      }

      // v-model on type="number" yields '' when empty and a number otherwise
      const qty = Number(form.quantity)
      if (form.quantity === '' || form.quantity === null || !Number.isFinite(qty)) {
        errors.quantity = 'Quantity is required'
      } else if (!Number.isInteger(qty)) {
        errors.quantity = 'Quantity must be a whole number'
      } else if (qty <= 0) {
        errors.quantity = 'Quantity must be greater than zero'
      }

      const cost = Number(form.unit_cost)
      if (form.unit_cost === '' || form.unit_cost === null || !Number.isFinite(cost)) {
        errors.unit_cost = 'Unit cost is required'
      } else if (cost < 0) {
        errors.unit_cost = 'Unit cost cannot be negative'
      }

      if (!form.expected_delivery_date) {
        errors.expected_delivery_date = 'Expected delivery date is required'
      } else if (form.expected_delivery_date < todayIso.value) {
        // ISO date strings compare correctly as plain strings
        errors.expected_delivery_date = 'Expected delivery date cannot be in the past'
      }

      return Object.keys(errors).length === 0
    }

    const submit = async () => {
      if (saving.value || !validate()) return
      saving.value = true
      submitError.value = null
      try {
        const notes = form.notes.trim()
        const created = await api.createPurchaseOrder({
          backlog_item_id: props.backlogItem.id,
          supplier_name: form.supplier_name.trim(),
          quantity: Number(form.quantity),
          unit_cost: Number(form.unit_cost),
          expected_delivery_date: form.expected_delivery_date,
          notes: notes || null
        })
        emit('po-created', created)
      } catch (err) {
        submitError.value = errorMessage(err, 'Failed to create purchase order')
        console.error('Failed to create purchase order:', err)
      } finally {
        saving.value = false
      }
    }

    const loadPurchaseOrder = async () => {
      const token = ++fetchToken
      // Dashboard caches the PO on the row after creating it; show that immediately, then refresh
      po.value = props.backlogItem.purchase_order || null
      loadError.value = null
      loading.value = true
      try {
        const data = await api.getPurchaseOrderByBacklogItem(props.backlogItem.id)
        if (token === fetchToken) po.value = data
      } catch (err) {
        if (token !== fetchToken) return
        loadError.value = err.response?.status === 404
          ? 'No purchase order found'
          : errorMessage(err, 'Failed to load purchase order')
        console.error('Failed to load purchase order:', err)
      } finally {
        if (token === fetchToken) loading.value = false
      }
    }

    // FastAPI puts the message in detail: a string for HTTPException, an array for 422 validation errors
    const errorMessage = (err, fallback) => {
      const detail = err.response?.data?.detail
      if (typeof detail === 'string') return detail
      if (Array.isArray(detail) && detail.length) return detail.map(d => d.msg).join('; ')
      return fallback
    }

    // Re-initialise every time the modal opens (or is re-targeted while open)
    watch(
      () => [props.isOpen, props.backlogItem?.id, props.mode],
      ([open]) => {
        if (!open || !props.backlogItem) return
        if (props.mode === 'view') loadPurchaseOrder()
        else resetForm()
      },
      { immediate: true }
    )

    const close = () => {
      emit('close')
    }

    const statusVariant = (status) => {
      const s = (status || '').toLowerCase()
      if (['received', 'delivered', 'completed'].includes(s)) return 'success'
      if (['cancelled', 'canceled', 'rejected'].includes(s)) return 'danger'
      if (['pending', 'draft'].includes(s)) return 'warning'
      return 'info'
    }

    // Parse YYYY-MM-DD as a local date; new Date('2026-11-26') is UTC midnight and renders
    // as the previous day in timezones west of UTC.
    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(dateString)
      const date = match ? new Date(+match[1], +match[2] - 1, +match[3]) : new Date(dateString)
      if (isNaN(date.getTime())) return dateString
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
    }

    return {
      currentCurrency,
      translateProductName,
      formatCurrency,
      formatCurrencyWithDecimals,
      todayIso,
      form,
      errors,
      saving,
      submitError,
      po,
      loading,
      loadError,
      shortfall,
      totalDisplay,
      submit,
      close,
      statusVariant,
      formatDate
    }
  }
}
</script>

<style scoped>
/* Layout, buttons, form controls and detail blocks come from src/styles/modal.css */
.modal {
  max-width: 680px;
}

.po-summary {
  padding-bottom: var(--space-6);
  margin-bottom: var(--space-6);
  border-bottom: 1px solid var(--color-border-subtle);
}

.danger-text {
  color: var(--color-danger);
}

.error {
  margin-top: 0;
}

.po-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  min-width: 0;
}

.form-group-wide {
  grid-column: 1 / -1;
}

.optional {
  font-weight: 400;
  color: var(--color-text-muted);
}

.form-control.invalid {
  border-color: var(--color-danger);
}

.form-control.invalid:focus {
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-danger) 25%, transparent);
}

.po-notes {
  height: auto;
  padding: var(--space-2) var(--space-3);
  line-height: var(--leading-normal);
  resize: vertical;
}

.field-error {
  font-size: var(--text-sm);
  color: var(--color-danger);
}

.po-total {
  display: flex;
  align-items: center;
  height: 36px;
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
}

.po-notes-item {
  grid-column: 1 / -1;
  white-space: pre-wrap;
}

@media (max-width: 639px) {
  .po-form {
    grid-template-columns: 1fr;
  }

  .po-summary {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    padding-bottom: var(--space-4);
    margin-bottom: var(--space-4);
  }
}
</style>
