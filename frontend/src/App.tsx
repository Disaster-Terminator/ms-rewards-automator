import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Config from './pages/Config'
import Logs from './pages/Logs'
import History from './pages/History'
import { useStore } from './store'
import { TooltipProvider } from '@/components/ui/tooltip'
import { Toaster } from '@/components/ui/sonner'

function App() {
  const { darkMode } = useStore()

  return (
    <TooltipProvider>
      <div className={darkMode ? 'dark' : 'light'}>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/config" element={<Config />} />
            <Route path="/logs" element={<Logs />} />
            <Route path="/history" element={<History />} />
          </Routes>
        </Layout>
        <Toaster position="bottom-right" richColors closeButton />
      </div>
    </TooltipProvider>
  )
}

export default App
