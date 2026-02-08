import { useState } from 'react'
import CameraCapture from './components/CameraCapture'
import UserProfile, {type UserData} from './components/UserProfile'
import Sidebar from './components/Sidebar'
import './App.css'

function App() {
  // State to track which page is visible
  const [currentPage, setCurrentPage] = useState<'camera' | 'profile'>('camera')
  
  // State to track if sidebar is open
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [userProfile, setUserProfile] = useState<UserData>({
    goal: 'loss',
    diet: 'Halal',
    peanut: false,
    tree_nut: false,
    dairy: false,
    gluten: false,
    egg: false,
    shellfish: false,
    sesame: false,
    soy: false,
    avoid_artificial_colors: false,
    avoid_artificial_sweeteners: false,
    avoid_ultra_processed: false,
    caffeine_sensitive: false,
    flags: []
  })  

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
          <CameraCapture {...userProfile} />
        ) : (
          <UserProfile {...userProfile} setUserProfile={setUserProfile} />
        )}
      </div>

    </div>
  )
}

export default App