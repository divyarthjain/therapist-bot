import { useCallback, useEffect, useRef, useState } from 'react'
import * as faceapi from '@vladmandic/face-api'

const MODEL_URL = '/models'
const DETECTION_INTERVAL_MS = 500

export interface FaceExpressions {
  happy: number
  sad: number
  angry: number
  neutral: number
  fearful: number
  disgusted: number
  surprised: number
}

export function useFaceDetection() {
  const [isModelLoaded, setIsModelLoaded] = useState(false)
  const [isDetecting, setIsDetecting] = useState(false)
  const [currentEmotion, setCurrentEmotion] = useState<string>('neutral')
  const [confidence, setConfidence] = useState(0)
  const [expressions, setExpressions] = useState<FaceExpressions | null>(null)

  const intervalRef = useRef<ReturnType<typeof setInterval>>(undefined)
  const videoRef = useRef<HTMLVideoElement | null>(null)

  // Load models once
  useEffect(() => {
    let cancelled = false
    async function loadModels() {
      try {
        await faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL)
        await faceapi.nets.faceExpressionNet.loadFromUri(MODEL_URL)
        if (!cancelled) setIsModelLoaded(true)
      } catch (err) {
        console.error('Failed to load face-api models:', err)
      }
    }
    loadModels()
    return () => { cancelled = true }
  }, [])

  const detect = useCallback(async () => {
    const video = videoRef.current
    if (!video || video.readyState < 2) return

    const result = await faceapi
      .detectSingleFace(video, new faceapi.TinyFaceDetectorOptions())
      .withFaceExpressions()

    if (result) {
      const expr = result.expressions as unknown as FaceExpressions
      setExpressions(expr)

      // Find dominant emotion
      let maxKey = 'neutral'
      let maxVal = 0
      for (const [key, val] of Object.entries(expr)) {
        if (val > maxVal) {
          maxVal = val
          maxKey = key
        }
      }
      setCurrentEmotion(maxKey)
      setConfidence(maxVal)
    }
  }, [])

  const startDetection = useCallback(
    (video: HTMLVideoElement) => {
      if (!isModelLoaded) return
      videoRef.current = video
      setIsDetecting(true)
      intervalRef.current = setInterval(detect, DETECTION_INTERVAL_MS)
    },
    [isModelLoaded, detect],
  )

  const stopDetection = useCallback(() => {
    clearInterval(intervalRef.current)
    setIsDetecting(false)
    videoRef.current = null
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => clearInterval(intervalRef.current)
  }, [])

  return {
    isModelLoaded,
    isDetecting,
    currentEmotion,
    confidence,
    expressions,
    startDetection,
    stopDetection,
  }
}
