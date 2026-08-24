import styles from './StatusMonitor.module.css'

function formatValue(value) {
    if (value === null || value === undefined) return '—'
    return value
}

function StatusCard({ label, value, status }) {
    return (
        <div className={`${styles.statusCard} ${styles[status]}`}>
            <div className={styles.statusValue}>{formatValue(value)}</div>
            <div className={styles.statusLabel}>{label}</div>
            <div className={`${styles.statusDot} ${styles[status]}`}></div>
        </div>
    )
}

export default function StatusMonitor({ loading, stats }) {
    if (loading) {
        return (
            <div className={styles.monitor}>
                <div className={styles.grid}>
                    {Array.from({ length: 9 }).map((_, i) => (
                        <div key={i} className={styles.statusCard}>
                            <div className={`${styles.statusValue} ${styles.loadingPulse}`}>&nbsp;</div>
                            <div className={`${styles.statusLabel} ${styles.loadingPulse}`}>&nbsp;</div>
                        </div>
                    ))}
                </div>
            </div>
        )
    }

    if (!stats) {
        return (
            <div className={styles.monitor}>
                <div className={styles.grid}>
                    <StatusCard label="总卡片" value="—" status="normal" />
                    <StatusCard label="待复习" value="—" status="warning" />
                    <StatusCard label="濒危技巧" value="—" status="critical" />
                    <StatusCard label="连续学习" value="—" status="normal" />
                    <StatusCard label="本周学习" value="—" status="normal" />
                    <StatusCard label="准确率" value="—" status="normal" />
                    <StatusCard label="累计复习" value="—" status="normal" />
                    <StatusCard label="今日新增" value="—" status="normal" />
                    <StatusCard label="下一复习" value="—" status="warning" />
                </div>
            </div>
        )
    }

    return (
        <div className={styles.monitor}>
            <div className={styles.grid}>
                <StatusCard label="总卡片" value={stats.totalCards} status="normal" />
                <StatusCard label="待复习" value={stats.dueToday} status="warning" />
                <StatusCard label="濒危技巧" value={stats.endangered} status="critical" />
                <StatusCard label="连续学习" value={`${stats.streakDays}天`} status="normal" />
                <StatusCard label="本周学习" value={stats.weeklyProgress} status="normal" />
                <StatusCard label="准确率" value={`${stats.accuracy}%`} status="normal" />
                <StatusCard label="累计复习" value={stats.totalReviews} status="normal" />
                <StatusCard label="今日新增" value={stats.newToday} status="normal" />
                <StatusCard label="下一复习" value={`${stats.nextReviewDays}天`} status="warning" />
            </div>
        </div>
    )
}