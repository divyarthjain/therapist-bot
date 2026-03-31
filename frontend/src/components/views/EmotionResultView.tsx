import { EMOTION_EMOJI } from '../../types'
import type { AudioAnalysisResult } from '../../types'
import type { ViewState } from '../Navigation'
import './EmotionResultView.css'

interface Props {
  result: AudioAnalysisResult | null
  onNavigate: (view: ViewState) => void
}

export function EmotionResultView({ result, onNavigate }: Props) {
  if (!result) {
    return (
      <div className="result-view flex-center">
        <h2 className="title-medium">No recent analysis</h2>
        <button className="btn-primary mt-4" onClick={() => onNavigate('audio')}>Go Record</button>
      </div>
    )
  }

  const emotion = result.emotion || 'neutral'
  const emoji = EMOTION_EMOJI[emotion] || '😐'
  const colorVar = `var(--color-${emotion})`

  return (
    <div className="result-view flex-center">
      <div className="card text-center" style={{ width: '100%' }}>
        <h2 className="title-large">Detected Emotion</h2>
        
        <div className="emotion-display" style={{ backgroundColor: colorVar }}>
          <span className="emotion-emoji">{emoji}</span>
        </div>
        
        <h3 className="title-medium" style={{ textTransform: 'capitalize' }}>
          {emotion}
        </h3>
        
        <p className="text-body mb-4" style={{ backgroundColor: '#F8F9FA', padding: '16px', borderRadius: '12px' }}>
          "{result.transcription}"
        </p>
        
        <div className="suggestion-card mb-4" style={{ borderColor: colorVar }}>
           <strong>Tip: </strong> 
           {emotion === 'happy' && "Keep riding this positive wave!"}
           {emotion === 'sad' && "It's okay to feel down. Try a 5-minute breathing exercise."}
           {emotion === 'angry' && "Take a step back. Count to 10 and drink some water."}
           {emotion === 'calm' && "Such a serene moment. Reflect on what brings you peace."}
           {emotion === 'fearful' && "You are safe. Ground yourself by finding 5 things you can see."}
           {emotion === 'disgusted' && "If something is bothering you, giving it space helps."}
           {emotion === 'surprised' && "Unexpected things happen! Embrace the novelty."}
           {emotion === 'neutral' && "A steady state is a good foundation for a great day."}
        </div>

        <button className="btn-primary" onClick={() => onNavigate('chat')}>
          💬 Discuss this with Serenity
        </button>
      </div>
    </div>
  )
}
