import type { ReactNode } from 'react'
import type { CallState, EmotionState } from '../types'
import { EMOTION_EMOJI } from '../types'
import './CallOverlay.css'

interface Props {
  callState: CallState
  emotionState: EmotionState | null
  isConnected: boolean
  lastUserText?: string
  lastAssistantText?: string
  onEndCall: () => void
  children?: ReactNode
}

const CALL_LABELS: Record<CallState, string> = {
  idle: 'Idle',
  listening: 'Listening',
  processing: 'Thinking',
  speaking: 'Speaking',
}

export function CallOverlay({
  callState,
  emotionState,
  isConnected,
  lastUserText,
  lastAssistantText,
  onEndCall,
  children,
}: Props) {
  const dominantEmotion = emotionState?.dominant ?? 'neutral'
  const emotionLabel = `${EMOTION_EMOJI[dominantEmotion] ?? '😐'} ${dominantEmotion}`

  return (
    <div className="call-overlay">
      <div className="call-overlay__backdrop" />
      <div className="call-overlay__shell">
        <div className="call-overlay__header">
          <div>
            <p className="call-overlay__eyebrow">Live therapy session</p>
            <h2 className="call-overlay__title">Dr. Serenity</h2>
          </div>
          <div className={`call-overlay__status ${isConnected ? 'online' : 'offline'}`}>
            <span className="call-overlay__status-dot" />
            <span>{isConnected ? 'Connected' : 'Reconnecting'}</span>
          </div>
        </div>

        <div className="call-overlay__media">
          <div className="call-overlay__video-panel">{children}</div>
          <div className="call-overlay__insights">
            <div className="call-overlay__signal">
              <div className={`call-overlay__orb call-overlay__orb--${callState}`} />
              <div>
                <p className="call-overlay__signal-label">{CALL_LABELS[callState]}</p>
                <p className="call-overlay__signal-subtitle">
                  Continuous voice turn-taking is active
                </p>
              </div>
            </div>

            <div className="call-overlay__emotion-card">
              <span className="call-overlay__card-label">Current emotional read</span>
              <strong>{emotionLabel}</strong>
              <span className="call-overlay__confidence">
                {Math.round((emotionState?.confidence ?? 0) * 100)}% confidence
              </span>
            </div>

            <div className="call-overlay__emotion-grid">
              <div className="call-overlay__mini-card">
                <span>Voice</span>
                <strong>
                  {EMOTION_EMOJI[emotionState?.audio.emotion ?? 'neutral'] ?? '😐'}{' '}
                  {emotionState?.audio.emotion ?? 'neutral'}
                </strong>
              </div>
              <div className="call-overlay__mini-card">
                <span>Face</span>
                <strong>
                  {EMOTION_EMOJI[emotionState?.video.emotion ?? 'neutral'] ?? '😐'}{' '}
                  {emotionState?.video.emotion ?? 'neutral'}
                </strong>
              </div>
            </div>

            <div className="call-overlay__transcript">
              <span className="call-overlay__card-label">You said</span>
              <p>{lastUserText || 'Start speaking whenever you are ready.'}</p>
            </div>

            <div className="call-overlay__transcript">
              <span className="call-overlay__card-label">Assistant</span>
              <p>{lastAssistantText || 'I am here with you.'}</p>
            </div>
          </div>
        </div>

        <div className="call-overlay__footer">
          <button className="call-overlay__end-call" onClick={onEndCall}>
            End Call
          </button>
        </div>
      </div>
    </div>
  )
}
