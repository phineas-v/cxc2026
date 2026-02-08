import './Sidebar.css'

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
  onNavigate: (page: 'camera' | 'profile') => void
  activePage: 'camera' | 'profile'
}

export default function Sidebar({ isOpen, onClose, onNavigate, activePage }: SidebarProps) {
  
  const handleNav = (page: 'camera' | 'profile') => {
    onNavigate(page)
    onClose() // Close sidebar after clicking
  }

  return (
    <>
      <div className={`sidebar-backdrop ${isOpen ? 'open' : ''}`} onClick={onClose} />
      <div className={`sidebar-panel ${isOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <h2>Menu</h2>
          <button onClick={onClose} className="close-btn">✕</button>
        </div>

        <nav className="sidebar-nav">
          <button 
            className={`nav-item ${activePage === 'camera' ? 'active' : ''}`}
            onClick={() => handleNav('camera')}
          >
            📸 Scan Food
          </button>
          
          <button 
            className={`nav-item ${activePage === 'profile' ? 'active' : ''}`}
            onClick={() => handleNav('profile')}
          >
            👤 My Profile
          </button>
        </nav>
      </div>
    </>
  )
}