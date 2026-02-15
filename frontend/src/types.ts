// ── WebSocket Messages ───────────────────────────────────────────────────────

export type WSOutgoingType = 'init' | 'message' | 'emotion' | 'voice_message'
export type WSIncomingType = 'session' | 'emotion_summary' | 'response' | 'error' | 'voice_response'

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

export interface WSVoiceMessage {
  type: 'voice_message'
  audio: string // base64-encoded WAV audio
  session_id?: string
}

export type WSOutgoing = WSInitMessage | WSChatMessage | WSEmotionMessage | WSVoiceMessage

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

export interface WSVoiceResponse {
  type: 'voice_response'
  response_text: string
  emotion_tags: string
  target_emotion: string
  audio_base64: string | null
  timings: Record<string, number>
  transcription: string
  done: boolean
}

export type WSIncoming =
  | WSSessionResponse
  | WSEmotionSummaryResponse
  | WSResponseChunk
  | WSErrorResponse
  | WSVoiceResponse

// ── Voice Call ───────────────────────────────────────────────────────────────

export type CallState = 'idle' | 'listening' | 'processing' | 'speaking'

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
