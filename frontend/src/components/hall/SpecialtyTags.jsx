import styles from './SpecialtyTags.module.css'

export default function SpecialtyTags({ specialties, topicsInfo = [] }) {
  if (!specialties || specialties.length === 0) return null

  const getTopicInfo = (spec) => {
    return topicsInfo.find(t => (t.name || t) === spec)
  }

  return (
    <div className={styles.specialtyTags}>
      {specialties.map(spec => {
        const topicInfo = getTopicInfo(spec)
        const hasCard = topicInfo?.has_card
        return (
          <span key={spec} className={`${styles.specialtyTag} ${hasCard ? styles.hasCard : ''}`}>
            {spec}
            {hasCard && <span className={styles.cardBadge}>✓</span>}
          </span>
        )
      })}
    </div>
  )
}
