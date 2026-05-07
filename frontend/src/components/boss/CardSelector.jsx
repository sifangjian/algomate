import SelectableCard from './SelectableCard'
import NoWeaknessHint from './NoWeaknessHint'
import styles from './CardSelector.module.css'

export default function CardSelector({ weaknessCards, otherCards, hasWeaknessCard, selectedCardId, onSelect, loading }) {
  return (
    <div className={styles.selector}>
      <h3 className={styles.title}>选择应战卡牌</h3>
      {!hasWeaknessCard && <NoWeaknessHint />}
      {weaknessCards.length > 0 && (
        <div className={styles.section}>
          <h4 className={styles.groupTitle}>🔥 弱点卡牌</h4>
          <div className={styles.cardGrid}>
            {weaknessCards.map((card) => (
              <SelectableCard
                key={card.id}
                card={card}
                isWeakness
                selected={card.id === selectedCardId}
                onSelect={() => onSelect(card.id)}
                loading={loading}
              />
            ))}
          </div>
        </div>
      )}
      {otherCards.length > 0 && (
        <div className={styles.section}>
          <h4 className={styles.groupTitle}>其他卡牌</h4>
          <div className={styles.cardGrid}>
            {otherCards.map((card) => (
              <SelectableCard
                key={card.id}
                card={card}
                isWeakness={false}
                selected={card.id === selectedCardId}
                onSelect={() => onSelect(card.id)}
                loading={loading}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
