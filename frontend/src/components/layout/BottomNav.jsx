import { NavLink } from 'react-router-dom'
import { useUIStore } from '../../stores/uiStore'
import TaskDrawer from '../ui/TaskDrawer/TaskDrawer'
import styles from './BottomNav.module.css'

const navItems = [
    {
        path: '/',
        icon: '🗺️',
        label: '冒险地图',
        exact: true,
    },
    {
        path: '/knowledge-spring',
        icon: '💬',
        label: '知识之泉',
    },
    {
        path: '/workshop',
        icon: '🎴',
        label: '卡牌工坊',
    },
]

export default function BottomNav() {
    const { setTaskDrawerOpen, getTaskSummary } = useUIStore()
    const taskSummary = getTaskSummary()

    return (
        <>
            <nav className={styles.bottomNav} role="navigation" aria-label="主导航">
                {navItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        end={item.exact}
                        className={({ isActive }) =>
                            `${styles.navItem} ${isActive ? styles.active : ''}`
                        }
                    >
                        <span className={styles.navIcon}>{item.icon}</span>
                        <span className={styles.navLabel}>{item.label}</span>
                    </NavLink>
                ))}

                <button
                    className={`${styles.navItem} ${styles.taskBtn}`}
                    onClick={() => setTaskDrawerOpen(true)}
                    aria-label={`今日任务，${(taskSummary.totalToday || 0) - (taskSummary.completedToday || 0)}项未完成`}
                >
                    <span className={styles.navIcon}>📋</span>
                    <span className={styles.navLabel}>今日任务</span>
                    {taskSummary.hasIncomplete && (
                        <span className={styles.badge} aria-hidden="true">
                            {(taskSummary.totalToday || 0) - (taskSummary.completedToday || 0)}
                        </span>
                    )}
                </button>
            </nav>

            <TaskDrawer />
        </>
    )
}
