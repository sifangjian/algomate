import { useEffect, useState } from 'react'
import { NavLink } from 'react-router-dom'
import { navItems } from './navConfig'
import { Icon } from '../ui/Icons'
import { cardService } from '../../services/cardService'
import styles from './SideNav.module.css'

const typeColors = {
    problem: '#60a5fa',
    solution: '#4ade80',
    technique: '#fbbf24',
    review: '#818cf8',
    warning: '#e55555',
}

export default function SideNav({ onCreateCard, stats, collapsed }) {
    const [recentActivities, setRecentActivities] = useState([])

    useEffect(() => {
        let cancelled = false
        async function fetchRecentActivities() {
            try {
                const res = await cardService.getRecentActivities()
                if (!cancelled) {
                    setRecentActivities(res?.activities || [])
                }
            } catch (err) {
                console.error('Failed to fetch recent activities:', err)
                if (!cancelled) {
                    setRecentActivities([])
                }
            }
        }
        fetchRecentActivities()
        return () => { cancelled = true }
    }, [])
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

            <div className={styles.statsPanel} title="今日修炼概览">
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

        </aside>
    )
}
