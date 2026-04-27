import { useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useGameStore } from '../stores/gameStore'
import { useUserStore } from '../stores/userStore'
import { useUIStore } from '../stores/uiStore'
import { realmService } from '../services/realmService'
import { userService } from '../services/userService'
import GameCard from '../components/ui/Card/GameCard'
import { showToast } from '../components/ui/Toast/index'
import styles from './AdventureMap.module.css'

export default function AdventureMap() {
    const navigate = useNavigate()
    const { realms, setRealms, setLoading, setError } = useGameStore()
    const { setUser } = useUserStore()
    const { setTaskSummary, addToast } = useUIStore()

    const fetchInitialData = useCallback(async () => {
        setLoading(true)
        try {
            const [realmsData] = await Promise.allSettled([
                realmService.getAll(),
                userService.getUser().catch(() => null),
            ])

            if (realmsData.status === 'fulfilled' && Array.isArray(realmsData.value)) {
                const sorted = [...realmsData.value].sort(
                    (a, b) => (a.order || 0) - (b.order || 0)
                )
                setRealms(sorted)
            } else {
                console.error('API Error:', realmsData)
                setError('获取秘境数据失败')
                showToast('获取秘境数据失败', 'error')
            }

            setUser({
                nickname: '冒险者',
                level: 5,
                title: '探索者',
                experience: 2500,
                nextLevelExp: 3000,
            })

            setTaskSummary({
                totalToday: 3,
                completedToday: 1,
                hasIncomplete: true,
            })
        } catch (err) {
            setError(err.message)
            showToast('加载失败: ' + err.message, 'error')
        } finally {
            setLoading(false)
        }
    }, [setRealms, setUser, setTaskSummary, setLoading, setError])

    useEffect(() => {
        fetchInitialData()
    }, [fetchInitialData])

    const handleRealmClick = useCallback(
        (realm) => {
            if (realm.status === 'locked') {
                showToast(`🔒 ${realm.unlockCondition?.description || '暂未解锁'}`, 'warning')
                return
            }
            if (realm.status === 'partial') {
                showToast('还需努力解锁此区域', 'info')
                return
            }
            if (!realm.npcInfo?.id) {
                showToast('NPC 尚未解锁', 'warning')
                return
            }
            navigate(`/npc/${realm.npcInfo.id}`)
        },
        [navigate]
    )

    const displayRealms = realms

    return (
        <div className={`${styles.container} page-container`}>
            <div className={styles.hero}>
                <div className={styles.heroContent}>
                    <h1 className={styles.heroTitle}>⚔️ 算法大陆</h1>
                    <p className={styles.heroDesc}>踏上冒险之旅，征服算法的每一个秘境</p>
                </div>
                <div className={styles.heroDecor} aria-hidden="true">
                    <span className={styles.star} style={{ '--delay': '0s' }}>✦</span>
                    <span className={styles.star} style={{ '--delay': '1s' }}>✦</span>
                    <span className={styles.star} style={{ '--delay': '2s' }}>✦</span>
                </div>
            </div>

            <section className={styles.realmSection} aria-label="秘境列表">
                <h2 className={styles.sectionTitle}>
                    <span>🗺️</span> 秘境地图
                </h2>

                <div className={styles.realmGrid}>
                    {displayRealms.map((realm, index) => (
                        <GameCard
                            key={realm.id}
                            className={`${styles.realmCard} ${realm.status}`}
                            glow={realm.status === 'unlocked'}
                            hoverable={realm.status !== 'locked'}
                            onClick={() => handleRealmClick(realm)}
                            style={{ animationDelay: `${index * 100}ms` }}
                        >
                            <div className={styles.cardHeader}>
                                <span className={styles.realmIcon}>{realm.icon}</span>
                                <div className={styles.cardHeaderInfo}>
                                    <h3 className={styles.realmName}>{realm.name}</h3>
                                    <span className={styles.realmOrder}>#{realm.order}</span>
                                </div>
                                {realm.status === 'locked' && (
                                    <span className={styles.lockIcon} aria-label="已锁定">🔒</span>
                                )}
                            </div>

                            <p className={styles.realmDesc}>{realm.description}</p>

                            {realm.status !== 'locked' && (
                                <div className={styles.progressSection}>
                                    <div className={styles.progressLabel}>
                                        <span>探索进度</span>
                                        <span>{realm.progress}%</span>
                                    </div>
                                    <div className={styles.progressBar} role="progressbar" aria-valuenow={realm.progress} aria-valuemin={0} aria-valuemax={100}>
                                        <div
                                            className={styles.progressFill}
                                            style={{ width: `${realm.progress}%` }}
                                        />
                                    </div>
                                </div>
                            )}

                            {realm.npcInfo && (
                                <div className={styles.npcTag}>
                                    <span>{realm.npcInfo.avatar}</span>
                                    <span>导师: {realm.npcInfo.name}</span>
                                </div>
                            )}

                            {realm.bossInfo && (
                                <div className={styles.bossTag}>
                                    <span>🐉</span>
                                    <span>Boss: {realm.bossInfo.name}</span>
                                    <span className={styles.difficulty}>
                                        {'★'.repeat(Math.max(0, realm.bossInfo.difficulty || 0))}
                                    </span>
                                </div>
                            )}

                            {realm.unlockCondition && realm.status !== 'unlocked' && (
                                <div className={styles.unlockHint}>
                                    <span>📋</span>
                                    <span>{realm.unlockCondition.description}</span>
                                </div>
                            )}
                        </GameCard>
                    ))}
                </div>
            </section>

            <section className={styles.statsSection} aria-label="快速统计">
                <div className={styles.statCards}>
                    <GameCard className={styles.statCard}>
                        <span className={styles.statIcon}>📚</span>
                        <div className={styles.statInfo}>
                            <span className={styles.statValue}>12</span>
                            <span className={styles.statLabel}>卡牌总数</span>
                        </div>
                    </GameCard>
                    <GameCard className={styles.statCard}>
                        <span className={styles.statIcon}>🎯</span>
                        <div className={styles.statInfo}>
                            <span className={styles.statValue}>8</span>
                            <span className={styles.statLabel}>已完成Boss战</span>
                        </div>
                    </GameCard>
                    <GameCard className={styles.statCard}>
                        <span className={styles.statIcon}>🔥</span>
                        <div className={styles.statInfo}>
                            <span className={styles.statValue}>7</span>
                            <span className={styles.statLabel}>连续学习天数</span>
                        </div>
                    </GameCard>
                </div>
            </section>
        </div>
    )
}
