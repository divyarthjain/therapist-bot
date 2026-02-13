import { useCallback, useState } from 'react'
import { useAudioRecorder } from '../hooks/useAudioRecorder'
import type { AudioAnalysisResult } from '../types'
import './AudioRecorder.css'

interface Props {
  sessionId: string | null
  onTranscription: (text: string) => void
  onAudioEmotion: (emotion: string) => void
}

export function AudioRecorder({ sessionId, onTranscription, onAudioEmotion }: Props) {
  const { isRecording, permissionDenied, startRecording, stopRecording } = useAudioRecorder()
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  const handleClick = useCallback(async () => {
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
        const data: AudioAnalysisResult = await res.json()

        if (data.transcription && !data.transcription.startsWith('[')) {
          onTranscription(data.transcription)
        }
        if (data.emotion && data.emotion !== 'neutral') {
          onAudioEmotion(data.emotion)
        }
      } catch (err) {
        console.error('Audio analysis failed:', err)
      } finally {
        setIsAnalyzing(false)
      }
    } else {
      startRecording()
    }
  }, [isRecording, stopRecording, startRecording, sessionId, onTranscription, onAudioEmotion])

  if (permissionDenied) {
    return (
      <button className="audio-recorder audio-recorder--denied" disabled title="Microphone access denied">
        🎙️
      </button>
    )
  }

  return (
    <button
      className={`audio-recorder ${isRecording ? 'audio-recorder--recording' : ''} ${isAnalyzing ? 'audio-recorder--analyzing' : ''}`}
      onClick={handleClick}
      disabled={isAnalyzing}
      title={isRecording ? 'Stop recording' : isAnalyzing ? 'Analyzing audio…' : 'Start recording'}
    >
      {isAnalyzing ? (
        <span className="audio-recorder__spinner" />
      ) : (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
          <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
        </svg>
      )}
    </button>
  )
}
