import React, { useState } from 'react'

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

  const handleChange = (e) => {
    const { name, value } = e.target
    setSettings({ ...settings, [name]: value })
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    console.log('设置保存:', settings)
    alert('设置已保存')
  }

  return (
    <div>
      <div className="page-header">
        <h2>个人设置</h2>
      </div>
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
        <button type="submit" className="btn btn-primary">保存设置</button>
      </form>
    </div>
  )
}

export default Settings
