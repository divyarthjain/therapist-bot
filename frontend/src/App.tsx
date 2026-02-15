import { useCallback, useEffect, useRef, useState } from 'react'
import { useWebSocket } from './hooks/useWebSocket'
import { useVoiceCall } from './hooks/useVoiceCall'
import { ChatPanel } from './components/ChatPanel'
import { AudioRecorder } from './components/AudioRecorder'
import { CallButton } from './components/CallButton'
import { WebcamEmotion } from './components/WebcamEmotion'
import { TherapistVisual } from './components/TherapistVisual'

function App() {
  const {
    isConnected,
    sessionId,
    messages,
    isStreaming,
    error,
    sendMessage,
    sendEmotion,
    sendVoiceMessage,
    lastVoiceResponse,
    clearLastVoiceResponse,
  } = useWebSocket()

  const { callState, isCallActive, toggleCall, playResponseAndResume, setCallState } = useVoiceCall({
    onSpeechEnd: sendVoiceMessage,
  })

  // State
  const [pendingTranscription, setPendingTranscription] = useState<string | null>(null)
  const [input, setInput] = useState('')
  const [isCameraActive, setIsCameraActive] = useState(true)

  // Refs
  const audioEmotionRef = useRef<string | undefined>(undefined)
  const videoEmotionRef = useRef<string | undefined>(undefined)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Effect: Handle pending transcription
  useEffect(() => {
    if (pendingTranscription) {
      setInput(pendingTranscription)
      setPendingTranscription(null)
      inputRef.current?.focus()
    }
  }, [pendingTranscription])

  useEffect(() => {
    if (!isCallActive || !lastVoiceResponse) return

    if (callState !== 'processing') {
      clearLastVoiceResponse()
      return
    }

    if (lastVoiceResponse.audio_base64) {
      playResponseAndResume(lastVoiceResponse.audio_base64)
    } else {
      setCallState('listening')
    }

    clearLastVoiceResponse()
  }, [lastVoiceResponse, isCallActive, callState, playResponseAndResume, clearLastVoiceResponse, setCallState])

  useEffect(() => {
    if (isCallActive && callState === 'processing' && error) {
      setCallState('listening')
    }
  }, [isCallActive, callState, error, setCallState])

  // Handlers
  const handleSendClick = useCallback(() => {
    const trimmed = input.trim()
    if (!trimmed || isStreaming || !isConnected) return

    sendMessage(trimmed, audioEmotionRef.current, videoEmotionRef.current)
    audioEmotionRef.current = undefined
    setInput('')
  }, [input, isStreaming, isConnected, sendMessage])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendClick()
    }
  }

  const handleAudioEmotion = useCallback((emotion: string) => {
    audioEmotionRef.current = emotion
  }, [])

  const handleVideoEmotion = useCallback(
    (emotion: string, confidence: number) => {
      videoEmotionRef.current = emotion
      sendEmotion(emotion, confidence)
    },
    [sendEmotion],
  )

  const handleTranscription = useCallback((text: string) => {
    setPendingTranscription(text)
  }, [])

  return (
    <div className="app">
      {/* Top Bar */}
      <div className="app__top-bar">
        <div className="app__top-bar-left">
          <span className="app__logo">🧠</span>
          <span className="app__title">Serenity</span>
          <div 
            className={`app__connection-dot ${isConnected ? 'app__connection-dot--connected' : ''}`} 
            title={isConnected ? 'Connected' : 'Disconnected'}
          />
        </div>
        <div className="app__top-bar-right">
          {/* Optional: Session timer or other indicators could go here */}
        </div>
      </div>

      {error && <div className="app__error">{error}</div>}

      {/* Main Stage */}
      <div className="app__stage">
        {/* Therapist Visual */}
         <TherapistVisual isStreaming={isStreaming} callState={callState} />

        {/* User PIP */}
        <div className="app__pip">
          <WebcamEmotion 
            isActive={isCameraActive}
            onEmotionDetected={handleVideoEmotion} 
          />
        </div>

        {/* Chat Overlay */}
         <div className="app__chat-overlay">
           <ChatPanel
             messages={messages}
             isStreaming={isStreaming}
             isConnected={isConnected}
           />
         </div>
       </div>

      {/* Bottom Control Bar */}
      <div className="app__bottom-bar">
        <CallButton callState={callState} onToggle={toggleCall} />

        {!isCallActive && (
          <AudioRecorder
            sessionId={sessionId}
            onTranscription={handleTranscription}
            onAudioEmotion={handleAudioEmotion}
          />
        )}

        <button 
          className="control-btn"
          onClick={() => setIsCameraActive(!isCameraActive)}
          title={isCameraActive ? "Turn camera off" : "Turn camera on"}
          style={{ 
            background: isCameraActive ? 'rgba(255, 255, 255, 0.1)' : 'rgba(255, 92, 92, 0.2)',
            borderColor: isCameraActive ? 'rgba(255, 255, 255, 0.15)' : 'rgba(255, 92, 92, 0.4)'
          }}
        >
          {isCameraActive ? '📷' : '🚫'}
        </button>

        <textarea
          ref={inputRef}
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={isConnected ? 'Type your message…' : 'Connecting…'}
          disabled={!isConnected}
          rows={1}
        />

        <button
          className="send-btn"
          onClick={handleSendClick}
          disabled={!input.trim() || isStreaming || !isConnected}
          title="Send message"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>
    </div>
  )
}

export default App
