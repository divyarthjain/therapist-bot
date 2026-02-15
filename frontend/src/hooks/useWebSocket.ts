import { useCallback, useEffect, useRef, useState } from 'react'
import type {
  ChatMessage,
  EmotionState,
  WSIncoming,
} from '../types'

interface LastVoiceResponse {
  audio_base64: string | null
  id: string
}

const WS_URL = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/chat`
const MAX_RECONNECT_DELAY = 30_000
const BASE_RECONNECT_DELAY = 1_000

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>(undefined)
  const reconnectDelay = useRef(BASE_RECONNECT_DELAY)

  const [isConnected, setIsConnected] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [emotionState, setEmotionState] = useState<EmotionState | null>(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastVoiceResponse, setLastVoiceResponse] = useState<LastVoiceResponse | null>(null)

  // Accumulates streaming tokens for the current assistant response
  const streamBuffer = useRef('')

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => {
      setIsConnected(true)
      setError(null)
      reconnectDelay.current = BASE_RECONNECT_DELAY
      ws.send(JSON.stringify({ type: 'init' }))
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data) as WSIncoming

      switch (data.type) {
        case 'session':
          setSessionId(data.session_id)
          break

        case 'emotion_summary':
          setEmotionState(data.emotions)
          break

        case 'response':
          if (data.done) {
            // Finalize the assistant message
            const finalContent = streamBuffer.current
            streamBuffer.current = ''
            setIsStreaming(false)
            setMessages((prev) => {
              const updated = [...prev]
              const last = updated[updated.length - 1]
              if (last && last.role === 'assistant') {
                updated[updated.length - 1] = { ...last, content: finalContent }
              }
              return updated
            })
          } else {
            streamBuffer.current += data.content
            const currentContent = streamBuffer.current
            setMessages((prev) => {
              const updated = [...prev]
              const last = updated[updated.length - 1]
              if (last && last.role === 'assistant' && isStreamingMsg(last)) {
                updated[updated.length - 1] = { ...last, content: currentContent }
              }
              return updated
            })
          }
          break

        case 'error':
          setError(data.message)
          setIsStreaming(false)
          break

        case 'voice_response':
          if (data.done) {
            if (data.transcription) {
              const userMsg: ChatMessage = {
                id: crypto.randomUUID(),
                role: 'user',
                content: data.transcription,
                timestamp: Date.now(),
              }
              setMessages((prev) => [...prev, userMsg])
            }
            if (data.response_text) {
              const assistantMsg: ChatMessage = {
                id: crypto.randomUUID(),
                role: 'assistant',
                content: data.response_text,
                timestamp: Date.now(),
              }
              setMessages((prev) => [...prev, assistantMsg])
            }
            setLastVoiceResponse({
              audio_base64: data.audio_base64 ?? null,
              id: crypto.randomUUID(),
            })
          }
          break
      }
    }

    ws.onclose = () => {
      setIsConnected(false)
      wsRef.current = null
      // Auto-reconnect with exponential backoff
      const delay = reconnectDelay.current
      reconnectDelay.current = Math.min(delay * 2, MAX_RECONNECT_DELAY)
      reconnectTimer.current = setTimeout(connect, delay)
    }

    ws.onerror = () => {
      setError('WebSocket connection error')
    }
  }, [])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectTimer.current)
      wsRef.current?.close()
    }
  }, [connect])

  const sendMessage = useCallback(
    (content: string, audioEmotion?: string, videoEmotion?: string) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return

      // Add user message
      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        content,
        timestamp: Date.now(),
      }
      setMessages((prev) => [...prev, userMsg])

      // Add placeholder for assistant streaming response
      const assistantMsg: ChatMessage = {
        id: `stream-${crypto.randomUUID()}`,
        role: 'assistant',
        content: '',
        timestamp: Date.now(),
      }
      setMessages((prev) => [...prev, assistantMsg])
      setIsStreaming(true)
      streamBuffer.current = ''

      wsRef.current.send(
        JSON.stringify({
          type: 'message',
          content,
          audio_emotion: audioEmotion,
          video_emotion: videoEmotion,
        }),
      )
    },
    [],
  )

  const sendEmotion = useCallback((emotion: string, confidence: number) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return
    wsRef.current.send(
      JSON.stringify({ type: 'emotion', emotion, confidence }),
    )
  }, [])

  const sendVoiceMessage = useCallback((audioBase64: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return
    wsRef.current.send(
      JSON.stringify({ type: 'voice_message', audio: audioBase64 }),
    )
  }, [])

  const clearLastVoiceResponse = useCallback(() => {
    setLastVoiceResponse(null)
  }, [])

  return {
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
  }
}

/** Check if a message is the streaming placeholder */
function isStreamingMsg(msg: ChatMessage): boolean {
  return msg.id.startsWith('stream-')
}
