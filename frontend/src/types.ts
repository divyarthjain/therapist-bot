// ── WebSocket Messages ───────────────────────────────────────────────────────

export type WSOutgoingType = 'init' | 'message' | 'emotion'
export type WSIncomingType = 'session' | 'emotion_summary' | 'response' | 'error'

export interface WSInitMessage {
  type: 'init'
  session_id?: string
}

export interface WSChatMessage {
  type: 'message'
  content: string
  audio_emotion?: string
  video_emotion?: string
}

export interface WSEmotionMessage {
  type: 'emotion'
  emotion: string
  confidence: number
}

export type WSOutgoing = WSInitMessage | WSChatMessage | WSEmotionMessage

export interface WSSessionResponse {
  type: 'session'
  session_id: string
}

export interface WSEmotionSummaryResponse {
  type: 'emotion_summary'
  emotions: EmotionState
}

export interface WSResponseChunk {
  type: 'response'
  content: string
  done: boolean
}

export interface WSErrorResponse {
  type: 'error'
  message: string
}

export type WSIncoming =
  | WSSessionResponse
  | WSEmotionSummaryResponse
  | WSResponseChunk
  | WSErrorResponse

// ── Chat ─────────────────────────────────────────────────────────────────────

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  emotion?: string
}

// ── Emotions ─────────────────────────────────────────────────────────────────

export interface ModalityEmotion {
  emotion: string
  confidence: number
  scores: Record<string, number>
}

export interface EmotionState {
  dominant: string
  confidence: number
  audio: ModalityEmotion
  video: ModalityEmotion
  fused_scores: Record<string, number>
  incongruence: boolean
}

// ── Audio Analysis ───────────────────────────────────────────────────────────

export interface AudioAnalysisResult {
  transcription: string
  emotion: string
  confidence: number
  events: string[]
  language: string
  session_id: string
  raw_text?: string
  error?: string
}

// ── Emotion Helpers ──────────────────────────────────────────────────────────

export const EMOTION_EMOJI: Record<string, string> = {
  happy: '😊',
  sad: '😢',
  angry: '😠',
  neutral: '😐',
  fearful: '😨',
  disgusted: '🤢',
  surprised: '😲',
}

export const EMOTION_COLORS: Record<string, string> = {
  happy: '#FFD93D',
  sad: '#6C9BCF',
  angry: '#E57373',
  neutral: '#B0BEC5',
  fearful: '#CE93D8',
  disgusted: '#A5D6A7',
  surprised: '#FFB74D',
}
