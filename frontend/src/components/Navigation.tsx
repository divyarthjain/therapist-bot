import './Navigation.css'

export type ViewState = 'home' | 'audio' | 'result' | 'chat' | 'profile'

interface Props {
  currentView: ViewState
  onNavigate: (view: ViewState) => void
}

export function Navigation({ currentView, onNavigate }: Props) {
  return (
    <nav className="bottom-nav">
      <button 
        className={`nav-btn ${currentView === 'home' || currentView === 'audio' || currentView === 'result' ? 'active' : ''}`}
        onClick={() => onNavigate('home')}
      >
        <span className="nav-icon">🏠</span>
        <span className="nav-label">Home</span>
      </button>

      <button 
        className={`nav-btn ${currentView === 'chat' ? 'active' : ''}`}
        onClick={() => onNavigate('chat')}
      >
        <span className="nav-icon">💬</span>
        <span className="nav-label">Chat</span>
      </button>

      <button 
        className={`nav-btn ${currentView === 'profile' ? 'active' : ''}`}
        onClick={() => onNavigate('profile')}
      >
        <span className="nav-icon">👤</span>
        <span className="nav-label">Profile</span>
      </button>
    </nav>
  )
}
