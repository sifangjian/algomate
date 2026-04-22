import React, { useState, useEffect } from 'react'

const mockQuestions = {
  choice: {
    id: 1,
    type: 'choice',
    title: '选择题示例',
    question: '以下哪种排序算法在最坏情况下的时间复杂度是 O(n log n)?',
    options: [
      { id: 'A', text: '冒泡排序' },
      { id: 'B', text: '快速排序' },
      { id: 'C', text: '堆排序' },
      { id: 'D', text: '插入排序' }
    ],
    correctAnswer: 'C'
  },
  short: {
    id: 2,
    type: 'short',
    title: '简答题示例',
    question: '请简要解释什么是动态规划，以及它与分治法的区别。',
    hint: '可以从问题分解、子问题重叠等角度考虑'
  },
  code: {
    id: 3,
    type: 'code',
    title: '代码题示例',
    question: '请实现一个函数，判断一个字符串是否是回文串（忽略大小写和非字母数字字符）。',
    functionName: 'isPalindrome',
    template: `function isPalindrome(s) {
  // 请在这里编写你的代码

}`
  }
}

function Practice() {
  const [practiceMode, setPracticeMode] = useState(null)
  const [currentQuestion, setCurrentQuestion] = useState(null)
  const [answer, setAnswer] = useState('')
  const [selectedOption, setSelectedOption] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [feedback, setFeedback] = useState(null)
  const [resultHistory, setResultHistory] = useState([])
  const [weakPoints, setWeakPoints] = useState([])
  const [showHistory, setShowHistory] = useState(false)

  useEffect(() => {
    fetchWeakPoints()
  }, [])

  const fetchWeakPoints = async () => {
    try {
      const response = await fetch('/api/practice/weak-points')
      if (response.ok) {
        const data = await response.json()
        setWeakPoints(data.weak_points || [])
      }
    } catch (error) {
      console.error('获取薄弱点失败:', error)
      setWeakPoints([
        { topic: '动态规划', error_count: 5, last_error: '2024-01-15' },
        { topic: '二叉树遍历', error_count: 3, last_error: '2024-01-14' }
      ])
    }
  }

  const handleSelectPracticeType = (type) => {
    const question = { ...mockQuestions[type], timestamp: Date.now() }
    setCurrentQuestion(question)
    setPracticeMode(type)
    setAnswer('')
    setSelectedOption(null)
    setFeedback(null)
  }

  const handleSubmit = async () => {
    if (!currentQuestion) return

    setIsSubmitting(true)
    setFeedback(null)

    const userAnswer = currentQuestion.type === 'choice' ? selectedOption : answer

    if (!userAnswer || (currentQuestion.type === 'choice' && !selectedOption)) {
      alert('请输入答案')
      setIsSubmitting(false)
      return
    }

    try {
      const response = await fetch('/api/practice/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question_id: currentQuestion.id,
          question_type: currentQuestion.type,
          user_answer: userAnswer,
          timestamp: new Date().toISOString()
        })
      })

      if (response.ok) {
        const data = await response.json()
        setFeedback(data)
      } else {
        const mockResult = evaluateAnswer(userAnswer)
        setFeedback(mockResult)
      }
    } catch (error) {
      console.error('提交答案失败:', error)
      const mockResult = evaluateAnswer(userAnswer)
      setFeedback(mockResult)
    } finally {
      setIsSubmitting(false)
    }
  }

  const evaluateAnswer = (userAnswer) => {
    let isCorrect = false
    let score = 0
    let feedbackText = ''
    let suggestions = []

    if (currentQuestion.type === 'choice') {
      isCorrect = userAnswer === currentQuestion.correctAnswer
      score = isCorrect ? 100 : 0
      feedbackText = isCorrect
        ? '回答正确！' + getEncouragement()
        : `回答错误。正确答案是 ${currentQuestion.correctAnswer}。` + getExplanation()
      suggestions = isCorrect ? [] : [
        '建议复习相关概念的原理',
        '可以查看相关笔记加深理解'
      ]
    } else if (currentQuestion.type === 'short') {
      const length = userAnswer.length
      if (length < 30) {
        score = 20
        feedbackText = '答案过于简短，请详细说明你的观点。'
        suggestions = ['尝试从多个角度分析问题', '给出具体的例子来支持你的观点']
      } else if (length < 80) {
        score = 60
        feedbackText = '答案基本正确，但可以更详细一些。'
        suggestions = ['建议补充更多细节', '可以加入实际应用场景']
      } else {
        score = 90
        feedbackText = '回答很好！' + getEncouragement()
        suggestions = ['继续保持这个良好的答题习惯']
      }
      suggestions.push('AI建议：答案已收到，将由老师人工批阅后给出最终分数')
    } else if (currentQuestion.type === 'code') {
      const hasContent = userAnswer.length > currentQuestion.template.length
      if (!hasContent) {
        score = 0
        feedbackText = '请先编写代码再提交。'
        suggestions = ['仔细阅读题目要求', '考虑边界情况的处理']
      } else if (userAnswer.includes('return') || userAnswer.includes('return ')) {
        score = 80
        feedbackText = '代码结构看起来不错！' + getEncouragement()
        suggestions = ['注意检查边界情况的处理', '可以考虑使用正则表达式简化逻辑']
      } else {
        score = 40
        feedbackText = '代码基本框架已给出，但需要完善返回值逻辑。'
        suggestions = ['确保函数有正确的返回值', '测试一些边界情况']
      }
    }

    return {
      is_correct: isCorrect,
      score,
      feedback: feedbackText,
      suggestions,
      weak_point_detected: score < 60 && currentQuestion.type !== 'choice'
    }
  }

  const getEncouragement = () => {
    const encouragements = [
      '继续保持！',
      '太棒了！',
      '做得好！',
      '你真优秀！',
      '继续保持这个势头！'
    ]
    return encouragements[Math.floor(Math.random() * encouragements.length)]
  }

  const getExplanation = () => {
    if (currentQuestion.type === 'choice' && currentQuestion.id === 1) {
      return ' 堆排序的最坏时间复杂度是 O(n log n)，而快速排序的最坏复杂度是 O(n²)。'
    }
    return ''
  }

  const saveToHistory = () => {
    if (!feedback) return

    const record = {
      id: Date.now(),
      question: currentQuestion.question,
      questionType: currentQuestion.type,
      userAnswer: currentQuestion.type === 'choice' ? selectedOption : answer,
      score: feedback.score,
      isCorrect: feedback.is_correct,
      timestamp: new Date().toLocaleString()
    }

    setResultHistory(prev => [record, ...prev])
  }

  useEffect(() => {
    if (feedback) {
      saveToHistory()
    }
  }, [feedback])

  const handlePracticeWeakPoint = (topic) => {
    alert(`即将开始 ${topic} 的专项练习...`)
  }

  const handleReset = () => {
    setPracticeMode(null)
    setCurrentQuestion(null)
    setAnswer('')
    setSelectedOption(null)
    setFeedback(null)
  }

  const renderQuestionDisplay = () => {
    if (!currentQuestion) return null

    return (
      <div className="card">
        <div className="card-title">
          {currentQuestion.title}
          <span style={{
            marginLeft: '10px',
            fontSize: '0.85rem',
            color: '#666',
            fontWeight: 'normal'
          }}>
            [{currentQuestion.type === 'choice' ? '选择题' : currentQuestion.type === 'short' ? '简答题' : '代码题'}]
          </span>
        </div>
        <div style={{ marginBottom: '20px' }}>
          <p style={{ fontSize: '1rem', lineHeight: '1.6' }}>{currentQuestion.question}</p>
          {currentQuestion.hint && (
            <p style={{ fontSize: '0.85rem', color: '#888', marginTop: '10px' }}>
              提示：{currentQuestion.hint}
            </p>
          )}
        </div>
      </div>
    )
  }

  const renderAnswerInput = () => {
    if (!currentQuestion || feedback) return null

    if (currentQuestion.type === 'choice') {
      return (
        <div className="card">
          <div className="card-title">请选择答案</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {currentQuestion.options.map(option => (
              <label
                key={option.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '12px',
                  border: '1px solid #ddd',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  backgroundColor: selectedOption === option.id ? '#e8f4fc' : 'white',
                  transition: 'all 0.2s'
                }}
              >
                <input
                  type="radio"
                  name="choice"
                  value={option.id}
                  checked={selectedOption === option.id}
                  onChange={() => setSelectedOption(option.id)}
                  style={{ marginRight: '10px' }}
                />
                <span style={{ fontWeight: '600', marginRight: '8px' }}>{option.id}.</span>
                <span>{option.text}</span>
              </label>
            ))}
          </div>
        </div>
      )
    }

    if (currentQuestion.type === 'short') {
      return (
        <div className="card">
          <div className="card-title">请输入答案</div>
          <div className="form-group">
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="请详细描述你的答案..."
              style={{
                minHeight: '150px',
                fontSize: '0.95rem',
                lineHeight: '1.6'
              }}
            />
          </div>
          <div style={{ fontSize: '0.85rem', color: '#888' }}>
            字数统计：{answer.length} 字
          </div>
        </div>
      )
    }

    if (currentQuestion.type === 'code') {
      return (
        <div className="card">
          <div className="card-title">请编写代码</div>
          <div className="form-group">
            <textarea
              value={answer || currentQuestion.template}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="请输入你的代码..."
              style={{
                minHeight: '250px',
                fontFamily: "'Monaco', 'Menlo', 'Ubuntu Mono', monospace",
                fontSize: '0.9rem',
                lineHeight: '1.5',
                backgroundColor: '#f8f8f8'
              }}
            />
          </div>
        </div>
      )
    }

    return null
  }

  const renderFeedback = () => {
    if (!feedback) return null

    return (
      <div className="card" style={{
        borderLeft: feedback.is_correct !== false && feedback.score >= 60 ? '4px solid #4caf50' : '4px solid #ff9800'
      }}>
        <div className="card-title">
          {feedback.is_correct ? '✓ 回答正确' : feedback.score >= 60 ? '○ 答案可接受' : '✗ 需要改进'}
          <span style={{
            marginLeft: '15px',
            fontSize: '1rem',
            fontWeight: 'bold',
            color: feedback.is_correct || feedback.score >= 60 ? '#4caf50' : '#ff9800'
          }}>
            {feedback.score}分
          </span>
        </div>

        <div style={{ marginBottom: '15px', lineHeight: '1.6' }}>
          {feedback.feedback}
        </div>

        {feedback.suggestions && feedback.suggestions.length > 0 && (
          <div style={{ marginBottom: '15px' }}>
            <div style={{ fontWeight: '600', marginBottom: '8px', color: '#2c3e50' }}>
              建议：
            </div>
            <ul style={{ marginLeft: '20px', color: '#666' }}>
              {feedback.suggestions.map((suggestion, index) => (
                <li key={index} style={{ marginBottom: '5px' }}>{suggestion}</li>
              ))}
            </ul>
          </div>
        )}

        {feedback.weak_point_detected && (
          <div style={{
            marginTop: '15px',
            padding: '12px',
            backgroundColor: '#fff3cd',
            borderRadius: '6px',
            border: '1px solid #ffc107'
          }}>
            <div style={{ fontWeight: '600', color: '#856404', marginBottom: '5px' }}>
              ⚠️ 薄弱点检测
            </div>
            <div style={{ color: '#856404', fontSize: '0.9rem' }}>
              系统检测到这可能是您的薄弱知识点。建议查看相关笔记或进行专项练习。
            </div>
          </div>
        )}

        <div style={{ marginTop: '20px', display: 'flex', gap: '10px' }}>
          <button className="btn btn-primary" onClick={handleReset}>
            继续练习
          </button>
          {currentQuestion.type === 'choice' && (
            <button className="btn btn-secondary" onClick={() => handleSelectPracticeType('choice')}>
              再做一题
            </button>
          )}
        </div>
      </div>
    )
  }

  const renderWeakPointsSection = () => {
    if (weakPoints.length === 0) return null

    return (
      <div className="card">
        <div className="card-title">薄弱点专项练习</div>
        <p style={{ color: '#666', marginBottom: '15px' }}>
          针对您的薄弱知识点进行专项强化练习
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {weakPoints.map((point, index) => (
            <div
              key={index}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '12px',
                backgroundColor: '#f8f9fa',
                borderRadius: '6px',
                border: '1px solid #e9ecef'
              }}
            >
              <div>
                <div style={{ fontWeight: '600', color: '#2c3e50' }}>{point.topic}</div>
                <div style={{ fontSize: '0.85rem', color: '#888', marginTop: '4px' }}>
                  错误次数：{point.error_count} | 上次错误：{point.last_error}
                </div>
              </div>
              <button
                className="btn btn-primary"
                style={{ padding: '8px 16px', fontSize: '0.85rem' }}
                onClick={() => handlePracticeWeakPoint(point.topic)}
              >
                开始练习
              </button>
            </div>
          ))}
        </div>
      </div>
    )
  }

  const renderResultHistory = () => {
    if (resultHistory.length === 0) return null

    return (
      <div className="card">
        <div className="card-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>答题历史</span>
          <span style={{ fontSize: '0.85rem', fontWeight: 'normal', color: '#666' }}>
            共 {resultHistory.length} 条记录
          </span>
        </div>
        <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
          {resultHistory.map((record, index) => (
            <div
              key={record.id}
              style={{
                padding: '12px',
                borderBottom: index < resultHistory.length - 1 ? '1px solid #eee' : 'none'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                <div style={{ fontWeight: '600', color: '#2c3e50', flex: 1 }}>
                  {record.question.length > 50 ? record.question.substring(0, 50) + '...' : record.question}
                </div>
                <span style={{
                  marginLeft: '10px',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  fontSize: '0.8rem',
                  fontWeight: 'bold',
                  backgroundColor: record.isCorrect ? '#4caf50' : record.score >= 60 ? '#ff9800' : '#f44336',
                  color: 'white'
                }}>
                  {record.score}分
                </span>
              </div>
              <div style={{ fontSize: '0.85rem', color: '#888' }}>
                类型：{record.questionType === 'choice' ? '选择题' : record.questionType === 'short' ? '简答题' : '代码题'} |
                答案：{record.userAnswer} | {record.timestamp}
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="page-header">
        <h2>练习中心</h2>
      </div>

      {!practiceMode && !currentQuestion && (
        <>
          <div className="card">
            <div className="card-title">开始练习</div>
            <p style={{ color: '#666', marginBottom: '15px' }}>选择练习类型：</p>
            <div style={{ display: 'flex', gap: '15px', flexWrap: 'wrap' }}>
              <button
                className="btn btn-primary"
                onClick={() => handleSelectPracticeType('choice')}
                style={{ padding: '15px 30px', fontSize: '1rem' }}
              >
                选择题
              </button>
              <button
                className="btn btn-primary"
                onClick={() => handleSelectPracticeType('short')}
                style={{ padding: '15px 30px', fontSize: '1rem' }}
              >
                简答题
              </button>
              <button
                className="btn btn-primary"
                onClick={() => handleSelectPracticeType('code')}
                style={{ padding: '15px 30px', fontSize: '1rem' }}
              >
                代码题
              </button>
            </div>
          </div>

          {renderWeakPointsSection()}

          {resultHistory.length > 0 && (
            <div className="card">
              <div className="card-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>答题历史</span>
                <button
                  className="btn btn-secondary"
                  style={{ padding: '5px 15px', fontSize: '0.85rem' }}
                  onClick={() => setShowHistory(!showHistory)}
                >
                  {showHistory ? '收起' : '查看详情'}
                </button>
              </div>
              <div style={{ color: '#888' }}>
                共 {resultHistory.length} 条记录，正确率 {
                  Math.round((resultHistory.filter(r => r.isCorrect || r.score >= 60).length / resultHistory.length) * 100)
                }%
              </div>
              {showHistory && renderResultHistory()}
            </div>
          )}
        </>
      )}

      {currentQuestion && !feedback && (
        <>
          {renderQuestionDisplay()}
          {renderAnswerInput()}

          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              className="btn btn-primary"
              onClick={handleSubmit}
              disabled={isSubmitting}
              style={{ padding: '12px 40px', fontSize: '1rem' }}
            >
              {isSubmitting ? '提交中...' : '提交答案'}
            </button>
            <button
              className="btn btn-secondary"
              onClick={handleReset}
              style={{ padding: '12px 40px', fontSize: '1rem' }}
            >
              返回
            </button>
          </div>
        </>
      )}

      {feedback && (
        <>
          {renderQuestionDisplay()}
          {renderFeedback()}
        </>
      )}
    </div>
  )
}

export default Practice