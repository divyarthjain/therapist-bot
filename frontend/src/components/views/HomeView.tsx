import type { ViewState } from '../Navigation'
import type { EmotionState } from '../../types'
import './HomeView.css'

interface Props {
  onNavigate: (view: ViewState) => void
  onStartCall: () => void
  isCallActive: boolean
  emotionSummary?: EmotionState | null
}

export function HomeView({ onNavigate, onStartCall, isCallActive, emotionSummary }: Props) {
  const getLivePrompt = () => {
    if (!emotionSummary || emotionSummary.dominant === 'neutral') {
      return 'Start speaking naturally. The therapist will listen, transcribe, and respond out loud.'
    }

    const moodMap: Record<string, string> = {
      happy: 'You sound steady and upbeat. We can build on that energy.',
      sad: 'You seem low right now. The live therapist is ready to slow down and listen.',
      angry: 'There is tension coming through. We can work through it in real time.',
      fearful: 'You seem anxious. The call flow is set up to respond gently and quickly.',
      disgusted: 'Something feels off. We can unpack it together live.',
      surprised: 'Something shifted. We can talk through it right away.',
      calm: 'You seem calm. This is a good moment to check in deeply.',
    }

    return moodMap[emotionSummary.dominant] || 'Start speaking naturally. The therapist is ready.'
  }

  return (
    <div className="home-view">
      <div className="home-header">
        <h1 className="title-large">Live Therapist</h1>
        <p className="text-body">Voice-first therapy with live listening, live speaking, and emotion-aware responses.</p>
      </div>

      <div className="card home-hero">
        <div className="home-hero__status">
          <span className={`home-hero__status-dot ${isCallActive ? 'active' : ''}`} />
          <span>{isCallActive ? 'Live call ready' : 'Standby'}</span>
        </div>

        <h2 className="title-medium">ChatGPT-style voice session</h2>
        <p className="text-body home-hero__copy">
          {getLivePrompt()}
        </p>

        <div className="home-actions">
          <button className="btn-primary" onClick={onStartCall}>
            {isCallActive ? 'Return To Live Call' : 'Start Live Call'}
          </button>
          <button className="btn-secondary" onClick={() => onNavigate('chat')}>
            Open Therapist Chat
          </button>
        </div>
      </div>

      <div className="card home-stack">
        <h3 className="title-medium" style={{ fontSize: '18px' }}>Voice stack</h3>
        <p className="text-body">
          Live microphone capture feeds STT, emotion analysis, Gemini therapist reasoning, and spoken reply playback in one loop.
        </p>
        <div className="home-stack__chips">
          <span className="home-stack__chip">Live STT</span>
          <span className="home-stack__chip">Emotion Fusion</span>
          <span className="home-stack__chip">Therapist LLM</span>
          <span className="home-stack__chip">Realtime TTS</span>
        </div>
      </div>
    </div>
  )
}
