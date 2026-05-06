import { useHallStore } from '../../stores/hallStore'
import NpcAvatar from './NpcAvatar'
import SpecialtyTags from './SpecialtyTags'
import CardCountBadge from './CardCountBadge'
import RecommendTip from './RecommendTip'
import styles from './NpcCard.module.css'

export default function NpcCard({ npc, isNewUser }) {
  const { setSelectedNpc } = useHallStore()
  const isRecommended = isNewUser && npc.name === '老夫子'

  return (
    <div
      className={`${styles.npcCard} ${isRecommended ? styles.recommended : ''}`}
      onClick={() => setSelectedNpc(npc)}
      role="button"
      tabIndex={0}
      aria-label={`${npc.name} - ${npc.title}`}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          setSelectedNpc(npc)
        }
      }}
    >
      <div className={styles.cardTop}>
        <NpcAvatar avatar={npc.avatar} name={npc.name} />
        {isRecommended && <RecommendTip />}
      </div>
      <div className={styles.cardBody}>
        <h3 className={styles.npcName}>{npc.name}</h3>
        <span className={styles.npcTitle}>{npc.title}</span>
        <SpecialtyTags specialties={npc.specialties} />
      </div>
      {npc.card_count > 0 && (
        <CardCountBadge count={npc.card_count} />
      )}
    </div>
  )
}
