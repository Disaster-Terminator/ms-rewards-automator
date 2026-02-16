import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'
import { initializeTauriEvents, connectWebSocket, initializeData, startHeartbeat } from './api'

const MAX_INIT_RETRIES = 5
const INIT_RETRY_DELAY = 2000

const init = async (retryCount = 0): Promise<void> => {
  try {
    await initializeTauriEvents()
    await connectWebSocket()
    await initializeData()
    startHeartbeat()
  } catch (error) {
    console.error(`Initialization failed (attempt ${retryCount + 1}/${MAX_INIT_RETRIES}):`, error)
    
    if (retryCount < MAX_INIT_RETRIES - 1) {
      await new Promise(resolve => setTimeout(resolve, INIT_RETRY_DELAY))
      return init(retryCount + 1)
    } else {
      console.error('Max initialization retries reached')
    }
  }
}

init()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)
