import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Icon } from '../ui/Icons'
import styles from './TopTabs.module.css'

const tabs = [
    { id: 'workbench', label: '工作台', icon: 'grid', path: '/hall' },
    { id: 'review', label: '修炼', icon: 'menu', path: '/review' },
]

export default function TopTabs() {
    const navigate = useNavigate()
    const location = useLocation()
    const [searchQuery, setSearchQuery] = useState('')

    const isActive = (path) => {
        if (path === '/hall' || path === '/') {
            return location.pathname === '/' || location.pathname === '/hall' || location.pathname === ''
        }
        return location.pathname.startsWith(path)
    }

    return (
        <div className={styles.topTabs}>
            <div className={styles.tabsLeft}>
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        className={`${styles.tab} ${isActive(tab.path) ? styles.active : ''}`}
                        onClick={() => navigate(tab.path)}
                    >
                        <span className={styles.tabIcon}>
                            <Icon name={tab.icon} size={16} />
                        </span>
                        <span className={styles.tabLabel}>{tab.label}</span>
                    </button>
                ))}
            </div>
            <div className={styles.spacer} />
            <div className={styles.tabsRight}>
                <div className={styles.searchBox}>
                    <span className={styles.searchIcon}>
                        <Icon name="search" size={14} color="var(--text-muted)" />
                    </span>
                    <input
                        type="text"
                        className={styles.searchInput}
                        placeholder="搜索..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>
                <button className={styles.settingsBtn} title="设置">
                    <Icon name="gear" size={14} />
                </button>
            </div>
        </div>
    )
}
