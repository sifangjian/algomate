import { NavLink } from 'react-router-dom'
import { navItems } from './navConfig'
import styles from './BottomNav.module.css'

export default function BottomNav() {
    return (
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
        </nav>
    )
}
