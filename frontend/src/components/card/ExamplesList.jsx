import { useState, useCallback, memo } from 'react'
import styles from './ExamplesList.module.css'

const SolutionItem = memo(function SolutionItem({ solution }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className={styles.solutionItem}>
      <button className={styles.solutionHeader} onClick={() => setExpanded(prev => !prev)}>
        <span className={styles.solutionName}>{solution.name || '解法'}</span>
        {solution.complexity && (
          <span className={styles.complexityTag}>{solution.complexity}</span>
        )}
        <span className={`${styles.toggle} ${expanded ? styles.toggleOpen : ''}`}>▼</span>
      </button>
      {expanded && (
        <div className={styles.solutionBody}>
          {solution.principle && (
            <div className={styles.principle}>
              <span className={styles.fieldLabel}>原理</span>
              <p>{solution.principle}</p>
            </div>
          )}
          {solution.code && (
            <div className={styles.codeSection}>
              <span className={styles.fieldLabel}>代码</span>
              <pre className={styles.codeBlock}>{solution.code}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
})

const ExampleItem = memo(function ExampleItem({ example, index }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className={styles.exampleItem}>
      <button className={styles.exampleHeader} onClick={() => setExpanded(prev => !prev)}>
        <span className={styles.exampleIndex}>#{index + 1}</span>
        <span className={styles.exampleTitle}>{example.title || `例题 ${index + 1}`}</span>
        <span className={`${styles.toggle} ${expanded ? styles.toggleOpen : ''}`}>▼</span>
      </button>
      {expanded && (
        <div className={styles.exampleBody}>
          {example.problem && (
            <div className={styles.problemSection}>
              <span className={styles.fieldLabel}>题目</span>
              <div className={styles.problemText}>{example.problem}</div>
            </div>
          )}
          {example.solutions && example.solutions.length > 0 && (
            <div className={styles.solutionsList}>
              <span className={styles.fieldLabel}>解法</span>
              {example.solutions.map((sol, si) => (
                <SolutionItem key={si} solution={sol} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
})

export default function ExamplesList({ examples }) {
  if (!examples || examples.length === 0) return null

  return (
    <div className={styles.examplesList}>
      {examples.map((example, i) => (
        <ExampleItem key={i} example={example} index={i} />
      ))}
    </div>
  )
}
