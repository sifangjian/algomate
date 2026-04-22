import React, { useState, useEffect } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import { Radar, Line, Bar } from 'react-chartjs-2'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler
)

function Progress() {
  const [radarData, setRadarData] = useState(null)
  const [trendData, setTrendData] = useState(null)
  const [statsData, setStatsData] = useState(null)
  const [accuracyData, setAccuracyData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [timeRange, setTimeRange] = useState('week')

  useEffect(() => {
    fetchProgressData()
  }, [timeRange])

  const fetchProgressData = async () => {
    try {
      const [masteryRes, trendRes, statsRes, accuracyRes] = await Promise.all([
        fetch('/api/progress/mastery'),
        fetch(`/api/progress/trend?range=${timeRange}`),
        fetch('/api/progress/stats'),
        fetch(`/api/progress/accuracy?range=${timeRange}`)
      ])
      const mastery = await masteryRes.json()
      const trend = await trendRes.json()
      const stats = await statsRes.json()
      const accuracy = await accuracyRes.json()
      
      setRadarData(mastery)
      setTrendData(trend)
      setStatsData(stats)
      setAccuracyData(accuracy)
    } catch (error) {
      console.error('获取进度数据失败:', error)
      initMockData()
    } finally {
      setLoading(false)
    }
  }

  const initMockData = () => {
    setRadarData({
      labels: ['数组', '字符串', '链表', '树', '图', '动态规划', '回溯', '贪心'],
      datasets: [{
        label: '掌握度',
        data: [75, 82, 68, 85, 45, 60, 55, 70],
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 2,
        pointBackgroundColor: 'rgba(54, 162, 235, 1)'
      }]
    })

    const labels = timeRange === 'day' 
      ? ['6:00', '9:00', '12:00', '15:00', '18:00', '21:00']
      : timeRange === 'week'
      ? ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
      : ['第1周', '第2周', '第3周', '第4周']

    setTrendData({
      labels,
      datasets: [{
        label: '刷题数量',
        data: timeRange === 'day' ? [2, 5, 3, 6, 4, 8] : timeRange === 'week' ? [12, 18, 15, 22, 20, 25, 16] : [65, 78, 85, 92],
        borderColor: 'rgba(75, 192, 192, 1)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        tension: 0.4,
        fill: true
      }]
    })

    setStatsData({
      today: { questions: 8, correct: 6, accuracy: 75 },
      week: { questions: 45, correct: 38, accuracy: 84 },
      month: { questions: 180, correct: 152, accuracy: 84 }
    })

    setAccuracyData({
      labels,
      datasets: [{
        label: '正确率 (%)',
        data: timeRange === 'day' ? [60, 80, 75, 85, 90, 88] : timeRange === 'week' ? [72, 78, 85, 80, 88, 92, 84] : [75, 78, 82, 84],
        borderColor: 'rgba(255, 99, 132, 1)',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        tension: 0.4,
        fill: true
      }]
    })
  }

  if (loading) {
    return (
      <div>
        <div className="page-header">
          <h2>学习进度</h2>
        </div>
        <div className="card">
          <p>加载中...</p>
        </div>
      </div>
    )
  }

  const radarOptions = {
    responsive: true,
    maintainAspectRatio: true,
    scales: {
      r: {
        beginAtZero: true,
        max: 100,
        ticks: {
          stepSize: 20
        }
      }
    },
    plugins: {
      legend: {
        position: 'bottom'
      }
    }
  }

  const lineOptions = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        position: 'bottom'
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        max: timeRange === 'month' ? 100 : 30
      }
    }
  }

  const barOptions = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        position: 'bottom'
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100
      }
    }
  }

  return (
    <div>
      <div className="page-header">
        <h2>学习进度</h2>
      </div>

      <div className="grid">
        <div className="card">
          <div className="card-title">算法类型掌握度</div>
          {radarData ? (
            <div style={{ maxWidth: '400px', margin: '0 auto' }}>
              <Radar data={radarData} options={radarOptions} />
            </div>
          ) : (
            <p style={{ color: '#666', textAlign: 'center' }}>暂无数据</p>
          )}
        </div>

        <div className="card">
          <div className="card-title">学习趋势</div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '10px', gap: '10px' }}>
            <button 
              className={`btn ${timeRange === 'day' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setTimeRange('day')}
              style={{ padding: '5px 10px', fontSize: '0.8rem' }}
            >
              每日
            </button>
            <button 
              className={`btn ${timeRange === 'week' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setTimeRange('week')}
              style={{ padding: '5px 10px', fontSize: '0.8rem' }}
            >
              每周
            </button>
            <button 
              className={`btn ${timeRange === 'month' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setTimeRange('month')}
              style={{ padding: '5px 10px', fontSize: '0.8rem' }}
            >
              每月
            </button>
          </div>
          {trendData ? (
            <div style={{ maxWidth: '500px', margin: '0 auto' }}>
              <Line data={trendData} options={lineOptions} />
            </div>
          ) : (
            <p style={{ color: '#666', textAlign: 'center' }}>暂无数据</p>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-title">统计概览</div>
        {statsData ? (
          <div className="stats-overview" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
            <div style={{ textAlign: 'center', padding: '20px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#2196f3' }}>{statsData.today.questions}</div>
              <div style={{ color: '#666', marginTop: '5px' }}>今日刷题</div>
              <div style={{ fontSize: '0.85rem', color: '#4caf50', marginTop: '5px' }}>
                正确率: {statsData.today.accuracy}%
              </div>
            </div>
            <div style={{ textAlign: 'center', padding: '20px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#4caf50' }}>{statsData.week.questions}</div>
              <div style={{ color: '#666', marginTop: '5px' }}>本周刷题</div>
              <div style={{ fontSize: '0.85rem', color: '#4caf50', marginTop: '5px' }}>
                正确率: {statsData.week.accuracy}%
              </div>
            </div>
            <div style={{ textAlign: 'center', padding: '20px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#ff9800' }}>{statsData.month.questions}</div>
              <div style={{ color: '#666', marginTop: '5px' }}>本月刷题</div>
              <div style={{ fontSize: '0.85rem', color: '#4caf50', marginTop: '5px' }}>
                正确率: {statsData.month.accuracy}%
              </div>
            </div>
          </div>
        ) : (
          <p style={{ color: '#666', textAlign: 'center' }}>暂无数据</p>
        )}
      </div>

      <div className="card">
        <div className="card-title">正确率变化曲线</div>
        {accuracyData ? (
          <div style={{ maxWidth: '600px', margin: '0 auto' }}>
            <Line data={accuracyData} options={lineOptions} />
          </div>
        ) : (
          <p style={{ color: '#666', textAlign: 'center' }}>暂无数据</p>
        )}
      </div>
    </div>
  )
}

export default Progress
