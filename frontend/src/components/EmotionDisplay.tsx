import type { EmotionState } from '../types'
import { EMOTION_EMOJI, EMOTION_COLORS } from '../types'
import './EmotionDisplay.css'

interface Props {
  emotionState: EmotionState | null
}

const EMOTIONS = ['happy', 'sad', 'angry', 'neutral', 'fearful', 'disgusted', 'surprised'] as const

export function EmotionDisplay({ emotionState }: Props) {
  if (!emotionState) {
    return (
      <div className="emotion-display">
        <h3 className="emotion-display__title">Emotional State</h3>
        <p className="emotion-display__empty">No emotion data yet. Start a conversation or enable your camera.</p>
      </div>
    )
  }

  const { dominant, confidence, audio, video, fused_scores, incongruence } = emotionState

  return (
    <div className="emotion-display">
      <h3 className="emotion-display__title">Emotional State</h3>

      {/* Dominant emotion */}
      <div className="emotion-display__dominant">
        <span className="emotion-display__emoji">
          {EMOTION_EMOJI[dominant] ?? '😐'}
        </span>
        <div>
          <div className="emotion-display__label">{dominant}</div>
          <div className="emotion-display__confidence-bar">
            <div
              className="emotion-display__confidence-fill"
              style={{
                width: `${Math.round(confidence * 100)}%`,
                background: EMOTION_COLORS[dominant] ?? '#B0BEC5',
              }}
            />
          </div>
          <span className="emotion-display__confidence-text">
            {Math.round(confidence * 100)}% confidence
          </span>
        </div>
      </div>

      {/* Incongruence warning */}
      {incongruence && (
        <div className="emotion-display__incongruence">
          ⚠️ Voice and facial expressions differ
        </div>
      )}

      {/* Modality breakdown */}
      <div className="emotion-display__modalities">
        <div className="emotion-display__modality">
          <span className="modality-label">🎙️ Voice</span>
          <span className="modality-value">
            {EMOTION_EMOJI[audio.emotion] ?? '😐'} {audio.emotion}
          </span>
        </div>
        <div className="emotion-display__modality">
          <span className="modality-label">📷 Face</span>
          <span className="modality-value">
            {EMOTION_EMOJI[video.emotion] ?? '😐'} {video.emotion}
          </span>
        </div>
      </div>

      {/* Fused scores bars */}
      <div className="emotion-display__scores">
        {EMOTIONS.map((emo) => {
          const score = fused_scores[emo] ?? 0
          if (score < 0.01) return null
          return (
            <div key={emo} className="emotion-display__score-row">
              <span className="score-label">
                {EMOTION_EMOJI[emo]} {emo}
              </span>
              <div className="score-bar">
                <div
                  className="score-bar__fill"
                  style={{
                    width: `${Math.round(score * 100)}%`,
                    background: EMOTION_COLORS[emo] ?? '#B0BEC5',
                  }}
                />
              </div>
              <span className="score-value">{Math.round(score * 100)}%</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
