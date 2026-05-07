import ChoiceQuestion from './ChoiceQuestion'
import ShortAnswerQuestion from './ShortAnswerQuestion'
import LeetCodeChallenge from './LeetCodeChallenge'
import styles from './QuestionRenderer.module.css'

export default function QuestionRenderer({ question, onSubmit, onGiveUp, loading }) {
  if (!question) return null

  return (
    <div className={styles.container}>
      {question.question_type === 'choice' && (
        <ChoiceQuestion question={question} onSubmit={onSubmit} loading={loading} />
      )}
      {question.question_type === 'short_answer' && (
        <ShortAnswerQuestion question={question} onSubmit={onSubmit} loading={loading} />
      )}
      {question.question_type === 'leetcode' && (
        <LeetCodeChallenge question={question} onSubmit={onSubmit} onGiveUp={onGiveUp} loading={loading} />
      )}
    </div>
  )
}
