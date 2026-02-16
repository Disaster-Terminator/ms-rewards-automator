import { NavLink } from 'react-router-dom'
import { 
  LayoutDashboard, 
  PlayCircle, 
  Settings, 
  FileText, 
  History,
  ChevronLeft,
  ChevronRight,
  Activity
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useStore } from '../store'
import { cn } from '@/lib/utils'
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from '@/components/ui/tooltip'

const navItems = [
  { path: '/', icon: LayoutDashboard, label: '仪表盘', color: 'primary' },
  { path: '/tasks', icon: PlayCircle, label: '任务控制', color: 'success' },
  { path: '/config', icon: Settings, label: '配置管理', color: 'warning' },
  { path: '/logs', icon: FileText, label: '日志查看', color: 'cyan' },
  { path: '/history', icon: History, label: '历史记录', color: 'purple' },
]

const colorClasses: Record<string, { active: string; icon: string }> = {
  primary: { active: 'bg-primary-500/10 text-primary-400 border-primary-500/30', icon: 'text-primary-400' },
  success: { active: 'bg-success-500/10 text-success-400 border-success-500/30', icon: 'text-success-400' },
  warning: { active: 'bg-warning-500/10 text-warning-400 border-warning-500/30', icon: 'text-warning-400' },
  cyan: { active: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30', icon: 'text-cyan-400' },
  purple: { active: 'bg-purple-500/10 text-purple-400 border-purple-500/30', icon: 'text-purple-400' },
}

const sidebarVariants = {
  expanded: { width: 240 },
  collapsed: { width: 64 },
}

const textVariants = {
  expanded: { opacity: 1, x: 0, display: 'block' },
  collapsed: { opacity: 0, x: -10, transitionEnd: { display: 'none' } },
}

export default function Sidebar() {
  const { sidebarCollapsed, toggleSidebar, taskStatus, wsConnected, darkMode } = useStore()

  return (
    <TooltipProvider delayDuration={0}>
      <motion.aside
        variants={sidebarVariants}
        animate={sidebarCollapsed ? 'collapsed' : 'expanded'}
        transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
        className={cn(
          'fixed left-0 top-0 h-full border-r z-50 flex flex-col',
          darkMode ? 'bg-surface-300 border-dark-600/50' : 'bg-white border-gray-200'
        )}
      >
        <div className={cn(
          'flex items-center justify-between h-14 px-3 border-b',
          darkMode ? 'border-dark-600/50' : 'border-gray-200'
        )}>
          <AnimatePresence mode="wait">
            {!sidebarCollapsed && (
              <motion.div 
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.2 }}
                className="flex items-center gap-2.5"
              >
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-primary-500/20">
                  <span className="text-dark-900 font-bold text-sm">MS</span>
                </div>
                <div className="flex flex-col">
                  <span className={cn(
                    'font-semibold text-sm leading-tight',
                    darkMode ? 'text-dark-100' : 'text-gray-900'
                  )}>Rewards</span>
                  <span className={cn(
                    'text-xs',
                    darkMode ? 'text-dark-400' : 'text-gray-500'
                  )}>Automator</span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          <motion.button
            onClick={toggleSidebar}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className={cn(
              'p-1.5 rounded-lg transition-colors',
              darkMode 
                ? 'text-dark-400 hover:text-dark-100 hover:bg-dark-600/50' 
                : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100',
              sidebarCollapsed && 'mx-auto'
            )}
          >
            {sidebarCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
          </motion.button>
        </div>

        <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors group',
                  isActive
                    ? colorClasses[item.color].active
                    : darkMode 
                      ? 'text-dark-400 hover:text-dark-100 hover:bg-dark-600/30'
                      : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100',
                  sidebarCollapsed && 'justify-center px-2'
                )
              }
            >
              {({ isActive }) => (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <motion.div
                      initial={false}
                      animate={{ scale: isActive ? 1.1 : 1 }}
                      className="flex items-center gap-3"
                    >
                      <item.icon 
                        size={20} 
                        className={cn(
                          'transition-transform duration-200 group-hover:scale-110',
                          isActive && colorClasses[item.color].icon
                        )} 
                      />
                      <AnimatePresence mode="wait">
                        {!sidebarCollapsed && (
                          <motion.span
                            variants={textVariants}
                            initial="collapsed"
                            animate="expanded"
                            exit="collapsed"
                            transition={{ duration: 0.2 }}
                            className="font-medium text-sm whitespace-nowrap"
                          >
                            {item.label}
                          </motion.span>
                        )}
                      </AnimatePresence>
                    </motion.div>
                  </TooltipTrigger>
                  {sidebarCollapsed && (
                    <TooltipContent side="right" sideOffset={10}>
                      {item.label}
                    </TooltipContent>
                  )}
                </Tooltip>
              )}
            </NavLink>
          ))}
        </nav>

        <div className={cn(
          'p-2 border-t',
          darkMode ? 'border-dark-600/50' : 'border-gray-200'
        )}>
          <AnimatePresence mode="wait">
            {!sidebarCollapsed ? (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                transition={{ duration: 0.2 }}
                className="space-y-2"
              >
                <div className={cn(
                  'flex items-center justify-between px-3 py-2 rounded-lg',
                  darkMode ? 'bg-dark-600/20' : 'bg-gray-100'
                )}>
                  <div className="flex items-center gap-2">
                    <Activity size={14} className={cn(
                      'transition-colors',
                      wsConnected ? 'text-success-400' : darkMode ? 'text-dark-500' : 'text-gray-400'
                    )} />
                    <span className={cn(
                      'text-xs',
                      darkMode ? 'text-dark-400' : 'text-gray-500'
                    )}>WebSocket</span>
                  </div>
                  <motion.div 
                    animate={{ 
                      scale: wsConnected ? [1, 1.2, 1] : 1,
                      backgroundColor: wsConnected ? '#98c379' : darkMode ? '#5c6370' : '#9ca3af'
                    }}
                    transition={{ duration: 0.3 }}
                    className={cn(
                      'w-2 h-2 rounded-full',
                      wsConnected && 'shadow-lg shadow-success-400/50'
                    )}
                  />
                </div>
                
                <AnimatePresence>
                  {taskStatus?.is_running && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="px-3 py-2 rounded-lg bg-success-500/10 border border-success-500/20"
                    >
                      <div className="flex items-center gap-2">
                        <motion.div 
                          animate={{ scale: [1, 1.2, 1] }}
                          transition={{ duration: 1, repeat: Infinity }}
                          className="w-2 h-2 bg-success-400 rounded-full shadow-lg shadow-success-400/50" 
                        />
                        <span className="text-xs text-success-400 font-medium">任务运行中</span>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
                
                <div className={cn(
                  'text-xs text-center py-1',
                  darkMode ? 'text-dark-500' : 'text-gray-400'
                )}>
                  v1.0.0
                </div>
              </motion.div>
            ) : (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex flex-col items-center gap-2 py-1"
              >
                <motion.div 
                  animate={{ 
                    scale: wsConnected ? [1, 1.2, 1] : 1,
                  }}
                  transition={{ duration: 0.3 }}
                  className={cn(
                    'w-2 h-2 rounded-full',
                    wsConnected ? 'bg-success-400 shadow-lg shadow-success-400/50' : darkMode ? 'bg-dark-500' : 'bg-gray-400'
                  )}
                />
                {taskStatus?.is_running && (
                  <motion.div 
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 1, repeat: Infinity }}
                    className="w-2 h-2 bg-success-400 rounded-full" 
                  />
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.aside>
    </TooltipProvider>
  )
}
