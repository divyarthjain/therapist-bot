import type { CallState } from '../types'
import './TherapistVisual.css'

interface Props {
  isStreaming: boolean
  callState?: CallState
}

export function TherapistVisual({ isStreaming, callState }: Props) {
  let orbClass = 'therapist-visual__orb'
  
  if (isStreaming) {
    orbClass += ' therapist-visual__orb--streaming'
  }
  
  if (callState === 'listening') {
    orbClass += ' therapist-visual__orb--listening'
  } else if (callState === 'processing') {
    orbClass += ' therapist-visual__orb--processing'
  } else if (callState === 'speaking') {
    orbClass += ' therapist-visual__orb--speaking'
  }

  return (
    <div className="therapist-visual">
      <div className="therapist-visual__orb-container">
        <div className="therapist-visual__glow" />
        <div className={orbClass} />
      </div>

      <div className="therapist-visual__info">
        <h2 className="therapist-visual__name">Dr. Serenity</h2>
        <div className="therapist-visual__role">AI Therapist</div>
        {callState && callState !== 'idle' && (
          <div className={`therapist-visual__call-status therapist-visual__call-status--${callState}`}>
            {callState === 'listening' ? 'Listening…' : callState === 'processing' ? 'Processing…' : 'Speaking…'}
          </div>
        )}
      </div>
    </div>
  )
}
