import type { CallState } from '../types'
import './CallOverlay.css'

interface Props {
  callState: CallState
  isConnected: boolean
  lastUserText?: string
  lastAssistantText?: string
  onEndCall: () => void
}

const STATE_LABELS: Record<CallState, string> = {
  idle: 'Ready',
  listening: 'Listening…',
  processing: 'Thinking…',
  speaking: 'Speaking…',
}

export function CallOverlay({
  callState,
  isConnected,
  lastUserText,
  lastAssistantText,
  onEndCall,
}: Props) {
  return (
    <div className="voice-overlay">
      <div className="voice-overlay__backdrop" />

      <div className="voice-overlay__content">
        {/* Status bar */}
        <div className="voice-overlay__status-bar">
          <div className={`voice-overlay__conn-dot ${isConnected ? 'online' : ''}`} />
          <span className="voice-overlay__conn-label">
            {isConnected ? 'Connected' : 'Reconnecting…'}
          </span>
        </div>

        {/* Center orb area */}
        <div className="voice-overlay__center">
          <div className={`voice-orb voice-orb--${callState}`}>
            <div className="voice-orb__ring voice-orb__ring--1" />
            <div className="voice-orb__ring voice-orb__ring--2" />
            <div className="voice-orb__ring voice-orb__ring--3" />
            <div className="voice-orb__core" />
          </div>

          <p className="voice-overlay__state-label">{STATE_LABELS[callState]}</p>
        </div>

        {/* Transcript area */}
        <div className="voice-overlay__transcripts">
          {lastUserText && (
            <div className="voice-overlay__transcript voice-overlay__transcript--user">
              <span className="voice-overlay__who">You</span>
              <p>{lastUserText}</p>
            </div>
          )}
          {lastAssistantText && (
            <div className="voice-overlay__transcript voice-overlay__transcript--ai">
              <span className="voice-overlay__who">Serenity</span>
              <p>{lastAssistantText}</p>
            </div>
          )}
          {!lastUserText && !lastAssistantText && (
            <p className="voice-overlay__hint">Start speaking — I'm listening.</p>
          )}
        </div>

        {/* End call button */}
        <div className="voice-overlay__footer">
          <button className="voice-overlay__end-btn" onClick={onEndCall}>
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
          <span className="voice-overlay__end-label">End</span>
        </div>
      </div>
    </div>
  )
}
