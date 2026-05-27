import { useState, useEffect, useCallback } from 'react'
import { cardService } from '../../services/cardService'
import { showToast } from '../ui/Toast/index'
import Button from '../ui/Button/Button'
import styles from './QuickQuiz.module.css'

export default function QuickQuiz({ task, onComplete, onBack }) {
  const [quizData, setQuizData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [answers, setAnswers] = useState({})
  const [submitted, setSubmitted] = useState(false)
  const [markedForReview, setMarkedForReview] = useState(new Set())
  const [showMarked, setShowMarked] = useState(false)

  useEffect(() => {
    setLoading(true)
    cardService.generateReviewQuiz(task.card_id, 5)
      .then(data => {
        const resp = data?.data || data
        setQuizData(resp)
      })
      .catch(() => {
        showToast('加载快速问答失败', 'error')
      })
      .finally(() => setLoading(false))
  }, [task.card_id])

  const handleAnswer = useCallback((qi, label) => {
    setAnswers(prev => ({ ...prev, [qi]: label }))
  }, [])

  const toggleMark = useCallback((qi) => {
    setMarkedForReview(prev => {
      const next = new Set(prev)
      if (next.has(qi)) next.delete(qi)
      else next.add(qi)
      return next
    })
  }, [])

  const handleSubmit = useCallback(async () => {
    setSubmitted(true)
    try {
      const data = await cardService.completeReviewV1(task.card_id, 'quick_quiz')
      const resp = data?.data || data
      showToast('问答完成！', 'success')
      if (resp?.remaining_endangered > 0) {
        showToast(`还有 ${resp.remaining_endangered} 张濒危卡牌需要修炼`, 'warning')
      }
    } catch {
      showToast('完成修炼失败', 'error')
    }
  }, [task.card_id])

  if (loading) {
    return <div className={styles.loading}>正在生成题目...</div>
  }

  if (!quizData?.questions?.length) {
    return (
      <div className={styles.container}>
        <button className={styles.backBtn} onClick={onBack}>← 返回任务列表</button>
        <div className={styles.emptyPanel}>
          <p>暂无问答题</p>
          <Button variant="ghost" onClick={onBack}>返回</Button>
        </div>
      </div>
    )
  }

  const questions = quizData.questions
  const correctCount = submitted
    ? questions.filter((q, i) => answers[i] === q.correct_answer).length
    : 0

  // 摘要视图
  if (submitted) {
    return (
      <div className={styles.container}>
        <button className={styles.backBtn} onClick={onBack}>← 返回任务列表</button>

        <div className={styles.summary}>
          <div className={styles.summaryHeader}>
            <span>{correctCount === questions.length ? '🎉' : correctCount >= questions.length / 2 ? '💪' : '📖'}</span>
            <span>
              成绩: {correctCount}/{questions.length} ({Math.round(correctCount / questions.length * 100)}%)
            </span>
          </div>
          <div className={styles.summaryStats}>
            <span>标记复习: {markedForReview.size} 题</span>
          </div>
          <div className={styles.summaryActions}>
            {markedForReview.size > 0 && (
              <Button variant="ghost" onClick={() => setShowMarked(!showMarked)}>
                {showMarked ? '收起标记题' : '查看标记题'}
              </Button>
            )}
            <Button variant="ghost" onClick={onBack}>返回任务列表</Button>
          </div>
        </div>

        {showMarked && markedForReview.size > 0 && (
          <div className={styles.markedSection}>
            <h4 className={styles.markedTitle}>标记复习的题目</h4>
            {questions.map((q, qi) => {
              if (!markedForReview.has(qi)) return null
              return (
                <div key={qi} style={{ marginBottom: 12 }}>
                  <p style={{ fontSize: '0.88rem', color: 'var(--color-text-primary)', margin: '0 0 6px' }}>
                    {qi + 1}. {q.question || q.content}
                  </p>
                  <p style={{ fontSize: '0.78rem', color: 'var(--color-danger)', margin: '0 0 4px' }}>
                    你的答案: {answers[qi] || '未作答'}
                  </p>
                  <p style={{ fontSize: '0.78rem', color: 'var(--color-success)', margin: '0 0 4px' }}>
                    正确答案: {q.correct_answer}
                  </p>
                  {q.explanation && (
                    <p style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', margin: 0 }}>
                      {q.explanation}
                    </p>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>✏️ 快速问答 - {task.card_name}</h2>
        <button className={styles.backBtn} onClick={onBack}>← 返回</button>
      </div>

      <div className={styles.quizContent}>
        {questions.map((q, qi) => {
          const isCorrect = submitted && q.correct_answer === answers[qi]
          const isWrong = submitted && answers[qi] && q.correct_answer !== answers[qi]

          return (
            <div key={qi} className={styles.quizQuestion}>
              <div className={styles.questionHeader}>
                <p className={styles.questionText}>
                  <span className={styles.questionNum}>{qi + 1}.</span> {q.question || q.content}
                </p>
                <button
                  className={`${styles.markBtn} ${markedForReview.has(qi) ? styles.markBtnActive : ''}`}
                  onClick={() => toggleMark(qi)}
                  title="标记复习"
                >
                  {markedForReview.has(qi) ? '🔖' : '📎'}
                </button>
              </div>

              <div className={styles.quizOptions}>
                {(q.options || []).map((opt, oi) => {
                  const label = String.fromCharCode(65 + oi)
                  const isSelected = answers[qi] === label
                  const correctOpt = submitted && q.correct_answer === label
                  const wrongOpt = submitted && isSelected && q.correct_answer !== label
                  return (
                    <button
                      key={oi}
                      className={`${styles.quizOption} ${isSelected ? styles.quizOptionSelected : ''} ${correctOpt ? styles.quizOptionCorrect : ''} ${wrongOpt ? styles.quizOptionWrong : ''}`}
                      onClick={() => !submitted && handleAnswer(qi, label)}
                      disabled={submitted}
                    >
                      <span className={styles.quizOptionLabel}>{label}</span>
                      <span className={styles.quizOptionText}>{opt}</span>
                    </button>
                  )
                })}
              </div>

              {submitted && q.explanation && (
                <div className={styles.quizExplanation}>{q.explanation}</div>
              )}
            </div>
          )
        })}

        <div style={{ paddingTop: 8 }}>
          {!submitted ? (
            <Button
              variant="accent"
              onClick={handleSubmit}
              disabled={Object.keys(answers).length === 0}
            >
              📝 提交答案 ({Object.keys(answers).length}/{questions.length})
            </Button>
          ) : null}
        </div>
      </div>
    </div>
  )
}
