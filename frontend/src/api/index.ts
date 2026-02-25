import axios from 'axios'
import { useStore, TaskStatus, Health, Points, Config, HistoryItem } from '../store'

declare const __TAURI_ENV_DEBUG__: string | undefined

const isTauri = typeof window !== 'undefined' && (window as any).__TAURI__ !== undefined
const isTauriDev = typeof __TAURI_ENV_DEBUG__ !== 'undefined' && __TAURI_ENV_DEBUG__ !== ''
const isTauriProduction = isTauri && !isTauriDev

let dynamicPort: number | null = null
let heartbeatInterval: ReturnType<typeof setInterval> | null = null
let isConnecting = false
let connectionPromise: Promise<void> | null = null

const getApiBase = async (): Promise<string> => {
  // If in browser (not Tauri), use relative path to leverage Vite proxy
  if (!isTauri) {
    return '/api'
  }

  // If in Tauri Dev, use hardcoded dev port
  if (isTauriDev) {
    return 'http://localhost:8000/api'
  }
  
  if (isTauriProduction) {
    if (dynamicPort) {
      return `http://localhost:${dynamicPort}/api`
    }
    
    try {
      const { invoke } = await import('@tauri-apps/api/core')
      const port = await invoke<number>('get_backend_port')
      if (port && port !== 8000) {
        dynamicPort = port
        const store = useStore.getState()
        store.setBackendPort(dynamicPort)
        return `http://localhost:${dynamicPort}/api`
      }
      return `http://localhost:${port}/api`
    } catch (e) {
      console.warn('Failed to get dynamic port from Tauri, falling back to default:', e)
      return 'http://localhost:8000/api'
    }
  }
  return '/api'
}

const getApi = async () => {
  const base = await getApiBase()
  return axios.create({
    baseURL: base,
    timeout: 15000,
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
}): Promise<{ message: string; status: string }> => {
  const api = await getApi()
  const response = await api.post('/task/start', options)
  return response.data
}

export const stopTask = async (): Promise<{ message: string; status: string }> => {
  const api = await getApi()
  const response = await api.post('/task/stop')
  return response.data
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
const HEARTBEAT_INTERVAL = 3000

export const startHeartbeat = () => {
  if (heartbeatInterval) {
    clearInterval(heartbeatInterval)
  }
  
  heartbeatInterval = setInterval(async () => {
    try {
      const api = await getApi()
      const [healthResponse, statusResponse] = await Promise.all([
        api.get('/health'),
        api.get('/status')
      ])
      
      const store = useStore.getState()
      store.setLastHeartbeat(new Date().toISOString())
      store.setBackendReady(true)
      store.setDataError(null)
      store.setHealth(healthResponse.data)
      store.setTaskStatus(statusResponse.data)
      
      // Auto-sync runner store if WS is failing
      if (!store.wsConnected && statusResponse.data.is_running) {
        const { useRunnerStore } = await import('../core/runnerStore')
        if (useRunnerStore.getState().status !== 'running') {
          useRunnerStore.getState().setStatus('running')
        }
      }
      
      heartbeatFailures = 0
    } catch (error) {
      heartbeatFailures++
      const store = useStore.getState()
      
      if (heartbeatFailures >= MAX_HEARTBEAT_FAILURES) {
        store.setBackendReady(false)
        heartbeatFailures = 0
      }
    }
  }, HEARTBEAT_INTERVAL)
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
let wsHeartbeatInterval: ReturnType<typeof setInterval> | null = null
const MAX_RECONNECT_DELAY = 10000 
const INITIAL_RECONNECT_DELAY = 1000
const WS_HEARTBEAT_INTERVAL = 30000

const scheduleReconnect = () => {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
  }
  
  const delay = Math.min(INITIAL_RECONNECT_DELAY * Math.pow(1.5, reconnectAttempts), MAX_RECONNECT_DELAY)
  reconnectAttempts++
  
  reconnectTimer = setTimeout(async () => {
    await connectWebSocket()
  }, delay)
}

export const connectWebSocket = async (): Promise<void> => {
  if (isConnecting && connectionPromise) {
    return connectionPromise
  }
  
  if (ws?.readyState === WebSocket.OPEN || ws?.readyState === WebSocket.CONNECTING) {
    return
  }
  
  isConnecting = true
  
  connectionPromise = new Promise(async (resolve) => {
    let wsUrl: string
    
    if (!isTauri) {
      // Browser mode: use relative path for proxy
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      wsUrl = `${protocol}//${window.location.host}/ws`
    } else if (isTauriDev) {
      wsUrl = 'ws://localhost:8000/ws'
    } else if (isTauriProduction) {
      let port = dynamicPort
      if (!port) {
        try {
          const { invoke } = await import('@tauri-apps/api/core')
          const p = await invoke<number>('get_backend_port')
          port = p || 8000
          dynamicPort = port
          useStore.getState().setBackendPort(port)
        } catch (e) {
          port = 8000
        }
      }
      wsUrl = `ws://localhost:${port}/ws`
    } else {
      wsUrl = `ws://localhost:8000/ws`
    }

    console.log('Connecting to WebSocket:', wsUrl)

    try {
      ws = new WebSocket(wsUrl)
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
      isConnecting = false
      scheduleReconnect()
      resolve()
      return
    }

    const connectionTimeout = setTimeout(() => {
      if (ws?.readyState !== WebSocket.OPEN) {
        console.warn('WebSocket connection timeout')
        ws?.close()
        isConnecting = false
        resolve()
      }
    }, 5000)

    ws.onopen = () => {
      clearTimeout(connectionTimeout)
      console.log('WebSocket connected')
      useStore.getState().setWsConnected(true)
      reconnectAttempts = 0
      isConnecting = false
      
      if (wsHeartbeatInterval) {
        clearInterval(wsHeartbeatInterval)
      }
      wsHeartbeatInterval = setInterval(() => {
        if (ws?.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }))
        }
      }, WS_HEARTBEAT_INTERVAL)
      
      resolve()
    }

    ws.onclose = (event) => {
      clearTimeout(connectionTimeout)
      console.log('WebSocket disconnected:', event.code, event.reason)
      useStore.getState().setWsConnected(false)
      isConnecting = false
      if (wsHeartbeatInterval) {
        clearInterval(wsHeartbeatInterval)
        wsHeartbeatInterval = null
      }
      scheduleReconnect()
      resolve()
    }

    ws.onerror = (error) => {
      clearTimeout(connectionTimeout)
      console.error('WebSocket error:', error)
      ws?.close() // Ensure onclose is triggered
      isConnecting = false
      resolve()
    }

    ws.onmessage = async (event) => {
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
              const lowerLog = data.data.toLowerCase();
              if (lowerLog.includes('登录失败') || 
                  lowerLog.includes('timeouterror') || 
                  lowerLog.includes('连接失败') ||
                  lowerLog.includes('error - 执行失败')) {
                const { useRunnerStore } = await import('../core/runnerStore')
                useRunnerStore.getState().setStatus('failed', data.data.split(':').pop()?.trim())
              }
            }
            break
          case 'task_event':
            if (data.event === 'stopped' || data.event === 'finished') {
              const { useRunnerStore } = await import('../core/runnerStore')
              useRunnerStore.getState().setStatus('standby')
            }
            break
          case 'ping':
            if (ws?.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({ type: 'pong' }))
            }
            break
        }
      } catch (error) {}
    }
  })
  
  return connectionPromise
}

