import { useEffect, useState } from 'react'
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
  Award
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useStore } from '../store'
import { initializeData, connectWebSocket, disconnectWebSocket, refreshData } from '../api'
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
  const colorClasses: Record<string, { icon: string; gradient: string }> = {
    primary: { icon: 'text-primary-400', gradient: 'from-primary-500/20 to-transparent' },
    success: { icon: 'text-success-400', gradient: 'from-success-500/20 to-transparent' },
    warning: { icon: 'text-warning-400', gradient: 'from-warning-500/20 to-transparent' },
    danger: { icon: 'text-danger-400', gradient: 'from-danger-500/20 to-transparent' },
    cyan: { icon: 'text-cyan-400', gradient: 'from-cyan-500/20 to-transparent' },
    purple: { icon: 'text-purple-400', gradient: 'from-purple-500/20 to-transparent' },
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      whileHover={{ scale: 1.02 }}
    >
      <Card className="group relative overflow-hidden">
        <div className={cn(
          'absolute inset-0 bg-gradient-to-br opacity-0 group-hover:opacity-100 transition-opacity duration-300',
          colorClasses[color].gradient
        )} />
        <CardContent className="relative p-5">
          <div className="flex items-center justify-between mb-3">
            <div className={cn(
              'p-2 rounded-lg bg-dark-600/30',
              colorClasses[color].icon
            )}>
              <Icon size={18} />
            </div>
            {badge && (
              <Badge variant={color === 'success' ? 'success' : color === 'warning' ? 'warning' : 'default'}>
                {badge}
              </Badge>
            )}
          </div>
          
          {loading ? (
            <div className="space-y-2">
              <div className="h-7 w-20 rounded animate-pulse bg-dark-700/50" />
              <div className="h-4 w-16 rounded animate-pulse bg-dark-700/50" />
            </div>
          ) : (
            <>
              <div className="text-2xl font-bold tracking-tight text-dark-100">
                {value ?? '---'}
                {subValue && <span className="text-base font-normal ml-1 text-dark-400">{subValue}</span>}
              </div>
              <div className="text-sm mt-1 text-dark-400">{label}</div>
              
              {change !== undefined && (
                <div className={cn(
                  'flex items-center gap-1 mt-2 text-sm font-medium',
                  changeType === 'positive' ? 'text-success-500' : 'text-danger-500'
                )}>
                  {changeType === 'positive' ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                  <span>{changeType === 'positive' ? '+' : ''}{change}</span>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </motion.div>
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
  const { 
    taskStatus, 
    health, 
    points, 
    config,
    lastDataUpdate,
    dataLoading,
    dataError,
  } = useStore()

  const [isRefreshing, setIsRefreshing] = useState(false)

  useEffect(() => {
    initializeData()
    connectWebSocket()
    
    return () => {
      disconnectWebSocket()
    }
  }, [])

  const handleRefresh = async () => {
    setIsRefreshing(true)
    await refreshData()
    setTimeout(() => setIsRefreshing(false), 500)
  }

  const formatUptime = (seconds: number) => {
    if (seconds < 60) return `${Math.round(seconds)}秒`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟`
    const hours = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    return `${hours}小时${mins}分钟`
  }

  const formatLastUpdate = (time: string | null) => {
    if (!time) return '未更新'
    const date = new Date(time)
    return date.toLocaleString('zh-CN', { 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    })
  }

  return (
    <motion.div 
      className="space-y-6"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      <motion.div variants={itemVariants} className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-dark-100">仪表盘</h1>
          <p className="text-sm mt-1 text-dark-400">MS Rewards Automator 运行状态概览</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-sm text-dark-400">
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
                    <div className="text-sm text-dark-300">{dataError}</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
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
          color={health?.overall === 'healthy' ? 'success' : health?.overall === 'warning' ? 'warning' : 'danger'}
          badge={health?.overall === 'healthy' ? '健康' : health?.overall === 'warning' ? '警告' : '异常'}
          loading={dataLoading}
        />
      </motion.div>

      <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2.5">
              <Target size={18} className="text-primary-500" />
              今日任务进度
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 rounded-lg bg-surface-400/50">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Monitor size={16} className="text-success-500" />
                  <span className="text-sm font-medium text-dark-200">桌面搜索</span>
                </div>
                <span className="text-sm font-mono text-dark-300">
                  {taskStatus?.desktop_searches_completed ?? 0} / {taskStatus?.desktop_searches_total || config?.search.desktop_count || 30}
                </span>
              </div>
              <Progress 
                value={((taskStatus?.desktop_searches_completed ?? 0) / (taskStatus?.desktop_searches_total || config?.search.desktop_count || 30)) * 100}
                indicatorClassName="bg-gradient-to-r from-success-500 to-success-400"
              />
            </div>

            <div className="p-4 rounded-lg bg-surface-400/50">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Smartphone size={16} className="text-warning-500" />
                  <span className="text-sm font-medium text-dark-200">移动搜索</span>
                </div>
                <span className="text-sm font-mono text-dark-300">
                  {taskStatus?.mobile_searches_completed ?? 0} / {taskStatus?.mobile_searches_total || config?.search.mobile_count || 20}
                </span>
              </div>
              <Progress 
                value={((taskStatus?.mobile_searches_completed ?? 0) / (taskStatus?.mobile_searches_total || config?.search.mobile_count || 20)) * 100}
                indicatorClassName="bg-gradient-to-r from-warning-500 to-warning-400"
              />
            </div>

            <div className="p-4 rounded-lg bg-surface-400/50">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Award size={16} className="text-primary-500" />
                  <span className="text-sm font-medium text-dark-200">每日任务</span>
                </div>
                <span className="text-sm font-mono text-dark-300">
                  {points?.points_gained_today ?? 0} 积分
                </span>
              </div>
              <div className="text-xs mt-1 text-dark-400">
                今日已获得积分
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2.5">
              <AlertTriangle size={18} className="text-primary-500" />
              任务提示
            </CardTitle>
          </CardHeader>
          <CardContent>
            {(() => {
              const tips: { type: 'error' | 'warning' | 'info'; message: string }[] = []
              
              const desktopTotal = taskStatus?.desktop_searches_total || config?.search.desktop_count || 30
              const mobileTotal = taskStatus?.mobile_searches_total || config?.search.mobile_count || 20
              const desktopCompleted = taskStatus?.desktop_searches_completed ?? 0
              const mobileCompleted = taskStatus?.mobile_searches_completed ?? 0
              
              if (taskStatus?.error_count && taskStatus.error_count > 0) {
                tips.push({ type: 'error', message: `任务执行过程中出现 ${taskStatus.error_count} 个错误` })
              }
              
              if (taskStatus?.warning_count && taskStatus.warning_count > 0) {
                tips.push({ type: 'warning', message: `任务执行过程中出现 ${taskStatus.warning_count} 个提示` })
              }
              
              const desktopRemaining = desktopTotal - desktopCompleted
              const mobileRemaining = mobileTotal - mobileCompleted
              
              if (desktopRemaining > 0 && !taskStatus?.is_running) {
                tips.push({ type: 'info', message: `桌面搜索还有 ${desktopRemaining} 次未完成` })
              }
              
              if (mobileRemaining > 0 && !taskStatus?.is_running) {
                tips.push({ type: 'info', message: `移动搜索还有 ${mobileRemaining} 次未完成` })
              }
              
              if (health?.overall === 'error') {
                tips.push({ type: 'error', message: '系统状态异常，请检查服务是否正常运行' })
              }
              
              if (points?.current_points === null || points?.current_points === undefined) {
                tips.push({ type: 'warning', message: '当前积分获取失败，请检查后端服务或登录状态' })
              }
              
              const allCompleted = desktopRemaining <= 0 && mobileRemaining <= 0
              
              if (tips.length === 0) {
                return (
                  <div className="flex items-center gap-3 p-4 rounded-lg border bg-success-500/5 border-success-500/20">
                    <CheckCircle size={18} className="text-success-500" />
                    <span className="text-dark-200">
                      {allCompleted ? '所有任务已完成' : '暂无提示'}
                    </span>
                  </div>
                )
              }
              
              return (
                <div className="space-y-3">
                  {tips.map((tip, index) => (
                    <motion.div 
                      key={index}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className={cn(
                        'flex items-start gap-3 p-3 rounded-lg border',
                        tip.type === 'error' 
                          ? 'bg-danger-500/5 border-danger-500/20'
                          : tip.type === 'warning' 
                          ? 'bg-warning-500/5 border-warning-500/20'
                          : 'bg-primary-500/5 border-primary-500/20'
                      )}
                    >
                      <AlertTriangle size={16} className={cn(
                        'flex-shrink-0 mt-0.5',
                        tip.type === 'error' ? 'text-danger-500' :
                        tip.type === 'warning' ? 'text-warning-500' :
                        'text-primary-500'
                      )} />
                      <span className="text-sm text-dark-200">{tip.message}</span>
                    </motion.div>
                  ))}
                </div>
              )
            })()}
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
                  <h2 className="text-lg font-semibold flex items-center gap-2.5 text-dark-100">
                    <motion.div 
                      animate={{ scale: [1, 1.2, 1] }}
                      transition={{ duration: 1, repeat: Infinity }}
                      className="w-2.5 h-2.5 bg-success-500 rounded-full shadow-lg shadow-success-500/50" 
                    />
                    任务执行中
                  </h2>
                  <span className="text-sm text-dark-400">
                    已运行 {formatUptime(taskStatus.elapsed_seconds)}
                  </span>
                </div>
                
                <div className="mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-dark-300">{taskStatus.current_operation}</span>
                    <span className="text-sm font-mono text-dark-400">{taskStatus.progress}/{taskStatus.total_steps}</span>
                  </div>
                  <Progress 
                    value={(taskStatus.progress / taskStatus.total_steps) * 100}
                  />
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="flex flex-col items-start gap-1 p-3 rounded-lg bg-surface-400/50">
                    <div className="text-sm text-dark-400">初始积分</div>
                    <div className="text-lg font-medium text-dark-100">{taskStatus.initial_points?.toLocaleString() ?? '---'}</div>
                  </div>
                  <div className="flex flex-col items-start gap-1 p-3 rounded-lg bg-surface-400/50">
                    <div className="text-sm text-dark-400">当前积分</div>
                    <div className="text-lg font-medium text-dark-100">{taskStatus.current_points?.toLocaleString() ?? '---'}</div>
                  </div>
                  <div className="flex flex-col items-start gap-1 p-3 rounded-lg bg-surface-400/50">
                    <div className="text-sm text-dark-400">获得积分</div>
                    <div className="text-lg font-medium text-success-500">+{taskStatus.points_gained}</div>
                  </div>
                  <div className="flex flex-col items-start gap-1 p-3 rounded-lg bg-surface-400/50">
                    <div className="text-sm text-dark-400">错误/警告</div>
                    <div className="text-lg font-medium">
                      <span className="text-danger-500">{taskStatus.error_count}</span>
                      <span className="mx-1 text-dark-500">/</span>
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
