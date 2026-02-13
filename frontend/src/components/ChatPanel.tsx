import type { ReactNode} from 'react'
import { useEffect, useRef, useState } from 'react'
import type { ChatMessage } from '../types'
import { MessageBubble } from './MessageBubble'
import './ChatPanel.css'

interface Props {
  messages: ChatMessage[]
  isStreaming: boolean
  isConnected: boolean
  onSend: (content: string) => void
  pendingTranscription: string | null
  onTranscriptionConsumed: () => void
  audioRecorder?: ReactNode
}

export function ChatPanel({
  messages,
  isStreaming,
  isConnected,
  onSend,
  pendingTranscription,
  onTranscriptionConsumed,
  audioRecorder,
}: Props) {
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (pendingTranscription) {
      setInput(pendingTranscription)
      onTranscriptionConsumed()
      inputRef.current?.focus()
    }
  }, [pendingTranscription, onTranscriptionConsumed])

  const handleSend = () => {
    const trimmed = input.trim()
    if (!trimmed || isStreaming || !isConnected) return
    onSend(trimmed)
    setInput('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="chat-panel">
      <div className="chat-panel__messages">
        {messages.length === 0 && (
          <div className="chat-panel__empty">
            <div className="chat-panel__empty-icon">🧠</div>
            <h2>Welcome to Serenity</h2>
            <p>
              I'm your AI therapeutic companion. Share what's on your mind — I'm here
              to listen. You can type, or use the microphone to speak.
            </p>
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {isStreaming && (
          <div className="chat-panel__typing">
            <span className="typing-dot" />
            <span className="typing-dot" />
            <span className="typing-dot" />
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="chat-panel__input-area">
        {audioRecorder}
        <textarea
          ref={inputRef}
          className="chat-panel__input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={isConnected ? 'Type your message…' : 'Connecting…'}
          disabled={!isConnected}
          rows={1}
        />
        <button
          className="chat-panel__send"
          onClick={handleSend}
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
