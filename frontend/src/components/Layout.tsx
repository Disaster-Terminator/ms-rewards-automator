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
      darkMode ? 'bg-canvas' : 'bg-canvas-light'
    )}>
      <Sidebar />
      <motion.div 
        animate={{ marginLeft: sidebarCollapsed ? 64 : 240 }}
        transition={{ type: 'spring', stiffness: 300, damping: 30, mass: 0.8 }}
        className="flex-1 flex flex-col"
      >
        <Header />
        <main className={clsx(
          'flex-1 p-6 overflow-auto transition-colors duration-300 max-w-7xl mx-auto w-full',
          darkMode 
            ? 'bg-gradient-to-br from-canvas via-surface/30 to-canvas' 
            : 'bg-gradient-to-br from-canvas-light via-white/50 to-canvas-light'
        )}>
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ type: 'spring', stiffness: 260, damping: 20 }}
          >
            {children}
          </motion.div>
        </main>
      </motion.div>
    </div>
  )
}
