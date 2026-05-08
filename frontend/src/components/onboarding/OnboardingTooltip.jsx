import OnboardingStepIndicator from './OnboardingStepIndicator'
import styles from './OnboardingTooltip.module.css'

export default function OnboardingTooltip({ title, description, step, totalSteps }) {
  return (
    <div className={styles.tooltip} role="tooltip" aria-live="polite">
      <OnboardingStepIndicator current={step} total={totalSteps} />
      <h3 className={styles.tooltipTitle}>{title}</h3>
      <p className={styles.tooltipDesc}>{description}</p>
    </div>
  )
}
