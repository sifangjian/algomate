import styles from './StatusMonitor.module.css'

const defaultStats = {
    totalCards: 47,
    dueToday: 5,
    endangered: 2,
    streakDays: 23,
    weeklyProgress: '5/7',
    accuracy: 87,
    totalReviews: 156,
    newToday: 0,
    nextReviewDays: 3,
}

function StatusCard({ label, value, status }) {
    return (
        <div className={`${styles.statusCard} ${styles[status]}`}>
            <div className={styles.statusValue}>{value}</div>
            <div className={styles.statusLabel}>{label}</div>
            <div className={`${styles.statusDot} ${styles[status]}`}></div>
        </div>
    )
}

export default function StatusMonitor({ stats }) {
    const s = stats || defaultStats

    return (
        <div className={styles.monitor}>
            <div className={styles.grid}>
                <StatusCard label="总卡片" value={s.totalCards} status="normal" />
                <StatusCard label="待复习" value={s.dueToday} status="warning" />
                <StatusCard label="濒危技巧" value={s.endangered} status="critical" />
                <StatusCard label="连续学习" value={`${s.streakDays}天`} status="normal" />
                <StatusCard label="本周学习" value={s.weeklyProgress} status="normal" />
                <StatusCard label="准确率" value={`${s.accuracy}%`} status="normal" />
                <StatusCard label="累计复习" value={s.totalReviews} status="normal" />
                <StatusCard label="今日新增" value={s.newToday} status="normal" />
                <StatusCard label="下一复习" value={`${s.nextReviewDays}天`} status="warning" />
            </div>
        </div>
    )
}
