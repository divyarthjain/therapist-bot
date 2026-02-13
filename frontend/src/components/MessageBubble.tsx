import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { ChatMessage } from '../types'
import { EMOTION_EMOJI } from '../types'
import './MessageBubble.css'

interface Props {
  message: ChatMessage
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user'
  const time = new Date(message.timestamp).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  })

  return (
    <div className={`bubble-row ${isUser ? 'bubble-row--user' : 'bubble-row--assistant'}`}>
      <div className={`bubble ${isUser ? 'bubble--user' : 'bubble--assistant'}`}>
        <div className="bubble__content">
          {isUser ? (
            <p>{message.content}</p>
          ) : (
            <Markdown remarkPlugins={[remarkGfm]}>{message.content || '…'}</Markdown>
          )}
        </div>
        <div className="bubble__meta">
          {message.emotion && (
            <span className="bubble__emotion">
              {EMOTION_EMOJI[message.emotion] ?? '😐'}
            </span>
          )}
          <span className="bubble__time">{time}</span>
        </div>
      </div>
    </div>
  )
}
