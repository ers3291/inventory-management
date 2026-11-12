// Primary navigation, shared by AppSidebar (links) and App.vue (topbar page title).
// Paths must match the routes in main.js exactly; `icon` keys must exist in AppSidebar's icon map.
export const navSections = [
  {
    id: 'main',
    title: '',
    items: [
      { to: '/', label: 'Overview', labelKey: 'nav.overview', icon: 'home' },
      { to: '/inventory', label: 'Inventory', labelKey: 'nav.inventory', icon: 'box' },
      { to: '/orders', label: 'Orders', labelKey: 'nav.orders', icon: 'cart' },
      { to: '/spending', label: 'Finance', labelKey: 'nav.finance', icon: 'wallet' },
      { to: '/demand', label: 'Demand Forecast', labelKey: 'nav.demandForecast', icon: 'trend' },
      { to: '/reports', label: 'Reports', labelKey: 'nav.reports', icon: 'chart' }
    ]
  }
]

export const navItems = navSections.flatMap((section) => section.items)
