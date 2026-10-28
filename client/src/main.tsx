import React from 'react'
import ReactDOM from 'react-dom/client'
import { Toaster } from 'react-hot-toast'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
    <Toaster
      position="top-right"
      toastOptions={{
        duration: 4000,
        style: { borderRadius: '10px', background: '#333', color: '#fff' },
        success: { style: { background: '#254B45', color: '#fff' } },
        error: { style: { background: '#dc2626', color: '#fff' } },
      }}
    />
  </React.StrictMode>
)
