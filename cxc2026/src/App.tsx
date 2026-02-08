import { useState } from 'react'
import CameraCapture from './components/CameraCapture'
import UserProfile from './components/UserProfile'
import Sidebar from './components/Sidebar'
import './App.css'
import AudioButton from './components/AudioButton'

function App() {
  // State to track which page is visible
  const [currentPage, setCurrentPage] = useState<'camera' | 'profile'>('camera')
  
  // State to track if sidebar is open
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)

  return (
    <div className="app-container">
      {/* 1. THE SIDEBAR (Always rendered, but hidden off-screen) */}
      <Sidebar 
        isOpen={isSidebarOpen} 
        onClose={() => setIsSidebarOpen(false)}
        activePage={currentPage}
        onNavigate={setCurrentPage}
      />

      {/* 2. THE HAMBURGER BUTTON (Fixed to top-left) */}
      {!isSidebarOpen && (
        <button 
          className="hamburger-btn"
          onClick={() => setIsSidebarOpen(true)}
          // You can keep your inline style if you want, or remove it if using the CSS class we made earlier
          style={{ color: currentPage === 'camera' ? 'white' : 'black' }} 
        >
          ☰
        </button>
      )}

      {/* 3. PAGE CONTENT */}
      <div className="main-content">
        {currentPage === 'camera' ? (
          <CameraCapture />
        ) : (
          <UserProfile />
        )}
      </div>

    </div>
  )
}

export default App