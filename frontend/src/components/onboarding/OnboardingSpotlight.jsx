import { useState, useEffect } from 'react'
import styles from './OnboardingSpotlight.module.css'

export default function OnboardingSpotlight({ targetSelector, tooltip, onInteract }) {
  const [targetRect, setTargetRect] = useState(null)

  useEffect(() => {
    const updateRect = () => {
      const el = document.querySelector(targetSelector)
      if (el) {
        setTargetRect(el.getBoundingClientRect())
      }
    }
    updateRect()
    window.addEventListener('resize', updateRect)
    const observer = new MutationObserver(updateRect)
    observer.observe(document.body, { childList: true, subtree: true })

    return () => {
      window.removeEventListener('resize', updateRect)
      observer.disconnect()
    }
  }, [targetSelector])

  useEffect(() => {
    if (!targetSelector) return
    const handleTargetClick = (e) => {
      const el = document.querySelector(targetSelector)
      if (el && el.contains(e.target)) {
        onInteract?.()
      }
    }
    document.addEventListener('click', handleTargetClick)
    return () => document.removeEventListener('click', handleTargetClick)
  }, [targetSelector, onInteract])

  if (!targetRect) return null

  const padding = 8

  return (
    <div className={styles.spotlightOverlay} role="region" aria-label="引导高亮区域">
      <div
        className={styles.spotlightHole}
        style={{
          top: targetRect.top - padding,
          left: targetRect.left - padding,
          width: targetRect.width + padding * 2,
          height: targetRect.height + padding * 2,
        }}
      />
      <div
        className={styles.spotlightTooltip}
        style={{
          top: targetRect.bottom + padding + 12,
          left: Math.max(16, Math.min(
            targetRect.left,
            window.innerWidth - 320
          )),
        }}
      >
        {tooltip}
      </div>
    </div>
  )
}
