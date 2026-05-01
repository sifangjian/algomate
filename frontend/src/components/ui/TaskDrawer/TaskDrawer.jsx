import { useEffect, useCallback } from 'react'
import { createPortal } from 'react-dom'
import { useNavigate } from 'react-router-dom'
import { useUIStore } from '../../../stores/uiStore'
import styles from './TaskDrawer.module.css'

const PRIORITY_ORDER = { critical: 0, high: 1, medium: 2, low: 3 }

const TYPE_CONFIG = {
    critical_review: { tag: '⚠️ 濒危', style: styles.typeTagCritical },
    forgetting_curve_review: { tag: '📖 修炼', style: styles.typeTagReview },
    boss_challenge: { tag: '🐉 Boss', style: styles.typeTagBoss },
}

export default function TaskDrawer() {
    const navigate = useNavigate()
    const {
        taskDrawerOpen,
        setTaskDrawerOpen,
        tasks,
        tasksLoading,
        taskSummary,
    } = useUIStore()

    const handleClose = useCallback(() => {
        setTaskDrawerOpen(false)
    }, [setTaskDrawerOpen])

    useEffect(() => {
        if (taskDrawerOpen) {
            document.body.style.overflow = 'hidden'
            const handleEsc = (e) => {
                if (e.key === 'Escape') handleClose()
            }
            document.addEventListener('keydown', handleEsc)
            return () => {
                document.body.style.overflow = ''
                document.removeEventListener('keydown', handleEsc)
            }
        }
        return () => {
            document.body.style.overflow = ''
        }
    }, [taskDrawerOpen, handleClose])

    if (!taskDrawerOpen) return null

    const sortedTasks = [...tasks].sort(
        (a, b) => (PRIORITY_ORDER[a.priority] ?? 99) - (PRIORITY_ORDER[b.priority] ?? 99)
    )

    const total = taskSummary.totalToday ?? tasks.length
    const completed = taskSummary.completedToday ?? 0
    const progressPercent = total > 0 ? Math.round((completed / total) * 100) : 0

    const handleTaskClick = (task) => {
        handleClose()
        navigate(`/boss/battle?cardId=${task.card_id}`)
    }

    return createPortal(
        <div className={styles.overlay} onClick={handleClose} role="presentation" aria-hidden="true">
            <aside
                className={styles.drawer}
                role="dialog"
                aria-label="今日任务"
                onClick={(e) => e.stopPropagation()}
            >
                <div className={styles.header}>
                    <h2>📋 今日任务</h2>
                    <button className={styles.closeBtn} onClick={handleClose} aria-label="关闭">
                        ✕
                    </button>
                </div>

                <div className={styles.body}>
                    {tasksLoading ? (
                        <div className={styles.loadingState}>
                            <div className={styles.spinner} />
                            <span className={styles.loadingText}>加载任务中...</span>
                        </div>
                    ) : sortedTasks.length === 0 ? (
                        <div className={styles.emptyState}>
                            <span className={styles.emptyIcon}>🎉</span>
                            <span className={styles.emptyText}>今日暂无修炼任务，好好休息吧！</span>
                        </div>
                    ) : (
                        <>
                            <div className={styles.summary}>
                                <p className={styles.progressText}>
                                    已完成 {completed}/{total}
                                </p>
                                <div className={styles.progressBar} role="progressbar" aria-valuenow={progressPercent} aria-valuemin={0} aria-valuemax={100}>
                                    <div className={styles.progressFill} style={{ width: `${progressPercent}%` }} />
                                </div>
                            </div>

                            <div className={styles.taskList}>
                                {sortedTasks.map((task) => {
                                    const config = TYPE_CONFIG[task.task_type] ?? { tag: '📌 任务', style: '' }
                                    const isCritical = (task.card_durability ?? 100) < 30
                                    const durabilityPercent = Math.min(100, Math.max(0, task.card_durability ?? 0))

                                    return (
                                        <div
                                            key={task.task_id}
                                            className={styles.taskItem}
                                            onClick={() => handleTaskClick(task)}
                                            role="button"
                                            tabIndex={0}
                                            onKeyDown={(e) => {
                                                if (e.key === 'Enter' || e.key === ' ') {
                                                    e.preventDefault()
                                                    handleTaskClick(task)
                                                }
                                            }}
                                        >
                                            <div className={styles.taskHeader}>
                                                <span className={`${styles.typeTag} ${config.style}`}>
                                                    {config.tag}
                                                </span>
                                                <span className={styles.cardName}>{task.card_name}</span>
                                            </div>
                                            <div className={styles.durabilityBar}>
                                                <div
                                                    className={`${styles.durabilityFill} ${isCritical ? styles.durabilityFillCritical : styles.durabilityFillNormal}`}
                                                    style={{ width: `${durabilityPercent}%` }}
                                                />
                                            </div>
                                            <span className={styles.reason}>{task.reason}</span>
                                        </div>
                                    )
                                })}
                            </div>
                        </>
                    )}
                </div>
            </aside>
        </div>,
        document.body
    )
}
