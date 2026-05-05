import { useState, useCallback } from 'react'
import { createPortal } from 'react-dom'
import styles from './OnboardingGuide.module.css'

const STORAGE_KEY = 'algomate_onboarding_completed'

const STEPS = [
  {
    icon: '⚔️',
    title: '欢迎来到算法大陆',
    description:
      '算法大陆是一个充满算法奥秘的奇幻世界。在这里，你将探索秘境、与导师对话、收集知识卡牌，成为真正的算法修行者！',
    button: '开始冒险 →',
  },
  {
    icon: '🌲',
    title: '探索新手森林',
    description:
      '新手森林是你冒险的起点。在这里，老夫子导师将引导你学习第一个算法知识。',
    button: '前往新手森林 →',
  },
  {
    icon: '🧙',
    title: '与导师对话',
    description:
      '与老夫子对话，学习算法知识。对话结束后，将你的修习心得转化为知识卡牌！',
    button: '知道了 →',
  },
  {
    icon: '🎴',
    title: '查看卡牌工坊',
    description:
      '获得的卡牌会存放在卡牌工坊中。卡牌是你的知识宝库，记得经常修炼保持耐久度！',
    button: '前往卡牌工坊 →',
  },
]

export default function OnboardingGuide({ open, onClose, onNavigate }) {
  const [step, setStep] = useState(0)

  const handleNext = useCallback(() => {
    if (step === 1) {
      onNavigate?.('/npc/novice_forest')
      setStep((s) => s + 1)
      return
    }

    if (step === STEPS.length - 1) {
      onNavigate?.('/workshop')
      localStorage.setItem(STORAGE_KEY, 'true')
      onClose?.()
      setStep(0)
      return
    }

    setStep((s) => s + 1)
  }, [step, onClose, onNavigate])

  const handleSkip = useCallback(() => {
    localStorage.setItem(STORAGE_KEY, 'true')
    onClose?.()
    setStep(0)
  }, [onClose])

  if (!open) return null

  const current = STEPS[step]

  return createPortal(
    <div className={styles.overlay} onClick={handleSkip} role="presentation">
      <div
        className={styles.card}
        role="dialog"
        aria-modal="true"
        aria-label="新手引导"
        onClick={(e) => e.stopPropagation()}
      >
        <button className={styles.skipBtn} onClick={handleSkip}>
          跳过
        </button>

        <div className={styles.stepContent} key={step}>
          <span className={styles.icon}>{current.icon}</span>
          <h2 className={styles.title}>{current.title}</h2>
          <p className={styles.description}>{current.description}</p>
          <button className={styles.actionBtn} onClick={handleNext}>
            {current.button}
          </button>
        </div>

        <div className={styles.indicators}>
          {STEPS.map((_, i) => (
            <span
              key={i}
              className={`${styles.dot} ${i === step ? styles.dotActive : ''}`}
            />
          ))}
        </div>
      </div>
    </div>,
    document.body
  )
}
