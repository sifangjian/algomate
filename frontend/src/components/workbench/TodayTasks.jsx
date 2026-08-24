import { Icon } from '../ui/Icons'
import styles from './TodayTasks.module.css'

const typeLabels = {
    problem: '题目',
    solution: '解法',
    technique: '技巧',
}

const typeIcons = {
    problem: 'book',
    solution: 'lightbulb',
    technique: 'star',
}

const typeColors = {
    problem: '#60a5fa',
    solution: '#4ade80',
    technique: '#fbbf24',
}

const statusBadges = {
    PENDING: { label: '待开始', className: 'pending' },
    IN_PROGRESS: { label: '进行中', className: 'inProgress' },
    DONE: { label: '已完成', className: 'done' },
}

export default function TodayTasks({ loading, tasks }) {
    const list = tasks || []

    if (loading) {
        return (
            <div className={styles.tasks}>
                {Array.from({ length: 3 }).map((_, i) => (
                    <div key={i} className={styles.taskRow}>
                        <span className={`${styles.taskIndex} ${styles.loadingPulse}`}>&nbsp;</span>
                        <span className={`${styles.taskName} ${styles.loadingPulse}`}>&nbsp;</span>
                        <span className={`${styles.taskType} ${styles.loadingPulse}`}>&nbsp;</span>
                    </div>
                ))}
            </div>
        )
    }

    if (list.length === 0) {
        return (
            <div className={styles.tasks}>
                <div className={styles.emptyState}>今日暂无任务</div>
            </div>
        )
    }

    return (
        <div className={styles.tasks}>
            {list.map((task, idx) => {
                const badge = statusBadges[task.status] || statusBadges.PENDING
                const typeColor = typeColors[task.type] || 'var(--text-secondary)'
                return (
                    <div key={task.id} className={styles.taskRow}>
                        <span className={styles.taskIndex}>{String(idx + 1).padStart(2, '0')}</span>
                        <span className={styles.taskTypeIcon} style={{ color: typeColor }}>
                            <Icon name={typeIcons[task.type] || 'code'} size={14} color={typeColor} />
                        </span>
                        <span className={styles.taskName}>{task.name}</span>
                        <span className={styles.taskType} style={{ color: typeColor }}>
                            {typeLabels[task.type] || task.type}
                        </span>
                        <span className={`${styles.taskStatus} ${styles[badge.className]}`}>
                            {badge.label}
                        </span>
                    </div>
                )
            })}
        </div>
    )
}