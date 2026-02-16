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
  onClick
}: {
  level: 'ERROR' | 'WARNING' | 'INFO' | 'DEBUG'
  count: number
  active: boolean
  onClick: () => void
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
    danger: active ? 'bg-danger-500/15 text-danger-400 border-danger-500/30' : 'text-dark-500 border-dark-600',
    warning: active ? 'bg-warning-500/15 text-warning-400 border-warning-500/30' : 'text-dark-500 border-dark-600',
    primary: active ? 'bg-primary-500/15 text-primary-400 border-primary-500/30' : 'text-dark-500 border-dark-600',
    neutral: active ? 'bg-dark-600/50 text-dark-300 border-dark-500' : 'text-dark-500 border-dark-600',
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
        active ? 'bg-dark-700/50' : 'bg-dark-700/30'
      )}>
        {count}
      </span>
    </button>
  )
}

export default function Logs() {
  const { logs, setLogs } = useStore()
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
      case 'DEBUG': return 'text-dark-500'
      default: return 'text-dark-200'
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
          <h1 className="text-xl font-bold text-dark-100">日志查看</h1>
          <p className="text-sm text-dark-400 mt-1">实时查看应用程序运行日志</p>
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
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-dark-400" />
            <input
              type="text"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              placeholder="搜索日志内容..."
              className="input pl-10"
            />
          </div>

          <div className="flex items-center gap-2">
            <Filter size={16} className="text-dark-400" />
            {(['ERROR', 'WARNING', 'INFO', 'DEBUG'] as const).map((level) => (
              <LevelButton
                key={level}
                level={level}
                count={levelStats[level]}
                active={levelFilter.includes(level)}
                onClick={() => toggleLevel(level)}
              />
            ))}
          </div>
        </div>

        <div className="flex items-center justify-between pb-4 border-b border-dark-600/50">
          <div className="flex items-center gap-4 text-sm text-dark-400">
            <span>显示 <span className="text-dark-200 font-medium">{filteredLogs.length}</span> / {logs.length} 条</span>
          </div>
          <label className="flex items-center gap-2 text-sm text-dark-400 cursor-pointer">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
              className="w-4 h-4 rounded border-dark-500 bg-dark-700 text-primary-500 focus:ring-primary-500"
            />
            自动滚动到底部
          </label>
        </div>
      </div>

      <div 
        ref={logContainerRef}
        className="flex-1 card overflow-auto bg-surface-400/50"
      >
        {filteredLogs.length > 0 ? (
          <div className="divide-y divide-dark-600/30">
            {filteredLogs.map((line, index) => (
              <div 
                key={index} 
                className={clsx(
                  'font-mono text-xs py-2 px-4 transition-colors duration-150 hover:bg-dark-600/30',
                  getLogClass(line)
                )}
              >
                {line}
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-dark-400">
            <FileText size={40} className="mb-3 opacity-50" />
            <p className="text-sm">暂无日志</p>
            <p className="text-xs text-dark-500 mt-1">启动任务后将显示实时日志</p>
          </div>
        )}
      </div>
    </div>
  )
}
