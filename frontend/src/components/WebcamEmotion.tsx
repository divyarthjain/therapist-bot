import { useCallback, useRef, useState } from 'react'
import { useFaceDetection } from '../hooks/useFaceDetection'
import { EMOTION_EMOJI } from '../types'
import './WebcamEmotion.css'

interface Props {
  onEmotionDetected: (emotion: string, confidence: number) => void
}

export function WebcamEmotion({ onEmotionDetected }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const [isActive, setIsActive] = useState(false)
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
    pollRef.current = setInterval(checkEmotionChange, 600)
  }, [checkEmotionChange])

  const toggle = useCallback(async () => {
    if (isActive) {
      // Stop
      stopDetection()
      clearInterval(pollRef.current)
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop())
        streamRef.current = null
      }
      if (videoRef.current) videoRef.current.srcObject = null
      setIsActive(false)
    } else {
      // Start
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 320, height: 240, facingMode: 'user' },
        })
        streamRef.current = stream
        if (videoRef.current) {
          videoRef.current.srcObject = stream
          videoRef.current.onloadedmetadata = () => {
            videoRef.current?.play()
            if (videoRef.current) {
              startDetection(videoRef.current)
              startPolling()
            }
          }
        }
        setIsActive(true)
      } catch (_err) {
        console.error('Camera access denied')
      }
    }
  }, [isActive, startDetection, stopDetection, startPolling])

  return (
    <div className="webcam-emotion">
      <div className="webcam-emotion__header">
        <span className="webcam-emotion__title">Camera</span>
        {isActive && <span className="webcam-emotion__live" />}
      </div>

      <div className="webcam-emotion__video-container">
        <video
          ref={videoRef}
          className="webcam-emotion__video"
          muted
          playsInline
        />
        {!isActive && (
          <div className="webcam-emotion__placeholder">
            <span>📷</span>
            <p>Camera off</p>
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
      </div>

      <button
        className={`webcam-emotion__toggle ${isActive ? 'webcam-emotion__toggle--active' : ''}`}
        onClick={toggle}
        disabled={!isModelLoaded}
        title={isModelLoaded ? (isActive ? 'Disable camera' : 'Enable camera') : 'Loading face detection models…'}
      >
        {!isModelLoaded ? 'Loading models…' : isActive ? 'Disable' : 'Enable'}
      </button>
    </div>
  )
}
