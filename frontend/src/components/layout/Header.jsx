import { Link } from 'react-router-dom'
import styles from './Header.module.css'

export default function Header() {
  return (
    <header className={styles.header} role="banner">
      <div className={styles.headerInner}>
        <Link to="/" className={styles.logo} aria-label="算法大陆首页">
          <span className={styles.logoIcon}>⚔️</span>
          <span className={styles.logoText}>算法大陆</span>
        </Link>
      </div>
    </header>
  )
}