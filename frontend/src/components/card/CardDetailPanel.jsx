import { useState, useEffect, useCallback, useRef } from 'react'
import { createPortal } from 'react-dom'
import { useNavigate } from 'react-router-dom'
import { useCardStore } from '../../stores/cardStore'
import { showToast } from '../ui/Toast/index'
import Button from '../ui/Button/Button'
import DimensionSection from '../card/DimensionSection'
import VisualLinksSection from '../card/VisualLinksSection'
import DialogueHistorySection from '../card/DialogueHistorySection'
import CardEditForm from '../card/CardEditForm'
import RetakeButton from '../card/RetakeButton'
import { ALGORITHM_ICONS } from '../../constants/algorithmConstants'
import styles from './CardDetailPanel.module.css'

function getStatusLabel(status) {
    switch (status) {
        case 'endangered': return '濒危'
        case 'pending_retake': return '待重修'
        default: return '正常'
    }
}

function getStatusClass(status) {
    switch (status) {
        case 'endangered': return styles.statusEndangered
        case 'pending_retake': return styles.statusPendingRetake
        default: return styles.statusNormal
    }
}

export default function CardDetailPanel({ open, onClose, sourceRect }) {
    const navigate = useNavigate()
    const { selectedCard, deleteCard } = useCardStore()
    const [isEditing, setIsEditing] = useState(true)
    const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false)
    const [isDeleting, setIsDeleting] = useState(false)
    const [expanded, setExpanded] = useState(false)
    const [closing, setClosing] = useState(false)
    const panelRef = useRef(null)
    const isClosingRef = useRef(false)

    useEffect(() => {
        if (open && sourceRect) {
            document.body.style.overflow = 'hidden'
            setExpanded(false)
            setClosing(false)
            isClosingRef.current = false
            const timer = requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    setExpanded(true)
                })
            })
            return () => {
                cancelAnimationFrame(timer)
                document.body.style.overflow = ''
            }
        }
        return () => {
            document.body.style.overflow = ''
        }
    }, [open, sourceRect])

    useEffect(() => {
        if (!open) {
            setIsEditing(true)
            setExpanded(false)
            setClosing(false)
            isClosingRef.current = false
        }
    }, [open])

    const handleEdit = useCallback(() => {
        setIsEditing(true)
    }, [])

    const handleCancelEdit = useCallback(() => {
        setIsEditing(false)
    }, [])

    const handleEditSave = useCallback(() => {
        setIsEditing(false)
    }, [])

    const handleDeleteRequest = useCallback(() => {
        setDeleteConfirmOpen(true)
    }, [])

    const handleDeleteConfirm = useCallback(async () => {
        if (!selectedCard) return
        setIsDeleting(true)
        try {
            await deleteCard(selectedCard.id)
            showToast(`卡牌「${selectedCard.name}」已删除`, 'success')
            setDeleteConfirmOpen(false)
            handleClose()
        } catch (err) {
            showToast(`删除失败: ${err.message}`, 'error')
        } finally {
            setIsDeleting(false)
        }
    }, [selectedCard, deleteCard])

    const handleClose = useCallback(() => {
        if (isClosingRef.current) return
        isClosingRef.current = true
        setClosing(true)
        setExpanded(false)

        const panel = panelRef.current
        if (panel) {
            const handler = (e) => {
                if (e.propertyName === 'top' || e.propertyName === 'left') {
                    panel.removeEventListener('transitionend', handler)
                    isClosingRef.current = false
                    onClose?.()
                }
            }
            panel.addEventListener('transitionend', handler)
            setTimeout(() => {
                panel.removeEventListener('transitionend', handler)
                isClosingRef.current = false
                onClose?.()
            }, 500)
        } else {
            isClosingRef.current = false
            onClose?.()
        }
    }, [onClose])

    const handleReview = useCallback(() => {
        if (selectedCard) {
            navigate(`/boss/battle?cardId=${selectedCard.id}`)
        }
    }, [selectedCard, navigate])

    useEffect(() => {
        if (open) {
            const handleEsc = (e) => {
                if (e.key === 'Escape') handleClose()
            }
            document.addEventListener('keydown', handleEsc)
            return () => document.removeEventListener('keydown', handleEsc)
        }
    }, [open, handleClose])

    if (!open || !selectedCard || !sourceRect) return null

    const maxDur = selectedCard.max_durability || 100
    const durPercent = Math.round((selectedCard.durability / maxDur) * 100)

    const collapsedStyle = {
        position: 'fixed',
        top: `${sourceRect.top}px`,
        left: `${sourceRect.left}px`,
        width: `${sourceRect.width}px`,
        height: `${sourceRect.height}px`,
        opacity: 0.9,
        borderRadius: '8px',
        transform: 'none',
    }

    const expandedStyle = {
        position: 'fixed',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        width: '480px',
        maxWidth: '90vw',
        maxHeight: '85vh',
        opacity: 1,
        borderRadius: '16px',
    }

    const panelStyle = closing
        ? collapsedStyle
        : expanded
            ? expandedStyle
            : collapsedStyle

    return createPortal(
        <div
            className={`${styles.overlay} ${expanded && !closing ? styles.overlayExpanded : ''}`}
            onClick={handleClose}
            role="presentation"
        >
            <div
                ref={panelRef}
                className={styles.panel}
                style={panelStyle}
                role="dialog"
                aria-label={selectedCard.name}
                onClick={(e) => e.stopPropagation()}
            >
                <div className={`${styles.panelContent} ${expanded && !closing ? styles.panelContentVisible : ''}`}>
                    <div className={styles.panelHeader}>
                        <div className={styles.panelHeaderLeft}>
                            <span className={styles.panelHeaderIcon}>
                                {ALGORITHM_ICONS[selectedCard.algorithm_type] || '📜'}
                            </span>
                            <h2 className={styles.panelHeaderName}>{selectedCard.name}</h2>
                        </div>
                        <button className={styles.panelCloseBtn} onClick={handleClose} aria-label="关闭">
                            ✕
                        </button>
                    </div>

                    <div className={styles.panelBody}>
                        <div className={styles.badges}>
                            {selectedCard.algorithm_type && (
                                <span className={styles.categoryBadge}>{selectedCard.algorithm_type}</span>
                            )}
                            <span className={`${styles.statusBadge} ${getStatusClass(selectedCard.status)}`}>
                                {getStatusLabel(selectedCard.status)}
                            </span>
                        </div>

                        <div className={styles.statsRow}>
                            <div className={styles.statItem}>
                                <span className={styles.statIcon}>🛡️</span>
                                <span className={styles.statValue}>{durPercent}%</span>
                                <span className={styles.statDesc}>
                                    {selectedCard.durability > 60 ? '状态良好' : selectedCard.durability >= 30 ? '需要关注' : '濒危警告'}
                                </span>
                                <div className={styles.durBar}>
                                    <div
                                        className={styles.durFill}
                                        style={{
                                            width: `${durPercent}%`,
                                            background: selectedCard.durability > 60
                                                ? 'linear-gradient(90deg, #10b981, #34d399)'
                                                : selectedCard.durability >= 30
                                                    ? 'linear-gradient(90deg, #f59e0b, #fbbf24)'
                                                    : 'linear-gradient(90deg, #ef4444, #f87171)',
                                        }}
                                    />
                                </div>
                            </div>
                            <div className={styles.statItem}>
                                <span className={styles.statIcon}>⭐</span>
                                <span className={styles.statValue}>
                                    {'★'.repeat(selectedCard.difficulty)}{'☆'.repeat(5 - selectedCard.difficulty)}
                                </span>
                                <span className={styles.statDesc}>
                                    {['', '入门', '简单', '中等', '困难', '地狱'][selectedCard.difficulty] || ''}
                                </span>
                            </div>
                            {selectedCard.review_level != null && (
                                <div className={styles.statItem}>
                                    <span className={styles.statIcon}>⚔️</span>
                                    <span className={styles.statValue}>Lv.{selectedCard.review_level}</span>
                                    <span className={styles.statDesc}>
                                        {selectedCard.review_level <= 1 ? '初窥门径'
                                            : selectedCard.review_level <= 3 ? '初学乍练'
                                                : selectedCard.review_level <= 5 ? '小有所成'
                                                    : selectedCard.review_level <= 7 ? '融会贯通'
                                                        : '登峰造极'}
                                    </span>
                                </div>
                            )}
                            <div className={styles.statItem}>
                                <span className={styles.statIcon}>📖</span>
                                <span className={styles.statValue}>{selectedCard.review_count || 0}</span>
                                <span className={styles.statDesc}>次修炼</span>
                            </div>
                        </div>

                        {!isEditing && (
                            <div className={styles.infoRow}>
                                <span>📅 {new Date(selectedCard.created_at).toLocaleDateString()}</span>
                                <span className={styles.infoDot}>·</span>
                                <span>
                                    🕐 {selectedCard.last_reviewed ? new Date(selectedCard.last_reviewed).toLocaleDateString() : '从未修炼'}
                                </span>
                            </div>
                        )}

                        {isEditing ? (
                            <CardEditForm
                                card={selectedCard}
                                onSave={handleEditSave}
                                onCancel={handleCancelEdit}
                            />
                        ) : (
                            <>
                                <DimensionSection card={selectedCard} />
                                <VisualLinksSection visualLinks={selectedCard.visual_links} />
                                <DialogueHistorySection card={selectedCard} />
                            </>
                        )}

                        {!isEditing && selectedCard.pending_retake && (
                            <div className={styles.retakeSection}>
                                <RetakeButton card={selectedCard} />
                            </div>
                        )}
                    </div>

                    {!isEditing && (
                        <div className={styles.panelFooter}>
                            <Button variant="primary" onClick={handleReview} className={styles.reviewBtn}>
                                📖 修炼
                            </Button>
                            <Button variant="ghost" onClick={handleEdit} className={styles.editBtn}>
                                ✏️ 编辑
                            </Button>
                            <Button variant="ghost" onClick={handleDeleteRequest} className={styles.deleteBtn}>
                                🗑️ 删除
                            </Button>
                        </div>
                    )}

                    {deleteConfirmOpen && (
                        <div className={styles.confirmOverlay} onClick={() => setDeleteConfirmOpen(false)}>
                            <div className={styles.confirmDialog} onClick={(e) => e.stopPropagation()}>
                                <h3>确认删除</h3>
                                <p>确定要删除「{selectedCard.name}」卡牌吗？</p>
                                <div className={styles.confirmActions}>
                                    <Button variant="ghost" onClick={() => setDeleteConfirmOpen(false)} disabled={isDeleting}>
                                        取消
                                    </Button>
                                    <Button variant="accent" onClick={handleDeleteConfirm} loading={isDeleting}>
                                        确认删除
                                    </Button>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>,
        document.body
    )
}
