import axios from 'axios'
import { useStore, TaskStatus, Health, Points, Config, HistoryItem } from '../store'

const isTauri = typeof window !== 'undefined' && '__TAURI__' in window

let API_BASE = '/api'
let dynamicPort: number | null = null
let heartbeatInterval: ReturnType<typeof setInterval> | null = null

const getApiBase = async (): Promise<string> => {
  if (isTauri) {
    if (dynamicPort) {
      return `http://localhost:${dynamicPort}/api`
    }
    
    try {
      const { invoke } = await import('@tauri-apps/api/core')
      dynamicPort = await invoke<number>('get_backend_port')
      const store = useStore.getState()
      store.setBackendPort(dynamicPort)
      if (dynamicPort) {
        return `http://localhost:${dynamicPort}/api`
      }
    } catch (e) {
      console.warn('Failed to get dynamic port from Tauri, falling back to default:', e)
    }
  }
  return API_BASE
}

const getApi = async () => {
  const base = await getApiBase()
  return axios.create({
    baseURL: base,
    timeout: 10000,
  })
}

export const fetchStatus = async (): Promise<TaskStatus> => {
  const api = await getApi()
  const response = await api.get('/status')
  return response.data
}

export const fetchHealth = async (): Promise<Health> => {
  const api = await getApi()
  const response = await api.get('/health')
  return response.data
}

export const fetchPoints = async (): Promise<Points> => {
  const api = await getApi()
  const response = await api.get('/points')
  return response.data
}

export const fetchConfig = async (): Promise<Config> => {
  const api = await getApi()
  const response = await api.get('/config')
  return response.data
}

export const updateConfig = async (config: Partial<Config>): Promise<void> => {
  const api = await getApi()
  await api.put('/config', config)
}

export const startTask = async (options: {
  mode?: string
  headless?: boolean
  desktop_only?: boolean
  mobile_only?: boolean
  skip_daily_tasks?: boolean
}): Promise<void> => {
  const api = await getApi()
  await api.post('/task/start', options)
}

export const stopTask = async (): Promise<void> => {
  const api = await getApi()
  await api.post('/task/stop')
}

export const fetchHistory = async (days: number = 7): Promise<HistoryItem[]> => {
  const api = await getApi()
  const response = await api.get('/history', { params: { days } })
  return response.data.history
}

export const fetchRecentLogs = async (lines: number = 100): Promise<string[]> => {
  const api = await getApi()
  const response = await api.get('/logs/recent', { params: { lines } })
  return response.data.logs
}

export const fetchDashboard = async () => {
  const api = await getApi()
  const response = await api.get('/dashboard')
  return response.data
}

let heartbeatFailures = 0
const MAX_HEARTBEAT_FAILURES = 3

export const startHeartbeat = () => {
  if (heartbeatInterval) {
    clearInterval(heartbeatInterval)
  }
  
  heartbeatInterval = setInterval(async () => {
    try {
      const api = await getApi()
      await api.get('/health')
      const store = useStore.getState()
      store.setLastHeartbeat(new Date().toISOString())
      store.setBackendReady(true)
      store.setDataError(null)
      heartbeatFailures = 0
    } catch (error) {
      heartbeatFailures++
      const store = useStore.getState()
      store.setBackendReady(false)
      
      if (heartbeatFailures >= MAX_HEARTBEAT_FAILURES) {
        store.setWsConnected(false)
        if (ws && ws.readyState !== WebSocket.CONNECTING) {
          ws.close()
        }
        connectWebSocket()
        heartbeatFailures = 0
      }
    }
  }, 5000)
}

export const stopHeartbeat = () => {
  if (heartbeatInterval) {
    clearInterval(heartbeatInterval)
    heartbeatInterval = null
  }
}

let ws: WebSocket | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let reconnectAttempts = 0
const MAX_RECONNECT_DELAY = 30000

const scheduleReconnect = () => {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
  }
  
  const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), MAX_RECONNECT_DELAY)
  reconnectAttempts++
  
  reconnectTimer = setTimeout(() => {
    console.log(`Attempting to reconnect WebSocket (attempt ${reconnectAttempts})...`)
    connectWebSocket()
  }, delay)
}

export const connectWebSocket = async () => {
  if (ws?.readyState === WebSocket.OPEN || ws?.readyState === WebSocket.CONNECTING) return

  let wsUrl: string
  let port = dynamicPort
  
  if (isTauri) {
    if (!port) {
      try {
        const { invoke } = await import('@tauri-apps/api/core')
        port = await invoke<number>('get_backend_port')
        dynamicPort = port
        useStore.getState().setBackendPort(port)
      } catch (e) {
        console.warn('Failed to get backend port:', e)
      }
    }
    wsUrl = `ws://localhost:${port || 8000}/ws`
  } else {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    wsUrl = `${protocol}//${window.location.host}/ws`
  }

  try {
    ws = new WebSocket(wsUrl)
  } catch (error) {
    console.error('Failed to create WebSocket:', error)
    scheduleReconnect()
    return
  }

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
    scheduleReconnect()
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

export const initializeTauriEvents = async () => {
  if (!isTauri) return
  
  try {
    const { listen } = await import('@tauri-apps/api/event')
    
    listen<string>('py-log', (event) => {
      const store = useStore.getState()
      store.addLog(event.payload)
    })
    
    listen<string>('py-error', (event) => {
      const store = useStore.getState()
      store.addLog(`[ERROR] ${event.payload}`)
    })
    
    listen<number | null>('backend-terminated', (event) => {
      console.log('Backend process terminated with code:', event.payload)
      const store = useStore.getState()
      store.setWsConnected(false)
      store.setBackendReady(false)
      if (event.payload !== 0) {
        store.setDataError('后端进程异常退出，请重启应用')
      }
    })
    
    console.log('Tauri event listeners initialized')
  } catch (e) {
    console.warn('Failed to initialize Tauri events:', e)
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
    store.setBackendReady(true)
  } catch (error) {
    console.error('Failed to initialize data:', error)
    store.setDataError('无法连接到服务器，请检查服务是否正常运行')
    store.setDataLoading(false)
    store.setBackendReady(false)
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
