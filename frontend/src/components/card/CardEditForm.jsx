import { useState, useCallback, useMemo, useEffect, memo } from 'react'
import { useCardStore } from '../../stores/cardStore'
import { cardService } from '../../services/cardService'
import { showToast } from '../ui/Toast/index'
import Button from '../ui/Button/Button'
import ExampleEditor from './ExampleEditor'
import styles from './CardEditForm.module.css'

function parseJSON(value) {
  if (!value) return {}
  if (typeof value === 'object') return value
  try {
    return JSON.parse(value)
  } catch {
    return {}
  }
}

const TIER_FIELDS = {
  basic: [
    { key: 'concept_definition', label: '💡 概念定义', rows: 3 },
    { key: 'features', label: '🔑 特点', rows: 3 },
    { key: 'confusing_concepts', label: '🔀 易混淆概念', rows: 2 },
  ],
  advanced: [
    { key: 'common_mistakes', label: '❌ 易错点', rows: 3 },
    { key: 'extensions', label: '🔄 拓展方向', rows: 3 },
    { key: 'advanced_solutions', label: '⚡ 高级解法', rows: 3 },
  ],
}

const PRACTICAL_TEXT_FIELDS = [
  { key: 'applicable_scenarios', label: '📋 适用场景', rows: 3 },
  { key: 'precautions', label: '⚠️ 注意事项', rows: 2 },
]

function FieldTextarea({ label, value, onChange, rows, onPolish, polishing, polishPreview, onAcceptPolish, onRejectPolish }) {
  return (
    <div className={styles.fieldGroup}>
      <div className={styles.fieldLabelRow}>
        <label className={styles.fieldLabel}>{label}</label>
        <button
          className={styles.polishBtn}
          onClick={onPolish}
          disabled={polishing || !value?.trim()}
        >
          {polishing ? '...' : '✨ 润色'}
        </button>
      </div>
      <textarea
        className={styles.fieldTextarea}
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        rows={rows}
      />
      {polishPreview && (
        <div className={styles.polishPreview}>
          <pre className={styles.polishContent}>{polishPreview.content}</pre>
          <div className={styles.polishActions}>
            <button className={styles.polishAccept} onClick={onAcceptPolish}>✓ 采用</button>
            <button className={styles.polishReject} onClick={onRejectPolish}>✕ 跳过</button>
          </div>
        </div>
      )}
    </div>
  )
}

