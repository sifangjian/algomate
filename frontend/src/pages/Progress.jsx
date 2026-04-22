import React from 'react'

function Progress() {
  return (
    <div>
      <div className="page-header">
        <h2>学习进度</h2>
      </div>
      <div className="grid">
        <div className="card">
          <div className="card-title">掌握度概览</div>
          <p>暂无数据</p>
        </div>
        <div className="card">
          <div className="card-title">学习趋势</div>
          <p>暂无数据</p>
        </div>
      </div>
      <div className="card">
        <div className="card-title">统计信息</div>
        <p>正确率变化：暂无数据</p>
      </div>
    </div>
  )
}

export default Progress
