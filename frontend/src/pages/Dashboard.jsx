import React, { useState, useEffect } from 'react'

function Dashboard() {
  const [todayReviews, setTodayReviews] = useState([])
  const [weakPoints, setWeakPoints] = useState([])
  const [stats, setStats] = useState({ learning_days: 0 })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const [reviewRes, weakRes, statsRes] = await Promise.all([
        fetch('/api/dashboard/today-review'),
        fetch('/api/dashboard/weak-points'),
        fetch('/api/dashboard/stats')
      ])
      const reviewData = await reviewRes.json()
      const weakData = await weakRes.json()
      const statsData = await statsRes.json()
      setTodayReviews(reviewData.reviews || [])
      setWeakPoints(weakData.weak_points || [])
      setStats(statsData || { learning_days: 0 })
    } catch (error) {
      console.error('获取仪表盘数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleStartReview = () => {
    window.location.href = '/practice'
  }

  const getDifficultyColor = (difficulty) => {
    switch (difficulty) {
      case '简单': return '#4caf50'
      case '中等': return '#ff9800'
      case '困难': return '#f44336'
      default: return '#999'
    }
  }

  if (loading) {
    return (
      <div>
        <div className="page-header">
          <h2>首页</h2>
        </div>
        <div className="card">
          <p>加载中...</p>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="page-header">
        <h2>首页</h2>
      </div>

      <div className="grid">
        <div className="card">
          <div className="card-title">今日复习计划</div>
          {todayReviews.length === 0 ? (
            <p style={{ color: '#666' }}>今日暂无复习计划</p>
          ) : (
            <div className="review-list">
              {todayReviews.map((review) => (
                <div key={review.id} className="review-item" style={{ padding: '10px 0', borderBottom: '1px solid #eee' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h4 style={{ margin: 0 }}>{review.title}</h4>
                    <span style={{
                      backgroundColor: getDifficultyColor(review.difficulty),
                      color: 'white',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      fontSize: '0.8rem'
                    }}>
                      {review.difficulty}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: '10px', marginTop: '5px', fontSize: '0.85rem', color: '#666' }}>
                    <span>{review.algorithm_type}</span>
                    <span>掌握度: {review.mastery_level}%</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <div className="card-title">薄弱点提醒</div>
          {weakPoints.length === 0 ? (
            <p style={{ color: '#666' }}>暂无薄弱点提醒</p>
          ) : (
            <div className="weak-points-list">
              {weakPoints.map((point) => (
                <div key={point.id} className="weak-point-item" style={{ padding: '8px 0', borderBottom: '1px solid #eee' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 500 }}>{point.title}</span>
                    <span style={{ color: '#f44336', fontWeight: 'bold' }}>{point.mastery_level}%</span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#666', marginTop: '3px' }}>
                    <span>{point.algorithm_type}</span>
                    <span style={{ marginLeft: '10px' }}>复习 {point.review_count} 次</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <div className="card-title">学习统计</div>
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <div style={{ fontSize: '48px', fontWeight: 'bold', color: '#2196f3' }}>{stats.learning_days}</div>
            <div style={{ color: '#666', marginTop: '5px' }}>连续学习天数</div>
          </div>
        </div>
      </div>

      <div className="card" style={{ textAlign: 'center', padding: '30px' }}>
        <button className="btn btn-primary" onClick={handleStartReview} style={{ fontSize: '1.1rem', padding: '12px 40px' }}>
          开始复习
        </button>
        {todayReviews.length > 0 && (
          <p style={{ marginTop: '10px', color: '#666' }}>
            您有 {todayReviews.length} 个复习任务待完成
          </p>
        )}
      </div>
    </div>
  )
}

export default Dashboard