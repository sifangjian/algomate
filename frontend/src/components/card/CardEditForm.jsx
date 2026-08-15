import { useState, useCallback } from 'react'
import { useCardStore } from '../../stores/cardStore'
import styles from './CardEditForm.module.css'

const FIELD_LABELS = {
  basic_content: {
    label: '基础入门',
    fields: [
      { key: 'concept_definition', label: '概念定义' },
      { key: 'features', label: '特点' },
      { key: 'confusing_concepts', label: '易混淆概念' },
    ],
  },
  practical_content: {
    label: '实战应用',
    fields: [
      { key: 'examples', label: '示例' },
      { key: 'common_pitfalls', label: '常见陷阱' },
    ],
  },
  advanced_content: {
    label: '进阶提升',
    fields: [
      { key: 'optimization', label: '优化' },
      { key: 'extended_applications', label: '扩展应用' },
      { key: 'related_algorithms', label: '相关算法' },
    ],
  },
}

function parseJson(str) {
  try { return JSON.parse(str || '{}') } catch { return {} }
}

export default function CardEditForm({ card, onSave, onCancel }) {
  const store = useCardStore()
  const updateCard = store?.updateCard
  const [dirty, setDirty] = useState(false)
  const [edits, setEdits] = useState({})

  const getContent = useCallback((sectionKey) => {
    if (edits[sectionKey]) {
      return edits[sectionKey]
    }
    return parseJson(card?.[sectionKey])
  }, [card, edits])

  const handleFieldChange = useCallback((sectionKey, fieldKey, value) => {
    const currentContent = getContent(sectionKey)
    setEdits(prev => ({
      ...prev,
      [sectionKey]: { ...currentContent, [fieldKey]: value },
    }))
    setDirty(true)
  }, [getContent])

  const handleSubmit = useCallback(async () => {
    if (!dirty || !card) return
    try {
      const merged = {
        ...card,
        ...Object.fromEntries(
          Object.entries(edits).map(([k, v]) => [k, v])
        ),
      }
      if (onSave) {
        await onSave(merged)
      } else if (updateCard) {
        await updateCard(card.id, merged)
      }
      setDirty(false)
    } catch (err) {
      console.error('Save failed:', err)
    }
  }, [dirty, card, edits, onSave, updateCard])

  const handleCancel = useCallback(() => {
    if (onCancel) onCancel()
  }, [onCancel])

  if (!card) {
    return null
  }

  return (
    <form className={styles.cardEditForm} onSubmit={(e) => { e.preventDefault(); handleSubmit() }}>
      {Object.entries(FIELD_LABELS).map(([sectionKey, section]) => {
        const content = getContent(sectionKey)
        return (
          <div key={sectionKey} className={styles.dimensionSection}>
            <div className={styles.dimensionHeader}>{section.label}</div>
            {section.fields.map((field) => (
              <div key={field.key} className={styles.fieldGroup}>
                <label className={styles.fieldLabel}>{field.label}</label>
                <textarea
                  className={styles.textarea}
                  value={content[field.key] || ''}
                  onChange={(e) => handleFieldChange(sectionKey, field.key, e.target.value)}
                  rows={4}
                />
              </div>
            ))}
          </div>
        )
      })}
      <div className={styles.formActions}>
        <button type="button" onClick={handleCancel} className={styles.cancelBtn}>取消</button>
        <button type="submit" disabled={!dirty} className={styles.saveBtn}>保存</button>
      </div>
    </form>
  )
}
