import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useUserStore } from '../../stores/userStore'
import { useUIStore } from '../../stores/uiStore'
import styles from './SideNav.module.css'

const navItems = [
  {
    path: '/',
    icon: '🗺️',
    label: '冒险地图',
    exact: true,
  },
  {
    path: '/npc/general',
    icon: '💬',
    label: '知识之泉',
  },
  {
    path: '/workshop',
    icon: '🎴',
    label: '卡牌工坊',
  },
]

export default function SideNav() {
  const { user } = useUserStore()
  const navigate = useNavigate()
  const { taskDrawerOpen, setTaskDrawerOpen, taskSummary } = useUIStore()

  const expPercentage = user.nextLevelExp > 0
    ? Math.round((user.experience / user.nextLevelExp) * 100)
    : 0

  return (
    <aside className={styles.sideNav} role="navigation" aria-label="主导航">
      <div className={styles.logoSection}>
        <Link to="/" className={styles.logo} aria-label="算法大陆首页">
          <span className={styles.logoIcon}>⚔️</span>
          <span className={styles.logoText}>算法大陆</span>
        </Link>
      </div>

      <div className={styles.userSection} role="region" aria-label="用户信息">
        <div className={styles.levelBadge} title={`Lv.${user.level} ${user.title}`}>
          <span className={styles.levelNum}>{user.level}</span>
          <span className={styles.levelLabel}>LV</span>
        </div>

        <div className={styles.userInfo}>
          <span className={styles.nickname}>{user.nickname}</span>
          <div className={styles.expBar} role="progressbar" aria-valuenow={expPercentage} aria-valuemin={0} aria-valuemax={100}>
            <div
              className={styles.expFill}
              style={{ width: `${expPercentage}%` }}
            />
          </div>
          <span className={styles.expText}>
            {user.experience}/{user.nextLevelExp} XP
          </span>
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

      <div className={styles.bottomSection}>
        <button
          className={styles.settingsBtn}
          onClick={() => navigate('/settings')}
          aria-label="设置"
          title="设置"
        >
          ⚙️
        </button>
      </div>

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
    </aside>
  )
}