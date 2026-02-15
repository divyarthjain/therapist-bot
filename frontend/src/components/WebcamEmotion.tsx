import { useCallback, useEffect, useRef } from 'react'
import { useFaceDetection } from '../hooks/useFaceDetection'
import { EMOTION_EMOJI } from '../types'
import './WebcamEmotion.css'

interface Props {
  isActive: boolean
  onEmotionDetected: (emotion: string, confidence: number) => void
}

export function WebcamEmotion({ isActive, onEmotionDetected }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const {
    isModelLoaded,
    isDetecting,
    currentEmotion,
    confidence,
    startDetection,
    stopDetection,
  } = useFaceDetection()

  const lastEmotionRef = useRef('')
  const checkEmotionChange = useCallback(() => {
    if (currentEmotion !== lastEmotionRef.current) {
      lastEmotionRef.current = currentEmotion
      onEmotionDetected(currentEmotion, confidence)
    }
  }, [currentEmotion, confidence, onEmotionDetected])

  // Poll for emotion changes while detecting
  const pollRef = useRef<ReturnType<typeof setInterval>>(undefined)
  const startPolling = useCallback(() => {
    // Clear existing interval if any to prevent duplicates
    if (pollRef.current) clearInterval(pollRef.current)
    pollRef.current = setInterval(checkEmotionChange, 600)
  }, [checkEmotionChange])

  // Handle camera start/stop based on isActive prop
  useEffect(() => {
    let mounted = true

    const startCamera = async () => {
      try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
           console.error("Browser API navigator.mediaDevices.getUserMedia not available");
           return;
        }
        
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 320, height: 240, facingMode: 'user' },
        })
        
        if (!mounted) {
          stream.getTracks().forEach(t => t.stop())
          return
        }

        streamRef.current = stream
        if (videoRef.current) {
          videoRef.current.srcObject = stream
          videoRef.current.onloadedmetadata = () => {
            if (mounted && videoRef.current) {
              videoRef.current.play().catch(e => console.error("Play failed", e))
              startDetection(videoRef.current)
              startPolling()
            }
          }
        }
      } catch (err) {
        console.error('Camera access denied:', err)
      }
    }

    const stopCamera = () => {
      stopDetection()
      if (pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = undefined
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop())
        streamRef.current = null
      }
      if (videoRef.current) {
        videoRef.current.srcObject = null
      }
    }

    if (isActive) {
      startCamera()
    } else {
      stopCamera()
    }

    return () => {
      mounted = false
      stopCamera()
    }
  }, [isActive, startDetection, stopDetection, startPolling])

  return (
    <div className="webcam-emotion">
      <video
        ref={videoRef}
        className={`webcam-emotion__video ${!isActive ? 'hidden' : ''}`}
        muted
        playsInline
      />
      {!isActive && (
        <div className="webcam-emotion__placeholder">
          <span className="webcam-emotion__placeholder-icon">📷</span>
        </div>
      )}
      {isActive && isDetecting && (
        <div className="webcam-emotion__overlay">
          <span className="webcam-emotion__detected">
            {EMOTION_EMOJI[currentEmotion] ?? '😐'} {currentEmotion}
          </span>
          <span className="webcam-emotion__confidence">
            {Math.round(confidence * 100)}%
          </span>
        </div>
      )}
      {isActive && !isModelLoaded && (
        <div className="webcam-emotion__loading">
           <span className="webcam-emotion__loading-spinner" />
        </div>
      )}
    </div>
  )
}
