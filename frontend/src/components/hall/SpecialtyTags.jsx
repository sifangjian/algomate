import styles from './SpecialtyTags.module.css'

export default function SpecialtyTags({ specialties }) {
  if (!specialties || specialties.length === 0) return null
  return (
    <div className={styles.specialtyTags}>
      {specialties.map(spec => (
        <span key={spec} className={styles.specialtyTag}>{spec}</span>
      ))}
    </div>
  )
}
