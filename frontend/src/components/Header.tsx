import {
  Bell,
  Moon,
  Sun,
  RefreshCw,
  Clock,
  Zap,
  Circle,
  Play,
  Square,
  Settings,
} from 'lucide-react'
import { useStore } from '../store'
import { refreshData, startTask, stopTask } from '../api'
import clsx from 'clsx'
import { useState, useEffect, useRef } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'

export default function Header() {
  const {
    taskStatus,
    health,
    darkMode,
    toggleDarkMode,
    sidebarCollapsed,
    lastDataUpdate,
    wsConnected,
    backendReady,
  } = useStore()

  const [isRefreshing, setIsRefreshing] = useState(false)
  const [isStarting, setIsStarting] = useState(false)
  const [isStopping, setIsStopping] = useState(false)
  const [, setTick] = useState(0)
  const navigate = useNavigate()
  const location = useLocation()
  const prevRunningRef = useRef(taskStatus?.is_running)

  useEffect(() => {
    const interval = setInterval(() => {
      setTick((t) => t + 1)
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (prevRunningRef.current && !taskStatus?.is_running) {
      refreshData()
    }
    prevRunningRef.current = taskStatus?.is_running
  }, [taskStatus?.is_running])

  const isRunning = taskStatus?.is_running
  const overallHealth = health?.overall || 'unknown'

  const handleRefresh = async () => {
    setIsRefreshing(true)
    await refreshData()
    setTimeout(() => setIsRefreshing(false), 500)
  }

  const handleStart = async () => {
    setIsStarting(true)
    try {
      await startTask({})
    } catch (error) {
      console.error('Failed to start task:', error)
    } finally {
      setTimeout(() => setIsStarting(false), 300)
    }
  }

  const handleStop = async () => {
    setIsStopping(true)
    try {
      await stopTask()
    } catch (error) {
      console.error('Failed to stop task:', error)
    } finally {
      setTimeout(() => setIsStopping(false), 300)
    }
  }

  const healthColorsDark: Record<string, string> = {
    healthy: 'text-success-400',
    warning: 'text-warning-400',
    error: 'text-danger-400',
    unknown: 'text-dark-400',
  }

  const healthColorsLight: Record<string, string> = {
    healthy: 'text-success-600',
    warning: 'text-warning-600',
    error: 'text-danger-600',
    unknown: 'text-gray-400',
  }

  const healthColors = darkMode ? healthColorsDark : healthColorsLight

  const formatLastUpdate = (time: string | null) => {
    if (!time) return '未更新'
    const date = new Date(time)
    const now = new Date()
    const diff = Math.floor((now.getTime() - date.getTime()) / 1000)

    if (diff < 5) return '刚刚'
    if (diff < 60) return `${diff}秒前`
    if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }

  const formatRuntime = (seconds: number) => {
    if (seconds < 60) return `${seconds}秒`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}分${seconds % 60}秒`
    const hours = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    return `${hours}时${mins}分`
  }

  return (
    <header
      data-tauri-drag-region
      className={clsx(
        'h-14 backdrop-blur-xl border-b flex items-center justify-between px-5 sticky top-0 z-40 transition-all duration-300',
        sidebarCollapsed ? 'ml-16' : 'ml-60',
        darkMode ? 'bg-surface/60 border-border' : 'bg-white/60 border-border-light',
        isRunning && 'border-b-2 border-b-success-500/30'
      )}
    >
      <div className="flex items-center gap-5">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-cyan-500 flex items-center justify-center shadow-glow-primary">
            <Zap size={16} className="text-dark-900" />
          </div>
          <div className="flex flex-col">
            <span
              className={clsx(
                'text-sm font-semibold',
                darkMode ? 'text-foreground' : 'text-foreground-light'
              )}
            >
              MS Rewards
            </span>
            <span className={clsx('text-[10px]', darkMode ? 'text-muted' : 'text-muted-foreground')}>
              v1.0.0
            </span>
          </div>
        </div>

        <div
          className={clsx('w-px h-6', darkMode ? 'bg-border' : 'bg-border-light')}
        />

        <div className="flex items-center gap-2.5">
          <div
            className={clsx(
              'w-2.5 h-2.5 rounded-full transition-all duration-300',
              wsConnected && backendReady
                ? 'bg-success-400 shadow-glow-success animate-pulse-soft'
                : darkMode
                  ? 'bg-muted'
                  : 'bg-muted-foreground'
            )}
          />
          <span
            className={clsx(
              'text-sm font-medium transition-colors',
              wsConnected && backendReady
                ? 'text-success-400'
                : darkMode
                  ? 'text-muted'
                  : 'text-muted-foreground'
            )}
          >
            {wsConnected && backendReady ? '已连接' : '离线'}
          </span>
        </div>

        {isRunning && taskStatus && (
          <div className="flex items-center gap-4 animate-fade-in">
            <span
              className={clsx(
                'text-sm max-w-[200px] truncate',
                darkMode ? 'text-muted' : 'text-muted-foreground'
              )}
            >
              {taskStatus.current_operation}
            </span>
            <div className="flex items-center gap-2">
              <div
                className={clsx(
                  'w-20 h-1.5 rounded-full overflow-hidden',
                  darkMode ? 'bg-surface-elevated' : 'bg-light-300'
                )}
              >
                <div
                  className="h-full bg-gradient-to-r from-primary-500 to-cyan-500 rounded-full transition-all duration-300"
                  style={{
                    width: `${(taskStatus.progress / Math.max(taskStatus.total_steps, 1)) * 100}%`,
                  }}
                />
              </div>
              <span
                className={clsx(
                  'text-xs font-mono',
                  darkMode ? 'text-muted' : 'text-muted-foreground'
                )}
              >
                {taskStatus.progress}/{taskStatus.total_steps}
              </span>
            </div>
            {taskStatus.elapsed_seconds > 0 && (
              <div
                className={clsx(
                  'flex items-center gap-1 text-xs',
                  darkMode ? 'text-muted' : 'text-muted-foreground'
                )}
              >
                <Clock size={12} />
                <span>{formatRuntime(taskStatus.elapsed_seconds)}</span>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="flex items-center gap-3">
        <div
          className={clsx(
            'flex items-center gap-2 text-xs',
            darkMode ? 'text-muted' : 'text-muted-foreground'
          )}
        >
          <Clock size={12} />
          <span>{formatLastUpdate(lastDataUpdate)}</span>
        </div>

        <div className={clsx('w-px h-5', darkMode ? 'bg-border' : 'bg-border-light')} />

        {overallHealth !== 'healthy' && overallHealth !== 'unknown' && (
          <div
            className={clsx(
              'flex items-center gap-1.5 px-2 py-1 rounded-lg',
              overallHealth === 'error' ? 'bg-danger-500/10' : 'bg-warning-500/10'
            )}
          >
            <Circle
              size={8}
              className={clsx('fill-current', healthColors[overallHealth])}
            />
            <span
              className={clsx(
                'text-xs',
                darkMode ? 'text-muted' : 'text-muted-foreground'
              )}
            >
              {overallHealth === 'error' ? '异常' : '警告'}
            </span>
          </div>
        )}

        <button
          onClick={isRunning ? handleStop : handleStart}
          disabled={!backendReady || isStarting || isStopping}
          className={clsx(
            'flex items-center gap-2 px-4 py-2 rounded-xl font-medium text-sm transition-all duration-300',
            isRunning
              ? 'bg-danger-500 text-white hover:bg-danger-600 shadow-glow-danger'
              : 'bg-gradient-to-r from-primary-500 to-cyan-500 text-dark-900 hover:shadow-glow-primary',
            (isStarting || isStopping) && 'opacity-70 cursor-wait',
            !backendReady && 'opacity-50 cursor-not-allowed'
          )}
        >
          {isStarting ? (
            <>
              <RefreshCw size={16} className="animate-spin" />
              <span>启动中...</span>
            </>
          ) : isStopping ? (
            <>
              <RefreshCw size={16} className="animate-spin" />
              <span>停止中...</span>
            </>
          ) : isRunning ? (
            <>
              <Square size={16} />
              <span>停止任务</span>
            </>
          ) : (
            <>
              <Play size={16} />
              <span>启动任务</span>
            </>
          )}
        </button>

        <div className={clsx('w-px h-5', darkMode ? 'bg-border' : 'bg-border-light')} />

        <button
          onClick={handleRefresh}
          className={clsx(
            'p-2 rounded-xl transition-all duration-200',
            darkMode
              ? 'text-muted hover:text-foreground hover:bg-surface'
              : 'text-muted-foreground hover:text-foreground-light hover:bg-light-200'
          )}
          title="刷新数据"
        >
          <RefreshCw size={16} className={clsx(isRefreshing && 'animate-spin')} />
        </button>

        <button
          className={clsx(
            'relative p-2 rounded-xl transition-all duration-200',
            darkMode
              ? 'text-muted hover:text-foreground hover:bg-surface'
              : 'text-muted-foreground hover:text-foreground-light hover:bg-light-200'
          )}
        >
          <Bell size={16} />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-danger-400 rounded-full" />
        </button>

        <button
          onClick={toggleDarkMode}
          className={clsx(
            'p-2 rounded-xl transition-all duration-200',
            darkMode
              ? 'text-muted hover:text-foreground hover:bg-surface'
              : 'text-muted-foreground hover:text-foreground-light hover:bg-light-200'
          )}
          title={darkMode ? '切换到亮色模式' : '切换到暗色模式'}
        >
          {darkMode ? <Sun size={16} /> : <Moon size={16} />}
        </button>

        <button
          onClick={() => navigate('/settings')}
          className={clsx(
            'p-2 rounded-xl transition-all duration-200',
            location.pathname === '/settings'
              ? darkMode
                ? 'bg-surface text-foreground'
                : 'bg-light-200 text-foreground-light'
              : darkMode
                ? 'text-muted hover:text-foreground hover:bg-surface'
                : 'text-muted-foreground hover:text-foreground-light hover:bg-light-200'
          )}
          title="设置"
        >
          <Settings size={16} />
        </button>
      </div>
    </header>
  )
}
