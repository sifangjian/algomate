import React, { useState } from 'react'

function Practice() {
  const [currentQuestion, setCurrentQuestion] = useState(null)
  const [answer, setAnswer] = useState('')

  return (
    <div>
      <div className="page-header">
        <h2>练习中心</h2>
      </div>
      <div className="card">
        <div className="card-title">开始练习</div>
        <p>选择练习类型：</p>
        <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
          <button className="btn btn-primary" onClick={() => setCurrentQuestion({ type: 'choice' })}>
            选择题
          </button>
          <button className="btn btn-primary" onClick={() => setCurrentQuestion({ type: 'short' })}>
            简答题
          </button>
          <button className="btn btn-primary" onClick={() => setCurrentQuestion({ type: 'code' })}>
            代码题
          </button>
        </div>
      </div>
      {currentQuestion && (
        <div className="card">
          <div className="card-title">答题</div>
          <p>题目类型：{currentQuestion.type}</p>
          <div className="form-group">
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="请输入答案"
            />
          </div>
          <button className="btn btn-primary">提交答案</button>
        </div>
      )}
    </div>
  )
}

export default Practice
