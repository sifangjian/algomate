import { useState, useEffect, useCallback, useRef } from 'react'
import styles from './OnboardingSpotlight.module.css'

export default function OnboardingSpotlight({ targetSelector, tooltip, onInteract }) {
  const [targetRect, setTargetRect] = useState(null)
  const [tooltipPosition, setTooltipPosition] = useState('bottom')
  const rafRef = useRef(null)

  const updateRect = useCallback(() => {
    const el = document.querySelector(targetSelector)
    if (el) {
      const rect = el.getBoundingClientRect()
      setTargetRect(rect)
      const tooltipHeight = 120
      if (rect.bottom + tooltipHeight + 20 > window.innerHeight) {
        setTooltipPosition('top')
      } else {
        setTooltipPosition('bottom')
      }
    }
  }, [targetSelector])

  useEffect(() => {
    updateRect()

    const handleScroll = () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
      rafRef.current = requestAnimationFrame(updateRect)
    }

    window.addEventListener('resize', updateRect)
    window.addEventListener('scroll', handleScroll, true)

    const observer = new MutationObserver(updateRect)
    observer.observe(document.body, { childList: true, subtree: true })

    return () => {
      window.removeEventListener('resize', updateRect)
      window.removeEventListener('scroll', handleScroll, true)
      observer.disconnect()
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
    }
  }, [targetSelector, updateRect])

  useEffect(() => {
    const el = document.querySelector(targetSelector)
    if (el && typeof el.scrollIntoView === 'function') {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' })
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

  const tooltipStyle = tooltipPosition === 'bottom'
    ? {
        top: targetRect.bottom + padding + 12,
        left: Math.max(16, Math.min(
          targetRect.left,
          window.innerWidth - 320
        )),
      }
    : {
        bottom: window.innerHeight - targetRect.top + padding + 12,
        left: Math.max(16, Math.min(
          targetRect.left,
          window.innerWidth - 320
        )),
      }

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
        className={`${styles.spotlightTooltip} ${tooltipPosition === 'top' ? styles.spotlightTooltipTop : ''}`}
        style={tooltipStyle}
      >
        {tooltip}
      </div>
    </div>
  )
}
