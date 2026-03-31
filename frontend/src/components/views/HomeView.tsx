import type { ViewState } from '../Navigation'
import type { EmotionState } from '../../types'
import './HomeView.css'

interface Props {
  onNavigate: (view: ViewState) => void
  emotionSummary?: EmotionState | null
}

export function HomeView({ onNavigate, emotionSummary }: Props) {
  // Mock a simple message based on emotion
  const getDailyMessage = () => {
    if (!emotionSummary || emotionSummary.dominant === 'neutral') {
       return "How are you feeling today?"
    }
    const moodMap: Record<string, string> = {
      happy: "You seem happy today! 😊",
      sad: "Take it easy today. I'm here to listen. 💙",
      angry: "It's okay to feel frustrated. Take a deep breath. 🌿",
      fearful: "You are safe here. Let's talk about it. 🌸",
      disgusted: "Something bothering you? Let's unpack it. 🤔",
      surprised: "Feeling surprised? What's on your mind? 😲",
      calm: "You seem calm today. Keep it up! 🍃"
    }
    return moodMap[emotionSummary.dominant] || "How are you feeling today?"
  }

  return (
    <div className="home-view">
      <div className="home-header">
        <h1 className="title-large">Hi, Welcome back!</h1>
        <p className="text-body">Your AI Therapist companion is ready to listen.</p>
      </div>

      <div className="card card--gradient">
        <h2 className="title-medium">Daily Check-in</h2>
        <p className="text-body" style={{ color: '#5C4A82', marginBottom: '16px' }}>
          {getDailyMessage()}
        </p>
        <div className="home-actions">
           <button className="btn-primary" onClick={() => onNavigate('audio')}>
              🎙️ Voice Journal
           </button>
           <button className="btn-secondary mt-2" onClick={() => onNavigate('chat')}>
              💬 Start Chat
           </button>
        </div>
      </div>

      <div className="card">
        <h3 className="title-medium" style={{ fontSize: '18px' }}>Recent Insights</h3>
        <p className="text-body">You've had 3 sessions this week. Your average mood has been <strong style={{color: 'var(--color-primary-dark)'}}>Calm</strong>.</p>
        <div className="insight-icons">
          <div className="insight-pulse animate-pulse-soft">🌿</div>
        </div>
      </div>
    </div>
  )
}
