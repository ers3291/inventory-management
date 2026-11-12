<template>
  <div class="reports">
    <div class="page-header">
      <h2>{{ t('reports.title') }}</h2>
      <p>{{ t('reports.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('reports.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="monthlyData.length === 0" class="card empty-state">
      <p>{{ t('reports.noData') }}</p>
    </div>
    <div v-else>
      <!-- Quarterly Performance -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.quarterly.title') }}</h3>
        </div>
        <div class="table-container">
          <table class="reports-table">
            <thead>
              <tr>
                <th>{{ t('reports.quarterly.quarter') }}</th>
                <th class="num">{{ t('reports.quarterly.totalOrders') }}</th>
                <th class="num">{{ t('reports.quarterly.totalRevenue') }}</th>
                <th class="num">{{ t('reports.quarterly.avgOrderValue') }}</th>
                <th class="num">{{ t('reports.quarterly.fulfillmentRate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="q in quarterlyData" :key="q.quarter">
                <td><strong>{{ formatQuarter(q.quarter) }}</strong></td>
                <td class="num">{{ formatCount(q.total_orders) }}</td>
                <td class="num">{{ formatMoney(q.total_revenue) }}</td>
                <td class="num">{{ formatMoney(q.avg_order_value) }}</td>
                <td class="num">
                  <span :class="getFulfillmentClass(q.fulfillment_rate)">
                    {{ formatPercent(q.fulfillment_rate) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Monthly Trends Chart -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.monthlyTrend.title') }}</h3>
        </div>
        <div class="chart-container">
          <div class="bar-chart" role="img" :aria-label="t('reports.monthlyTrend.title')">
            <div v-for="bar in chartBars" :key="bar.month" class="bar-wrapper">
              <div class="bar-container">
                <div
                  class="bar"
                  :style="{ height: bar.height + 'px' }"
                  :title="bar.label + ': ' + bar.revenueDisplay"
                ></div>
              </div>
              <!-- Label wrapper reserves vertical room; the rotated label inside is absolutely
                   positioned so its text width never widens the bar column -->
              <div class="bar-label-slot">
                <div class="bar-label">{{ bar.label }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Month-over-Month Comparison -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.monthOverMonth.title') }}</h3>
        </div>
        <div class="table-container">
          <table class="reports-table">
            <thead>
              <tr>
                <th>{{ t('reports.monthOverMonth.month') }}</th>
                <th class="num">{{ t('reports.monthOverMonth.orders') }}</th>
                <th class="num">{{ t('reports.monthOverMonth.revenue') }}</th>
                <th class="num">{{ t('reports.monthOverMonth.change') }}</th>
                <th class="num">{{ t('reports.monthOverMonth.growthRate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in monthOverMonthRows" :key="row.month">
                <td><strong>{{ row.label }}</strong></td>
                <td class="num">{{ formatCount(row.order_count) }}</td>
                <td class="num">{{ formatMoney(row.revenue) }}</td>
                <td class="num">
                  <span :class="row.changeClass">{{ row.changeDisplay }}</span>
                </td>
                <td class="num">
                  <span :class="row.changeClass">{{ row.growthDisplay }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Summary Stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ isFullYear ? t('reports.stats.totalRevenueYtd') : t('reports.stats.totalRevenuePeriod') }}</div>
          <div class="stat-value">{{ formatMoney(summaryStats.totalRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.stats.avgMonthlyRevenue') }}</div>
          <div class="stat-value">{{ formatMoney(summaryStats.avgMonthlyRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ isFullYear ? t('reports.stats.totalOrdersYtd') : t('reports.stats.totalOrdersPeriod') }}</div>
          <div class="stat-value">{{ formatCount(summaryStats.totalOrders) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.stats.bestQuarter') }}</div>
          <div class="stat-value">{{ summaryStats.bestQuarter ? formatQuarter(summaryStats.bestQuarter) : '-' }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrencyWithDecimals } from '../utils/currency'

// Bar chart max height in px (matches .bar-container height in the styles below)
const MAX_BAR_HEIGHT = 200
const MONTH_KEYS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

export default {
  name: 'Reports',
  setup() {
    const { t, currentLocale, currentCurrency } = useI18n()
    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      getCurrentFilters
    } = useFilters()

    const loading = ref(true)
    const error = ref(null)
    const quarterlyData = ref([])
    const monthlyData = ref([])

    // Incremented per load so a slow response from an earlier filter selection
    // can't overwrite the data for the filters the user picked afterwards
    let requestId = 0

    const loadData = async () => {
      const thisRequest = ++requestId
      loading.value = true
      error.value = null
      try {
        const filters = getCurrentFilters()
        // Both reports are independent, so fetch them in parallel
        const [quarterly, monthly] = await Promise.all([
          api.getQuarterlyReports(filters),
          api.getMonthlyTrends(filters)
        ])
        if (thisRequest !== requestId) return
        quarterlyData.value = Array.isArray(quarterly) ? quarterly : []
        monthlyData.value = Array.isArray(monthly) ? monthly : []
      } catch (err) {
        if (thisRequest !== requestId) return
        error.value = t('reports.loadError', { message: err.message })
        console.error('Failed to load reports:', err)
      } finally {
        if (thisRequest === requestId) loading.value = false
      }
    }

    // Reload whenever any global filter changes, like Dashboard and Orders
    watch([selectedPeriod, selectedLocation, selectedCategory, selectedStatus], loadData)
    onMounted(loadData)

    const isFullYear = computed(() => selectedPeriod.value === 'all')

    const numberLocale = computed(() => (currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'))

    // Shared currency util converts USD -> JPY when the Japanese locale is active
    const formatMoney = (amount) => formatCurrencyWithDecimals(Number(amount) || 0, currentCurrency.value, 2)

    const formatCount = (value) => (Number(value) || 0).toLocaleString(numberLocale.value)

    const formatPercent = (value) => {
      const num = Number(value)
      return Number.isFinite(num) ? `${num.toFixed(1)}%` : '-'
    }

    // "YYYY-MM" -> localized "Jan 2025" / "2025年1月"; returns the raw string if it isn't a valid month
    const formatMonth = (monthStr) => {
      const match = /^(\d{4})-(\d{2})$/.exec(monthStr || '')
      if (!match) return monthStr || '-'
      const monthIndex = parseInt(match[2], 10) - 1
      if (monthIndex < 0 || monthIndex > 11) return monthStr
      return t('reports.monthLabel', { month: t(`months.${MONTH_KEYS[monthIndex]}`), year: match[1] })
    }

    // "Q1-2025" -> localized "Q1-2025" / "2025年 第1四半期"
    const formatQuarter = (quarterStr) => {
      const match = /^Q([1-4])-(\d{4})$/.exec(quarterStr || '')
      if (!match) return quarterStr || '-'
      return t('reports.quarterLabel', { quarter: match[1], year: match[2] })
    }

    const getFulfillmentClass = (rate) => {
      if (rate >= 90) return 'badge success'
      if (rate >= 75) return 'badge warning'
      return 'badge danger'
    }

    // Max is computed once per data change instead of once per bar per render
    const chartBars = computed(() => {
      const maxRevenue = Math.max(0, ...monthlyData.value.map(m => m.revenue || 0))
      return monthlyData.value.map(m => ({
        month: m.month,
        label: formatMonth(m.month),
        revenueDisplay: formatMoney(m.revenue),
        height: maxRevenue > 0 ? ((m.revenue || 0) / maxRevenue) * MAX_BAR_HEIGHT : 0
      }))
    })

    const monthOverMonthRows = computed(() => {
      return monthlyData.value.map((m, index) => {
        const row = {
          ...m,
          label: formatMonth(m.month),
          changeClass: '',
          changeDisplay: '-',
          growthDisplay: '-'
        }
        if (index === 0) return row

        const previous = monthlyData.value[index - 1].revenue || 0
        const change = (m.revenue || 0) - previous
        // Sign is prepended separately so negatives read "-$1,234" rather than "$-1,234"
        const sign = change > 0 ? '+' : change < 0 ? '-' : ''
        row.changeClass = change > 0 ? 'positive-change' : change < 0 ? 'negative-change' : ''
        row.changeDisplay = sign + formatMoney(Math.abs(change))
        row.growthDisplay = previous === 0
          ? t('reports.notApplicable')
          : `${change > 0 ? '+' : ''}${((change / previous) * 100).toFixed(1)}%`
        return row
      })
    })

    const summaryStats = computed(() => {
      const totalRevenue = monthlyData.value.reduce((sum, m) => sum + (m.revenue || 0), 0)
      const totalOrders = monthlyData.value.reduce((sum, m) => sum + (m.order_count || 0), 0)
      const avgMonthlyRevenue = monthlyData.value.length > 0 ? totalRevenue / monthlyData.value.length : 0
      // Start below zero so a quarter is still picked when every quarter has zero revenue
      const best = quarterlyData.value.reduce(
        (top, q) => ((q.total_revenue || 0) > top.revenue ? { quarter: q.quarter, revenue: q.total_revenue || 0 } : top),
        { quarter: '', revenue: -Infinity }
      )
      return { totalRevenue, totalOrders, avgMonthlyRevenue, bestQuarter: best.quarter }
    })

    return {
      t,
      loading,
      error,
      quarterlyData,
      monthlyData,
      isFullYear,
      chartBars,
      monthOverMonthRows,
      summaryStats,
      formatMoney,
      formatCount,
      formatPercent,
      formatQuarter,
      getFulfillmentClass
    }
  }
}
</script>

<style scoped>
/*
 * Page header, cards, tables, badges, stat cards and loading/error states are styled
 * globally in App.vue. Only the bar chart and change colours are view-specific here.
 */

/* ---------- Monthly revenue bar chart ---------- */
/* Left padding gives the first rotated label room, since labels hang down-left of each bar */
.chart-container {
  padding: var(--space-4) 0 0 var(--space-8);
  overflow: hidden;
}

/*
 * Fluid bars: each column is flex 1 1 0 with min-width 0, so 12 columns always share the
 * card width (no fixed widths). Bar heights stay in px from getBarHeight() (max 200px).
 */
.bar-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  gap: var(--space-2);
}

.bar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1 1 0;
  min-width: 0;
  max-width: 5rem;
}

/* Each column draws its own slice of the x-axis line directly under the bar */
.bar-container {
  height: 200px;
  display: flex;
  align-items: flex-end;
  width: 100%;
  border-bottom: 1px solid var(--color-border);
}

.bar {
  width: 100%;
  background: var(--color-primary);
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  transition: background-color var(--transition-fast);
  cursor: pointer;
}

.bar:hover {
  background: var(--color-primary-hover);
}

/* Fixed-height slot under the axis; holds the rotated label without affecting width */
.bar-label-slot {
  position: relative;
  width: 100%;
  /* ~55px label rotated 45deg drops ~45px, plus the top offset */
  height: 4.5rem;
}

/* Right edge anchored to the column centre, rotated -45deg around that point */
.bar-label {
  position: absolute;
  top: var(--space-2);
  right: 50%;
  transform: rotate(-45deg);
  transform-origin: right center;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  white-space: nowrap;
}

/* Narrow screens: columns are ~20px wide, so turn labels vertical to stop them overlapping */
@media (max-width: 639px) {
  .bar-chart {
    gap: var(--space-1);
  }

  .bar-label-slot {
    height: 4.5rem;
  }

  /* Vertical text centred under the bar; rotate(180deg) makes it read bottom-to-top
     with the end of the label touching the axis */
  .bar-label {
    top: var(--space-1);
    right: auto;
    left: 50%;
    writing-mode: vertical-rl;
    transform: translateX(-50%) rotate(180deg);
    /* Override the desktop right-edge origin, which would flip the label a full width sideways */
    transform-origin: center;
  }
}

/* Keep quarter/month names (e.g. Q1-2025, Jan 2025) on one line */
td strong {
  white-space: nowrap;
}

/* Shown when the active filters match no orders */
.empty-state {
  padding: var(--space-12) var(--space-4);
  text-align: center;
  color: var(--color-text-muted);
}

/* ---------- Month-over-month change ---------- */
.positive-change {
  color: var(--color-success);
  font-weight: 500;
}

.negative-change {
  color: var(--color-danger);
  font-weight: 500;
}
</style>
