import { Link, useNavigate } from 'react-router-dom'
import { useUserStore } from '../../stores/userStore'
import styles from './Header.module.css'

export default function Header() {
  const { user } = useUserStore()
  const navigate = useNavigate()

  const expPercentage = user.nextLevelExp > 0
    ? Math.round((user.experience / user.nextLevelExp) * 100)
    : 0

  return (
    <header className={styles.header} role="banner">
      <div className={styles.headerInner}>
        <Link to="/" className={styles.logo} aria-label="算法大陆首页">
          <span className={styles.logoIcon}>⚔️</span>
          <span className={styles.logoText}>算法大陆</span>
        </Link>

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

          <button
            className={styles.settingsBtn}
            onClick={() => navigate('/settings')}
            aria-label="设置"
            title="设置"
          >
            ⚙️
          </button>
        </div>
      </div>
    </header>
  )
}
