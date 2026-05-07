import styles from './AnswerFeedback.module.css'

export default function AnswerFeedback({ result }) {
  if (!result) return null

  return (
    <div className={styles.feedback}>
      {result.feedback && (
        <div className={styles.section}>
          <h4 className={styles.title}>错误分析</h4>
          <p className={styles.text}>{result.feedback}</p>
        </div>
      )}
      {result.improvement && (
        <div className={styles.section}>
          <h4 className={styles.title}>改进建议</h4>
          <p className={styles.text}>{result.improvement}</p>
        </div>
      )}
      {result.explanation && (
        <div className={styles.section}>
          <h4 className={styles.title}>正确解析</h4>
          <p className={styles.text}>{result.explanation}</p>
        </div>
      )}
    </div>
  )
}
