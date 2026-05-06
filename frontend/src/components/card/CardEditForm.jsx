import { useState, useCallback, useMemo, useEffect, memo } from 'react'
import { cardService } from '../../services/cardService'
import { useCardStore } from '../../stores/cardStore'
import { showToast } from '../ui/Toast/index'
import Button from '../ui/Button/Button'
import styles from './CardEditForm.module.css'

const EDITABLE_DIMENSIONS = [
  { key: 'core_concept', label: '💡 核心概念', rows: 3 },
  { key: 'key_points', label: '🔑 关键要点', rows: 4 },
  { key: 'code_template', label: '💻 代码模板', rows: 6 },
  { key: 'time_complexity', label: '⏱️ 时间复杂度', rows: 2 },
  { key: 'space_complexity', label: '📦 空间复杂度', rows: 2 },
  { key: 'typical_problems', label: '🎯 典型题目', rows: 4 },
  { key: 'common_mistakes', label: '⚠️ 常见错误', rows: 3 },
  { key: 'optimization', label: '🚀 优化思路', rows: 3 },
  { key: 'extensions', label: '🔗 扩展知识', rows: 3 },
  { key: 'summary', label: '📝 总结', rows: 3 },
]

function dimensionToString(value) {
  if (value == null) return ''
  if (typeof value === 'string') return value
  if (Array.isArray(value)) {
    try {
      return JSON.stringify(value)
    } catch {
      return String(value)
    }
  }
  return String(value)
}

function CardEditForm({ card, onSave, onCancel }) {
  const { updateCard, setSelectedCard } = useCardStore()
  const [form, setForm] = useState({})
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    if (!card) return
    const initial = {}
    EDITABLE_DIMENSIONS.forEach(({ key }) => {
      initial[key] = dimensionToString(card[key])
    })
    initial.name = card.name || ''
    initial.algorithm_type = card.algorithm_type || ''
    setForm(initial)
  }, [card])

  const hasChanges = useMemo(() => {
    if (!card) return false
    return EDITABLE_DIMENSIONS.some(({ key }) => {
      const original = dimensionToString(card[key])
      const current = (form[key] || '').trim()
      return original !== current
    }) || (form.name || '').trim() !== (card.name || '') ||
      (form.algorithm_type || '').trim() !== (card.algorithm_type || '')
  }, [form, card])

  const handleFieldChange = useCallback((key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }))
  }, [])

  const handleSave = useCallback(async () => {
    if (!card || !hasChanges) return
    setIsSaving(true)
    try {
      const payload = {}
      if ((form.name || '').trim() !== (card.name || '')) {
        payload.name = form.name.trim()
      }
      if ((form.algorithm_type || '').trim() !== (card.algorithm_type || '')) {
        payload.algorithm_type = form.algorithm_type.trim() || null
      }
      EDITABLE_DIMENSIONS.forEach(({ key }) => {
        const original = dimensionToString(card[key])
        const current = (form[key] || '').trim()
        if (original !== current) {
          payload[key] = current || null
        }
      })

      const result = await cardService.updateCard(card.id, payload)
      if (result && result.code === 40002) {
        showToast('卡牌内容未变更', 'warning')
        return
      }
      const updatedCard = result.data || result
      updateCard(card.id, updatedCard)
      setSelectedCard(updatedCard)
      showToast(`卡牌「${card.name}」已更新`, 'success')
      onSave?.(updatedCard)
    } catch (err) {
      if (err.message?.includes('40002') || err.message?.includes('未变更')) {
        showToast('卡牌内容未变更', 'warning')
      } else {
        showToast(`保存失败: ${err.message}`, 'error')
      }
    } finally {
      setIsSaving(false)
    }
  }, [card, form, hasChanges, updateCard, setSelectedCard, onSave])

  if (!card) return null

  return (
    <div className={styles.form}>
      <div className={styles.nameRow}>
        <div className={styles.fieldGroup}>
          <label className={styles.fieldLabel}>🎴 卡牌名称</label>
          <input
            className={styles.fieldInput}
            value={form.name || ''}
            onChange={(e) => handleFieldChange('name', e.target.value)}
            placeholder="卡牌名称"
          />
        </div>
        <div className={styles.fieldGroup}>
          <label className={styles.fieldLabel}>🏷️ 算法类型</label>
          <input
            className={styles.fieldInput}
            value={form.algorithm_type || ''}
            onChange={(e) => handleFieldChange('algorithm_type', e.target.value)}
            placeholder="如：Dynamic Programming"
          />
        </div>
      </div>

      <div className={styles.dimensionsGrid}>
        {EDITABLE_DIMENSIONS.map(({ key, label, rows }) => (
          <div key={key} className={styles.fieldGroup}>
            <label className={styles.fieldLabel}>{label}</label>
            <textarea
              className={styles.fieldTextarea}
              value={form[key] || ''}
              onChange={(e) => handleFieldChange(key, e.target.value)}
              placeholder={`输入${label.replace(/^[^\s]+\s/, '')}...`}
              rows={rows}
            />
          </div>
        ))}
      </div>

      <div className={styles.actions}>
        <Button
          variant="accent"
          onClick={handleSave}
          loading={isSaving}
          disabled={!hasChanges}
        >
          💾 保存
        </Button>
        <Button variant="ghost" onClick={onCancel} disabled={isSaving}>
          取消
        </Button>
      </div>
    </div>
  )
}

export default memo(CardEditForm)
