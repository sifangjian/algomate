import styles from './OnboardingStepIndicator.module.css'

export default function OnboardingStepIndicator({ current, total }) {
  return (
    <div
      className={styles.stepIndicator}
      aria-label={`引导步骤 ${current}/${total}`}
      role="progressbar"
    >
      {Array.from({ length: total }, (_, i) => (
        <div
          key={i}
          className={`${styles.stepDot} ${i + 1 === current ? styles.stepDotActive : ''} ${i + 1 < current ? styles.stepDotDone : ''}`}
        />
      ))}
    </div>
  )
}
