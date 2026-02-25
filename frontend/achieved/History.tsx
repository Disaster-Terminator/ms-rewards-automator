import { useEffect, useState } from 'react'
import { 
  History as HistoryIcon, 
  Calendar,
  Coins,
  Monitor,
  Smartphone,
  Clock,
  AlertTriangle,
  TrendingUp,
  BarChart3,
  RefreshCw
} from 'lucide-react'
import { useStore } from '../store'
import { fetchHistory } from '../api'
import clsx from 'clsx'

function StatCard({
  icon: Icon,
  label,
  value,
  subValue,
  color = 'primary',
  darkMode = true
}: {
  icon: React.ElementType
  label: string
  value: string | number
  subValue?: string
  color?: 'primary' | 'success' | 'warning' | 'danger' | 'cyan'
  darkMode?: boolean
}) {
  const colorClasses = {
    primary: { icon: 'text-primary-400', gradient: 'from-primary-500/20 to-transparent', value: 'text-primary-400' },
    success: { icon: 'text-success-400', gradient: 'from-success-500/20 to-transparent', value: 'text-success-400' },
    warning: { icon: 'text-warning-400', gradient: 'from-warning-500/20 to-transparent', value: 'text-warning-400' },
    danger: { icon: 'text-danger-400', gradient: 'from-danger-500/20 to-transparent', value: 'text-danger-400' },
    cyan: { icon: 'text-cyan-400', gradient: 'from-cyan-500/20 to-transparent', value: 'text-cyan-400' },
  }

  return (
    <div className={clsx(
      'stat-card',
      `bg-gradient-to-br ${colorClasses[color].gradient}`
    )}>
      <div className="flex items-center gap-2 mb-3">
        <Icon size={18} className={colorClasses[color].icon} />
        <span className={clsx('text-sm', darkMode ? 'text-dark-400' : 'text-light-600')}>{label}</span>
      </div>
      <div className={clsx('stat-value', colorClasses[color].value)}>
        {value}
      </div>
      {subValue && <div className="stat-label">{subValue}</div>}
    </div>
  )
}

function ChartBar({
  date,
  points,
  maxPoints,
  delay,
  darkMode = true
}: {
  date: string
  points: number
  maxPoints: number
  delay: number
  darkMode?: boolean
}) {
  const height = maxPoints > 0 ? (points / maxPoints) * 140 : 0
  
  return (
    <div className="flex-1 flex flex-col items-center gap-2 group">
      <div className="relative w-full flex justify-center">
        <div 
          className="w-full max-w-[24px] bg-gradient-to-t from-primary-500 to-primary-400 rounded-t-md transition-all duration-300 group-hover:from-primary-400 group-hover:to-cyan-400 cursor-pointer"
          style={{ 
            height: points > 0 ? Math.max(height, 4) : 0,
            animationDelay: `${delay}ms`
          }}
        >
          <div className={clsx(
            'absolute -top-8 left-1/2 -translate-x-1/2 px-2 py-1 rounded text-xs opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none',
            darkMode ? 'bg-dark-700 text-dark-100' : 'bg-light-800 text-light-100'
          )}>
            +{points} 积分
          </div>
        </div>
      </div>
      <span className={clsx('text-xs transform -rotate-45 origin-left whitespace-nowrap', darkMode ? 'text-dark-500' : 'text-light-500')}>
        {date}
      </span>
    </div>
  )
}

function HistoryRow({
  item,
  index,
  darkMode = true
}: {
  item: {
    timestamp: string
    points_gained: number
    desktop_searches: number
    mobile_searches: number
    errors: number
    duration_seconds: number
  }
  index: number
  darkMode?: boolean
}) {
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.round(seconds % 60)
    return `${mins}分${secs}秒`
  }

  return (
    <tr 
      className={clsx(
        'border-b transition-colors duration-200 animate-fade-in',
        darkMode ? 'border-dark-600/30 hover:bg-surface-400/50' : 'border-light-300 hover:bg-light-100'
      )}
      style={{ animationDelay: `${index * 30}ms` }}
    >
      <td className="py-3 px-4">
        <div className="flex items-center gap-2">
          <Calendar size={14} className={darkMode ? 'text-dark-400' : 'text-light-500'} />
          <span className={clsx('text-sm', darkMode ? 'text-dark-200' : 'text-light-700')}>{formatDate(item.timestamp)}</span>
        </div>
      </td>
      <td className="py-3 px-4">
        <span className={clsx(
          'font-medium text-sm',
          item.points_gained > 0 ? 'text-success-400' : darkMode ? 'text-dark-500' : 'text-light-500'
        )}>
          {item.points_gained > 0 ? `+${item.points_gained}` : '0'}
        </span>
      </td>
      <td className="py-3 px-4">
        <div className="flex items-center gap-2">
          <Monitor size={14} className="text-success-400" />
          <span className={clsx('text-sm', darkMode ? 'text-dark-200' : 'text-light-700')}>{item.desktop_searches}</span>
        </div>
      </td>
      <td className="py-3 px-4">
        <div className="flex items-center gap-2">
          <Smartphone size={14} className="text-warning-400" />
          <span className={clsx('text-sm', darkMode ? 'text-dark-200' : 'text-light-700')}>{item.mobile_searches}</span>
        </div>
      </td>
      <td className="py-3 px-4">
        <div className="flex items-center gap-2">
          <Clock size={14} className={darkMode ? 'text-dark-400' : 'text-light-500'} />
          <span className={clsx('text-sm font-mono', darkMode ? 'text-dark-200' : 'text-light-700')}>{formatDuration(item.duration_seconds)}</span>
        </div>
      </td>
      <td className="py-3 px-4">
        <span className={clsx(
          'font-medium text-sm',
          item.errors > 0 ? 'text-danger-400' : darkMode ? 'text-dark-500' : 'text-light-500'
        )}>
          {item.errors}
        </span>
      </td>
    </tr>
  )
}

