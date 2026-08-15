import { Icon } from '../ui/Icons'
import styles from './StatusBar.module.css'

export default function StatusBar() {
    return (
        <div className={styles.statusBar}>
            <div className={styles.left}>
                <span className={styles.dot}></span>
                <span className={styles.label}>AlgoMate</span>
            </div>
            <div className={styles.center}>
                <span className={styles.item}>v0.1.0</span>
                <span className={styles.separator}>|</span>
                <span className={`${styles.item} ${styles.statusOk}`}>
                    <Icon name="database" size={12} /> API
                </span>
                <span className={styles.separator}>|</span>
                <span className={`${styles.item} ${styles.statusOk}`}>
                    <Icon name="check" size={12} /> DB
                </span>
            </div>
            <div className={styles.right}>
                <span className={styles.item}>done: 1</span>
                <span className={styles.separator}>|</span>
                <span className={styles.item}>cards: 47</span>
                <span className={styles.separator}>|</span>
                <span className={styles.item}>reviews: 156</span>
                <span className={styles.separator}>|</span>
                <span className={styles.item}>updated: just now</span>
            </div>
        </div>
    )
}