function CardEditForm({ card, onSave, onCancel }) {
  const { updateCard, setSelectedCard } = useCardStore()
  const [form, setForm] = useState({})
  const [isSaving, setIsSaving] = useState(false)
  const [polishingField, setPolishingField] = useState(null)
  const [polishPreview, setPolishPreview] = useState(null)

  useEffect(() => {
    if (!card) return
    const basic = parseJSON(card.basic_content)
    const practical = parseJSON(card.practical_content)
    const advanced = parseJSON(card.advanced_content)

    setForm({
      basic: { concept_definition: '', features: '', confusing_concepts: '', ...basic },
      practical: {
        examples: practical.examples || [],
        applicable_scenarios: practical.applicable_scenarios || '',
        precautions: practical.precautions || '',
      },
      advanced: { common_mistakes: '', extensions: '', advanced_solutions: '', ...advanced },
      my_notes: card.my_notes || '',
      visual_links: card.visual_links || '',
    })
  }, [card])

  const hasChanges = useMemo(() => {
    if (!card || !form.basic) return false
    const origBasic = parseJSON(card.basic_content)
    const origPractical = parseJSON(card.practical_content)
    const origAdvanced = parseJSON(card.advanced_content)

    const basicChanged = Object.keys(form.basic).some(
      k => (form.basic[k] || '') !== (origBasic[k] || '')
    )
    const practicalChanged = JSON.stringify(form.practical) !== JSON.stringify({
      examples: origPractical.examples || [],
      applicable_scenarios: origPractical.applicable_scenarios || '',
      precautions: origPractical.precautions || '',
    })
    const advancedChanged = Object.keys(form.advanced).some(
      k => (form.advanced[k] || '') !== (origAdvanced[k] || '')
    )
    const notesChanged = (form.my_notes || '') !== (card.my_notes || '')
    return basicChanged || practicalChanged || advancedChanged || notesChanged
  }, [form, card])

  const handleBasicChange = useCallback((key, value) => {
    setForm(prev => ({ ...prev, basic: { ...prev.basic, [key]: value } }))
  }, [])

  const handleAdvancedChange = useCallback((key, value) => {
    setForm(prev => ({ ...prev, advanced: { ...prev.advanced, [key]: value } }))
  }, [])

  const handlePracticalTextChange = useCallback((key, value) => {
    setForm(prev => ({ ...prev, practical: { ...prev.practical, [key]: value } }))
  }, [])

  const handleExampleChange = useCallback((index, updatedExample) => {
    setForm(prev => {
      const examples = [...prev.practical.examples]
      examples[index] = updatedExample
      return { ...prev, practical: { ...prev.practical, examples } }
    })
  }, [])

  const handleExampleRemove = useCallback((index) => {
    setForm(prev => ({
      ...prev,
      practical: {
        ...prev.practical,
        examples: prev.practical.examples.filter((_, i) => i !== index),
      },
    }))
  }, [])

  const handleAddExample = useCallback(() => {
    setForm(prev => ({
      ...prev,
      practical: {
        ...prev.practical,
        examples: [...prev.practical.examples, { title: '', problem: '', solutions: [] }],
      },
    }))
  }, [])

  const handlePolish = useCallback(async (tier, key) => {
    const fieldKey = `${tier}.${key}`
    const content = tier === 'my_notes' ? form.my_notes : form[tier]?.[key]
    if (!content?.trim()) {
      showToast('请先输入内容再进行润色', 'warning')
      return
    }
    setPolishingField(fieldKey)
    setPolishPreview(null)
    try {
      const result = await cardService.polishCard({ content, type: key })
      const polished = result.data?.polished_content || result.polished_content
      setPolishPreview({ field: fieldKey, tier, key, content: polished })
    } catch (err) {
      showToast(`润色失败: ${err.message}`, 'error')
    } finally {
      setPolishingField(null)
    }
  }, [form])

  const handleAcceptPolish = useCallback(() => {
    if (!polishPreview) return
    const { tier, key, content } = polishPreview
    if (tier === 'my_notes') {
      setForm(prev => ({ ...prev, my_notes: content }))
    } else {
      setForm(prev => ({ ...prev, [tier]: { ...prev[tier], [key]: content } }))
    }
    setPolishPreview(null)
  }, [polishPreview])

  const handleRejectPolish = useCallback(() => {
    setPolishPreview(null)
  }, [])

  const handleSave = useCallback(async () => {
    if (!card || !hasChanges) return
    setIsSaving(true)
    try {
      const payload = {
        basic_content: form.basic,
        practical_content: form.practical,
        advanced_content: form.advanced,
        my_notes: form.my_notes,
        visual_links: form.visual_links,
      }
      const updatedCard = await updateCard(card.id, payload)
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

  if (!card || !form.basic) return null

  return (
    <div className={styles.form}>
      {/* 基础层 */}
      <div className={styles.tierSection} style={{ borderLeftColor: '#6366f1' }}>
        <h4 className={styles.tierTitle}>📘 基础</h4>
        {TIER_FIELDS.basic.map(({ key, label, rows }) => (
          <FieldTextarea
            key={key}
            label={label}
            value={form.basic[key]}
            onChange={(v) => handleBasicChange(key, v)}
            rows={rows}
            onPolish={() => handlePolish('basic', key)}
            polishing={polishingField === `basic.${key}`}
            polishPreview={polishPreview?.field === `basic.${key}` ? polishPreview : null}
            onAcceptPolish={handleAcceptPolish}
            onRejectPolish={handleRejectPolish}
          />
        ))}
      </div>

      {/* 实战层 */}
      <div className={styles.tierSection} style={{ borderLeftColor: '#10b981' }}>
        <h4 className={styles.tierTitle}>⚔️ 实战</h4>

        <div className={styles.examplesEditor}>
          <div className={styles.examplesHeader}>
            <span className={styles.fieldLabel}>例题列表</span>
            <button className={styles.addExampleBtn} onClick={handleAddExample}>+ 添加例题</button>
          </div>
          {(form.practical.examples || []).map((example, i) => (
            <ExampleEditor
              key={i}
              example={example}
              index={i}
              onChange={handleExampleChange}
              onRemove={handleExampleRemove}
            />
          ))}
        </div>

        {PRACTICAL_TEXT_FIELDS.map(({ key, label, rows }) => (
          <FieldTextarea
            key={key}
            label={label}
            value={form.practical[key]}
            onChange={(v) => handlePracticalTextChange(key, v)}
            rows={rows}
            onPolish={() => handlePolish('practical', key)}
            polishing={polishingField === `practical.${key}`}
            polishPreview={polishPreview?.field === `practical.${key}` ? polishPreview : null}
            onAcceptPolish={handleAcceptPolish}
            onRejectPolish={handleRejectPolish}
          />
        ))}
      </div>

      {/* 进阶层 */}
      <div className={styles.tierSection} style={{ borderLeftColor: '#8b5cf6' }}>
        <h4 className={styles.tierTitle}>🚀 进阶</h4>
        {TIER_FIELDS.advanced.map(({ key, label, rows }) => (
          <FieldTextarea
            key={key}
            label={label}
            value={form.advanced[key]}
            onChange={(v) => handleAdvancedChange(key, v)}
            rows={rows}
            onPolish={() => handlePolish('advanced', key)}
            polishing={polishingField === `advanced.${key}`}
            polishPreview={polishPreview?.field === `advanced.${key}` ? polishPreview : null}
            onAcceptPolish={handleAcceptPolish}
            onRejectPolish={handleRejectPolish}
          />
        ))}
      </div>

      {/* 个人笔记 */}
      <FieldTextarea
        label="📝 个人笔记"
        value={form.my_notes}
        onChange={(v) => setForm(prev => ({ ...prev, my_notes: v }))}
        rows={3}
        onPolish={() => handlePolish('my_notes', 'my_notes')}
        polishing={polishingField === 'my_notes.my_notes'}
        polishPreview={polishPreview?.field === 'my_notes.my_notes' ? polishPreview : null}
        onAcceptPolish={handleAcceptPolish}
        onRejectPolish={handleRejectPolish}
      />

      <div className={styles.actions}>
        <Button variant="accent" onClick={handleSave} loading={isSaving} disabled={!hasChanges}>
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
