import { ReactNode } from 'react'
import { motion } from 'framer-motion'
import Sidebar from './Sidebar'
import Header from './Header'
import { useStore } from '../store'
import clsx from 'clsx'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const { sidebarCollapsed, darkMode } = useStore()

  return (
    <div className={clsx(
      'min-h-screen flex transition-colors duration-300',
      darkMode ? 'bg-dark-900' : 'bg-light-100'
    )}>
      <Sidebar />
      <motion.div 
        animate={{ marginLeft: sidebarCollapsed ? 64 : 240 }}
        transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
        className="flex-1 flex flex-col"
      >
        <Header />
        <main className={clsx(
          'flex-1 p-6 overflow-auto transition-colors duration-300',
          darkMode 
            ? 'bg-gradient-to-br from-dark-900 via-surface-300/50 to-dark-900' 
            : 'bg-gradient-to-br from-light-100 via-white to-light-100'
        )}>
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            {children}
          </motion.div>
        </main>
      </motion.div>
    </div>
  )
}
