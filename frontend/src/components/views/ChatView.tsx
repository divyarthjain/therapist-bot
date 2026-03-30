import { useRef, useEffect, useState } from 'react'
import type { ChatMessage } from '../../types'
import { MessageBubble } from '../MessageBubble'
import './ChatView.css'

interface Props {
  messages: ChatMessage[]
  isConnected: boolean
  isStreaming: boolean
  isCallActive: boolean
  onSendMessage: (msg: string, audioEmo?: string, videoEmo?: string) => void
  onToggleCall: () => void
}

export function ChatView({
  messages,
  isConnected,
  isStreaming,
  isCallActive,
  onSendMessage,
  onToggleCall
}: Props) {
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = () => {
    if (!input.trim() || isStreaming || !isConnected) return
    onSendMessage(input.trim(), undefined, undefined)
    setInput('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="chat-view">
      <div className="chat-view__header flex-between">
        <div className="chat-view__title">
          <span className="api-dot" style={{ backgroundColor: isConnected ? 'var(--color-primary)' : 'var(--color-error)' }}></span>
          <h2 className="title-medium" style={{ margin: 0 }}>Dr. Serenity</h2>
        </div>
      </div>

      <div className="chat-view__messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            <p className="text-body" style={{ textAlign: 'center' }}>
              Say hello! Dr. Serenity is here to listen.
              <br />
              <span style={{ fontSize: '12px', marginTop: '8px', display: 'block' }}>
                You can type below or use the microphone to talk.
              </span>
            </p>
          </div>
        )}
        
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        
        {isStreaming && (
          <div className="chat-typing">
            <span className="typing-dot" />
            <span className="typing-dot" />
            <span className="typing-dot" />
          </div>
        )}
        <div ref={bottomRef} className="chat-bottom-spacer" />
      </div>



      <div className="chat-view__input-area">
         <button 
           className={`chat-mic-btn ${isCallActive ? 'active' : ''}`}
           onClick={onToggleCall}
           title={isCallActive ? 'Stop Voice Call' : 'Start Voice Call'}
         >
           {isCallActive ? '⏹' : '🎙️'}
         </button>
         
         <div className="chat-input-wrapper">
           <textarea
             className="chat-input-field"
             value={input}
             onChange={e => setInput(e.target.value)}
             onKeyDown={handleKeyDown}
             placeholder={isConnected ? "Type a message..." : "Connecting..."}
             disabled={!isConnected || isStreaming}
             rows={1}
           />
           <button 
             className="chat-send-btn"
             onClick={handleSend}
             disabled={!input.trim() || isStreaming || !isConnected}
           >
             <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
               <line x1="22" y1="2" x2="11" y2="13" />
               <polygon points="22 2 15 22 11 13 2 9 22 2" />
             </svg>
           </button>
         </div>
      </div>
    </div>
  )
}
