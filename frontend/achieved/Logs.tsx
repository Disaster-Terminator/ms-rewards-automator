import { useEffect, useRef, useState } from 'react'
import { 
  FileText, 
  Search, 
  RefreshCw,
  Download,
  Trash2,
  AlertTriangle,
  Info,
  AlertCircle,
  Bug,
  Filter
} from 'lucide-react'
import { useStore } from '../store'
import { fetchRecentLogs } from '../api'
import clsx from 'clsx'

function LevelButton({
  level,
  count,
  active,
  onClick,
  darkMode = true
}: {
  level: 'ERROR' | 'WARNING' | 'INFO' | 'DEBUG'
  count: number
  active: boolean
  onClick: () => void
  darkMode?: boolean
}) {
  const levelConfig = {
    ERROR: { icon: AlertCircle, color: 'danger', label: '错误' },
    WARNING: { icon: AlertTriangle, color: 'warning', label: '警告' },
    INFO: { icon: Info, color: 'primary', label: '信息' },
    DEBUG: { icon: Bug, color: 'neutral', label: '调试' },
  }

  const config = levelConfig[level]
  const Icon = config.icon

  const colorClasses = {
    danger: active ? 'bg-danger-500/15 text-danger-400 border-danger-500/30' : darkMode ? 'text-dark-500 border-dark-600' : 'text-light-500 border-light-300',
    warning: active ? 'bg-warning-500/15 text-warning-400 border-warning-500/30' : darkMode ? 'text-dark-500 border-dark-600' : 'text-light-500 border-light-300',
    primary: active ? 'bg-primary-500/15 text-primary-400 border-primary-500/30' : darkMode ? 'text-dark-500 border-dark-600' : 'text-light-500 border-light-300',
    neutral: active ? (darkMode ? 'bg-dark-600/50 text-dark-300 border-dark-500' : 'bg-light-200 text-light-600 border-light-300') : (darkMode ? 'text-dark-500 border-dark-600' : 'text-light-500 border-light-300'),
  }

  return (
    <button
      onClick={onClick}
      className={clsx(
        'flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium border transition-all duration-200',
        colorClasses[config.color as keyof typeof colorClasses]
      )}
    >
      <Icon size={14} />
      <span>{config.label}</span>
      <span className={clsx(
        'px-1.5 py-0.5 rounded text-xs',
        darkMode ? (active ? 'bg-dark-700/50' : 'bg-dark-700/30') : (active ? 'bg-light-300' : 'bg-light-200')
      )}>
        {count}
      </span>
    </button>
  )
}

