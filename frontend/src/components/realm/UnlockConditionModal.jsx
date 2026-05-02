import Modal from '../ui/Modal/Modal'
import styles from './UnlockConditionModal.module.css'

export default function UnlockConditionModal({ realm, unlockData, open, onClose }) {
    if (!realm) return null

    const required = unlockData?.required_cards ?? 0
    const current = unlockData?.current_cards ?? 0
    const percentage = required > 0 ? Math.min(100, Math.round((current / required) * 100)) : 0

    return (
        <Modal
            open={open}
            onClose={onClose}
            title={`${realm.icon} ${realm.name}`}
            size="sm"
            ariaLabel="秘境解锁条件"
        >
            <div className={styles.content}>
                <p className={styles.desc}>{realm.description}</p>

                <div className={styles.lockedBanner}>
                    <span className={styles.lockedIcon}>🔒</span>
                    <span className={styles.lockedText}>此秘境尚未解锁</span>
                </div>

                <div className={styles.conditionSection}>
                    <h3 className={styles.sectionTitle}>解锁条件</h3>
                    <p className={styles.conditionDesc}>
                        需要 {required} 张精通度≥60 的卡牌
                    </p>
                </div>

                <div className={styles.progressSection}>
                    <div className={styles.progressLabel}>
                        <span>当前进度</span>
                        <span>{current} / {required} 张卡牌</span>
                    </div>
                    <div className={styles.progressBar} role="progressbar" aria-valuenow={percentage} aria-valuemin={0} aria-valuemax={100}>
                        <div
                            className={styles.progressFill}
                            style={{ width: `${percentage}%` }}
                        />
                    </div>
                    <span className={styles.progressPercent}>{percentage}%</span>
                </div>

                <div className={styles.hintSection}>
                    <span className={styles.hintIcon}>💡</span>
                    <span className={styles.hintText}>继续修习，提升卡牌精通度即可解锁</span>
                </div>
            </div>
        </Modal>
    )
}