export default function History() {
  const { history, setHistory, darkMode } = useStore()
  const [loading, setLoading] = useState(false)
  const [days, setDays] = useState(7)

  useEffect(() => {
    loadHistory()
  }, [days])

  const loadHistory = async () => {
    setLoading(true)
    try {
      const data = await fetchHistory(days)
      setHistory(data)
    } catch (error) {
      console.error('Failed to load history:', error)
    } finally {
      setLoading(false)
    }
  }

  const totalPoints = history.reduce((sum, h) => sum + h.points_gained, 0)
  const totalSearches = history.reduce((sum, h) => sum + h.desktop_searches + h.mobile_searches, 0)
  const totalErrors = history.reduce((sum, h) => sum + h.errors, 0)
  const avgPoints = history.length > 0 ? Math.round(totalPoints / history.length) : 0

  const chartData = history.slice(0, 14).reverse().map((h) => ({
    date: new Date(h.timestamp).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }),
    points: h.points_gained,
    searches: h.desktop_searches + h.mobile_searches,
  }))

  const maxPoints = Math.max(...chartData.map((d) => d.points), 1)

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">历史记录</h1>
          <p className="page-subtitle">查看任务执行历史和积分统计</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={days}
            onChange={(e) => setDays(parseInt(e.target.value))}
            className="select w-36"
          >
            <option value={7}>最近 7 天</option>
            <option value={14}>最近 14 天</option>
            <option value={30}>最近 30 天</option>
          </select>
          <button onClick={loadHistory} className="btn-secondary">
            <RefreshCw size={16} className={clsx(loading && 'animate-spin')} />
            刷新
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          icon={Coins}
          label="总积分"
          value={`+${totalPoints.toLocaleString()}`}
          subValue={`过去 ${days} 天`}
          color="primary"
          darkMode={darkMode}
        />
        <StatCard
          icon={TrendingUp}
          label="日均积分"
          value={`+${avgPoints}`}
          subValue="平均每天"
          color="success"
          darkMode={darkMode}
        />
        <StatCard
          icon={BarChart3}
          label="总搜索"
          value={totalSearches.toLocaleString()}
          subValue="次搜索"
          color="cyan"
          darkMode={darkMode}
        />
        <StatCard
          icon={AlertTriangle}
          label="错误数"
          value={totalErrors}
          subValue="次错误"
          color="danger"
          darkMode={darkMode}
        />
      </div>

      {chartData.length > 0 && (
        <div className="card">
          <h2 className="section-title">
            <BarChart3 size={18} className="text-primary-400" />
            积分趋势
          </h2>
          <div className="h-44 flex items-end gap-1 pt-4">
            {chartData.map((d, i) => (
              <ChartBar
                key={i}
                date={d.date}
                points={d.points}
                maxPoints={maxPoints}
                delay={i * 50}
                darkMode={darkMode}
              />
            ))}
          </div>
        </div>
      )}

      <div className="card">
        <h2 className="section-title">
          <HistoryIcon size={18} className="text-purple-400" />
          执行记录
        </h2>

        {loading ? (
          <div className={clsx('flex items-center justify-center h-32', darkMode ? 'text-dark-400' : 'text-light-500')}>
            <RefreshCw size={24} className="animate-spin" />
          </div>
        ) : history.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className={clsx('border-b', darkMode ? 'border-dark-600/50' : 'border-light-300')}>
                  <th className={clsx('text-left py-3 px-4 font-medium text-sm', darkMode ? 'text-dark-400' : 'text-light-600')}>时间</th>
                  <th className={clsx('text-left py-3 px-4 font-medium text-sm', darkMode ? 'text-dark-400' : 'text-light-600')}>积分</th>
                  <th className={clsx('text-left py-3 px-4 font-medium text-sm', darkMode ? 'text-dark-400' : 'text-light-600')}>桌面搜索</th>
                  <th className={clsx('text-left py-3 px-4 font-medium text-sm', darkMode ? 'text-dark-400' : 'text-light-600')}>移动搜索</th>
                  <th className={clsx('text-left py-3 px-4 font-medium text-sm', darkMode ? 'text-dark-400' : 'text-light-600')}>耗时</th>
                  <th className={clsx('text-left py-3 px-4 font-medium text-sm', darkMode ? 'text-dark-400' : 'text-light-600')}>错误</th>
                </tr>
              </thead>
              <tbody>
                {history.map((item, index) => (
                  <HistoryRow key={index} item={item} index={index} darkMode={darkMode} />
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className={clsx('flex flex-col items-center justify-center h-32', darkMode ? 'text-dark-400' : 'text-light-500')}>
            <HistoryIcon size={32} className="mb-2 opacity-50" />
            <p className="text-sm">暂无历史记录</p>
            <p className={clsx('text-xs mt-1', darkMode ? 'text-dark-500' : 'text-light-500')}>执行任务后将显示历史记录</p>
          </div>
        )}
      </div>
    </div>
  )
}
