import { useCallback, useRef, useState } from 'react'
import { useWebSocket } from './hooks/useWebSocket'
import { ChatPanel } from './components/ChatPanel'
import { AudioRecorder } from './components/AudioRecorder'
import { WebcamEmotion } from './components/WebcamEmotion'
import { EmotionDisplay } from './components/EmotionDisplay'

function App() {
  const {
    isConnected,
    sessionId,
    messages,
    emotionState,
    isStreaming,
    error,
    sendMessage,
    sendEmotion,
  } = useWebSocket()

  const [pendingTranscription, setPendingTranscription] = useState<string | null>(null)
  const audioEmotionRef = useRef<string | undefined>(undefined)
  const videoEmotionRef = useRef<string | undefined>(undefined)

  const handleSend = useCallback(
    (content: string) => {
      sendMessage(content, audioEmotionRef.current, videoEmotionRef.current)
      audioEmotionRef.current = undefined
    },
    [sendMessage],
  )

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

  const handleTranscriptionConsumed = useCallback(() => {
    setPendingTranscription(null)
  }, [])

  return (
    <div className="app">
      <header className="app__header">
        <span className="app__logo">🧠</span>
        <h1 className="app__title">Serenity</h1>
        <div className="app__connection">
          <span
            className={`app__connection-dot ${isConnected ? 'app__connection-dot--connected' : ''}`}
          />
          {isConnected ? 'Connected' : 'Disconnected'}
        </div>
      </header>

      {error && <div className="app__error">{error}</div>}

      <div className="app__body">
        <aside className="app__sidebar-left">
          <EmotionDisplay emotionState={emotionState} />
        </aside>

        <main className="app__center">
          <ChatPanel
            messages={messages}
            isStreaming={isStreaming}
            isConnected={isConnected}
            onSend={handleSend}
            pendingTranscription={pendingTranscription}
            onTranscriptionConsumed={handleTranscriptionConsumed}
            audioRecorder={
              <AudioRecorder
                sessionId={sessionId}
                onTranscription={handleTranscription}
                onAudioEmotion={handleAudioEmotion}
              />
            }
          />
        </main>

        <aside className="app__sidebar-right">
          <WebcamEmotion onEmotionDetected={handleVideoEmotion} />
        </aside>
      </div>
    </div>
  )
}

export default App
