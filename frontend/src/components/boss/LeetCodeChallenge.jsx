import Button from '../ui/Button/Button'
import { QUESTION_TYPE_LABELS } from './constants'
import styles from './LeetCodeChallenge.module.css'

export default function LeetCodeChallenge({ question, onSubmit, onGiveUp, loading }) {
  return (
    <div className={styles.container}>
      <span className={styles.typeBadge}>{QUESTION_TYPE_LABELS.leetcode}</span>
      <div className={styles.leetcodeCard}>
        <div className={styles.header}>
          <span className={styles.icon}>🔗</span>
          <span className={styles.title}>
            {question.leetcode_title || 'LeetCode 挑战'}
          </span>
          {question.leetcode_difficulty && (
            <span className={`${styles.diff} ${styles[question.leetcode_difficulty]}`}>
              {question.leetcode_difficulty === 'easy'
                ? '简单'
                : question.leetcode_difficulty === 'medium'
                  ? '中等'
                  : '困难'}
            </span>
          )}
        </div>
        {question.content && (
          <div className={styles.description}>{question.content}</div>
        )}
        {question.leetcode_description && (
          <div className={styles.description}>{question.leetcode_description}</div>
        )}
        {question.leetcode_url && (
          <a
            className={styles.link}
            href={question.leetcode_url}
            target="_blank"
            rel="noopener noreferrer"
          >
            前往 LeetCode 解题 →
          </a>
        )}
      </div>
      <div className={styles.actions}>
        <Button
          variant="danger"
          size="lg"
          fullWidth
          onClick={() => onSubmit({ is_solved: true })}
          loading={loading}
          disabled={loading}
        >
          我已解决
        </Button>
        <Button
          variant="secondary"
          size="lg"
          fullWidth
          onClick={onGiveUp}
          disabled={loading}
        >
          暂时放弃
        </Button>
      </div>
    </div>
  )
}
