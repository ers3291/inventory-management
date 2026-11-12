import { ref, computed } from 'vue'
import { useI18n } from './useI18n'

// Base user data (language-independent)
const baseUserData = {
  id: 1,
  email: 'john.doe@catalystcomponents.com',
  phone: '+1 (111) 111-1111',
  avatar: null,
  joinDate: '2022-03-15'
}

// Built-in demo tasks. Mutable state (status, and deletion = removal from this array)
// lives in a module-level ref so every component sees the same reactive data and edits
// survive locale switches. Titles are locale-dependent and merged in by currentUser below.
const mockTasks = ref([
  { id: 1, priority: 'high', dueDate: '2025-10-08', status: 'pending' },
  { id: 2, priority: 'medium', dueDate: '2025-10-06', status: 'pending' },
  { id: 3, priority: 'medium', dueDate: '2025-10-10', status: 'pending' },
  { id: 4, priority: 'low', dueDate: '2025-10-15', status: 'pending' }
])

// Localized titles for the built-in tasks, keyed by task id
const mockTaskTitles = {
  en: {
    1: 'Review Q4 inventory levels',
    2: 'Approve Tokyo warehouse orders',
    3: 'Update reorder points for Circuit Boards',
    4: 'Review monthly spending report'
  },
  ja: {
    1: '第4四半期の在庫レベルを確認',
    2: '東京倉庫の注文を承認',
    3: '回路基板の再注文点を更新',
    4: '月次支出レポートを確認'
  }
}

// Mock current user data with language-aware fields
const createCurrentUser = () => {
  const { currentLocale } = useI18n()

  return computed(() => {
    const isJapanese = currentLocale.value === 'ja'
    const titles = mockTaskTitles[isJapanese ? 'ja' : 'en']

    return {
      ...baseUserData,
      name: isJapanese ? '田中 太郎' : 'John Doe',
      jobTitle: isJapanese ? 'オペレーションマネージャー' : 'Operations Manager',
      department: isJapanese ? 'サプライチェーン運営部' : 'Supply Chain Operations',
      location: isJapanese ? 'サンフランシスコ' : 'San Francisco',
      // Fresh copies on every recompute: this output is read-only. Mutate via
      // toggleMockTask/deleteMockTask so changes land in the mockTasks ref.
      tasks: mockTasks.value.map(task => ({ ...task, title: titles[task.id] }))
    }
  })
}

const currentUser = createCurrentUser()

export function useAuth() {
  const isAuthenticated = ref(true)

  const logout = () => {
    // In a real app, this would clear tokens, etc.
    console.log('Logout clicked - would redirect to login')
    alert('Logout functionality - in a real app, this would clear session and redirect to login')
  }

  const getInitials = (name) => {
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
  }

  const isMockTask = (id) => mockTasks.value.some(task => task.id === id)

  const toggleMockTask = (id) => {
    const task = mockTasks.value.find(task => task.id === id)
    if (task) {
      task.status = task.status === 'pending' ? 'completed' : 'pending'
    }
  }

  const deleteMockTask = (id) => {
    mockTasks.value = mockTasks.value.filter(task => task.id !== id)
  }

  return {
    currentUser,
    isMockTask,
    toggleMockTask,
    deleteMockTask,
    isAuthenticated,
    logout,
    getInitials
  }
}
