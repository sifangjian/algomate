import Modal from '../ui/Modal/Modal'
import styles from './PartialRealmPanel.module.css'

export default function PartialRealmPanel({ realm, open, onClose, onNpcClick }) {
    if (!realm) return null

    const npcs = Array.isArray(realm.npcInfo) ? realm.npcInfo : []
    const unlockCondition = realm.unlockCondition

    return (
        <Modal
            open={open}
            onClose={onClose}
            title={`${realm.icon} ${realm.name}`}
            size="sm"
            ariaLabel="部分解锁秘境详情"
        >
            <div className={styles.content}>
                <p className={styles.desc}>{realm.description}</p>

                <div className={styles.progressSection}>
                    <div className={styles.progressLabel}>
                        <span>解锁进度</span>
                        <span>
                            {unlockCondition?.current ?? 0} / {unlockCondition?.required ?? '?'} 张卡牌
                        </span>
                    </div>
                    <div className={styles.progressBar}>
                        <div
                            className={styles.progressFill}
                            style={{
                                width: `${unlockCondition?.required ? Math.min(100, Math.round(((unlockCondition.current || 0) / unlockCondition.required) * 100)) : 0}%`,
                            }}
                        />
                    </div>
                </div>

                {npcs.length > 0 && (
                    <div className={styles.npcSection}>
                        <h3 className={styles.sectionTitle}>已解锁导师</h3>
                        <ul className={styles.npcList}>
                            {npcs.map((npc) => (
                                <li key={npc.id} className={styles.npcItem} onClick={() => onNpcClick(npc.id)}>
                                    <span className={styles.npcAvatar}>{npc.avatar}</span>
                                    <span className={styles.npcName}>{npc.name}</span>
                                    <span className={styles.npcArrow}>→</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                )}

                <div className={styles.lockedSection}>
                    <h3 className={styles.sectionTitle}>未解锁内容</h3>
                    <div className={styles.lockedHint}>
                        <span className={styles.lockedIcon}>🔒</span>
                        <span>{unlockCondition?.description || '完成前置秘境解锁更多内容'}</span>
                    </div>
                </div>
            </div>
        </Modal>
    )
}
