import { useState, useEffect } from 'react'
import { 
  Play, 
  Square, 
  Settings, 
  Monitor, 
  Smartphone,
  Eye,
  EyeOff,
  SkipForward,
  RefreshCw,
  XCircle,
  Zap,
  AlertCircle,
  Timer,
  Coins,
  CheckCircle
} from 'lucide-react'
import { useStore } from '../store'
import { startTask, stopTask, fetchStatus } from '../api'
import clsx from 'clsx'

function ModeCard({ 
  label, 
  description, 
  selected, 
  disabled, 
  onClick,
  darkMode = true
}: {
  label: string
  description: string
  selected: boolean
  disabled: boolean
  onClick: () => void
  darkMode?: boolean
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={clsx(
        'p-4 rounded-xl border text-left transition-all duration-200 ease-smooth group',
        selected
          ? 'border-primary-500/50 bg-primary-500/10 shadow-lg shadow-primary-500/10'
          : darkMode 
            ? 'border-dark-600/50 bg-surface-400/50 hover:border-dark-500/50 hover:bg-surface-400'
            : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50',
        disabled && 'opacity-50 cursor-not-allowed'
      )}
    >
      <div className="flex items-center justify-between mb-2">
        <div className={clsx(
          'font-semibold transition-colors',
          selected ? 'text-primary-400' : darkMode ? 'text-dark-200 group-hover:text-dark-100' : 'text-gray-700 group-hover:text-gray-900'
        )}>
          {label}
        </div>
        {selected && (
          <div className="w-2 h-2 bg-primary-400 rounded-full animate-pulse-soft" />
        )}
      </div>
      <div className={clsx('text-sm', darkMode ? 'text-dark-400' : 'text-gray-500')}>{description}</div>
    </button>
  )
}

function OptionToggle({
  icon: Icon,
  label,
  description,
  checked,
  disabled,
  onChange,
  color = 'primary',
  darkMode = true
}: {
  icon: React.ElementType
  label: string
  description?: string
  checked: boolean
  disabled: boolean
  onChange: (checked: boolean) => void
  color?: 'primary' | 'success' | 'warning' | 'neutral'
  darkMode?: boolean
}) {
  const colorClasses: Record<string, { icon: string; check: string }> = {
    primary: { icon: 'text-primary-400', check: 'text-primary-400' },
    success: { icon: 'text-success-400', check: 'text-success-400' },
    warning: { icon: 'text-warning-400', check: 'text-warning-400' },
    neutral: { icon: 'text-dark-400', check: 'text-dark-300' },
  }

  return (
    <label className={clsx(
      'flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all duration-200',
      darkMode 
        ? 'bg-surface-400/50 hover:bg-surface-400 border border-transparent hover:border-dark-600/50'
        : 'bg-gray-50 hover:bg-gray-100 border border-transparent hover:border-gray-200',
      disabled && 'opacity-50 cursor-not-allowed'
    )}>
      <div className="relative">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          disabled={disabled}
          className="sr-only"
        />
        <div className={clsx(
          'w-10 h-6 rounded-full transition-all duration-200 flex items-center',
          checked ? 'bg-primary-500/30' : darkMode ? 'bg-dark-600' : 'bg-gray-300'
        )}>
          <div className={clsx(
            'w-4 h-4 rounded-full transition-all duration-200 shadow-sm',
            checked 
              ? 'translate-x-5 bg-primary-400 shadow-primary-400/50' 
              : darkMode ? 'translate-x-1 bg-dark-400' : 'translate-x-1 bg-gray-500'
          )} />
        </div>
      </div>
      <div className="flex items-center gap-2.5 flex-1">
        <Icon size={18} className={clsx(
          'transition-colors',
          checked ? colorClasses[color].icon : darkMode ? 'text-dark-400' : 'text-gray-400'
        )} />
        <div>
          <div className={clsx(
            'font-medium text-sm transition-colors',
            checked ? (darkMode ? 'text-dark-100' : 'text-gray-900') : (darkMode ? 'text-dark-300' : 'text-gray-600')
          )}>
            {label}
          </div>
          {description && (
            <div className={clsx('text-xs mt-0.5', darkMode ? 'text-dark-500' : 'text-gray-400')}>{description}</div>
          )}
        </div>
      </div>
    </label>
  )
}

