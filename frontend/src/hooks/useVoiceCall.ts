import { useState, useCallback, useRef, useEffect } from 'react'
import { MicVAD } from '@ricky0123/vad-web'
import type { CallState } from '../types'

interface UseVoiceCallOptions {
  onSpeechEnd: (audioBase64: string) => void
}

export function useVoiceCall(options: UseVoiceCallOptions) {
  const [callState, setCallState] = useState<CallState>('idle')

  const vadRef = useRef<MicVAD | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const currentSourceRef = useRef<AudioBufferSourceNode | null>(null)
  const onSpeechEndRef = useRef(options.onSpeechEnd)

  useEffect(() => {
    onSpeechEndRef.current = options.onSpeechEnd
  }, [options.onSpeechEnd])

  const stopPlayback = useCallback(() => {
    if (currentSourceRef.current) {
      currentSourceRef.current.stop()
      currentSourceRef.current.disconnect()
      currentSourceRef.current = null
    }
  }, [])

  const float32ToWavBase64 = useCallback((audio: Float32Array) => {
    const numChannels = 1
    const sampleRate = 16000
    const bitsPerSample = 16
    const bytesPerSample = bitsPerSample / 8
    const blockAlign = numChannels * bytesPerSample
    const byteRate = sampleRate * blockAlign
    const dataSize = audio.length * bytesPerSample
    const buffer = new ArrayBuffer(44 + dataSize)
    const view = new DataView(buffer)

    const writeString = (offset: number, value: string) => {
      for (let i = 0; i < value.length; i += 1) {
        view.setUint8(offset + i, value.charCodeAt(i))
      }
    }

    writeString(0, 'RIFF')
    view.setUint32(4, 36 + dataSize, true)
    writeString(8, 'WAVE')
    writeString(12, 'fmt ')
    view.setUint32(16, 16, true)
    view.setUint16(20, 1, true)
    view.setUint16(22, numChannels, true)
    view.setUint32(24, sampleRate, true)
    view.setUint32(28, byteRate, true)
    view.setUint16(32, blockAlign, true)
    view.setUint16(34, bitsPerSample, true)
    writeString(36, 'data')
    view.setUint32(40, dataSize, true)

    let offset = 44
    for (let i = 0; i < audio.length; i += 1) {
      const sample = Math.max(-1, Math.min(1, audio[i]))
      view.setInt16(offset, sample * 32767, true)
      offset += 2
    }

    const bytes = new Uint8Array(buffer)
    let binary = ''
    for (let i = 0; i < bytes.length; i += 1) {
      binary += String.fromCharCode(bytes[i])
    }
    return btoa(binary)
  }, [])

  const toggleCall = useCallback(async () => {
    if (callState === 'idle') {
      const vad = await MicVAD.new({
        positiveSpeechThreshold: 0.8,
        negativeSpeechThreshold: 0.3,
        redemptionMs: 800,
        onSpeechStart: () => {
          stopPlayback()
          setCallState('listening')
        },
        onSpeechEnd: (audio: Float32Array) => {
          setCallState('processing')
          const base64 = float32ToWavBase64(audio)
          onSpeechEndRef.current(base64)
        },
      })
      vadRef.current = vad
      await vad.start()
      setCallState('listening')
      return
    }

    if (vadRef.current) {
      vadRef.current.destroy()
      vadRef.current = null
    }
    stopPlayback()
    if (audioContextRef.current) {
      audioContextRef.current.close()
      audioContextRef.current = null
    }
    setCallState('idle')
  }, [callState, float32ToWavBase64, stopPlayback])

  const playResponseAndResume = useCallback(async (audioBase64: string) => {
    stopPlayback()
    setCallState('speaking')
    try {
      if (!audioContextRef.current) {
        audioContextRef.current = new AudioContext({ latencyHint: 'interactive' })
      }
      await audioContextRef.current.resume()

      const binary = atob(audioBase64)
      const bytes = new Uint8Array(binary.length)
      for (let i = 0; i < binary.length; i += 1) {
        bytes[i] = binary.charCodeAt(i)
      }
      const audioBuffer = await audioContextRef.current.decodeAudioData(bytes.buffer)
      const source = audioContextRef.current.createBufferSource()
      source.buffer = audioBuffer
      source.connect(audioContextRef.current.destination)
      currentSourceRef.current = source
      source.onended = () => {
        currentSourceRef.current = null
        setCallState('listening')
      }
      source.start()
    } catch (err) {
      console.error('Failed to play voice response', err)
      setCallState('listening')
    }
  }, [stopPlayback])

  useEffect(() => {
    return () => {
      if (vadRef.current) {
        vadRef.current.destroy()
        vadRef.current = null
      }
      if (currentSourceRef.current) {
        currentSourceRef.current.stop()
        currentSourceRef.current.disconnect()
        currentSourceRef.current = null
      }
      if (audioContextRef.current) {
        audioContextRef.current.close()
        audioContextRef.current = null
      }
    }
  }, [])

  return {
    callState,
    isCallActive: callState !== 'idle',
    toggleCall,
    playResponseAndResume,
    stopPlayback,
    setCallState,
  }
}
