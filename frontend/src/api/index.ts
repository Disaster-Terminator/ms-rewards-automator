import axios from 'axios'
import { useStore, TaskStatus, Health, Points, Config, HistoryItem } from '../store'

const API_BASE = '/api'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
})

export const fetchStatus = async (): Promise<TaskStatus> => {
  const response = await api.get('/status')
  return response.data
}

export const fetchHealth = async (): Promise<Health> => {
  const response = await api.get('/health')
  return response.data
}

export const fetchPoints = async (): Promise<Points> => {
  const response = await api.get('/points')
  return response.data
}

export const fetchConfig = async (): Promise<Config> => {
  const response = await api.get('/config')
  return response.data
}

export const updateConfig = async (config: Partial<Config>): Promise<void> => {
  await api.put('/config', config)
}

export const startTask = async (options: {
  mode?: string
  headless?: boolean
  desktop_only?: boolean
  mobile_only?: boolean
  skip_daily_tasks?: boolean
}): Promise<void> => {
  await api.post('/task/start', options)
}

export const stopTask = async (): Promise<void> => {
  await api.post('/task/stop')
}

export const fetchHistory = async (days: number = 7): Promise<HistoryItem[]> => {
  const response = await api.get('/history', { params: { days } })
  return response.data.history
}

export const fetchRecentLogs = async (lines: number = 100): Promise<string[]> => {
  const response = await api.get('/logs/recent', { params: { lines } })
  return response.data.logs
}

export const fetchDashboard = async () => {
  const response = await api.get('/dashboard')
  return response.data
}

let ws: WebSocket | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let reconnectAttempts = 0
const MAX_RECONNECT_ATTEMPTS = 5

export const connectWebSocket = () => {
  if (ws?.readyState === WebSocket.OPEN) return

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/ws`

  ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    console.log('WebSocket connected')
    useStore.getState().setWsConnected(true)
    reconnectAttempts = 0
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  ws.onclose = () => {
    console.log('WebSocket disconnected')
    useStore.getState().setWsConnected(false)
    
    if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000)
      reconnectAttempts++
      
      reconnectTimer = setTimeout(() => {
        console.log(`Attempting to reconnect WebSocket (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})...`)
        connectWebSocket()
      }, delay)
    }
  }

  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      const store = useStore.getState()

      switch (data.type) {
        case 'status_update':
          store.setTaskStatus(data.data)
          break
        case 'health_update':
          store.setHealth(data.data)
          break
        case 'points_update':
          store.setPoints(data.data)
          break
        case 'log':
          if (data.data) {
            store.addLog(data.data)
          }
          break
        case 'task_event':
          console.log('Task event:', data.event, data.message)
          break
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error)
    }
  }
}

export const disconnectWebSocket = () => {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
  if (ws) {
    ws.close()
    ws = null
  }
}

export const initializeData = async () => {
  const store = useStore.getState()
  store.setDataLoading(true)
  store.setDataError(null)

  try {
    const [status, health, points, config, history, logs] = await Promise.all([
      fetchStatus(),
      fetchHealth(),
      fetchPoints(),
      fetchConfig(),
      fetchHistory(),
      fetchRecentLogs(),
    ])

    store.setTaskStatus(status)
    store.setHealth(health)
    store.setPoints(points)
    store.setConfig(config)
    store.setHistory(history)
    store.setLogs(logs)
    store.setLastDataUpdate(new Date().toISOString())
    store.setDataLoading(false)
  } catch (error) {
    console.error('Failed to initialize data:', error)
    store.setDataError('无法连接到服务器，请检查服务是否正常运行')
    store.setDataLoading(false)
  }
}

export const refreshData = async () => {
  const store = useStore.getState()
  
  try {
    const [status, health, points] = await Promise.all([
      fetchStatus(),
      fetchHealth(),
      fetchPoints(),
    ])

    store.setTaskStatus(status)
    store.setHealth(health)
    store.setPoints(points)
  } catch (error) {
    console.error('Failed to refresh data:', error)
  }
}
