import { useState, useEffect, useCallback, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { taskService } from '../services/learningService'
import { cardService } from '../services/cardService'
import { learningService } from '../services/learningService'
import LoadingScreen from '../components/ui/Loading/LoadingScreen'
import Button from '../components/ui/Button/Button'
import { showToast } from '../components/ui/Toast/index'
import styles from './DailyReview.module.css'

const PRIORITY_ORDER = { critical: 0, high: 1, medium: 2, low: 3 }

const TASK_TYPE_CONFIG = {
    critical_review: { label: '濒危', className: styles.reasonCritical },
    forgetting_curve_review: { label: '遗忘曲线', className: styles.reasonForgetting },
    boss_challenge: { label: 'Boss挑战', className: styles.reasonBoss },
}

function getDurabilityClass(durability, maxDurability) {
    const pct = (durability / maxDurability) * 100
    if (pct < 30) return styles.durabilityFillCritical
    if (pct < 60) return styles.durabilityFillWarning
    return styles.durabilityFillNormal
}

function getAlgorithmIcon(category) {
    const map = {
        Search: '🔍',
        Sorting: '📊',
        'Dynamic Programming': '🎯',
        Graph: '🕸️',
        Tree: '🌲',
        Recursion: '🔄',
        Array: '📋',
        String: '📝',
        Greedy: '💰',
        Math: '🔢',
    }
    return map[category] || '📜'
}

export default function DailyReview() {
    const navigate = useNavigate()
    const [tasks, setTasks] = useState([])
    const [loading, setLoading] = useState(true)
    const [completedTaskIds, setCompletedTaskIds] = useState(new Set())
    const [reviewMode, setReviewMode] = useState(null)
    const [selectedTask, setSelectedTask] = useState(null)
    const [quizData, setQuizData] = useState(null)
    const [quizAnswers, setQuizAnswers] = useState({})
    const [quizSubmitted, setQuizSubmitted] = useState(false)
    const [reviewContent, setReviewContent] = useState(null)
    const [reviewLoading, setReviewLoading] = useState(false)
    const [reviewStats, setReviewStats] = useState(null)

    const fetchTasks = useCallback(async () => {
        setLoading(true)
        try {
            const data = await taskService.getTodayTasks()
            setTasks(data?.tasks || [])
        } catch {
            showToast('获取今日修炼任务失败', 'error')
        } finally {
            setLoading(false)
        }
    }, [])

    useEffect(() => {
        fetchTasks()
        cardService.getReviewStats().then(data => setReviewStats(data)).catch(() => {})
    }, [fetchTasks])

    const sortedTasks = useMemo(() => {
        return [...tasks].sort((a, b) => {
            const pa = PRIORITY_ORDER[a.priority] ?? 3
            const pb = PRIORITY_ORDER[b.priority] ?? 3
            return pa - pb
        })
    }, [tasks])

    const completedCount = completedTaskIds.size
    const totalCount = tasks.length

    const handleReview = useCallback(async (task) => {
        setReviewLoading(true)
        setReviewMode('review')
        setSelectedTask(task)
        try {
            const card = await cardService.getById(task.card_id)
            setReviewContent(card)
        } catch {
            showToast('加载知识回顾失败', 'error')
            setReviewMode(null)
            setSelectedTask(null)
        } finally {
            setReviewLoading(false)
        }
    }, [])

    const handleQuiz = useCallback(async (task) => {
        setReviewLoading(true)
        setReviewMode('quiz')
        setSelectedTask(task)
        setQuizAnswers({})
        setQuizSubmitted(false)
        try {
            const data = await learningService.generateQuiz(task.card_name || task.algorithm_type || '')
            setQuizData(data)
        } catch {
            showToast('加载快速问答失败', 'error')
            setReviewMode(null)
            setSelectedTask(null)
        } finally {
            setReviewLoading(false)
        }
    }, [])

    const handleBoss = useCallback((task) => {
        navigate(`/boss/battle?cardId=${task.card_id}`)
    }, [navigate])

    const handleQuizAnswer = useCallback((questionIndex, answer) => {
        setQuizAnswers(prev => ({ ...prev, [questionIndex]: answer }))
    }, [])

    const handleQuizSubmit = useCallback(async () => {
        setQuizSubmitted(true)
        if (selectedTask) {
            try {
                await cardService.completeReview(selectedTask.card_id, 'success')
                setCompletedTaskIds(prev => new Set([...prev, selectedTask.card_id]))
                showToast('问答完成！', 'success')
            } catch {
                showToast('完成修炼失败', 'error')
            }
        }
    }, [selectedTask])

    const handleCompleteReview = useCallback(async () => {
        if (!selectedTask) return
        try {
            await cardService.completeReview(selectedTask.card_id, 'success')
            setCompletedTaskIds(prev => new Set([...prev, selectedTask.card_id]))
            showToast('知识回顾完成！', 'success')
            setReviewMode(null)
            setSelectedTask(null)
            setReviewContent(null)
        } catch {
            showToast('完成回顾失败', 'error')
        }
    }, [selectedTask])

    const handleBack = useCallback(() => {
        setReviewMode(null)
        setSelectedTask(null)
        setReviewContent(null)
        setQuizData(null)
        setQuizAnswers({})
        setQuizSubmitted(false)
    }, [])

    if (loading) {
        return <LoadingScreen />
    }

    if (reviewMode && selectedTask) {
        return (
            <div className={`${styles.container} page-container`}>
                <button className={styles.backBtn} onClick={handleBack}>
                    ← 返回任务列表
                </button>

                {reviewLoading ? (
                    <div className={styles.panelLoading}>
                        <LoadingScreen />
                    </div>
                ) : reviewMode === 'review' ? (
                    <div className={styles.reviewPanel}>
                        <h2 className={styles.panelTitle}>📖 知识回顾 - {selectedTask.card_name}</h2>
                        {reviewContent ? (
                            <div className={styles.reviewContent}>
                                {reviewContent.knowledge_content && (
                                    <div className={styles.reviewSection}>
                                        <h3 className={styles.reviewSectionTitle}>知识内容</h3>
                                        <p className={styles.reviewSectionText}>{reviewContent.knowledge_content}</p>
                                    </div>
                                )}
                                {reviewContent.key_points?.length > 0 && (
                                    <div className={styles.reviewSection}>
                                        <h3 className={styles.reviewSectionTitle}>关键要点</h3>
                                        <ul className={styles.reviewKeyPoints}>
                                            {reviewContent.key_points.map((kp, i) => (
                                                <li key={i} className={styles.reviewKeyPoint}>{kp}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                                {reviewContent.summary && (
                                    <div className={styles.reviewSection}>
                                        <h3 className={styles.reviewSectionTitle}>心得总结</h3>
                                        <p className={styles.reviewSectionText}>{reviewContent.summary}</p>
                                    </div>
                                )}
                                <div className={styles.panelActions}>
                                    <Button variant="accent" onClick={handleCompleteReview}>
                                        ✅ 完成回顾
                                    </Button>
                                </div>
                            </div>
                        ) : (
                            <div className={styles.emptyPanel}>
                                <p>暂无知识内容</p>
                            </div>
                        )}
                    </div>
                ) : reviewMode === 'quiz' ? (
                    <div className={styles.quizPanel}>
                        <h2 className={styles.panelTitle}>✏️ 快速问答 - {selectedTask.card_name}</h2>
                        {quizData?.questions?.length > 0 ? (
                            <div className={styles.quizContent}>
                                {quizData.questions.map((q, qi) => (
                                    <div key={qi} className={styles.quizQuestion}>
                                        <p className={styles.quizQuestionText}>
                                            <span className={styles.quizQuestionNum}>{qi + 1}.</span> {q.question || q.content}
                                        </p>
                                        <div className={styles.quizOptions}>
                                            {(q.options || []).map((opt, oi) => {
                                                const label = String.fromCharCode(65 + oi)
                                                const isSelected = quizAnswers[qi] === label
                                                const isCorrect = quizSubmitted && q.correct_answer === label
                                                const isWrong = quizSubmitted && isSelected && q.correct_answer !== label
                                                return (
                                                    <button
                                                        key={oi}
                                                        className={`${styles.quizOption} ${isSelected ? styles.quizOptionSelected : ''} ${isCorrect ? styles.quizOptionCorrect : ''} ${isWrong ? styles.quizOptionWrong : ''}`}
                                                        onClick={() => !quizSubmitted && handleQuizAnswer(qi, label)}
                                                        disabled={quizSubmitted}
                                                    >
                                                        <span className={styles.quizOptionLabel}>{label}</span>
                                                        <span className={styles.quizOptionText}>{opt}</span>
                                                    </button>
                                                )
                                            })}
                                        </div>
                                        {quizSubmitted && q.explanation && (
                                            <div className={styles.quizExplanation}>{q.explanation}</div>
                                        )}
                                    </div>
                                ))}
                                <div className={styles.panelActions}>
                                    {!quizSubmitted ? (
                                        <Button
                                            variant="accent"
                                            onClick={handleQuizSubmit}
                                            disabled={Object.keys(quizAnswers).length === 0}
                                        >
                                            📝 提交答案
                                        </Button>
                                    ) : (
                                        <Button variant="ghost" onClick={handleBack}>
                                            返回任务列表
                                        </Button>
                                    )}
                                </div>
                            </div>
                        ) : (
                            <div className={styles.emptyPanel}>
                                <p>暂无问答题</p>
                                <Button variant="ghost" onClick={handleBack}>返回</Button>
                            </div>
                        )}
                    </div>
                ) : null}
            </div>
        )
    }

    return (
        <div className={`${styles.container} page-container`}>
            <div className={styles.header}>
                <h1 className={styles.pageTitle}>📋 每日修炼</h1>
                <p className={styles.pageSubtitle}>巩固算法知识，保持卡牌耐久</p>
            </div>

            {totalCount > 0 && (
                <div className={styles.statsSection}>
                    <div className={styles.statItem}>
                        <span className={styles.statValue}>{completedCount}/{totalCount}</span>
                        <span className={styles.statLabel}>已完成</span>
                    </div>
                    <div className={styles.statItem}>
                        <span className={styles.statValue}>{totalCount - completedCount}</span>
                        <span className={styles.statLabel}>待修炼</span>
                    </div>
                </div>
            )}

            {reviewStats && (
                <div className={styles.reviewStatsSection}>
                    <h3 className={styles.reviewStatsTitle}>修炼统计</h3>
                    <div className={styles.reviewStatsGrid}>
                        <div className={styles.reviewStatCard}>
                            <span className={styles.reviewStatValue}>{reviewStats.total_review_count ?? 0}</span>
                            <span className={styles.reviewStatLabel}>累计修炼</span>
                        </div>
                        <div className={styles.reviewStatCard}>
                            <span className={styles.reviewStatValue}>{reviewStats.weekly_review_days ?? 0}</span>
                            <span className={styles.reviewStatLabel}>本周修炼天数</span>
                        </div>
                        <div className={styles.reviewStatCard}>
                            <span className={styles.reviewStatValue}>{reviewStats.completed_today ?? 0}</span>
                            <span className={styles.reviewStatLabel}>今日已完成</span>
                        </div>
                    </div>
                    {reviewStats.review_level_distribution && Object.keys(reviewStats.review_level_distribution).length > 0 && (
                        <div className={styles.levelDistribution}>
                            <span className={styles.levelDistTitle}>修炼等级分布</span>
                            <div className={styles.levelDistBars}>
                                {Object.entries(reviewStats.review_level_distribution).map(([level, count]) => (
                                    <div key={level} className={styles.levelDistItem}>
                                        <span className={styles.levelDistLabel}>Lv.{level}</span>
                                        <div className={styles.levelDistBar}>
                                            <div className={styles.levelDistFill} style={{ width: `${Math.min(100, count * 20)}%` }} />
                                        </div>
                                        <span className={styles.levelDistCount}>{count}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {tasks.length === 0 ? (
                <div className={styles.emptyState}>
                    <span className={styles.emptyIcon}>📋</span>
                    <p className={styles.emptyText}>修习更多算法技巧后，这里会出现每日修炼任务</p>
                </div>
            ) : (
                <div className={styles.taskList}>
                    {sortedTasks.map((task) => {
                        const isCompleted = completedTaskIds.has(task.card_id)
                        const typeConfig = TASK_TYPE_CONFIG[task.task_type] || TASK_TYPE_CONFIG.boss_challenge
                        const durability = task.card_durability ?? 0
                        const maxDurability = 100
                        const durabilityPct = Math.min(100, Math.max(0, durability))

                        return (
                            <div
                                key={task.task_id}
                                className={`${styles.taskCard} ${isCompleted ? styles.completed : ''}`}
                            >
                                <div className={styles.taskHeader}>
                                    <div className={styles.taskNameArea}>
                                        <span className={styles.taskIcon}>
                                            {getAlgorithmIcon(task.algorithm_type)}
                                        </span>
                                        <span className={styles.taskName}>{task.card_name}</span>
                                    </div>
                                    <span className={`${styles.reason} ${typeConfig.className}`}>
                                        {typeConfig.label}
                                    </span>
                                </div>

                                <div className={styles.durabilityBar}>
                                    <div
                                        className={`${styles.durabilityFill} ${getDurabilityClass(durability, maxDurability)}`}
                                        style={{ width: `${durabilityPct}%` }}
                                    />
                                </div>
                                <span className={styles.durabilityText}>
                                    耐久 {durability}/{maxDurability}
                                </span>

                                {!isCompleted ? (
                                    <div className={styles.actionButtons}>
                                        <button
                                            className={styles.actionBtn}
                                            onClick={() => handleReview(task)}
                                        >
                                            📖 知识回顾
                                        </button>
                                        <button
                                            className={styles.actionBtn}
                                            onClick={() => handleQuiz(task)}
                                        >
                                            ✏️ 快速问答
                                        </button>
                                        <button
                                            className={styles.actionBtn}
                                            onClick={() => handleBoss(task)}
                                        >
                                            🐉 Boss挑战
                                        </button>
                                    </div>
                                ) : (
                                    <div className={styles.completedBadge}>✅ 今日已修炼</div>
                                )}
                            </div>
                        )
                    })}
                </div>
            )}
        </div>
    )
}
