import { 
  Bell, 
  Moon, 
  Sun,
  RefreshCw,
  Clock,
  Zap,
  Circle
} from 'lucide-react'
import { useStore } from '../store'
import { refreshData } from '../api'
import clsx from 'clsx'
import { useState, useEffect } from 'react'

export default function Header() {
  const { 
    taskStatus, 
    health, 
    darkMode, 
    toggleDarkMode,
    sidebarCollapsed,
    lastDataUpdate,
    wsConnected
  } = useStore()

  const [isRefreshing, setIsRefreshing] = useState(false)
  const [, setTick] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setTick(t => t + 1)
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  const isRunning = taskStatus?.is_running
  const overallHealth = health?.overall || 'unknown'

  const handleRefresh = async () => {
    setIsRefreshing(true)
    await refreshData()
    setTimeout(() => setIsRefreshing(false), 500)
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

  return (
    <header className={clsx(
      'h-14 backdrop-blur-md border-b flex items-center justify-between px-5 sticky top-0 z-40 transition-all duration-300',
      sidebarCollapsed ? 'ml-16' : 'ml-60',
      darkMode 
        ? 'bg-surface-300/80 border-dark-600/50' 
        : 'bg-white/80 border-gray-200'
    )}>
      <div className="flex items-center gap-5">
        <div className="flex items-center gap-2.5">
          <div className={clsx(
            'w-2 h-2 rounded-full transition-all duration-300',
            isRunning 
              ? 'bg-success-400 shadow-lg shadow-success-400/50 animate-pulse-soft' 
              : darkMode ? 'bg-dark-500' : 'bg-gray-400'
          )} />
          <span className={clsx(
            'text-sm font-medium transition-colors',
            isRunning ? 'text-success-400' : darkMode ? 'text-dark-400' : 'text-gray-500'
          )}>
            {isRunning ? '运行中' : '空闲'}
          </span>
        </div>

        {isRunning && taskStatus && (
          <div className="flex items-center gap-4 animate-fade-in">
            <span className={clsx(
              'text-sm max-w-[200px] truncate',
              darkMode ? 'text-dark-300' : 'text-gray-600'
            )}>
              {taskStatus.current_operation}
            </span>
            <div className="flex items-center gap-2">
              <div className={clsx(
                'w-20 h-1.5 rounded-full overflow-hidden',
                darkMode ? 'bg-dark-700' : 'bg-gray-200'
              )}>
                <div 
                  className="h-full bg-gradient-to-r from-primary-500 to-cyan-500 rounded-full transition-all duration-300"
                  style={{ width: `${(taskStatus.progress / taskStatus.total_steps) * 100}%` }}
                />
              </div>
              <span className={clsx(
                'text-xs font-mono',
                darkMode ? 'text-dark-400' : 'text-gray-500'
              )}>
                {taskStatus.progress}/{taskStatus.total_steps}
              </span>
            </div>
          </div>
        )}
      </div>

      <div className="flex items-center gap-4">
        <div className={clsx(
          'flex items-center gap-2 text-xs',
          darkMode ? 'text-dark-400' : 'text-gray-500'
        )}>
          <Clock size={12} />
          <span>{formatLastUpdate(lastDataUpdate)}</span>
        </div>

        <div className={clsx(
          'w-px h-5',
          darkMode ? 'bg-dark-600/50' : 'bg-gray-200'
        )} />

        <div className="flex items-center gap-2">
          <div className={clsx(
            'flex items-center gap-1.5 px-2 py-1 rounded-md',
            wsConnected 
              ? 'bg-success-500/10' 
              : darkMode ? 'bg-dark-600/30' : 'bg-gray-100'
          )}>
            <Circle size={8} className={wsConnected ? 'text-success-400 fill-success-400' : darkMode ? 'text-dark-500' : 'text-gray-400'} />
            <span className={clsx(
              'text-xs',
              darkMode ? 'text-dark-300' : 'text-gray-600'
            )}>
              {wsConnected ? '已连接' : '离线'}
            </span>
          </div>
          
          {overallHealth !== 'healthy' && overallHealth !== 'unknown' && (
            <div className={clsx(
              'flex items-center gap-1.5 px-2 py-1 rounded-md',
              overallHealth === 'error' ? 'bg-danger-500/10' : 'bg-warning-500/10'
            )}>
              <Circle size={8} className={clsx(
                'fill-current',
                healthColors[overallHealth]
              )} />
              <span className={clsx(
                'text-xs',
                darkMode ? 'text-dark-300' : 'text-gray-600'
              )}>
                {overallHealth === 'error' ? '异常' : '警告'}
              </span>
            </div>
          )}
        </div>

        <div className={clsx(
          'w-px h-5',
          darkMode ? 'bg-dark-600/50' : 'bg-gray-200'
        )} />

        <button 
          onClick={handleRefresh}
          className={clsx(
            'p-2 rounded-lg transition-all duration-200',
            darkMode 
              ? 'text-dark-400 hover:text-dark-100 hover:bg-dark-600/50' 
              : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'
          )}
          title="刷新数据"
        >
          <RefreshCw size={16} className={clsx(isRefreshing && 'animate-spin')} />
        </button>

        <button className={clsx(
          'relative p-2 rounded-lg transition-all duration-200',
          darkMode 
            ? 'text-dark-400 hover:text-dark-100 hover:bg-dark-600/50' 
            : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'
        )}>
          <Bell size={16} />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-danger-400 rounded-full" />
        </button>

        <button 
          onClick={toggleDarkMode}
          className={clsx(
            'p-2 rounded-lg transition-all duration-200',
            darkMode 
              ? 'text-dark-400 hover:text-dark-100 hover:bg-dark-600/50' 
              : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'
          )}
          title={darkMode ? '切换到亮色模式' : '切换到暗色模式'}
        >
          {darkMode ? <Sun size={16} /> : <Moon size={16} />}
        </button>

        <div className={clsx(
          'w-px h-5',
          darkMode ? 'bg-dark-600/50' : 'bg-gray-200'
        )} />

        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-primary-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-primary-500/20">
            <Zap size={14} className="text-dark-900" />
          </div>
        </div>
      </div>
    </header>
  )
}
