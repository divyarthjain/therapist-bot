import { useEffect, useState } from 'react'
import { Navigation } from './components/Navigation'
import type { ViewState } from './components/Navigation'
import { HomeView } from './components/views/HomeView'
import { AudioUploadView } from './components/views/AudioUploadView'
import { EmotionResultView } from './components/views/EmotionResultView'
import { ChatView } from './components/views/ChatView'
import { ProfileView } from './components/views/ProfileView'
import { AuthView } from './components/views/AuthView'
import { WebcamEmotion } from './components/WebcamEmotion'
import { CallOverlay } from './components/CallOverlay'

import { useAuth } from './hooks/useAuth'
import { useWebSocket } from './hooks/useWebSocket'
import { useVoiceCall } from './hooks/useVoiceCall'
import type { AudioAnalysisResult } from './types'

function App() {
  const { user, loading } = useAuth()
  const [currentView, setCurrentView] = useState<ViewState>('chat')
  const [audioResult, setAudioResult] = useState<AudioAnalysisResult | null>(null)

  // Global hooks that persist connection across views
  const {
    isConnected,
    sessionId,
    messages,
    emotionState,
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

  // Voice playback logic (from original app)
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

  const lastUserMessage = [...messages].reverse().find((message) => message.role === 'user')
  const lastAssistantMessage = [...messages].reverse().find((message) => message.role === 'assistant')
  const startLiveCall = () => {
    setCurrentView('chat')
    if (!isCallActive) {
      void toggleCall()
    }
  }

  // View routing rendering
  const renderView = () => {
    switch (currentView) {
      case 'home':
        return (
          <HomeView
            onNavigate={setCurrentView}
            onStartCall={startLiveCall}
            isCallActive={isCallActive}
            emotionSummary={emotionState}
          />
        )
      case 'audio':
        return (
          <AudioUploadView 
            sessionId={sessionId} 
            onAnalysisResult={setAudioResult} 
            onNavigate={setCurrentView} 
          />
        )
      case 'result':
        return <EmotionResultView result={audioResult} onNavigate={setCurrentView} />
      case 'chat':
        return (
          <ChatView 
            messages={messages}
            isConnected={isConnected}
            isStreaming={isStreaming}
            isCallActive={isCallActive}
            onSendMessage={sendMessage}
            onToggleCall={toggleCall}
          />
        )
      case 'profile':
        return <ProfileView />
      default:
        return (
          <HomeView
            onNavigate={setCurrentView}
            onStartCall={startLiveCall}
            isCallActive={isCallActive}
            emotionSummary={emotionState}
          />
        )
    }
  }

  // If auth is still loading the session
  if (loading) {
     return <div className="app-container flex-center">Loading Serenity...</div>
  }

  // Restrict access if no logged in user
  if (!user) {
     return (
       <div className="app-container">
         <main className="view-content" style={{ padding: 0 }}>
           <AuthView />
         </main>
       </div>
     )
  }

  return (
    <div className="app-container">
      {/* Container for the Active View */}
      <main className="view-content">
        {error && <div className="error-banner">{error}</div>}
        {renderView()}
      </main>
      
      {/* Fixed Bottom Navigation */}
      <Navigation currentView={currentView} onNavigate={setCurrentView} />

      {!isCallActive && (
        <div
          className="global-pip"
          style={{
            position: 'absolute',
            top: '16px',
            right: '16px',
            width: '96px',
            height: '96px',
            borderRadius: '18px',
            overflow: 'hidden',
            zIndex: 50,
            boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
          }}
        >
          <WebcamEmotion isActive={true} onEmotionDetected={sendEmotion} />
        </div>
      )}

      {isCallActive && (
        <CallOverlay
          callState={callState}
          emotionState={emotionState}
          isConnected={isConnected}
          lastUserText={lastUserMessage?.content}
          lastAssistantText={lastAssistantMessage?.content}
          onEndCall={toggleCall}
        >
          <WebcamEmotion isActive={true} onEmotionDetected={sendEmotion} />
        </CallOverlay>
      )}

    </div>
  )
}

export default App
