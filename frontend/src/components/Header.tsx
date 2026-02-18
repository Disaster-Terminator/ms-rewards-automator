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

  const formatRuntime = (seconds: number) => {
    const rounded = Math.round(seconds * 10) / 10
    if (rounded < 60) return `${rounded}秒`
    if (rounded < 3600) return `${Math.floor(rounded / 60)}分${Math.round(rounded % 60)}秒`
    const hours = Math.floor(rounded / 3600)
    const mins = Math.floor((rounded % 3600) / 60)
    return `${hours}时${mins}分`
  }

  return (
    <header
      data-tauri-drag-region
      className={clsx(
        'h-12 backdrop-blur-xl flex items-center justify-between px-4 sticky top-0 z-40 transition-all duration-300',
        darkMode ? 'bg-white/[0.02]' : 'bg-white/40',
        isRunning && 'border-b border-success-500/20'
      )}
    >
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-primary-500 to-cyan-500 flex items-center justify-center shadow-glow-primary">
            <Zap size={14} className="text-dark-900" />
          </div>
          <div className="flex flex-col">
            <span
              className={clsx(
                'text-xs font-semibold',
                darkMode ? 'text-foreground' : 'text-foreground-light'
              )}
            >
              MS Rewards
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div
            className={clsx(
              'w-2 h-2 rounded-full transition-all duration-300',
              wsConnected && backendReady
                ? 'bg-success-400 shadow-glow-success'
                : darkMode
                  ? 'bg-muted'
                  : 'bg-muted-foreground'
            )}
          />
          <span
            className={clsx(
              'text-xs font-medium transition-colors',
              wsConnected && backendReady
                ? 'text-success-400'
                : darkMode
                  ? 'text-muted'
                  : 'text-muted-foreground'
            )}
          >
            {wsConnected && backendReady ? '在线' : '离线'}
          </span>
        </div>

        {isRunning && taskStatus && (
          <div className="flex items-center gap-3 animate-fade-in">
            <div className="flex items-center gap-2">
              <div
                className={clsx(
                  'w-16 h-1 rounded-full overflow-hidden',
                  darkMode ? 'bg-white/10' : 'bg-black/10'
                )}
              >
                <div
                  className="h-full bg-gradient-to-r from-success-500 to-cyan-500 rounded-full transition-all duration-300"
                  style={{
                    width: `${(taskStatus.progress / Math.max(taskStatus.total_steps, 1)) * 100}%`,
                  }}
                />
              </div>
              <span
                className={clsx(
                  'text-[10px] font-mono',
                  darkMode ? 'text-muted' : 'text-muted-foreground'
                )}
              >
                {taskStatus.progress}/{taskStatus.total_steps}
              </span>
            </div>
            {taskStatus.elapsed_seconds > 0 && (
              <div
                className={clsx(
                  'flex items-center gap-1 text-[10px]',
                  darkMode ? 'text-muted' : 'text-muted-foreground'
                )}
              >
                <Clock size={10} />
                <span>{formatRuntime(taskStatus.elapsed_seconds)}</span>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="flex items-center gap-2">
        {overallHealth !== 'healthy' && overallHealth !== 'unknown' && (
          <div
            className={clsx(
              'flex items-center gap-1.5 px-2 py-0.5 rounded-lg',
              overallHealth === 'error' ? 'bg-danger-500/10' : 'bg-warning-500/10'
            )}
          >
            <Circle
              size={6}
              className={clsx('fill-current', healthColors[overallHealth])}
            />
            <span
              className={clsx(
                'text-[10px]',
                darkMode ? 'text-muted' : 'text-muted-foreground'
              )}
            >
              {overallHealth === 'error' ? '异常' : '警告'}
            </span>
          </div>
        )}

        <button
          onClick={isRunning ? handleStop : handleStart}
          disabled={isRunning ? isStopping : (!backendReady || isStarting)}
          className={clsx(
            'flex items-center gap-1.5 px-2.5 py-1 rounded-lg font-medium text-xs transition-all duration-300',
            isRunning
              ? 'bg-danger-500 text-white hover:bg-danger-600'
              : 'bg-gradient-to-r from-primary-500 to-cyan-500 text-dark-900',
            (isStarting || isStopping) && 'opacity-70 cursor-wait',
            !backendReady && 'opacity-50 cursor-not-allowed'
          )}
        >
          {isStarting ? (
            <>
              <RefreshCw size={12} className="animate-spin flex-shrink-0" />
              <span>启动中</span>
            </>
          ) : isStopping ? (
            <>
              <RefreshCw size={12} className="animate-spin flex-shrink-0" />
              <span>停止中</span>
            </>
          ) : isRunning ? (
            <>
              <Square size={12} className="flex-shrink-0" />
              <span>停止</span>
            </>
          ) : (
            <>
              <Play size={12} className="flex-shrink-0" />
              <span>启动</span>
            </>
          )}
        </button>

        <button
          onClick={handleRefresh}
          className={clsx(
            'p-1.5 rounded-lg transition-all duration-200',
            darkMode
              ? 'text-muted hover:text-foreground hover:bg-white/5'
              : 'text-muted-foreground hover:text-foreground-light hover:bg-black/5'
          )}
          title="刷新数据"
        >
          <RefreshCw size={14} className={clsx(isRefreshing && 'animate-spin')} />
        </button>

        <button
          className={clsx(
            'relative p-1.5 rounded-lg transition-all duration-200',
            darkMode
              ? 'text-muted hover:text-foreground hover:bg-white/5'
              : 'text-muted-foreground hover:text-foreground-light hover:bg-black/5'
          )}
        >
          <Bell size={14} />
          <span className="absolute top-1 right-1 w-1 h-1 bg-danger-400 rounded-full" />
        </button>

        <button
          onClick={toggleDarkMode}
          className={clsx(
            'p-1.5 rounded-lg transition-all duration-200',
            darkMode
              ? 'text-muted hover:text-foreground hover:bg-white/5'
              : 'text-muted-foreground hover:text-foreground-light hover:bg-black/5'
          )}
          title={darkMode ? '切换到亮色模式' : '切换到暗色模式'}
        >
          {darkMode ? <Sun size={14} /> : <Moon size={14} />}
        </button>

        <button
          onClick={() => navigate('/config')}
          className={clsx(
            'p-1.5 rounded-lg transition-all duration-200',
            location.pathname === '/config'
              ? darkMode
                ? 'bg-white/10 text-foreground'
                : 'bg-black/10 text-foreground-light'
              : darkMode
                ? 'text-muted hover:text-foreground hover:bg-white/5'
                : 'text-muted-foreground hover:text-foreground-light hover:bg-black/5'
          )}
          title="设置"
        >
          <Settings size={14} />
        </button>
      </div>
    </header>
  )
}
