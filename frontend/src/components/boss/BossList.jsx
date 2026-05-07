import BossCard from './BossCard'
import styles from './BossList.module.css'

export default function BossList({ bosses, selectedBossId, onSelect }) {
  return (
    <div className={styles.list}>
      <h3 className={styles.title}>Boss列表</h3>
      <div className={styles.cards}>
        {bosses.map((boss) => (
          <BossCard
            key={boss.id}
            boss={boss}
            selected={boss.id === selectedBossId}
            onSelect={() => onSelect(boss)}
          />
        ))}
      </div>
      {bosses.length === 0 && (
        <div className={styles.empty}>暂无Boss</div>
      )}
    </div>
  )
}
