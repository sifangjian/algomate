import { useState, useEffect, useCallback } from 'react'
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
        difficulty: 3,
        noteContent: '',
        prerequisites: [],
    })
    const [errors, setErrors] = useState({})
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [polishingField, setPolishingField] = useState(null)
    const [polishPreview, setPolishPreview] = useState(null)
    const [allCards, setAllCards] = useState([])

    useEffect(() => {
        if (!open) return
        cardService.getAll().then(data => {
            setAllCards(data?.cards || [])
        })
    }, [open])

    const resetForm = useCallback(() => {
        setForm({
            name: '',
            algorithm_type: '',
            difficulty: 3,
            noteContent: '',
            prerequisites: [],
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
            const payload = {
                name: form.name.trim(),
                algorithm_type: form.algorithm_type.trim() || null,
                difficulty: form.difficulty,
            }
            if (form.prerequisites && form.prerequisites.length > 0) {
                payload.prerequisites = form.prerequisites
            }
            const newCard = await cardService.createCard(payload)
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
                    <label className={styles.fieldLabel}>前置节点（可选，用于在算法地图中建立依赖关系）</label>
                    <div className={styles.prereqSelector}>
                        {allCards.map((card) => (
                            <label key={card.id} className={`${styles.prereqChip} ${form.prerequisites.includes(card.id) ? styles.prereqChipActive : ''}`}>
                                <input
                                    type="checkbox"
                                    checked={form.prerequisites.includes(card.id)}
                                    onChange={(e) => {
                                        setForm(prev => ({
                                            ...prev,
                                            prerequisites: e.target.checked
                                                ? [...prev.prerequisites, card.id]
                                                : prev.prerequisites.filter(p => p !== card.id),
                                        }))
                                    }}
                                    style={{ display: 'none' }}
                                />
                                <span>{card.name}</span>
                                {card.algorithm_type && (
                                    <span style={{ marginLeft: 4, fontSize: '0.75em', opacity: 0.7 }}>
                                        ({card.algorithm_type})
                                    </span>
                                )}
                            </label>
                        ))}
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
