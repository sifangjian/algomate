import React, { useState, useEffect } from 'react'

function Settings() {
  const [settings, setSettings] = useState({
    apiKey: '',
    emailHost: '',
    emailPort: 587,
    emailUsername: '',
    emailPassword: '',
    reviewTime: '09:00',
    forgettingCurveParam: 30
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    fetchSettings()
  }, [])

  const fetchSettings = async () => {
    try {
      const res = await fetch('/api/settings/')
      const data = await res.json()
      setSettings({
        apiKey: data.api_key || '',
        emailHost: data.email_host || '',
        emailPort: data.email_port || 587,
        emailUsername: data.email_username || '',
        emailPassword: '',
        reviewTime: data.review_time || '09:00',
        forgettingCurveParam: data.forgetting_curve_param || 30
      })
    } catch (error) {
      console.error('获取设置失败:', error)
      setMessage('加载设置失败')
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setSettings({ ...settings, [name]: value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setMessage('')
    try {
      const res = await fetch('/api/settings/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          api_key: settings.apiKey,
          email_host: settings.emailHost,
          email_port: parseInt(settings.emailPort),
          email_username: settings.emailUsername,
          email_password: settings.emailPassword,
          review_time: settings.reviewTime,
          forgetting_curve_param: parseInt(settings.forgettingCurveParam)
        })
      })
      if (res.ok) {
        setMessage('设置已保存')
        setSettings({ ...settings, emailPassword: '' })
      } else {
        setMessage('保存失败')
      }
    } catch (error) {
      console.error('保存设置失败:', error)
      setMessage('保存失败')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div>
        <div className="page-header">
          <h2>个人设置</h2>
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
        <h2>个人设置</h2>
      </div>
      {message && (
        <div className="card" style={{ backgroundColor: message.includes('失败') ? '#ffe6e6' : '#e6f4ea' }}>
          <p style={{ color: message.includes('失败') ? '#c53030' : '#2d6a4f', margin: 0 }}>{message}</p>
        </div>
      )}
      <form onSubmit={handleSubmit}>
        <div className="card">
          <div className="card-title">API 配置</div>
          <div className="form-group">
            <label>API Key</label>
            <input
              type="password"
              name="apiKey"
              value={settings.apiKey}
              onChange={handleChange}
              placeholder="输入您的 API Key"
            />
          </div>
        </div>
        <div className="card">
          <div className="card-title">邮件服务器配置</div>
          <div className="form-group">
            <label>邮件服务器</label>
            <input
              type="text"
              name="emailHost"
              value={settings.emailHost}
              onChange={handleChange}
              placeholder="smtp.example.com"
            />
          </div>
          <div className="form-group">
            <label>端口</label>
            <input
              type="number"
              name="emailPort"
              value={settings.emailPort}
              onChange={handleChange}
            />
          </div>
          <div className="form-group">
            <label>用户名</label>
            <input
              type="text"
              name="emailUsername"
              value={settings.emailUsername}
              onChange={handleChange}
            />
          </div>
          <div className="form-group">
            <label>密码</label>
            <input
              type="password"
              name="emailPassword"
              value={settings.emailPassword}
              onChange={handleChange}
              placeholder="留空则保持不变"
            />
          </div>
        </div>
        <div className="card">
          <div className="card-title">复习设置</div>
          <div className="form-group">
            <label>每日提醒时间</label>
            <input
              type="time"
              name="reviewTime"
              value={settings.reviewTime}
              onChange={handleChange}
            />
          </div>
          <div className="form-group">
            <label>遗忘曲线参数（天）</label>
            <input
              type="number"
              name="forgettingCurveParam"
              value={settings.forgettingCurveParam}
              onChange={handleChange}
            />
          </div>
        </div>
        <button type="submit" className="btn btn-primary" disabled={saving}>
          {saving ? '保存中...' : '保存设置'}
        </button>
      </form>
    </div>
  )
}

export default Settings