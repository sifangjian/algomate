import { Icon } from '../ui/Icons'
import styles from './BrandHeader.module.css'

export default function BrandHeader({ collapsed, onToggle }) {
    return (
        <header className={styles.brandHeader} data-collapsed={collapsed}>
            {collapsed ? (
                <div className={styles.iconOnly}>
                    <Icon name="diamond" size={18} color="var(--accent)" />
                </div>
            ) : (
                <div className={styles.brandContent}>
                    <div className={styles.brandRow}>
                        <Icon name="diamond" size={14} color="var(--accent)" />
                        <span className={styles.brandName}>AlgoMate</span>
                    </div>
                    <span className={styles.brandSubtitle}>算法修习助手 · v0.1.0</span>
                </div>
            )}
            <button className={styles.toggleBtn} onClick={onToggle} title={collapsed ? '展开侧边栏' : '收起侧边栏'}>
                <Icon name={collapsed ? 'chevronRight' : 'chevronLeft'} size={14} color="var(--text-muted)" />
            </button>
        </header>
    )
}
