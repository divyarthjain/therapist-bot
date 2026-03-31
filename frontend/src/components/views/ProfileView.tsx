import { useAuth } from '../../hooks/useAuth'
import { supabase } from '../../lib/supabase'
import './ProfileView.css'

export function ProfileView() {
  const { isDummyConfig, dummyLogout, user } = useAuth()

  const handleLogout = async () => {
    if (isDummyConfig) {
      dummyLogout()
      return
    }
    await supabase.auth.signOut()
  }
  return (
    <div className="profile-view">
      <div className="profile-header flex-center">
        <div className="profile-avatar">
          <img src="https://i.pravatar.cc/150?u=a042581f4e29026704d" alt="User Avatar" />
        </div>
        <h2 className="title-medium mt-2" style={{ marginBottom: '4px' }}>{user?.email?.split('@')[0] || "Guest Writer"}</h2>
        <p className="text-body" style={{ fontSize: '13px' }}>{user?.email || "guest@example.com"}</p>
      </div>

      <div className="card mt-3">
         <h3 className="title-medium">Your Mood History</h3>
         <div className="mood-history-list">
            <div className="mood-item">
              <span className="mood-emoji" style={{backgroundColor: 'var(--color-happy)'}}>😊</span>
              <div className="mood-details">
                <div className="mood-date">Today</div>
                <div className="mood-name">Happy & Calmed</div>
              </div>
            </div>
            <div className="mood-item">
              <span className="mood-emoji" style={{backgroundColor: 'var(--color-neutral)'}}>😐</span>
              <div className="mood-details">
                <div className="mood-date">Yesterday</div>
                <div className="mood-name">Neutral</div>
              </div>
            </div>
            <div className="mood-item">
              <span className="mood-emoji" style={{backgroundColor: 'var(--color-fearful)'}}>😨</span>
              <div className="mood-details">
                <div className="mood-date">Monday</div>
                <div className="mood-name">Anxious</div>
              </div>
            </div>
         </div>
      </div>

      <div className="menu-list mt-3">
         <button className="menu-item flex-between">
           <span>Profile Settings</span>
           <span className="menu-arrow">›</span>
         </button>
         <button className="menu-item flex-between">
           <span>Notifications</span>
           <span className="menu-arrow">›</span>
         </button>
         <button className="menu-item flex-between" style={{ color: 'var(--color-error)' }} onClick={handleLogout}>
           <span>Logout</span>
           <span className="menu-arrow" style={{color: 'transparent'}}>›</span>
         </button>
      </div>
    </div>
  )
}
