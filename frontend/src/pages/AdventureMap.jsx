import { useEffect, useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useGameStore } from '../stores/gameStore'
import { useUserStore } from '../stores/userStore'
import { useUIStore } from '../stores/uiStore'
import { realmService } from '../services/realmService'
import { userService } from '../services/userService'
import { taskService } from '../services/learningService'
import { statsService } from '../services/statsService'
import GameCard from '../components/ui/Card/GameCard'
import PartialRealmPanel from '../components/realm/PartialRealmPanel'
import { showToast } from '../components/ui/Toast/index'
import styles from './AdventureMap.module.css'

export default function AdventureMap() {
    const navigate = useNavigate()
    const { realms, setRealms, setLoading, setError } = useGameStore()
    const { setUser } = useUserStore()
    const { setTasks, setTasksLoading, addToast } = useUIStore()
    const [stats, setStats] = useState({ total_cards: 0, total_realms: 0, consecutive_days: 0 })
    const [selectedPartialRealm, setSelectedPartialRealm] = useState(null)

    const fetchInitialData = useCallback(async () => {
        setLoading(true)
        setTasksLoading(true)
        try {
            const [realmsData, userData, tasksData, statsData] = await Promise.allSettled([
                realmService.getAll(),
                userService.getUser().catch(() => null),
                taskService.getTodayTasks(),
                statsService.getOverview(),
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

            if (userData.status === 'fulfilled' && userData.value) {
                setUser(userData.value)
            }

            if (tasksData.status === 'fulfilled' && tasksData.value?.tasks) {
                setTasks(tasksData.value.tasks)
            } else {
                setTasks([])
                if (tasksData.status === 'rejected') {
                    console.error('Tasks API Error:', tasksData.reason)
                    showToast('获取今日任务失败', 'error')
                }
            }

            if (statsData.status === 'fulfilled' && statsData.value) {
                setStats(statsData.value)
            } else {
                if (statsData.status === 'rejected') {
                    console.error('Stats API Error:', statsData.reason)
                    showToast('获取统计数据失败', 'error')
                }
            }
        } catch (err) {
            setError(err.message)
            showToast('加载失败: ' + err.message, 'error')
            setTasks([])
        } finally {
            setLoading(false)
            setTasksLoading(false)
        }
    }, [setRealms, setUser, setTasks, setTasksLoading, setLoading, setError])

    useEffect(() => {
        fetchInitialData()
    }, [fetchInitialData])

    const handleRealmClick = useCallback(
        (realm) => {
            if (realm.status === 'locked') {
                const unlockDesc = realm.unlockCondition?.description || '暂未解锁'
                showToast(`🔒 ${realm.name} - ${unlockDesc}`, 'warning')
                return
            }
            if (realm.status === 'partial') {
                setSelectedPartialRealm(realm)
                return
            }
            const npcId = Array.isArray(realm.npcInfo) ? realm.npcInfo[0]?.id : realm.npcInfo?.id
            if (!npcId) {
                showToast('NPC 尚未解锁', 'warning')
                return
            }
            navigate(`/npc/${npcId}`)
        },
        [navigate]
    )

    const handlePartialNpcClick = useCallback(
        (npcId) => {
            setSelectedPartialRealm(null)
            navigate(`/npc/${npcId}`)
        },
        [navigate]
    )

    const handlePartialClose = useCallback(() => {
        setSelectedPartialRealm(null)
    }, [])

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
                                        <span>修为</span>
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

                            {Array.isArray(realm.npcInfo) && realm.npcInfo.length > 0 && (
                                realm.npcInfo.map((npc) => (
                                    <div key={npc.id} className={styles.npcTag}>
                                        <span>{npc.avatar}</span>
                                        <span>导师: {npc.name}</span>
                                    </div>
                                ))
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
                            <span className={styles.statValue}>{stats.total_cards}</span>
                            <span className={styles.statLabel}>卡牌总数</span>
                        </div>
                    </GameCard>
                    <GameCard className={styles.statCard}>
                        <span className={styles.statIcon}>🎯</span>
                        <div className={styles.statInfo}>
                            <span className={styles.statValue}>{stats.total_realms}</span>
                            <span className={styles.statLabel}>秘境总数</span>
                        </div>
                    </GameCard>
                    <GameCard className={styles.statCard}>
                        <span className={styles.statIcon}>🔥</span>
                        <div className={styles.statInfo}>
                            <span className={styles.statValue}>{stats.consecutive_days}</span>
                            <span className={styles.statLabel}>连续修习天数</span>
                        </div>
                    </GameCard>
                </div>
            </section>

            <PartialRealmPanel
                realm={selectedPartialRealm}
                open={!!selectedPartialRealm}
                onClose={handlePartialClose}
                onNpcClick={handlePartialNpcClick}
            />
        </div>
    )
}