export const disconnectWebSocket = () => {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
  if (wsHeartbeatInterval) {
    clearInterval(wsHeartbeatInterval)
    wsHeartbeatInterval = null
  }
  if (ws) {
    ws.onclose = null
    ws.onerror = null
    ws.close()
    ws = null
  }
  isConnecting = false
  connectionPromise = null
}

export const initializeTauriEvents = async () => {
  if (!isTauri) return
  try {
    const { listen } = await import('@tauri-apps/api/event')
    listen<string>('py-log', (event) => useStore.getState().addLog(event.payload))
    listen<string>('py-error', (event) => useStore.getState().addLog(`[ERROR] ${event.payload}`))
    listen<number | null>('backend-terminated', (event) => {
      useStore.getState().setWsConnected(false)
      useStore.getState().setBackendReady(false)
      scheduleReconnect()
    })
  } catch (e) {}
}

export const initializeData = async () => {
  const store = useStore.getState()
  store.setDataLoading(true)
  try {
    const [status, health, points, config, logs] = await Promise.all([
      fetchStatus(),
      fetchHealth(),
      fetchPoints(),
      fetchConfig(),
      fetchRecentLogs(),
    ])
    store.setTaskStatus(status)
    store.setHealth(health)
    store.setPoints(points)
    store.setConfig(config)
    store.setLogs(logs)
    store.setBackendReady(true)
  } catch (error) {
    store.setBackendReady(false)
  } finally {
    store.setDataLoading(false)
  }
}

export const refreshData = async () => {
  try {
    const [status, health, points] = await Promise.all([
      fetchStatus(),
      fetchHealth(),
      fetchPoints(),
    ])
    useStore.getState().setTaskStatus(status)
    useStore.getState().setHealth(health)
    useStore.getState().setPoints(points)
  } catch (error) {}
}
