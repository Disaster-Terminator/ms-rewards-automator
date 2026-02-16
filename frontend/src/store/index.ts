import { create } from 'zustand'

export interface TaskStatus {
  is_running: boolean
  current_operation: string
  progress: number
  total_steps: number
  desktop_searches_completed: number
  desktop_searches_total: number
  mobile_searches_completed: number
  mobile_searches_total: number
  initial_points: number | null
  current_points: number | null
  points_gained: number
  error_count: number
  warning_count: number
  start_time: string | null
  elapsed_seconds: number
}

export interface Health {
  overall: string
  system: {
    status: string
    cpu_percent: number
    memory_percent: number
    memory_used_gb: number
    memory_total_gb: number
    disk_percent: number
    disk_free_gb: number
    issues: string[]
  }
  network: {
    status: string
    connection_rate: number
    successful_connections: number
    total_tests: number
  }
  browser: {
    status: string
    processes: number
    memory_mb: number
    issues: string[]
  }
  search_stats: {
    total: number
    successful: number
    failed: number
    success_rate: number
  }
  uptime_seconds: number
  recommendations: string[]
}

export interface Points {
  current_points: number | null
  lifetime_points: number | null
  points_gained_today: number
  last_updated: string | null
}

export interface Config {
  search: {
    desktop_count: number
    mobile_count: number
    wait_interval: number
  }
  browser: {
    headless: boolean
    type: string
    force_dark_mode: boolean
  }
  account: {
    storage_state_path: string
    login_url: string
  }
  login: {
    auto_login: {
      enabled: boolean
      email: string
      password: string
      totp_secret: string
    }
  }
  task_system: {
    enabled: boolean
    debug_mode: boolean
  }
  notification: {
    enabled: boolean
    telegram: {
      bot_token: string
      chat_id: string
    }
  }
  scheduler: {
    enabled: boolean
    mode: string
    random_start_hour: number
    random_end_hour: number
  }
  logging: {
    level: string
  }
  bing_theme: {
    enabled: boolean
    force_theme: boolean
  }
  monitoring: {
    health_check: {
      enabled: boolean
      interval: number
    }
  }
}

export interface HistoryItem {
  timestamp: string
  points_gained: number
  desktop_searches: number
  mobile_searches: number
  errors: number
  duration_seconds: number
}

interface Store {
  sidebarCollapsed: boolean
  darkMode: boolean
  taskStatus: TaskStatus | null
  health: Health | null
  points: Points | null
  config: Config | null
  history: HistoryItem[]
  logs: string[]
  wsConnected: boolean
  lastDataUpdate: string | null
  dataLoading: boolean
  dataError: string | null

  toggleSidebar: () => void
  toggleDarkMode: () => void
  setTaskStatus: (status: TaskStatus) => void
  setHealth: (health: Health) => void
  setPoints: (points: Points) => void
  setConfig: (config: Config) => void
  setHistory: (history: HistoryItem[]) => void
  addLog: (log: string) => void
  setLogs: (logs: string[]) => void
  setWsConnected: (connected: boolean) => void
  setLastDataUpdate: (time: string) => void
  setDataLoading: (loading: boolean) => void
  setDataError: (error: string | null) => void
}

export const useStore = create<Store>((set) => ({
  sidebarCollapsed: false,
  darkMode: true,
  taskStatus: null,
  health: null,
  points: null,
  config: null,
  history: [],
  logs: [],
  wsConnected: false,
  lastDataUpdate: null,
  dataLoading: true,
  dataError: null,

  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
  toggleDarkMode: () => set((state) => ({ darkMode: !state.darkMode })),
  setTaskStatus: (status) => set({ taskStatus: status, lastDataUpdate: new Date().toISOString() }),
  setHealth: (health) => set({ health, lastDataUpdate: new Date().toISOString() }),
  setPoints: (points) => set({ points, lastDataUpdate: new Date().toISOString() }),
  setConfig: (config) => set({ config }),
  setHistory: (history) => set({ history }),
  addLog: (log) => set((state) => ({ logs: [...state.logs.slice(-500), log] })),
  setLogs: (logs) => set({ logs }),
  setWsConnected: (connected) => set({ wsConnected: connected }),
  setLastDataUpdate: (time) => set({ lastDataUpdate: time }),
  setDataLoading: (loading) => set({ dataLoading: loading }),
  setDataError: (error) => set({ dataError: error }),
}))
