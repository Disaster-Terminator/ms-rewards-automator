import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Tasks from './pages/Tasks'
import Config from './pages/Config'
import Logs from './pages/Logs'
import History from './pages/History'
import { useStore } from './store'
import { TooltipProvider } from '@/components/ui/tooltip'

function App() {
  const { darkMode } = useStore()

  return (
    <TooltipProvider>
      <div className={darkMode ? 'dark' : 'light'}>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/tasks" element={<Tasks />} />
            <Route path="/config" element={<Config />} />
            <Route path="/logs" element={<Logs />} />
            <Route path="/history" element={<History />} />
          </Routes>
        </Layout>
      </div>
    </TooltipProvider>
  )
}

export default App
