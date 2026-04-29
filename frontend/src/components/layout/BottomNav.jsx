import { NavLink, useLocation } from 'react-router-dom'
import { useUIStore } from '../../stores/uiStore'
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
  const location = useLocation()
  const { taskDrawerOpen, setTaskDrawerOpen, taskSummary } = useUIStore()

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
            aria-current={({ isActive }) => (isActive ? 'page' : undefined)}
          >
            <span className={styles.navIcon}>{item.icon}</span>
            <span className={styles.navLabel}>{item.label}</span>
          </NavLink>
 ))}

        <button
          className={`${styles.navItem} ${styles.taskBtn}`}
          onClick={() => setTaskDrawerOpen(true)}
          aria-label={`今日任务，${taskSummary.totalToday - taskSummary.completedToday}项未完成`}
        >
          <span className={styles.navIcon}>📋</span>
          <span className={styles.navLabel}>今日任务</span>
          {taskSummary.hasIncomplete && (
            <span className={styles.badge} aria-hidden="true">
              {taskSummary.totalToday - taskSummary.completedToday}
            </span>
          )}
        </button>
      </nav>

      {taskDrawerOpen && (
        <div
          className={styles.drawerOverlay}
          onClick={() => setTaskDrawerOpen(false)}
          role="presentation"
          aria-hidden="true"
        >
          <aside
            className={styles.drawer}
            role="dialog"
            aria-label="今日任务"
            onClick={(e) => e.stopPropagation()}
          >
            <div className={styles.drawerHeader}>
              <h2>📋 今日任务</h2>
              <button
                className={styles.closeBtn}
                onClick={() => setTaskDrawerOpen(false)}
                aria-label="关闭"
              >
                ✕
              </button>
            </div>
            <div className={styles.drawerBody}>
              <p className={styles.taskProgress}>
                已完成 {taskSummary.completedToday}/{taskSummary.totalToday}
              </p>
            </div>
          </aside>
        </div>
      )}
    </>
  )
}
