import { useState, useEffect, useRef, useMemo, useCallback } from 'react'
import {
  Coins,
  Monitor,
  Smartphone,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  Target,
  Award,
  Play,
  Square,
  Eye,
  EyeOff,
  SkipForward,
  ChevronDown,
  ChevronUp,
  Terminal,
  ExternalLink,
  Activity,
  Flame,
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useStore } from '../store'
import { refreshData, startTask, stopTask, fetchStatus } from '../api'
import { cn, getErrorMessage } from '@/lib/utils'
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
      className="h-full"
    >
      <Card className="group relative overflow-hidden h-full mica-card-glow">
        <div
          className={cn(
            'absolute inset-0 bg-gradient-to-br opacity-0 group-hover:opacity-100 transition-opacity duration-300',
            colorClasses[color].gradient
          )}
        />
        <CardContent className="relative p-4">
          <div className="flex items-center justify-between mb-2">
            <div
              className={cn(
                'p-2 rounded-lg',
                darkMode ? 'bg-white/5' : 'bg-black/5',
                colorClasses[color].icon
              )}
            >
              <Icon size={16} />
            </div>
            {badge && (
              <Badge
                variant={
                  color === 'success' ? 'success' : color === 'warning' ? 'warning' : 'default'
                }
                className="text-[10px] px-1.5 py-0.5"
              >
                {badge}
              </Badge>
            )}
          </div>

          {loading ? (
            <div className="space-y-1.5">
              <div
                className={cn(
                  'h-6 w-16 rounded animate-pulse',
                  darkMode ? 'bg-white/5' : 'bg-black/5'
                )}
              />
              <div
                className={cn(
                  'h-3 w-12 rounded animate-pulse',
                  darkMode ? 'bg-white/5' : 'bg-black/5'
                )}
              />
            </div>
          ) : (
            <>
              <div
                className={cn(
                  'text-xl font-bold tracking-tight',
                  darkMode ? 'text-dark-100' : 'text-light-900'
                )}
              >
                {value ?? '---'}
                {subValue && (
                  <span
                    className={cn(
                      'text-sm font-normal ml-1',
                      darkMode ? 'text-dark-400' : 'text-light-500'
                    )}
                  >
                    {subValue}
                  </span>
                )}
              </div>
              <div className={cn('text-xs mt-0.5', darkMode ? 'text-dark-400' : 'text-light-600')}>
                {label}
              </div>

              {change !== undefined && (
                <div
                  className={cn(
                    'flex items-center gap-1 mt-1.5 text-xs font-medium',
                    changeType === 'positive' ? 'text-success-500' : 'text-danger-500'
                  )}
                >
                  {changeType === 'positive' ? (
                    <TrendingUp size={12} />
                  ) : (
                    <TrendingDown size={12} />
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
        'p-2.5 rounded-xl text-left transition-all duration-200 ease-smooth group',
        selected
          ? 'bg-primary-500/15 shadow-lg shadow-primary-500/10'
          : darkMode
            ? 'bg-white/[0.02] hover:bg-white/[0.05]'
            : 'bg-black/5 hover:bg-black/10',
        disabled && 'opacity-50 cursor-not-allowed'
      )}
    >
      <div className="flex items-center justify-between mb-0.5">
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
        'flex items-center gap-2.5 p-2 rounded-xl cursor-pointer transition-all duration-200',
        darkMode
          ? 'bg-white/[0.02] hover:bg-white/[0.04]'
          : 'bg-black/5 hover:bg-black/10',
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
            'w-8 h-4.5 rounded-full transition-all duration-200 flex items-center',
            checked ? 'bg-primary-500/30' : darkMode ? 'bg-white/10' : 'bg-black/20'
          )}
        >
          <div
            className={cn(
              'w-3 h-3 rounded-full transition-all duration-200 shadow-sm',
              checked
                ? 'translate-x-4 bg-primary-400 shadow-primary-400/50'
                : darkMode
                  ? 'translate-x-0.5 bg-dark-400'
                  : 'translate-x-0.5 bg-gray-500'
            )}
          />
        </div>
      </div>
      <div className="flex items-center gap-1.5 flex-1">
        <Icon
          size={14}
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
      staggerChildren: 0.08,
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
    { value: 'normal', label: '正常模式', description: '20 搜索' },
    { value: 'usermode', label: '用户模式', description: '3 搜索' },
    { value: 'dev', label: '开发模式', description: '2 搜索' },
  ]

  const recentLogs = useMemo(() => {
    return logs.slice(-8)
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
      const errorMsg = getErrorMessage(error, '启动任务失败')
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
      const errorMsg = getErrorMessage(error, '停止任务失败')
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
    return 'text-gray-400'
  }, [])

  const isRunning = taskStatus?.is_running

  return (
    <motion.div
      className="h-full flex flex-col gap-4"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      <AnimatePresence>
        {dataError && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <Card className="border-danger-500/30 bg-danger-500/10 backdrop-blur-xl">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <AlertTriangle className="text-danger-500" size={18} />
                  <div>
                    <div className="text-danger-500 font-medium text-sm">连接错误</div>
                    <div className={cn('text-xs', darkMode ? 'text-dark-300' : 'text-light-600')}>
                      {dataError}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {!backendReady && !dataError && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <Card className="border-warning-500/30 bg-warning-500/10 backdrop-blur-xl">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <RefreshCw className="text-warning-500 animate-spin" size={18} />
                  <div>
                    <div className="text-warning-500 font-medium text-sm">正在连接后端服务...</div>
                    <div className={cn('text-xs', darkMode ? 'text-dark-300' : 'text-light-600')}>
                      请稍候，后端服务正在启动中
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex-1 grid grid-cols-12 gap-4 min-h-0">
        <div className="col-span-12 lg:col-span-8 flex flex-col gap-4">
          <motion.div variants={itemVariants} className="grid grid-cols-4 gap-3">
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
              subValue={`/${taskStatus?.desktop_searches_total || config?.search.desktop_count || 20}`}
              color="success"
              loading={dataLoading}
            />

            <StatCard
              icon={Smartphone}
              label="移动搜索"
              value={taskStatus?.mobile_searches_completed ?? 0}
              subValue={`/${taskStatus?.mobile_searches_total || config?.search.mobile_count || 0}`}
              color="warning"
              loading={dataLoading}
            />

            <StatCard
              icon={Activity}
              label="运行时间"
              value={formatUptime(health?.uptime_seconds ?? 0)}
              color={
                health?.overall === 'healthy'
                  ? 'success'
                  : health?.overall === 'warning'
                    ? 'warning'
                    : 'danger'
              }
              loading={dataLoading}
            />
          </motion.div>

          <motion.div variants={itemVariants} className="flex-1 min-h-0">
            <Card className="h-full mica-card flex flex-col">
              <CardHeader className="pb-2 pt-4 px-4">
                <CardTitle className="flex items-center gap-2 text-base">
                  {isRunning ? (
                    <motion.div
                      animate={{ scale: [1, 1.2, 1] }}
                      transition={{ duration: 1, repeat: Infinity }}
                      className="w-2 h-2 bg-success-500 rounded-full shadow-lg shadow-success-500/50"
                    />
                  ) : (
                    <Flame size={16} className="text-primary-500" />
                  )}
                  任务控制台
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col gap-4 px-4 pb-4">
                {isRunning && taskStatus ? (
                  <div className="flex-1 flex flex-col gap-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-success-500/20 flex items-center justify-center">
                          <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                          >
                            <RefreshCw size={20} className="text-success-400" />
                          </motion.div>
                        </div>
                        <div>
                          <div className={cn('text-sm font-medium', darkMode ? 'text-dark-100' : 'text-light-900')}>
                            {taskStatus.current_operation}
                          </div>
                          <div className={cn('text-xs', darkMode ? 'text-dark-400' : 'text-light-600')}>
                            已运行 {formatUptime(taskStatus.elapsed_seconds)}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-success-400">
                          +{taskStatus.points_gained}
                        </div>
                        <div className={cn('text-xs', darkMode ? 'text-dark-400' : 'text-light-600')}>
                          获得积分
                        </div>
                      </div>
                    </div>

                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className={cn('text-xs', darkMode ? 'text-dark-300' : 'text-light-600')}>
                          执行进度
                        </span>
                        <span className={cn('text-xs font-mono', darkMode ? 'text-dark-400' : 'text-light-500')}>
                          {taskStatus.progress}/{taskStatus.total_steps}
                        </span>
                      </div>
                      <Progress value={(taskStatus.progress / taskStatus.total_steps) * 100} className="h-2" />
                    </div>

                    <div className="grid grid-cols-4 gap-3">
                      <div className={cn('p-3 rounded-xl text-center', darkMode ? 'bg-white/[0.02]' : 'bg-black/5')}>
                        <div className={cn('text-xs mb-1', darkMode ? 'text-dark-400' : 'text-light-600')}>初始积分</div>
                        <div className={cn('text-base font-semibold', darkMode ? 'text-dark-100' : 'text-light-900')}>
                          {taskStatus.initial_points?.toLocaleString() ?? '---'}
                        </div>
                      </div>
                      <div className={cn('p-3 rounded-xl text-center', darkMode ? 'bg-white/[0.02]' : 'bg-black/5')}>
                        <div className={cn('text-xs mb-1', darkMode ? 'text-dark-400' : 'text-light-600')}>当前积分</div>
                        <div className={cn('text-base font-semibold', darkMode ? 'text-dark-100' : 'text-light-900')}>
                          {taskStatus.current_points?.toLocaleString() ?? '---'}
                        </div>
                      </div>
                      <div className={cn('p-3 rounded-xl text-center', darkMode ? 'bg-white/[0.02]' : 'bg-black/5')}>
                        <div className={cn('text-xs mb-1', darkMode ? 'text-dark-400' : 'text-light-600')}>错误</div>
                        <div className="text-base font-semibold text-danger-400">
                          {taskStatus.error_count}
                        </div>
                      </div>
                      <div className={cn('p-3 rounded-xl text-center', darkMode ? 'bg-white/[0.02]' : 'bg-black/5')}>
                        <div className={cn('text-xs mb-1', darkMode ? 'text-dark-400' : 'text-light-600')}>警告</div>
                        <div className="text-base font-semibold text-warning-400">
                          {taskStatus.warning_count}
                        </div>
                      </div>
                    </div>

                    <button
                      onClick={handleStop}
                      disabled={isStopping}
                      className={cn(
                        'w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-medium text-sm transition-all duration-300',
                        'bg-danger-500 text-white hover:bg-danger-600',
                        isStopping && 'opacity-70 cursor-wait'
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
                ) : (
                  <div className="flex-1 flex flex-col gap-4">
                    <div>
                      <label className={cn('text-xs font-medium mb-2 block', darkMode ? 'text-dark-300' : 'text-light-600')}>
                        执行模式
                      </label>
                      <div className="grid grid-cols-3 gap-2">
                        {modes.map((mode) => (
                          <ModeCard
                            key={mode.value}
                            {...mode}
                            selected={options.mode === mode.value}
                            disabled={isRunning ?? false}
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
                          'flex items-center gap-2 text-xs font-medium transition-colors',
                          darkMode ? 'text-dark-400 hover:text-dark-200' : 'text-light-500 hover:text-light-700'
                        )}
                      >
                        {showAdvanced ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                        高级选项
                      </button>

                      <AnimatePresence>
                        {showAdvanced && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            className="mt-2 grid grid-cols-2 gap-2"
                          >
                            <OptionToggle
                              icon={options.headless ? EyeOff : Eye}
                              label="无头模式"
                              checked={options.headless}
                              disabled={isRunning ?? false}
                              onChange={(checked) => setOptions({ ...options, headless: checked })}
                              color="primary"
                              darkMode={darkMode}
                            />

                            <OptionToggle
                              icon={Monitor}
                              label="仅桌面搜索"
                              checked={options.desktop_only}
                              disabled={isRunning ?? false}
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
                              disabled={isRunning ?? false}
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
                              disabled={isRunning ?? false}
                              onChange={(checked) => setOptions({ ...options, skip_daily_tasks: checked })}
                              color="neutral"
                              darkMode={darkMode}
                            />
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>

                    {actionFeedback && (
                      <div
                        className={cn(
                          'p-2.5 rounded-xl flex items-center gap-2 text-sm',
                          actionFeedback.type === 'success'
                            ? 'bg-success-500/10 text-success-400'
                            : 'bg-danger-500/10 text-danger-400'
                        )}
                      >
                        {actionFeedback.type === 'success' ? (
                          <CheckCircle size={14} />
                        ) : (
                          <AlertTriangle size={14} />
                        )}
                        <span className="text-xs">{actionFeedback.message}</span>
                      </div>
                    )}

                    <button
                      onClick={handleStart}
                      disabled={isStarting || !backendReady}
                      className={cn(
                        'w-full flex items-center justify-center gap-2 px-4 py-4 rounded-xl font-semibold text-sm transition-all duration-300',
                        'bg-gradient-to-r from-primary-500 to-cyan-500 text-dark-900 hover:shadow-glow-primary',
                        (isStarting || !backendReady) && 'opacity-50 cursor-not-allowed'
                      )}
                    >
                      {isStarting ? (
                        <>
                          <RefreshCw size={18} className="animate-spin" />
                          <span>启动中...</span>
                        </>
                      ) : (
                        <>
                          <Play size={18} />
                          <span>启动任务</span>
                        </>
                      )}
                    </button>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </div>

        <motion.div variants={itemVariants} className="col-span-12 lg:col-span-4 flex flex-col gap-4">
          <Card className="mica-card">
            <CardHeader className="pb-2 pt-4 px-4">
              <CardTitle className="flex items-center gap-2 text-base">
                <Target size={16} className="text-primary-500" />
                今日进度
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 px-4 pb-4">
              <div className={cn('p-3 rounded-xl', darkMode ? 'bg-white/[0.02]' : 'bg-black/5')}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Monitor size={14} className="text-success-500" />
                    <span className={cn('text-xs font-medium', darkMode ? 'text-dark-200' : 'text-light-700')}>
                      桌面搜索
                    </span>
                  </div>
                  <span className={cn('text-xs font-mono', darkMode ? 'text-dark-300' : 'text-light-600')}>
                    {taskStatus?.desktop_searches_completed ?? 0} /{' '}
                    {taskStatus?.desktop_searches_total || config?.search.desktop_count || 20}
                  </span>
                </div>
                <Progress
                  value={
                    ((taskStatus?.desktop_searches_completed ?? 0) /
                      (taskStatus?.desktop_searches_total || config?.search.desktop_count || 20)) *
                    100
                  }
                  indicatorClassName="bg-gradient-to-r from-success-500 to-success-400"
                  className="h-1.5"
                />
              </div>

              <div className={cn('p-3 rounded-xl', darkMode ? 'bg-white/[0.02]' : 'bg-black/5')}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Smartphone size={14} className="text-warning-500" />
                    <span className={cn('text-xs font-medium', darkMode ? 'text-dark-200' : 'text-light-700')}>
                      移动搜索
                    </span>
                  </div>
                  <span className={cn('text-xs font-mono', darkMode ? 'text-dark-300' : 'text-light-600')}>
                    {taskStatus?.mobile_searches_completed ?? 0} /{' '}
                    {taskStatus?.mobile_searches_total || config?.search.mobile_count || 0}
                  </span>
                </div>
                <Progress
                  value={
                    ((taskStatus?.mobile_searches_completed ?? 0) /
                      (taskStatus?.mobile_searches_total || config?.search.mobile_count || 1)) *
                    100
                  }
                  indicatorClassName="bg-gradient-to-r from-warning-500 to-warning-400"
                  className="h-1.5"
                />
              </div>

              <div className={cn('p-3 rounded-xl', darkMode ? 'bg-white/[0.02]' : 'bg-black/5')}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Award size={14} className="text-primary-500" />
                    <span className={cn('text-xs font-medium', darkMode ? 'text-dark-200' : 'text-light-700')}>
                      今日获得
                    </span>
                  </div>
                  <span className="text-base font-bold text-primary-400">
                    +{points?.points_gained_today ?? 0}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="flex-1 min-h-0 mica-card flex flex-col">
            <CardHeader className="pb-2 pt-4 px-4 flex-shrink-0">
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Terminal size={16} className="text-primary-500" />
                  实时日志
                </CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 px-2 text-xs"
                  onClick={() => (window.location.href = '/logs')}
                >
                  <ExternalLink size={12} className="mr-1" />
                  全部
                </Button>
              </div>
            </CardHeader>
            <CardContent className="flex-1 min-h-0 px-4 pb-4">
              <div className="terminal h-full">
                <div className="terminal-header">
                  <div className="terminal-dot-red" />
                  <div className="terminal-dot-yellow" />
                  <div className="terminal-dot-green" />
                  <span className="ml-2 text-xs text-gray-400">logs</span>
                </div>
                <div
                  ref={logContainerRef}
                  className="terminal-body h-[calc(100%-36px)] overflow-y-auto"
                >
                  {recentLogs.length > 0 ? (
                    recentLogs.map((log, index) => (
                      <div key={index} className={cn('terminal-line truncate', getLogColor(log))}>
                        <span className="terminal-prompt">$</span>
                        {log}
                      </div>
                    ))
                  ) : (
                    <div className="flex items-center justify-center h-full text-gray-500">
                      等待日志输出...
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      <motion.div
        variants={itemVariants}
        className="flex items-center justify-between px-1"
      >
        <div className="flex items-center gap-2">
          <div
            className={cn(
              'w-2 h-2 rounded-full',
              backendReady ? 'bg-success-400 shadow-glow-success' : 'bg-warning-400'
            )}
          />
          <span className={cn('text-xs', darkMode ? 'text-dark-400' : 'text-light-500')}>
            {backendReady ? '系统就绪' : '连接中...'}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className={cn('text-xs', darkMode ? 'text-dark-400' : 'text-light-500')}>
            更新于 {formatLastUpdate(lastDataUpdate)}
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="h-7 px-2"
          >
            <RefreshCw size={12} className={cn(isRefreshing && 'animate-spin')} />
          </Button>
        </div>
      </motion.div>
    </motion.div>
  )
}
