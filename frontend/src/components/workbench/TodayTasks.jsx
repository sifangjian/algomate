import { Icon } from '../ui/Icons'
import styles from './TodayTasks.module.css'

const defaultTasks = [
    { id: 1, name: 'LRU Cache 实现', type: 'problem', status: 'PENDING' },
    { id: 2, name: '快速幂算法模板', type: 'solution', status: 'IN_PROGRESS' },
    { id: 3, name: '滑动窗口最大值', type: 'technique', status: 'DONE' },
    { id: 4, name: '二叉树 Morris 遍历', type: 'technique', status: 'PENDING' },
]

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

export default function TodayTasks({ tasks }) {
    const list = tasks || defaultTasks

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
