import { useCallback, useState } from 'react'
import { useAudioRecorder } from '../../hooks/useAudioRecorder'
import type { AudioAnalysisResult } from '../../types'
import type { ViewState } from '../Navigation'
import './AudioUploadView.css'

interface Props {
  sessionId: string | null
  onAnalysisResult: (result: AudioAnalysisResult) => void
  onNavigate: (view: ViewState) => void
}

export function AudioUploadView({ sessionId, onAnalysisResult, onNavigate }: Props) {
  const { isRecording, permissionDenied, startRecording, stopRecording } = useAudioRecorder()
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const handleToggleRecord = useCallback(async () => {
    setErrorMsg(null)
    
    if (isRecording) {
      const blob = await stopRecording()
      if (blob.size === 0) return

      setIsAnalyzing(true)
      try {
        const formData = new FormData()
        formData.append('file', blob, 'recording.webm')
        if (sessionId) {
          formData.append('session_id', sessionId)
        }

        const res = await fetch('/api/analyze-audio', {
          method: 'POST',
          body: formData,
        })
        
        if (!res.ok) {
           throw new Error('Analysis failed')
        }

        const data: AudioAnalysisResult = await res.json()
        onAnalysisResult(data)
        onNavigate('result')
      } catch (err) {
        console.error('Audio analysis failed:', err)
        setErrorMsg('Failed to analyze audio. Please try again.')
      } finally {
        setIsAnalyzing(false)
      }
    } else {
      startRecording()
    }
  }, [isRecording, stopRecording, startRecording, sessionId, onAnalysisResult, onNavigate])

  return (
    <div className="audio-upload-view flex-center">
      <div className="card text-center" style={{ width: '100%' }}>
        <h2 className="title-large">Voice Journal</h2>
        <p className="text-body mb-4">
          Speak your mind. We'll listen and help you understand your primary emotion.
        </p>
        
        {errorMsg && <div className="error-banner">{errorMsg}</div>}

        <div className="recorder-container mb-4">
           {permissionDenied ? (
             <div className="permission-denied card">
               <p>Microphone access denied. Please allow permissions.</p>
             </div>
           ) : (
             <button 
               className={`mic-button ${isRecording ? 'recording' : ''} ${isAnalyzing ? 'analyzing' : ''}`}
               onClick={handleToggleRecord}
               disabled={isAnalyzing}
             >
               {isAnalyzing ? (
                 <span className="spinner"></span>
               ) : isRecording ? (
                 <span className="icon-stop">⏹</span>
               ) : (
                 <span className="icon-record">🎙️</span>
               )}
             </button>
           )}
        </div>
        
        <h3 className="title-medium" style={{ color: isRecording ? 'var(--color-error)' : 'var(--color-text)' }}>
          {isAnalyzing ? "Analyzing..." : isRecording ? "Listening..." : "Tap to record"}
        </h3>
      </div>
    </div>
  )
}
