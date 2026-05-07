import { useState } from 'react'
import Button from '../ui/Button/Button'
import { showToast } from '../ui/Toast/index'
import { QUESTION_TYPE_LABELS } from './constants'
import styles from './ChoiceQuestion.module.css'

export default function ChoiceQuestion({ question, onSubmit, loading }) {
  const [selectedOption, setSelectedOption] = useState('')

  const options = Array.isArray(question.options)
    ? question.options
    : Object.keys(question.options || {}).sort().map((k) => question.options[k])

  const handleSubmit = () => {
    if (!selectedOption) {
      showToast('请选择一个选项', 'warning')
      return
    }
    onSubmit({ answer: selectedOption })
  }

  return (
    <div className={styles.container}>
      <span className={styles.typeBadge}>{QUESTION_TYPE_LABELS.choice}</span>
      <div className={styles.content}>{question.content}</div>
      <div className={styles.options}>
        {options.map((option, i) => {
          const label = String.fromCharCode(65 + i)
          return (
            <button
              key={i}
              className={`${styles.option} ${selectedOption === label ? styles.selected : ''}`}
              onClick={() => setSelectedOption(label)}
              disabled={loading}
            >
              <span className={styles.optionLabel}>{label}</span>
              <span className={styles.optionText}>{option}</span>
            </button>
          )
        })}
      </div>
      <Button
        variant="danger"
        size="lg"
        fullWidth
        onClick={handleSubmit}
        loading={loading}
        disabled={!selectedOption || loading}
      >
        提交挑战
      </Button>
    </div>
  )
}
