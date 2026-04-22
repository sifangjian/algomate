import React from 'react'

function Dashboard() {
  return (
    <div>
      <div className="page-header">
        <h2>首页</h2>
      </div>
      <div className="grid">
        <div className="card">
          <div className="card-title">今日复习计划</div>
          <p>暂无复习计划</p>
        </div>
        <div className="card">
          <div className="card-title">薄弱点提醒</div>
          <p>暂无薄弱点提醒</p>
        </div>
        <div className="card">
          <div className="card-title">学习统计</div>
          <p>学习天数：0 天</p>
        </div>
      </div>
      <div className="card">
        <button className="btn btn-primary">开始复习</button>
      </div>
    </div>
  )
}

export default Dashboard
