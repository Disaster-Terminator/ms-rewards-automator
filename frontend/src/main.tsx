import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'
import { initializeTauriEvents, connectWebSocket, initializeData, startHeartbeat } from './api'

const MAX_INIT_RETRIES = 10
const INIT_RETRY_DELAY = 1500

const init = async (retryCount = 0): Promise<void> => {
  console.log(`Initializing application (attempt ${retryCount + 1}/${MAX_INIT_RETRIES})...`)
  
  try {
    await initializeTauriEvents()
    
    await connectWebSocket()
    
    await initializeData()
    
    startHeartbeat()
    
    console.log('Application initialized successfully')
  } catch (error) {
    console.error(`Initialization failed (attempt ${retryCount + 1}/${MAX_INIT_RETRIES}):`, error)
    
    if (retryCount < MAX_INIT_RETRIES - 1) {
      const delay = INIT_RETRY_DELAY * Math.min(retryCount + 1, 5)
      console.log(`Retrying in ${delay}ms...`)
      await new Promise(resolve => setTimeout(resolve, delay))
      return init(retryCount + 1)
    } else {
      console.error('Max initialization retries reached. Please check if the backend is running.')
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
