import NpcCard from './NpcCard'
import styles from './NpcGrid.module.css'

export default function NpcGrid({ npcs, isNewUser }) {
  if (!npcs || npcs.length === 0) {
    return (
      <div className={styles.emptyState}>
        <p>未找到匹配的导师</p>
      </div>
    )
  }

  return (
    <div className={styles.npcGrid}>
      {npcs.map(npc => (
        <NpcCard
          key={npc.id}
          npc={npc}
          isNewUser={isNewUser}
        />
      ))}
    </div>
  )
}