function ProgressSection({
  icon: Icon,
  label,
  current,
  total,
  color,
  darkMode = true
}: {
  icon: React.ElementType
  label: string
  current: number
  total: number
  color: 'success' | 'warning'
  darkMode?: boolean
}) {
  const percentage = total > 0 ? (current / total) * 100 : 0
  const colorClasses = {
    success: { icon: 'text-success-400', progress: 'progress-fill-success' },
    warning: { icon: 'text-warning-400', progress: 'progress-fill-warning' },
  }

  return (
    <div className={clsx(
      'p-4 rounded-xl',
      darkMode ? 'bg-surface-400/50' : 'bg-gray-50'
    )}>
      <div className="flex items-center gap-2 mb-3">
        <Icon size={16} className={colorClasses[color].icon} />
        <span className={clsx('text-sm font-medium', darkMode ? 'text-dark-300' : 'text-gray-600')}>{label}</span>
      </div>
      <div className="flex items-baseline gap-1 mb-3">
        <span className={clsx('text-2xl font-bold', darkMode ? 'text-dark-100' : 'text-gray-900')}>{current}</span>
        <span className={darkMode ? 'text-dark-400' : 'text-gray-500'}>/</span>
        <span className={darkMode ? 'text-dark-400' : 'text-gray-500'}>{total}</span>
      </div>
      <div className={clsx('progress-bar', darkMode ? '' : 'bg-gray-200')}>
        <div 
          className={colorClasses[color].progress}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}

export default function Tasks() {
  const { taskStatus, config, darkMode, backendReady } = useStore()
  const [loading, setLoading] = useState(false)
  const [actionFeedback, setActionFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  const [options, setOptions] = useState({
    mode: 'normal',
    headless: false,
    desktop_only: false,
    mobile_only: false,
    skip_daily_tasks: false,
  })

  useEffect(() => {
    fetchStatus()
  }, [])

  useEffect(() => {
    if (actionFeedback) {
      const timer = setTimeout(() => setActionFeedback(null), 5000)
      return () => clearTimeout(timer)
    }
  }, [actionFeedback])

  const handleStart = async () => {
    setLoading(true)
    setActionFeedback(null)
    try {
      const result = await startTask(options)
      setActionFeedback({ type: 'success', message: result.message || '任务已启动' })
      await fetchStatus()
    } catch (error: any) {
      console.error('Failed to start task:', error)
      const errorMsg = error?.response?.data?.detail || error?.message || '启动任务失败'
      setActionFeedback({ type: 'error', message: errorMsg })
    } finally {
      setLoading(false)
    }
  }

  const handleStop = async () => {
    setLoading(true)
    setActionFeedback(null)
    try {
      const result = await stopTask()
      setActionFeedback({ type: 'success', message: result.message || '任务已停止' })
      await fetchStatus()
    } catch (error: any) {
      console.error('Failed to stop task:', error)
      const errorMsg = error?.response?.data?.detail || error?.message || '停止任务失败'
      setActionFeedback({ type: 'error', message: errorMsg })
    } finally {
      setLoading(false)
    }
  }

  const modes = [
    { value: 'normal', label: '正常模式', description: '30+20 搜索，完整功能' },
    { value: 'usermode', label: '用户模式', description: '3+3 搜索，验证稳定性' },
    { value: 'dev', label: '开发模式', description: '2+2 搜索，快速调试' },
  ]

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.round(seconds % 60)
    return `${mins}分${secs}秒`
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">任务控制</h1>
          <p className="page-subtitle">配置并启动 MS Rewards 自动任务</p>
        </div>
        <div className={clsx(
          'flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300',
          taskStatus?.is_running 
            ? 'bg-success-500/15 text-success-400 border border-success-500/30' 
            : darkMode 
              ? 'bg-dark-600/50 text-dark-400 border border-dark-600/50'
              : 'bg-gray-100 text-gray-500 border border-gray-200'
        )}>
          {taskStatus?.is_running ? (
            <>
              <div className="w-2 h-2 bg-success-400 rounded-full animate-pulse-soft shadow-lg shadow-success-400/50" />
              运行中
            </>
          ) : (
            <>
              <div className={clsx('w-2 h-2 rounded-full', darkMode ? 'bg-dark-500' : 'bg-gray-400')} />
              空闲
            </>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className={clsx('card', darkMode ? '' : 'bg-white border-gray-200 shadow-sm')}>
          <h2 className={clsx('section-title', darkMode ? '' : 'text-gray-900')}>
            <Settings size={18} className="text-primary-400" />
            任务配置
          </h2>

          <div className="space-y-5">
            <div>
              <label className="label">执行模式</label>
              <div className="grid grid-cols-3 gap-3">
                {modes.map((mode) => (
                  <ModeCard
                    key={mode.value}
                    {...mode}
                    selected={options.mode === mode.value}
                    disabled={taskStatus?.is_running || false}
                    onClick={() => setOptions({ ...options, mode: mode.value })}
                    darkMode={darkMode}
                  />
                ))}
              </div>
            </div>

            <div>
              <label className="label">运行选项</label>
              <div className="space-y-2">
                <OptionToggle
                  icon={options.headless ? EyeOff : Eye}
                  label="无头模式"
                  description="不显示浏览器窗口"
                  checked={options.headless}
                  disabled={taskStatus?.is_running || false}
                  onChange={(checked) => setOptions({ ...options, headless: checked })}
                  color="primary"
                  darkMode={darkMode}
                />

                <OptionToggle
                  icon={Monitor}
                  label="仅桌面搜索"
                  checked={options.desktop_only}
                  disabled={taskStatus?.is_running || false}
                  onChange={(checked) => setOptions({ 
                    ...options, 
                    desktop_only: checked,
                    mobile_only: checked ? false : options.mobile_only
                  })}
                  color="success"
                  darkMode={darkMode}
                />

                <OptionToggle
                  icon={Smartphone}
                  label="仅移动搜索"
                  checked={options.mobile_only}
                  disabled={taskStatus?.is_running || false}
                  onChange={(checked) => setOptions({ 
                    ...options, 
                    mobile_only: checked,
                    desktop_only: checked ? false : options.desktop_only
                  })}
                  color="warning"
                  darkMode={darkMode}
                />

                <OptionToggle
                  icon={SkipForward}
                  label="跳过每日任务"
                  checked={options.skip_daily_tasks}
                  disabled={taskStatus?.is_running || false}
                  onChange={(checked) => setOptions({ ...options, skip_daily_tasks: checked })}
                  color="neutral"
                  darkMode={darkMode}
                />
              </div>
            </div>
          </div>

          <div className="mt-6 flex gap-3">
            <button
              onClick={handleStart}
              disabled={taskStatus?.is_running || loading || !backendReady}
              className={clsx(
                'flex-1 btn-primary',
                (taskStatus?.is_running || loading || !backendReady) && 'opacity-50 cursor-not-allowed'
              )}
            >
              {loading ? (
                <RefreshCw size={16} className="animate-spin" />
              ) : (
                <Play size={16} />
              )}
              启动任务
            </button>

            <button
              onClick={handleStop}
              disabled={!taskStatus?.is_running || loading}
              className={clsx(
                'flex-1 btn-danger',
                (!taskStatus?.is_running || loading) && 'opacity-50 cursor-not-allowed'
              )}
            >
              <Square size={16} />
              停止任务
            </button>
          </div>
          
          {!backendReady && (
            <div className={clsx(
              'mt-4 p-3 rounded-lg flex items-center gap-2',
              darkMode ? 'bg-warning-500/10 text-warning-400 border border-warning-500/20' : 'bg-yellow-50 text-yellow-700 border border-yellow-200'
            )}>
              <AlertCircle size={16} />
              <span className="text-sm">后端服务未连接，请等待服务启动...</span>
            </div>
          )}
          
          {actionFeedback && (
            <div className={clsx(
              'mt-4 p-3 rounded-lg flex items-center gap-2',
              actionFeedback.type === 'success' 
                ? darkMode ? 'bg-success-500/10 text-success-400 border border-success-500/20' : 'bg-green-50 text-green-700 border border-green-200'
                : darkMode ? 'bg-danger-500/10 text-danger-400 border border-danger-500/20' : 'bg-red-50 text-red-700 border border-red-200'
            )}>
              {actionFeedback.type === 'success' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
              <span className="text-sm">{actionFeedback.message}</span>
            </div>
          )}
        </div>

        <div className={clsx('card', darkMode ? '' : 'bg-white border-gray-200 shadow-sm')}>
          <h2 className={clsx('section-title', darkMode ? '' : 'text-gray-900')}>
            <Zap size={18} className="text-warning-400" />
            当前状态
          </h2>

          {taskStatus ? (
            <div className="space-y-4">
              <div className={clsx('data-row', darkMode ? '' : 'border-gray-100')}>
                <div className="flex items-center gap-2">
                  <AlertCircle size={16} className={darkMode ? 'text-dark-400' : 'text-gray-400'} />
                  <span className={clsx('text-sm', darkMode ? 'text-dark-300' : 'text-gray-600')}>当前操作</span>
                </div>
                <span className={clsx('font-medium text-sm', darkMode ? 'text-dark-100' : 'text-gray-900')}>{taskStatus.current_operation}</span>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className={clsx('text-sm', darkMode ? 'text-dark-400' : 'text-gray-500')}>总体进度</span>
                  <span className={clsx('text-sm font-mono', darkMode ? 'text-dark-300' : 'text-gray-600')}>{taskStatus.progress}/{taskStatus.total_steps}</span>
                </div>
                <div className={clsx('progress-bar h-2.5', darkMode ? '' : 'bg-gray-200')}>
                  <div 
                    className="progress-fill-primary"
                    style={{ width: `${(taskStatus.progress / taskStatus.total_steps) * 100}%` }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <ProgressSection
                  icon={Monitor}
                  label="桌面搜索"
                  current={taskStatus.desktop_searches_completed}
                  total={taskStatus.desktop_searches_total || config?.search.desktop_count || 30}
                  color="success"
                  darkMode={darkMode}
                />
                <ProgressSection
                  icon={Smartphone}
                  label="移动搜索"
                  current={taskStatus.mobile_searches_completed}
                  total={taskStatus.mobile_searches_total || config?.search.mobile_count || 20}
                  color="warning"
                  darkMode={darkMode}
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className={clsx('p-3 rounded-xl text-center', darkMode ? 'bg-surface-400/50' : 'bg-gray-50')}>
                  <div className="flex items-center justify-center gap-1.5 mb-1">
                    <Coins size={14} className={darkMode ? 'text-dark-400' : 'text-gray-400'} />
                    <span className={clsx('text-xs', darkMode ? 'text-dark-400' : 'text-gray-500')}>初始积分</span>
                  </div>
                  <div className={clsx('text-lg font-bold', darkMode ? 'text-dark-100' : 'text-gray-900')}>
                    {taskStatus.initial_points?.toLocaleString() ?? '---'}
                  </div>
                </div>
                <div className={clsx('p-3 rounded-xl text-center', darkMode ? 'bg-surface-400/50' : 'bg-gray-50')}>
                  <div className="flex items-center justify-center gap-1.5 mb-1">
                    <Coins size={14} className="text-primary-400" />
                    <span className={clsx('text-xs', darkMode ? 'text-dark-400' : 'text-gray-500')}>当前积分</span>
                  </div>
                  <div className={clsx('text-lg font-bold', darkMode ? 'text-dark-100' : 'text-gray-900')}>
                    {taskStatus.current_points?.toLocaleString() ?? '---'}
                  </div>
                </div>
                <div className="p-3 bg-success-500/10 rounded-xl text-center border border-success-500/20">
                  <div className="flex items-center justify-center gap-1.5 mb-1">
                    <Coins size={14} className="text-success-400" />
                    <span className="text-success-400 text-xs">获得积分</span>
                  </div>
                  <div className="text-lg font-bold text-success-400">
                    +{taskStatus.points_gained}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className={clsx('data-row', darkMode ? '' : 'border-gray-100')}>
                  <div className="flex items-center gap-2">
                    <Timer size={16} className={darkMode ? 'text-dark-400' : 'text-gray-400'} />
                    <span className={clsx('text-sm', darkMode ? 'text-dark-300' : 'text-gray-600')}>运行时间</span>
                  </div>
                  <span className={clsx('font-medium font-mono text-sm', darkMode ? 'text-dark-100' : 'text-gray-900')}>
                    {formatDuration(taskStatus.elapsed_seconds)}
                  </span>
                </div>
                <div className={clsx('data-row', darkMode ? '' : 'border-gray-100')}>
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      <XCircle size={16} className="text-danger-400" />
                      <span className={clsx('text-sm', darkMode ? 'text-dark-300' : 'text-gray-600')}>错误</span>
                    </div>
                    <span className="text-danger-400 font-bold">{taskStatus.error_count}</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      <AlertCircle size={16} className="text-warning-400" />
                      <span className={clsx('text-sm', darkMode ? 'text-dark-300' : 'text-gray-600')}>提示</span>
                    </div>
                    <span className="text-warning-400 font-bold">{taskStatus.warning_count}</span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className={clsx('flex flex-col items-center justify-center h-64', darkMode ? 'text-dark-400' : 'text-gray-400')}>
              <Zap size={32} className="mb-3 opacity-50" />
              <span className="text-sm">暂无状态数据</span>
              <span className={clsx('text-xs mt-1', darkMode ? 'text-dark-500' : 'text-gray-400')}>启动任务后将显示实时状态</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
