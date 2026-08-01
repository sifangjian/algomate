import { useState, useCallback } from 'react'
import { useCardStore } from '../../stores/cardStore'
import { cardService } from '../../services/cardService'
import Input from '../ui/Input/Input'
import Button from '../ui/Button/Button'
import Modal from '../ui/Modal/Modal'
import { showToast } from '../ui/Toast/index'
import { ALGORITHM_CATEGORIES } from '../../constants/algorithmConstants'
import styles from './CreateCardModal.module.css'

export default function CreateCardModal({ open, onClose, onCreated }) {
    const { addCard } = useCardStore()

    const [form, setForm] = useState({
        name: '',
        algorithm_type: '',
        card_type: 'tip',
        difficulty: 3,
        noteContent: '',
    })
    const [errors, setErrors] = useState({})
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [polishingField, setPolishingField] = useState(null)
    const [polishPreview, setPolishPreview] = useState(null)

    const resetForm = useCallback(() => {
        setForm({
            name: '',
            algorithm_type: '',
            card_type: 'tip',
            difficulty: 3,
            noteContent: '',
        })
        setErrors({})
        setPolishingField(null)
        setPolishPreview(null)
        setIsSubmitting(false)
    }, [])

    const handleClose = useCallback(() => {
        resetForm()
        onClose()
    }, [onClose, resetForm])

    const handleFieldChange = useCallback((field, value) => {
        setForm((prev) => ({ ...prev, [field]: value }))
        setErrors((prev) => {
            if (prev[field]) {
                const next = { ...prev }
                delete next[field]
                return next
            }
            return prev
        })
    }, [])

    const handlePolish = useCallback(async (field) => {
        const content = form.noteContent
        if (!content.trim()) {
            showToast('请先输入内容再进行润色', 'warning')
            return
        }
        setPolishingField(field)
        setPolishPreview(null)
        try {
            const result = await cardService.polishCard({ content, type: field })
            setPolishPreview({ field, content: result.polished_content })
        } catch (err) {
            showToast(`AI润色失败: ${err.message}`, 'error')
            setPolishingField(null)
        }
    }, [form.noteContent])

    const handleAcceptPolish = useCallback(() => {
        if (!polishPreview) return
        setForm((prev) => ({ ...prev, noteContent: polishPreview.content }))
        setPolishPreview(null)
        setPolishingField(null)
    }, [polishPreview])

    const handleRejectPolish = useCallback(() => {
        setPolishPreview(null)
        setPolishingField(null)
    }, [])

    const validate = useCallback(() => {
        const newErrors = {}
        if (!form.name.trim()) newErrors.name = '卡牌名称不能为空'
        setErrors(newErrors)
        return Object.keys(newErrors).length === 0
    }, [form.name])

    const handleSubmit = useCallback(async () => {
        if (!validate()) return
        setIsSubmitting(true)
        try {
            const newCard = await cardService.createCard({
                name: form.name.trim(),
                card_type: form.card_type,
                algorithm_type: form.algorithm_type.trim() || null,
                difficulty: form.difficulty,
            })
            addCard(newCard)
            showToast(`卡牌「${newCard.name}」创建成功！`, 'success')
            onCreated?.(newCard)
            handleClose()
        } catch (err) {
            showToast(`创建失败: ${err.message}`, 'error')
        } finally {
            setIsSubmitting(false)
        }
    }, [form, validate, addCard, onCreated, handleClose])

    return (
        <Modal open={open} onClose={handleClose} title="✨ 创建新卡牌" size="lg">
            <div className={styles.createForm}>
                <Input
                    label="卡牌名称"
                    placeholder="输入卡牌名称，如：二分查找"
                    value={form.name}
                    onChange={(e) => handleFieldChange('name', e.target.value)}
                    error={errors.name}
                    icon="🎴"
                    id="card-name"
                />

                <div className={styles.formField}>
                    <label className={styles.fieldLabel} htmlFor="card-type">
                        算法类型
                    </label>
                    <input
                        id="card-type"
                        className={styles.fieldInput}
                        placeholder="选择或输入算法类型"
                        value={form.algorithm_type}
                        onChange={(e) => handleFieldChange('algorithm_type', e.target.value)}
                        list="type-list"
                    />
                    <datalist id="type-list">
                        {ALGORITHM_CATEGORIES.map((t) => (
                            <option key={t} value={t} />
                        ))}
                    </datalist>
                </div>

                <div className={styles.formField}>
                    <label className={styles.fieldLabel}>卡牌类型</label>
                    <div style={{ display: 'flex', gap: '12px', marginTop: 4 }}>
                        <label style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <input
                                type="radio"
                                name="card_type"
                                value="tip"
                                checked={form.card_type === 'tip'}
                                onChange={() => handleFieldChange('card_type', 'tip')}
                            />
                            💡 技巧卡
                        </label>
                        <label style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <input
                                type="radio"
                                name="card_type"
                                value="problem"
                                checked={form.card_type === 'problem'}
                                onChange={() => handleFieldChange('card_type', 'problem')}
                            />
                            📝 题目卡
                        </label>
                    </div>
                </div>

                <div className={styles.formField}>
                    <label className={styles.fieldLabel}>难度</label>
                    <div className={styles.starRating}>
                        {[1, 2, 3, 4, 5].map((star) => (
                            <button
                                key={star}
                                type="button"
                                className={`${styles.starBtn} ${star <= form.difficulty ? styles.starActive : ''}`}
                                onClick={() => handleFieldChange('difficulty', star)}
                                aria-label={`${star}星`}
                            >
                                {star <= form.difficulty ? '★' : '☆'}
                            </button>
                        ))}
                        <span className={styles.starLabel}>{form.difficulty}/5</span>
                    </div>
                </div>

                <div className={styles.createActions}>
                    <Button variant="ghost" onClick={handleClose} disabled={isSubmitting}>
                        取消
                    </Button>
                    <Button
                        variant="accent"
                        onClick={handleSubmit}
                        loading={isSubmitting}
                        disabled={!!polishingField}
                    >
                        创建卡牌
                    </Button>
                </div>
            </div>
        </Modal>
    )
}
