import { useState, useEffect, useRef, useMemo, useCallback } from 'react'
import {
  Coins,
  Monitor,
  Smartphone,
  TrendingUp,
  TrendingDown,
  Clock,
  AlertTriangle,
  CheckCircle,
  Zap,
  RefreshCw,
  Target,
  Award,
  Play,
  Square,
  Settings,
  Eye,
  EyeOff,
  SkipForward,
  ChevronDown,
  ChevronUp,
  Terminal,
  ExternalLink,
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useStore } from '../store'
import { refreshData, startTask, stopTask, fetchStatus } from '../api'
import { cn } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'

function StatCard({
  icon: Icon,
  label,
  value,
  subValue,
  change,
  changeType,
  color = 'primary',
  badge,
  loading = false,
}: {
  icon: React.ElementType
  label: string
  value: string | number | null
  subValue?: string
  change?: number
  changeType?: 'positive' | 'negative'
  color?: 'primary' | 'success' | 'warning' | 'danger' | 'cyan' | 'purple'
  badge?: string
  loading?: boolean
}) {
  const { darkMode } = useStore()
  const colorClasses: Record<string, { icon: string; gradient: string }> = {
    primary: {
      icon: 'text-primary-400',
      gradient: 'from-primary-500/20 to-transparent',
    },
    success: {
      icon: 'text-success-400',
      gradient: 'from-success-500/20 to-transparent',
    },
    warning: {
      icon: 'text-warning-400',
      gradient: 'from-warning-500/20 to-transparent',
    },
    danger: {
      icon: 'text-danger-400',
      gradient: 'from-danger-500/20 to-transparent',
    },
    cyan: {
      icon: 'text-cyan-400',
      gradient: 'from-cyan-500/20 to-transparent',
    },
    purple: {
      icon: 'text-purple-400',
      gradient: 'from-purple-500/20 to-transparent',
    },
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      whileHover={{ scale: 1.02 }}
    >
      <Card className="group relative overflow-hidden">
        <div
          className={cn(
            'absolute inset-0 bg-gradient-to-br opacity-0 group-hover:opacity-100 transition-opacity duration-300',
            colorClasses[color].gradient
          )}
        />
        <CardContent className="relative p-5">
          <div className="flex items-center justify-between mb-3">
            <div
              className={cn(
                'p-2 rounded-lg',
                darkMode ? 'bg-dark-600/30' : 'bg-light-200',
                colorClasses[color].icon
              )}
            >
              <Icon size={18} />
            </div>
            {badge && (
              <Badge
                variant={
                  color === 'success' ? 'success' : color === 'warning' ? 'warning' : 'default'
                }
              >
                {badge}
              </Badge>
            )}
          </div>

          {loading ? (
            <div className="space-y-2">
              <div
                className={cn(
                  'h-7 w-20 rounded animate-pulse',
                  darkMode ? 'bg-dark-700/50' : 'bg-light-300'
                )}
              />
              <div
                className={cn(
                  'h-4 w-16 rounded animate-pulse',
                  darkMode ? 'bg-dark-700/50' : 'bg-light-300'
                )}
              />
            </div>
          ) : (
            <>
              <div
                className={cn(
                  'text-2xl font-bold tracking-tight',
                  darkMode ? 'text-dark-100' : 'text-light-900'
                )}
              >
                {value ?? '---'}
                {subValue && (
                  <span
                    className={cn(
                      'text-base font-normal ml-1',
                      darkMode ? 'text-dark-400' : 'text-light-500'
                    )}
                  >
                    {subValue}
                  </span>
                )}
              </div>
              <div className={cn('text-sm mt-1', darkMode ? 'text-dark-400' : 'text-light-600')}>
                {label}
              </div>

              {change !== undefined && (
                <div
                  className={cn(
                    'flex items-center gap-1 mt-2 text-sm font-medium',
                    changeType === 'positive' ? 'text-success-500' : 'text-danger-500'
                  )}
                >
                  {changeType === 'positive' ? (
                    <TrendingUp size={14} />
                  ) : (
                    <TrendingDown size={14} />
                  )}
                  <span>
                    {changeType === 'positive' ? '+' : ''}
                    {change}
                  </span>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )
}

function ModeCard({
  label,
  description,
  selected,
  disabled,
  onClick,
  darkMode = true,
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
      className={cn(
        'p-3 rounded-xl border text-left transition-all duration-200 ease-smooth group',
        selected
          ? 'border-primary-500/50 bg-primary-500/10 shadow-lg shadow-primary-500/10'
          : darkMode
            ? 'border-dark-600/50 bg-surface-400/50 hover:border-dark-500/50 hover:bg-surface-400'
            : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50',
        disabled && 'opacity-50 cursor-not-allowed'
      )}
    >
      <div className="flex items-center justify-between mb-1">
        <div
          className={cn(
            'font-semibold text-sm transition-colors',
            selected
              ? 'text-primary-400'
              : darkMode
                ? 'text-dark-200 group-hover:text-dark-100'
                : 'text-gray-700 group-hover:text-gray-900'
          )}
        >
          {label}
        </div>
        {selected && <div className="w-1.5 h-1.5 bg-primary-400 rounded-full animate-pulse-soft" />}
      </div>
      <div className={cn('text-xs', darkMode ? 'text-dark-400' : 'text-gray-500')}>
        {description}
      </div>
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
  darkMode = true,
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
    <label
      className={cn(
        'flex items-center gap-3 p-2.5 rounded-xl cursor-pointer transition-all duration-200',
        darkMode
          ? 'bg-surface-400/50 hover:bg-surface-400 border border-transparent hover:border-dark-600/50'
          : 'bg-gray-50 hover:bg-gray-100 border border-transparent hover:border-gray-200',
        disabled && 'opacity-50 cursor-not-allowed'
      )}
    >
      <div className="relative">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          disabled={disabled}
          className="sr-only"
        />
        <div
          className={cn(
            'w-9 h-5 rounded-full transition-all duration-200 flex items-center',
            checked ? 'bg-primary-500/30' : darkMode ? 'bg-dark-600' : 'bg-gray-300'
          )}
        >
          <div
            className={cn(
              'w-3.5 h-3.5 rounded-full transition-all duration-200 shadow-sm',
              checked
                ? 'translate-x-4.5 bg-primary-400 shadow-primary-400/50'
                : darkMode
                  ? 'translate-x-0.5 bg-dark-400'
                  : 'translate-x-0.5 bg-gray-500'
            )}
          />
        </div>
      </div>
      <div className="flex items-center gap-2 flex-1">
        <Icon
          size={16}
          className={cn(
            'transition-colors',
            checked ? colorClasses[color].icon : darkMode ? 'text-dark-400' : 'text-gray-400'
          )}
        />
        <div>
          <div
            className={cn(
              'font-medium text-sm transition-colors',
              checked
                ? darkMode
                  ? 'text-dark-100'
                  : 'text-gray-900'
                : darkMode
                  ? 'text-dark-300'
                  : 'text-gray-600'
            )}
          >
            {label}
          </div>
          {description && (
            <div className={cn('text-xs mt-0.5', darkMode ? 'text-dark-500' : 'text-gray-400')}>
              {description}
            </div>
          )}
        </div>
      </div>
    </label>
  )
}

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
}

export default function Dashboard() {
  const { taskStatus, health, points, config, lastDataUpdate, dataLoading, dataError, darkMode, backendReady, logs } =
    useStore()

  const [isRefreshing, setIsRefreshing] = useState(false)
  const [isStarting, setIsStarting] = useState(false)
  const [isStopping, setIsStopping] = useState(false)
  const [actionFeedback, setActionFeedback] = useState<{
    type: 'success' | 'error'
    message: string
  } | null>(null)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [options, setOptions] = useState({
    mode: 'normal',
    headless: false,
    desktop_only: false,
    mobile_only: false,
    skip_daily_tasks: false,
  })

  const logContainerRef = useRef<HTMLDivElement>(null)
  const prevRunningRef = useRef(taskStatus?.is_running)

  const modes = [
    { value: 'normal', label: '正常模式', description: '30+20 搜索' },
    { value: 'usermode', label: '用户模式', description: '3+3 搜索' },
    { value: 'dev', label: '开发模式', description: '2+2 搜索' },
  ]

  const recentLogs = useMemo(() => {
    return logs.slice(-10)
  }, [logs])

  useEffect(() => {
    fetchStatus()
  }, [])

  useEffect(() => {
    if (prevRunningRef.current && !taskStatus?.is_running) {
      refreshData()
    }
    prevRunningRef.current = taskStatus?.is_running
  }, [taskStatus?.is_running])

  useEffect(() => {
    if (actionFeedback) {
      const timer = setTimeout(() => setActionFeedback(null), 5000)
      return () => clearTimeout(timer)
    }
  }, [actionFeedback])

  const handleRefresh = async () => {
    setIsRefreshing(true)
    await refreshData()
    setTimeout(() => setIsRefreshing(false), 500)
  }

  const handleStart = async () => {
    setIsStarting(true)
    setActionFeedback(null)
    try {
      const result = await startTask(options)
      setActionFeedback({ type: 'success', message: result.message || '任务已启动' })
      await fetchStatus()
    } catch (error: unknown) {
      console.error('Failed to start task:', error)
      const errorObj = error as { response?: { data?: { detail?: string } }; message?: string }
      const errorMsg = errorObj?.response?.data?.detail || errorObj?.message || '启动任务失败'
      setActionFeedback({ type: 'error', message: errorMsg })
    } finally {
      setTimeout(() => setIsStarting(false), 300)
    }
  }

  const handleStop = async () => {
    setIsStopping(true)
    setActionFeedback(null)
    try {
      const result = await stopTask()
      setActionFeedback({ type: 'success', message: result.message || '任务已停止' })
      await fetchStatus()
    } catch (error: unknown) {
      console.error('Failed to stop task:', error)
      const errorObj = error as { response?: { data?: { detail?: string } }; message?: string }
      const errorMsg = errorObj?.response?.data?.detail || errorObj?.message || '停止任务失败'
      setActionFeedback({ type: 'error', message: errorMsg })
    } finally {
      setTimeout(() => setIsStopping(false), 300)
    }
  }

  const formatUptime = useCallback((seconds: number) => {
    if (seconds < 60) return `${Math.round(seconds)}秒`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟`
    const hours = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    return `${hours}小时${mins}分钟`
  }, [])

  const formatLastUpdate = useCallback((time: string | null) => {
    if (!time) return '未更新'
    const date = new Date(time)
    return date.toLocaleString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  }, [])

  const getLogColor = useCallback((log: string) => {
    if (log.includes('ERROR') || log.includes('error')) return 'text-danger-400'
    if (log.includes('WARNING') || log.includes('warning')) return 'text-warning-400'
    if (log.includes('SUCCESS') || log.includes('success') || log.includes('✓'))
      return 'text-success-400'
    if (log.includes('INFO') || log.includes('info')) return 'text-primary-400'
    return darkMode ? 'text-dark-300' : 'text-light-600'
  }, [darkMode])

  return (
    <motion.div
      className="space-y-6"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      <motion.div variants={itemVariants} className="flex items-center justify-between">
        <div>
          <h1 className="page-title">控制台</h1>
          <p className="page-subtitle">MS Rewards Automator 任务控制中心</p>
        </div>
        <div className="flex items-center gap-3">
          <div
            className={cn(
              'flex items-center gap-2 text-sm',
              darkMode ? 'text-dark-400' : 'text-light-600'
            )}
          >
            <Clock size={14} />
            <span>更新于: {formatLastUpdate(lastDataUpdate)}</span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center gap-1.5"
          >
            <RefreshCw size={14} className={cn(isRefreshing && 'animate-spin')} />
            刷新
          </Button>
        </div>
      </motion.div>

      <AnimatePresence>
        {dataError && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <Card className="border-danger-500/30 bg-danger-500/5">
              <CardContent className="p-5">
                <div className="flex items-center gap-3">
                  <AlertTriangle className="text-danger-500" size={20} />
                  <div>
                    <div className="text-danger-500 font-medium">连接错误</div>
                    <div className={cn('text-sm', darkMode ? 'text-dark-300' : 'text-light-600')}>
                      {dataError}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {!backendReady && !dataError && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <Card className="border-warning-500/30 bg-warning-500/5">
              <CardContent className="p-5">
                <div className="flex items-center gap-3">
                  <RefreshCw className="text-warning-500 animate-spin" size={20} />
                  <div>
                    <div className="text-warning-500 font-medium">正在连接后端服务...</div>
                    <div className={cn('text-sm', darkMode ? 'text-dark-300' : 'text-light-600')}>
                      请稍候，后端服务正在启动中
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div
        variants={itemVariants}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
      >
        <StatCard
          icon={Coins}
          label="当前积分"
          value={points?.current_points?.toLocaleString() ?? null}
          change={points?.points_gained_today}
          changeType="positive"
          color="primary"
          badge="今日"
          loading={dataLoading}
        />

        <StatCard
          icon={Monitor}
          label="桌面搜索"
          value={taskStatus?.desktop_searches_completed ?? 0}
          subValue={`/ ${taskStatus?.desktop_searches_total || config?.search.desktop_count || 30}`}
          color="success"
          badge="桌面"
          loading={dataLoading}
        />

        <StatCard
          icon={Smartphone}
          label="移动搜索"
          value={taskStatus?.mobile_searches_completed ?? 0}
          subValue={`/ ${taskStatus?.mobile_searches_total || config?.search.mobile_count || 20}`}
          color="warning"
          badge="移动"
          loading={dataLoading}
        />

        <StatCard
          icon={Zap}
          label="运行时间"
          value={formatUptime(health?.uptime_seconds ?? 0)}
          color={
            health?.overall === 'healthy'
              ? 'success'
              : health?.overall === 'warning'
                ? 'warning'
                : 'danger'
          }
          badge={
            health?.overall === 'healthy'
              ? '健康'
              : health?.overall === 'warning'
                ? '警告'
                : '异常'
          }
          loading={dataLoading}
        />
      </motion.div>

      <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2.5">
              <Settings size={18} className="text-primary-500" />
              任务控制面板
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
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
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className={cn(
                  'flex items-center gap-2 text-sm font-medium transition-colors',
                  darkMode ? 'text-dark-300 hover:text-dark-100' : 'text-light-600 hover:text-light-900'
                )}
              >
                {showAdvanced ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                高级选项
              </button>

              <AnimatePresence>
                {showAdvanced && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-3 space-y-2"
                  >
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
                      onChange={(checked) =>
                        setOptions({
                          ...options,
                          desktop_only: checked,
                          mobile_only: checked ? false : options.mobile_only,
                        })
                      }
                      color="success"
                      darkMode={darkMode}
                    />

                    <OptionToggle
                      icon={Smartphone}
                      label="仅移动搜索"
                      checked={options.mobile_only}
                      disabled={taskStatus?.is_running || false}
                      onChange={(checked) =>
                        setOptions({
                          ...options,
                          mobile_only: checked,
                          desktop_only: checked ? false : options.desktop_only,
                        })
                      }
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
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleStart}
                disabled={taskStatus?.is_running || isStarting || !backendReady}
                className={cn(
                  'flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-medium text-sm transition-all duration-300',
                  'bg-gradient-to-r from-primary-500 to-cyan-500 text-dark-900 hover:shadow-glow-primary',
                  (taskStatus?.is_running || isStarting || !backendReady) &&
                    'opacity-50 cursor-not-allowed'
                )}
              >
                {isStarting ? (
                  <>
                    <RefreshCw size={16} className="animate-spin" />
                    <span>启动中...</span>
                  </>
                ) : (
                  <>
                    <Play size={16} />
                    <span>启动任务</span>
                  </>
                )}
              </button>

              <button
                onClick={handleStop}
                disabled={!taskStatus?.is_running || isStopping}
                className={cn(
                  'flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-medium text-sm transition-all duration-300',
                  'bg-danger-500 text-white hover:bg-danger-600 shadow-glow-danger',
                  (!taskStatus?.is_running || isStopping) && 'opacity-50 cursor-not-allowed'
                )}
              >
                {isStopping ? (
                  <>
                    <RefreshCw size={16} className="animate-spin" />
                    <span>停止中...</span>
                  </>
                ) : (
                  <>
                    <Square size={16} />
                    <span>停止任务</span>
                  </>
                )}
              </button>
            </div>

            {actionFeedback && (
              <div
                className={cn(
                  'p-3 rounded-lg flex items-center gap-2',
                  actionFeedback.type === 'success'
                    ? darkMode
                      ? 'bg-success-500/10 text-success-400 border border-success-500/20'
                      : 'bg-green-50 text-green-700 border border-green-200'
                    : darkMode
                      ? 'bg-danger-500/10 text-danger-400 border border-danger-500/20'
                      : 'bg-red-50 text-red-700 border border-red-200'
                )}
              >
                {actionFeedback.type === 'success' ? (
                  <CheckCircle size={16} />
                ) : (
                  <AlertTriangle size={16} />
                )}
                <span className="text-sm">{actionFeedback.message}</span>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2.5">
              <Target size={18} className="text-primary-500" />
              今日进度
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className={cn('p-4 rounded-lg', darkMode ? 'bg-surface-400/50' : 'bg-light-100')}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Monitor size={16} className="text-success-500" />
                  <span
                    className={cn('text-sm font-medium', darkMode ? 'text-dark-200' : 'text-light-700')}
                  >
                    桌面搜索
                  </span>
                </div>
                <span
                  className={cn('text-sm font-mono', darkMode ? 'text-dark-300' : 'text-light-600')}
                >
                  {taskStatus?.desktop_searches_completed ?? 0} /{' '}
                  {taskStatus?.desktop_searches_total || config?.search.desktop_count || 30}
                </span>
              </div>
              <Progress
                value={
                  ((taskStatus?.desktop_searches_completed ?? 0) /
                    (taskStatus?.desktop_searches_total || config?.search.desktop_count || 30)) *
                  100
                }
                indicatorClassName="bg-gradient-to-r from-success-500 to-success-400"
              />
            </div>

            <div className={cn('p-4 rounded-lg', darkMode ? 'bg-surface-400/50' : 'bg-light-100')}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Smartphone size={16} className="text-warning-500" />
                  <span
                    className={cn('text-sm font-medium', darkMode ? 'text-dark-200' : 'text-light-700')}
                  >
                    移动搜索
                  </span>
                </div>
                <span
                  className={cn('text-sm font-mono', darkMode ? 'text-dark-300' : 'text-light-600')}
                >
                  {taskStatus?.mobile_searches_completed ?? 0} /{' '}
                  {taskStatus?.mobile_searches_total || config?.search.mobile_count || 20}
                </span>
              </div>
              <Progress
                value={
                  ((taskStatus?.mobile_searches_completed ?? 0) /
                    (taskStatus?.mobile_searches_total || config?.search.mobile_count || 20)) *
                  100
                }
                indicatorClassName="bg-gradient-to-r from-warning-500 to-warning-400"
              />
            </div>

            <div className={cn('p-4 rounded-lg', darkMode ? 'bg-surface-400/50' : 'bg-light-100')}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Award size={16} className="text-primary-500" />
                  <span
                    className={cn('text-sm font-medium', darkMode ? 'text-dark-200' : 'text-light-700')}
                  >
                    每日任务
                  </span>
                </div>
                <span
                  className={cn('text-sm font-mono', darkMode ? 'text-dark-300' : 'text-light-600')}
                >
                  {points?.points_gained_today ?? 0} 积分
                </span>
              </div>
              <div className={cn('text-xs mt-1', darkMode ? 'text-dark-400' : 'text-light-500')}>
                今日已获得积分
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2.5">
              <Terminal size={18} className="text-primary-500" />
              实时日志
              <Badge variant="outline" className="ml-2">
                最近 {recentLogs.length} 条
              </Badge>
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              className="flex items-center gap-1.5"
              onClick={() => (window.location.href = '/logs')}
            >
              <ExternalLink size={14} />
              查看全部
            </Button>
          </CardHeader>
          <CardContent>
            <div
              ref={logContainerRef}
              className={cn(
                'h-40 overflow-y-auto rounded-lg p-3 font-mono text-xs space-y-1',
                darkMode ? 'bg-dark-700/50' : 'bg-light-200'
              )}
            >
              {recentLogs.length > 0 ? (
                recentLogs.map((log, index) => (
                  <div key={index} className={cn('truncate', getLogColor(log))}>
                    {log}
                  </div>
                ))
              ) : (
                <div
                  className={cn(
                    'flex items-center justify-center h-full',
                    darkMode ? 'text-dark-400' : 'text-light-500'
                  )}
                >
                  暂无日志
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <AnimatePresence>
        {taskStatus?.is_running && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <Card className="border-primary-500/30 bg-primary-500/5">
              <CardContent className="p-5">
                <div className="flex items-center justify-between mb-4">
                  <h2
                    className={cn(
                      'text-lg font-semibold flex items-center gap-2.5',
                      darkMode ? 'text-dark-100' : 'text-light-900'
                    )}
                  >
                    <motion.div
                      animate={{ scale: [1, 1.2, 1] }}
                      transition={{ duration: 1, repeat: Infinity }}
                      className="w-2.5 h-2.5 bg-success-500 rounded-full shadow-lg shadow-success-500/50"
                    />
                    任务执行中
                  </h2>
                  <span className={cn('text-sm', darkMode ? 'text-dark-400' : 'text-light-600')}>
                    已运行 {formatUptime(taskStatus.elapsed_seconds)}
                  </span>
                </div>

                <div className="mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className={cn('text-sm', darkMode ? 'text-dark-300' : 'text-light-600')}>
                      {taskStatus.current_operation}
                    </span>
                    <span
                      className={cn(
                        'text-sm font-mono',
                        darkMode ? 'text-dark-400' : 'text-light-500'
                      )}
                    >
                      {taskStatus.progress}/{taskStatus.total_steps}
                    </span>
                  </div>
                  <Progress value={(taskStatus.progress / taskStatus.total_steps) * 100} />
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div
                    className={cn(
                      'flex flex-col items-start gap-1 p-3 rounded-lg',
                      darkMode ? 'bg-surface-400/50' : 'bg-light-100'
                    )}
                  >
                    <div className={cn('text-sm', darkMode ? 'text-dark-400' : 'text-light-600')}>
                      初始积分
                    </div>
                    <div
                      className={cn(
                        'text-lg font-medium',
                        darkMode ? 'text-dark-100' : 'text-light-900'
                      )}
                    >
                      {taskStatus.initial_points?.toLocaleString() ?? '---'}
                    </div>
                  </div>
                  <div
                    className={cn(
                      'flex flex-col items-start gap-1 p-3 rounded-lg',
                      darkMode ? 'bg-surface-400/50' : 'bg-light-100'
                    )}
                  >
                    <div className={cn('text-sm', darkMode ? 'text-dark-400' : 'text-light-600')}>
                      当前积分
                    </div>
                    <div
                      className={cn(
                        'text-lg font-medium',
                        darkMode ? 'text-dark-100' : 'text-light-900'
                      )}
                    >
                      {taskStatus.current_points?.toLocaleString() ?? '---'}
                    </div>
                  </div>
                  <div
                    className={cn(
                      'flex flex-col items-start gap-1 p-3 rounded-lg',
                      darkMode ? 'bg-surface-400/50' : 'bg-light-100'
                    )}
                  >
                    <div className={cn('text-sm', darkMode ? 'text-dark-400' : 'text-light-600')}>
                      获得积分
                    </div>
                    <div className="text-lg font-medium text-success-500">
                      +{taskStatus.points_gained}
                    </div>
                  </div>
                  <div
                    className={cn(
                      'flex flex-col items-start gap-1 p-3 rounded-lg',
                      darkMode ? 'bg-surface-400/50' : 'bg-light-100'
                    )}
                  >
                    <div className={cn('text-sm', darkMode ? 'text-dark-400' : 'text-light-600')}>
                      错误/警告
                    </div>
                    <div className="text-lg font-medium">
                      <span className="text-danger-500">{taskStatus.error_count}</span>
                      <span className={cn('mx-1', darkMode ? 'text-dark-500' : 'text-light-400')}>
                        /
                      </span>
                      <span className="text-warning-500">{taskStatus.warning_count}</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
