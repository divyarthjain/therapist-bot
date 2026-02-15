import { useMemo } from 'react'
import type { EmotionState } from '../types'
import './TherapistVisual.css'

interface Props {
  isStreaming: boolean
  emotionState: EmotionState | null
}

export function TherapistVisual({ isStreaming, emotionState }: Props) {
  const dominantEmotion = useMemo(() => {
    if (!emotionState) return null
    return emotionState.dominant
  }, [emotionState])

  return (
    <div className="therapist-visual">
      <div className="therapist-visual__orb-container">
        <div className="therapist-visual__glow" />
        <div 
          className={`therapist-visual__orb ${isStreaming ? 'therapist-visual__orb--streaming' : ''}`} 
        />
      </div>

      <div className="therapist-visual__info">
        <h2 className="therapist-visual__name">Dr. Serenity</h2>
        <div className="therapist-visual__role">AI Therapist</div>
      </div>

      {dominantEmotion && (
        <div className="therapist-visual__emotion">
          <span>Detected:</span>
          <span style={{ color: '#fff', fontWeight: 500 }}>{dominantEmotion}</span>
        </div>
      )}
    </div>
  )
}
