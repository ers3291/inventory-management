// Design tokens must load before any component styles so var(--*) resolves everywhere
import './styles/tokens.css'
// Shared modal family (overlay, panel, buttons, form controls) used by every *Modal.vue
import './styles/modal.css'
import { createApp } from 'vue'
import { initTheme } from './composables/useTheme'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import Dashboard from './views/Dashboard.vue'
import Inventory from './views/Inventory.vue'
import Orders from './views/Orders.vue'
import Demand from './views/Demand.vue'
import Spending from './views/Spending.vue'
import Reports from './views/Reports.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Dashboard },
    { path: '/inventory', component: Inventory },
    { path: '/orders', component: Orders },
    { path: '/demand', component: Demand },
    { path: '/spending', component: Spending },
    { path: '/reports', component: Reports }
  ]
})

// Set data-theme on <html> before mounting so components never render with the wrong palette
initTheme()

const app = createApp(App)
app.use(router)
app.mount('#app')
