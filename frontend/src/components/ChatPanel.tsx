import { useEffect, useRef } from 'react'
import type { ChatMessage } from '../types'
import { MessageBubble } from './MessageBubble'
import './ChatPanel.css'

interface Props {
  messages: ChatMessage[]
  isStreaming: boolean
  isConnected: boolean
}

export function ChatPanel({
  messages,
  isStreaming,
  isConnected,
}: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="chat-panel">
      <div className="chat-panel__messages">
        {messages.length === 0 && (
          <div className="chat-panel__empty">
            <h2>Your Session</h2>
            <p>
              Your conversation transcript will appear here.
              <br />
              {isConnected ? 'Ready to listen.' : 'Connecting...'}
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
    </div>
  )
}
