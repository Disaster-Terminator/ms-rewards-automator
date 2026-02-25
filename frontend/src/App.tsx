import { Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import { useStore } from './store'
import { TooltipProvider } from '@/components/ui/tooltip'
import { Toaster } from '@/components/ui/sonner'

function App() {
  const { darkMode } = useStore()

  return (
    <TooltipProvider>
      <div className={darkMode ? 'dark' : 'light'}>
        <Routes>
          <Route path="*" element={<Dashboard />} />
        </Routes>
        <Toaster position="bottom-right" richColors closeButton />
      </div>
    </TooltipProvider>
  )
}

export default App
