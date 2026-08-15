import { NavLink } from 'react-router-dom'
import { navItems } from './navConfig'
import { Icon } from '../ui/Icons'
import styles from './SideNav.module.css'

const recentActivities = [
    { time: '14:32', action: '新建技巧', target: '滑动窗口', type: 'technique' },
    { time: '13:05', action: '复习完成', target: 'DFS 遍历', type: 'review' },
    { time: '11:48', action: '新建解法', target: '快速幂', type: 'solution' },
    { time: '10:20', action: '濒危技巧', target: '回溯剪枝', type: 'warning' },
    { time: '09:15', action: '新建题目', target: 'LC.209', type: 'problem' },
]

const typeColors = {
    problem: '#60a5fa',
    solution: '#4ade80',
    technique: '#fbbf24',
    review: '#818cf8',
    warning: '#e55555',
}

export default function SideNav({ onCreateCard, stats, collapsed }) {
    const todayStats = stats || {
        due: 5,
        endangered: 2,
        completed: 1,
        learningDays: 23,
    }

    return (
        <aside className={styles.sideNav} data-collapsed={collapsed} role="navigation" aria-label="主导航">
            <button className={styles.createBtn} onClick={onCreateCard}>
                <Icon name="plus" size={14} color="var(--accent)" />
                <span>新建卡片</span>
            </button>

            <div className={styles.statsPanel}>
                <div className={styles.statsHeader}>
                    <span className={styles.statsTitle}>今日修炼</span>
                </div>
                <div className={styles.statsRow}>
                    <div className={styles.statItem}>
                        <span className={`${styles.statNum} ${styles.warning}`}>{todayStats.due}</span>
                        <span className={styles.statLabel}>待复习</span>
                    </div>
                    <div className={styles.statItem}>
                        <span className={`${styles.statNum} ${styles.critical}`}>{todayStats.endangered}</span>
                        <span className={styles.statLabel}>濒危</span>
                    </div>
                    <div className={styles.statItem}>
                        <span className={`${styles.statNum} ${styles.normal}`}>{todayStats.completed}</span>
                        <span className={styles.statLabel}>已完成</span>
                    </div>
                </div>
            </div>

            <nav className={styles.navSection}>
                {navItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        end={item.exact}
                        className={({ isActive }) =>
                            `${styles.navItem} ${isActive ? styles.active : ''}`
                        }
                    >
                        <span className={styles.navIcon}>
                            <Icon name={item.icon} size={16} color={item.color} />
                        </span>
                        <span className={styles.navLabel}>{item.label}</span>
                        <span className={styles.navSubtitle}>{item.subtitle}</span>
                    </NavLink>
                ))}
            </nav>

            <div className={styles.recentSection}>
                <div className={styles.recentHeader}>最近活动</div>
                <div className={styles.recentList}>
                    {recentActivities.map((act, idx) => (
                        <div key={idx} className={styles.recentItem}>
                            <span className={styles.recentTime}>{act.time}</span>
                            <span className={styles.recentAction} style={{ color: typeColors[act.type] || 'var(--text-secondary)' }}>
                                {act.action}
                            </span>
                            <span className={styles.recentTarget}>{act.target}</span>
                        </div>
                    ))}
                </div>
            </div>

            <div className={styles.bottomInfo}>
                <div className={styles.bottomRow}>
                    <span className={styles.bottomLabel}>会话</span>
                    <span className={styles.bottomValue}>session-001</span>
                </div>
                <div className={styles.bottomRow}>
                    <span className={styles.bottomLabel}>学习</span>
                    <span className={styles.bottomValue}>{todayStats.learningDays} 天</span>
                </div>
            </div>
        </aside>
    )
}
