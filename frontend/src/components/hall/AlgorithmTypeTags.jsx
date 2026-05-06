import styles from './AlgorithmTypeTags.module.css'

export default function AlgorithmTypeTags({ types, selected, onSelect }) {
  return (
    <div className={styles.typeTags} role="radiogroup" aria-label="算法类型筛选">
      {types.map(type => (
        <button
          key={type.value}
          className={`${styles.typeTag} ${selected === type.value ? styles.typeTagActive : ''}`}
          onClick={() => onSelect(type.value)}
          role="radio"
          aria-checked={selected === type.value}
        >
          {type.label}
        </button>
      ))}
    </div>
  )
}
