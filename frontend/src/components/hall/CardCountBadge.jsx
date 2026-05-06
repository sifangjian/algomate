import styles from './CardCountBadge.module.css'

export default function CardCountBadge({ count }) {
  if (!count || count <= 0) return null
  return (
    <div className={styles.cardCountBadge} aria-label={`已获${count}张卡牌`}>
      已获{count}张卡牌
    </div>
  )
}
