import { useState, useEffect, useCallback } from 'react'
import { settingService } from '../services/settingService'
import GameCard from '../components/ui/Card/GameCard'
import Button from '../components/ui/Button/Button'
import Input from '../components/ui/Input/Input'
import Modal, { ConfirmDialog } from '../components/ui/Modal/Modal'
import { showToast } from '../components/ui/Toast/index'
import styles from './Settings.module.css'

const DEFAULT_SETTINGS = {
  apiConfig: {
    openaiApiKey: '',
    openaiModel: 'gpt-4',
    apiConnectionStatus: 'unknown',
  },
  emailConfig: {
    smtpHost: '',
    smtpPort: 587,
    senderEmail: '',
    authorizationCode: '',
    emailTestStatus: 'idle',
  },
  gameConfig: {
    difficulty: 'normal',
  },
  reminderConfig: {
    enabled: true,
    reminderTime: '20:00',
    channels: {
      email: true,
      browserNotification: false,
    },
  },
}

const DIFFICULTY_OPTIONS = [
  { value: 'easy', label: '简单', desc: '试炼较简单，经验获取少' },
  { value: 'normal', label: '普通', desc: '平衡模式' },
  { value: 'hard', label: '困难', desc: '试炼有挑战，经验获取多' },
]

export default function Settings() {
  const [settings, setSettings] = useState(DEFAULT_SETTINGS)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testingApi, setTestingApi] = useState(false)
  const [testingEmail, setTestingEmail] = useState(false)
  const [showApiKey, setShowApiKey] = useState(false)
  const [showAuthCode, setShowAuthCode] = useState(false)
  const [resetConfirmOpen, setResetConfirmOpen] = useState(false)

  const isDirty =
    JSON.stringify(settings) !== JSON.stringify(DEFAULT_SETTINGS)

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = useCallback(async () => {
    try {
      const data = await settingService.getSettings()
      if (data) {
        setSettings((prev) => ({
          ...prev,
          apiConfig: {
            ...prev.apiConfig,
            openaiApiKey: data.api_key || '',
            openaiModel: 'gpt-4',
          },
          emailConfig: {
            ...prev.emailConfig,
            smtpHost: data.email_host || '',
            smtpPort: data.email_port || 587,
            senderEmail: data.email_username || '',
          },
          reminderConfig: {
            ...prev.reminderConfig,
            reminderTime: data.review_time || '20:00',
          },
        }))
      }
    } catch {
    } finally {
      setLoading(false)
    }
  }, [])

  const updateApiConfig = useCallback((key, value) => {
    setSettings((prev) => ({
      ...prev,
      apiConfig: { ...prev.apiConfig, [key]: value },
    }))
  }, [])

  const updateEmailConfig = useCallback((key, value) => {
    setSettings((prev) => ({
      ...prev,
      emailConfig: { ...prev.emailConfig, [key]: value },
    }))
  }, [])

  const updateGameConfig = useCallback((value) => {
    setSettings((prev) => ({
      ...prev,
      gameConfig: { ...prev.gameConfig, difficulty: value },
    }))
  }, [])

  const updateReminderConfig = useCallback((key, value) => {
    setSettings((prev) => ({
      ...prev,
      reminderConfig: { ...prev.reminderConfig, [key]: value },
    }))
  }, [])

  const handleTestApi = useCallback(async () => {
    if (!settings.apiConfig.openaiApiKey.trim()) {
      showToast('请先输入API Key', 'warning')
      return
    }
    setTestingApi(true)
    try {
      const result = await settingService.testApi(settings.apiConfig.openaiApiKey)
      updateApiConfig('apiConnectionStatus', result.connected ? 'connected' : 'error')
      showToast(result.connected ? '✅ API连接成功!' : `❌ 连接失败: ${result.message}`, result.connected ? 'success' : 'error')
    } catch (err) {
      updateApiConfig('apiConnectionStatus', 'error')
      showToast(`测试失败: ${err.message}`, 'error')
    } finally {
      setTestingApi(false)
    }
  }, [settings.apiConfig.openaiApiKey, updateApiConfig])

  const handleTestEmail = useCallback(async () => {
    setTestingEmail(true)
    try {
      const result = await settingService.testEmail({
        host: settings.emailConfig.smtpHost,
        port: settings.emailConfig.smtpPort,
        email: settings.emailConfig.senderEmail,
        password: settings.emailConfig.authorizationCode,
      })
      updateEmailConfig('emailTestStatus', result.success ? 'success' : 'fail')
      showToast(result.success ? '✅ 测试邮件发送成功!' : `❌ 发送失败: ${result.message}`, result.success ? 'success' : 'error')
    } catch (err) {
      updateEmailConfig('emailTestStatus', 'fail')
      showToast(`发送失败: ${err.message}`, 'error')
    } finally {
      setTestingEmail(false)
    }
  }, [settings.emailConfig, updateEmailConfig])

  const handleSave = useCallback(async () => {
    setSaving(true)
    try {
      await settingService.saveSettings({
        api_key: settings.apiConfig.openaiApiKey,
        email_host: settings.emailConfig.smtpHost,
        email_port: Number(settings.emailConfig.smtpPort),
        email_username: settings.emailConfig.senderEmail,
        email_password: settings.emailConfig.authorizationCode,
        review_time: settings.reminderConfig.reminderTime,
      })
      showToast('设置已保存 ✓', 'success')
    } catch (err) {
      showToast(`保存失败: ${err.message}`, 'error')
    } finally {
      setSaving(false)
    }
  }, [settings])

  const handleReset = useCallback(() => {
    setSettings(DEFAULT_SETTINGS)
    setResetConfirmOpen(false)
    showToast('已恢复默认设置', 'info')
  }, [])

  if (loading) {
    return (
      <div className={`${styles.container} page-container`}>
        <div className={styles.loadingState}>
          <span>⚙️</span>
          <p>加载设置中...</p>
        </div>
      </div>
    )
  }

  return (
    <div className={`${styles.container} page-container`}>
      <h1 className={styles.pageTitle}>⚙️ 系统设置</h1>
      <p className={styles.pageSubtitle}>配置你的算法大陆体验</p>

      <section className={styles.section} aria-label="API配置">
        <h2 className={styles.sectionTitle}>🔑 API 配置</h2>
        <GameCard className={styles.sectionCard}>
          <Input
            label="OpenAI API Key"
            type={showApiKey ? 'text' : 'password'}
            value={settings.apiConfig.openaiApiKey}
            onChange={(e) => updateApiConfig('openaiApiKey', e.target.value)}
            icon="🔐"
            helperText="用于AI对话和试炼生成功能"
          />
          <div className={styles.inputRow}>
            <button
              className={styles.toggleBtn}
              onClick={() => setShowApiKey(!showApiKey)}
              type="button"
            >
              {showApiKey ? '🙈 隐藏' : '👁️ 显示'}
            </button>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleTestApi}
              loading={testingApi}
            >
              测试连接
            </Button>
            <ConnectionDot status={settings.apiConfig.apiConnectionStatus} />
          </div>
        </GameCard>
      </section>

      <section className={styles.section} aria-label="邮件配置">
        <h2 className={styles.sectionTitle}>📧 邮件配置</h2>
        <GameCard className={styles.sectionCard}>
          <div className={styles.formGrid}>
            <Input
              label="SMTP 服务器"
              value={settings.emailConfig.smtpHost}
              onChange={(e) => updateEmailConfig('smtpHost', e.target.value)}
              placeholder="例如: smtp.gmail.com"
              icon="🖥️"
            />
            <Input
              label="端口"
              type="number"
              value={settings.emailConfig.smtpPort}
              onChange={(e) => updateEmailConfig('smtpPort', e.target.value)}
              min={1}
              max={65535}
            />
          </div>
          <Input
            label="发件人邮箱"
            type="email"
            value={settings.emailConfig.senderEmail}
            onChange={(e) => updateEmailConfig('senderEmail', e.target.value)}
            placeholder="your@email.com"
            icon="📬"
          />
          <Input
            label="SMTP 授权码"
            type={showAuthCode ? 'text' : 'password'}
            value={settings.emailConfig.authorizationCode}
            onChange={(e) => updateEmailConfig('authorizationCode', e.target.value)}
            icon="🔒"
          />
          <div className={styles.inputRow}>
            <button
              className={styles.toggleBtn}
              onClick={() => setShowAuthCode(!showAuthCode)}
              type="button"
            >
              {showAuthCode ? '🙈 隐藏' : '👁️ 显示'}
            </button>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleTestEmail}
              loading={testingEmail}
            >
              发送测试邮件
            </Button>
            <ConnectionDot status={settings.emailConfig.emailTestStatus} />
          </div>
        </GameCard>
      </section>

      <section className={styles.section} aria-label="游戏设置">
        <h2 className={styles.sectionTitle}>🎮 游戏设置</h2>
        <GameCard className={styles.sectionCard}>
          <label className={styles.fieldLabel}>难度选择</label>
          <div className={styles.radioGroup}>
            {DIFFICULTY_OPTIONS.map((opt) => (
              <label key={opt.value} className={styles.radioOption}>
                <input
                  type="radio"
                  name="difficulty"
                  value={opt.value}
                  checked={settings.gameConfig.difficulty === opt.value}
                  onChange={() => updateGameConfig(opt.value)}
                />
                <span className={styles.radioContent}>
                  <strong>{opt.label}</strong>
                  <small>{opt.desc}</small>
                </span>
              </label>
            ))}
          </div>
        </GameCard>
      </section>

      <section className={styles.section} aria-label="提醒设置">
        <h2 className={styles.sectionTitle}>⏰ 提醒设置</h2>
        <GameCard className={styles.sectionCard}>
          <div className={styles.toggleRow}>
            <label className={styles.fieldLabel}>启用修炼提醒</label>
            <button
              className={`${styles.switch} ${settings.reminderConfig.enabled ? styles.switchOn : ''}`}
              onClick={() =>
                updateReminderConfig('enabled', !settings.reminderConfig.enabled)
              }
              role="switch"
              aria-checked={settings.reminderConfig.enabled}
            >
              <span className={styles.switchThumb} />
            </button>
          </div>

          {settings.reminderConfig.enabled && (
            <>
              <Input
                label="提醒时间"
                type="time"
                value={settings.reminderConfig.reminderTime}
                onChange={(e) =>
                  updateReminderConfig('reminderTime', e.target.value)
                }
              />

              <label className={styles.fieldLabel}>提醒渠道</label>
              <div className={styles.checkboxGroup}>
                <label className={styles.checkboxOption}>
                  <input
                    type="checkbox"
                    checked={settings.reminderConfig.channels.email}
                    onChange={(e) =>
                      updateReminderConfig('channels', {
                        ...settings.reminderConfig.channels,
                        email: e.target.checked,
                      })
                    }
                  />
                  <span>📧 邮件通知</span>
                </label>
                <label className={styles.checkboxOption}>
                  <input
                    type="checkbox"
                    checked={settings.reminderConfig.channels.browserNotification}
                    onChange={(e) =>
                      updateReminderConfig('channels', {
                        ...settings.reminderConfig.channels,
                        browserNotification: e.target.checked,
                      })
                    }
                  />
                  <span>🔔 浏览器通知</span>
                </label>
              </div>
            </>
          )}
        </GameCard>
      </section>

      <div className={styles.actions}>
        <Button
          variant="primary"
          size="lg"
          onClick={handleSave}
          disabled={!isDirty}
          loading={saving}
          icon='💾'
        >
          保存设置
        </Button>
        <Button
          variant="ghost"
          onClick={() => setResetConfirmOpen(true)}
        >
          恢复默认
        </Button>
      </div>

      <ConfirmDialog
        open={resetConfirmOpen}
        onClose={() => setResetConfirmOpen(false)}
        onConfirm={handleReset}
        title="恢复默认设置"
        message="确定要将所有设置恢复为默认值吗？此操作不可撤销。"
        confirmText="确认恢复默认"
        cancelText="取消"
        variant="danger"
      />
    </div>
  )
}

function ConnectionDot({ status }) {
  const config = {
    unknown: { bg: '#64748b', label: '未测试' },
    connected: { bg: '#10b981', label: '已连接' },
    disconnected: { bg: '#ef4444', label: '未连接' },
    error: { bg: '#ef4444', label: '错误' },
    idle: { bg: '#64748b', label: '' },
    success: { bg: '#10b981', label: '成功' },
    fail: { bg: '#ef4444', label: '失败' },
    sending: { bg: '#f59e0b', label: '发送中...' },
  }

  const c = config[status] || config.unknown

  return (
    <span
      className={styles.connectionDot}
      style={{ background: c.bg }}
      title={c.label}
      role="status"
    >
      {c.bg === '#10b981' && '✓'}
      {c.bg === '#ef4444' && '✕'}
    </span>
  )
}
