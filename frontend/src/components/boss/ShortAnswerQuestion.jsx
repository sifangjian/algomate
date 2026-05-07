import { useState } from 'react'
import Button from '../ui/Button/Button'
import { showToast } from '../ui/Toast/index'
import { QUESTION_TYPE_LABELS } from './constants'
import styles from './ShortAnswerQuestion.module.css'

export default function ShortAnswerQuestion({ question, onSubmit, loading }) {
  const [answer, setAnswer] = useState('')

  const handleSubmit = () => {
    if (!answer.trim()) {
      showToast('请输入答案', 'warning')
      return
    }
    onSubmit({ answer: answer.trim() })
  }

  return (
    <div className={styles.container}>
      <span className={styles.typeBadge}>{QUESTION_TYPE_LABELS.short_answer}</span>
      <div className={styles.content}>{question.content}</div>
      <textarea
        className={styles.textarea}
        value={answer}
        onChange={(e) => setAnswer(e.target.value.slice(0, 2000))}
        placeholder="请输入你的答案..."
        disabled={loading}
        maxLength={2000}
      />
      <div className={styles.charCount}>{answer.length}/2000</div>
      <Button
        variant="danger"
        size="lg"
        fullWidth
        onClick={handleSubmit}
        loading={loading}
        disabled={!answer.trim() || loading}
      >
        提交挑战
      </Button>
    </div>
  )
}
