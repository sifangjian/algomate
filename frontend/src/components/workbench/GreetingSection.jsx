import styles from './GreetingSection.module.css'

function getGreeting() {
    const hour = new Date().getHours()
    if (hour < 6) return '凌晨好，注意休息'
    if (hour < 12) return '早上好，开始今天的工作'
    if (hour < 14) return '中午好，午休片刻'
    if (hour < 18) return '下午好，继续加油'
    return '晚上好，辛苦了'
}

function formatDate(date) {
    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
    const y = date.getFullYear()
    const m = String(date.getMonth() + 1).padStart(2, '0')
    const d = String(date.getDate()).padStart(2, '0')
    return `${y}-${m}-${d} · ${weekdays[date.getDay()]} · ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

export default function GreetingSection({ stats }) {
    const now = new Date()
    const data = stats || {
        dueCount: 5,
        completedCount: 1,
    }

    return (
        <div className={styles.greeting}>
            <h1 className={styles.title}>{getGreeting()}</h1>
            <div className={styles.meta}>
                <span className={styles.metaItem}>PATH: /hall</span>
                <span className={styles.metaSep}>|</span>
                <span className={styles.metaItem}>{formatDate(now)}</span>
                <span className={styles.metaSep}>|</span>
                <span className={styles.metaItem}>
                    <span className={styles.statusWarning}>{data.dueCount}</span> 项待办
                </span>
                <span className={styles.metaSep}>|</span>
                <span className={styles.metaItem}>
                    <span className={styles.statusNormal}>{data.completedCount}</span> 项完成
                </span>
            </div>
        </div>
    )
}
