import { NavLink } from 'react-router-dom'
import { useUIStore } from '../../stores/uiStore'
import { navItems, taskNavItem } from './navConfig'
import styles from './SideNav.module.css'

export default function SideNav() {
    const { setTaskDrawerOpen, getTaskSummary } = useUIStore()
    const taskSummary = getTaskSummary()

    return (
        <aside className={styles.sideNav} role="navigation" aria-label="主导航">
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
                        <span className={styles.navIcon}>{item.icon}</span>
                        <span className={styles.navLabel}>{item.label}</span>
                    </NavLink>
                ))}

                <button
                    className={`${styles.navItem} ${styles.taskBtn}`}
                    onClick={() => setTaskDrawerOpen(true)}
                    aria-label={`今日任务，${(taskSummary.totalToday || 0) - (taskSummary.completedToday || 0)}项未完成`}
                >
                    <span className={styles.navIcon}>{taskNavItem.icon}</span>
                    <span className={styles.navLabel}>{taskNavItem.label}</span>
                    {taskSummary.hasIncomplete && (
                        <span className={styles.badge} aria-hidden="true">
                            {(taskSummary.totalToday || 0) - (taskSummary.completedToday || 0)}
                        </span>
                    )}
                </button>
            </nav>
        </aside>
    )
}