export default function Logs() {
  const { logs, setLogs, darkMode } = useStore()
  const [filter, setFilter] = useState('')
  const [levelFilter, setLevelFilter] = useState<string[]>(['INFO', 'WARNING', 'ERROR', 'DEBUG'])
  const [autoScroll, setAutoScroll] = useState(true)
  const logContainerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    loadLogs()
  }, [])

  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight
    }
  }, [logs, autoScroll])

  const loadLogs = async () => {
    try {
      const data = await fetchRecentLogs(500)
      setLogs(data)
    } catch (error) {
      console.error('Failed to load logs:', error)
    }
  }

  const getLogLevel = (line: string): string => {
    if (line.includes('ERROR') || line.includes('CRITICAL')) return 'ERROR'
    if (line.includes('WARNING') || line.includes('WARN')) return 'WARNING'
    if (line.includes('DEBUG')) return 'DEBUG'
    return 'INFO'
  }

  const filteredLogs = logs.filter((line) => {
    const level = getLogLevel(line)
    if (!levelFilter.includes(level)) return false
    if (filter && !line.toLowerCase().includes(filter.toLowerCase())) return false
    return true
  })

  const getLogClass = (line: string): string => {
    const level = getLogLevel(line)
    switch (level) {
      case 'ERROR': return 'text-danger-400 bg-danger-500/5'
      case 'WARNING': return 'text-warning-400 bg-warning-500/5'
      case 'DEBUG': return darkMode ? 'text-dark-500' : 'text-light-500'
      default: return darkMode ? 'text-dark-200' : 'text-light-700'
    }
  }

  const exportLogs = () => {
    const content = logs.join('\n')
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `logs_${new Date().toISOString().slice(0, 10)}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  const clearLogs = () => {
    setLogs([])
  }

  const toggleLevel = (level: string) => {
    if (levelFilter.includes(level)) {
      setLevelFilter(levelFilter.filter((l) => l !== level))
    } else {
      setLevelFilter([...levelFilter, level])
    }
  }

  const levelStats = {
    ERROR: logs.filter((l) => getLogLevel(l) === 'ERROR').length,
    WARNING: logs.filter((l) => getLogLevel(l) === 'WARNING').length,
    INFO: logs.filter((l) => getLogLevel(l) === 'INFO').length,
    DEBUG: logs.filter((l) => getLogLevel(l) === 'DEBUG').length,
  }

  return (
    <div className="space-y-6 h-[calc(100vh-8rem)] flex flex-col animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">日志查看</h1>
          <p className="page-subtitle">实时查看应用程序运行日志</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={loadLogs} className="btn-secondary">
            <RefreshCw size={16} />
            刷新
          </button>
          <button onClick={exportLogs} className="btn-secondary">
            <Download size={16} />
            导出
          </button>
          <button onClick={clearLogs} className="btn-danger">
            <Trash2 size={16} />
            清空
          </button>
        </div>
      </div>

      <div className="card">
        <div className="flex items-center gap-4 mb-4">
          <div className="flex-1 relative">
            <Search size={16} className={clsx('absolute left-3 top-1/2 -translate-y-1/2', darkMode ? 'text-dark-400' : 'text-light-500')} />
            <input
              type="text"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              placeholder="搜索日志内容..."
              className="input pl-10"
            />
          </div>

          <div className="flex items-center gap-2">
            <Filter size={16} className={darkMode ? 'text-dark-400' : 'text-light-500'} />
            {(['ERROR', 'WARNING', 'INFO', 'DEBUG'] as const).map((level) => (
              <LevelButton
                key={level}
                level={level}
                count={levelStats[level]}
                active={levelFilter.includes(level)}
                onClick={() => toggleLevel(level)}
                darkMode={darkMode}
              />
            ))}
          </div>
        </div>

        <div className={clsx('flex items-center justify-between pb-4 border-b', darkMode ? 'border-dark-600/50' : 'border-light-300')}>
          <div className={clsx('flex items-center gap-4 text-sm', darkMode ? 'text-dark-400' : 'text-light-600')}>
            <span>显示 <span className={clsx('font-medium', darkMode ? 'text-dark-200' : 'text-light-800')}>{filteredLogs.length}</span> / {logs.length} 条</span>
          </div>
          <label className={clsx('flex items-center gap-2 text-sm cursor-pointer', darkMode ? 'text-dark-400' : 'text-light-600')}>
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
              className="w-4 h-4 rounded text-primary-500 focus:ring-primary-500"
            />
            自动滚动到底部
          </label>
        </div>
      </div>

      <div 
        ref={logContainerRef}
        className={clsx('flex-1 card overflow-auto', darkMode ? 'bg-surface-400/50' : 'bg-light-50')}
      >
        {filteredLogs.length > 0 ? (
          <div className={clsx('divide-y', darkMode ? 'divide-dark-600/30' : 'divide-light-200')}>
            {filteredLogs.map((line, index) => (
              <div 
                key={index} 
                className={clsx(
                  'font-mono text-xs py-2 px-4 transition-colors duration-150',
                  darkMode ? 'hover:bg-dark-600/30' : 'hover:bg-light-200',
                  getLogClass(line)
                )}
              >
                {line}
              </div>
            ))}
          </div>
        ) : (
          <div className={clsx('flex flex-col items-center justify-center h-full', darkMode ? 'text-dark-400' : 'text-light-500')}>
            <FileText size={40} className="mb-3 opacity-50" />
            <p className="text-sm">暂无日志</p>
            <p className={clsx('text-xs mt-1', darkMode ? 'text-dark-500' : 'text-light-500')}>启动任务后将显示实时日志</p>
          </div>
        )}
      </div>
    </div>
  )
}
