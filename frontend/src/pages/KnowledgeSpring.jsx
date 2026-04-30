import { useEffect, useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { npcService, LOCATION_TO_REALM_ID } from '../services/npcService'
import GameCard from '../components/ui/Card/GameCard'
import { showToast } from '../components/ui/Toast/index'
import styles from './KnowledgeSpring.module.css'

export default function KnowledgeSpring() {
    const navigate = useNavigate()
    const [npcs, setNpcs] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    const fetchNpcs = useCallback(async () => {
        setLoading(true)
        setError(null)
        try {
            let data = await npcService.getUnlockedNpcs()
            if (!Array.isArray(data) || data.length === 0) {
                data = await npcService.getAllNpcs()
            }
            if (Array.isArray(data)) {
                setNpcs(data)
            } else {
                setNpcs([])
            }
        } catch (err) {
            setError(err.message || '获取导师数据失败')
            showToast('获取导师数据失败', 'error')
        } finally {
            setLoading(false)
        }
    }, [])

    useEffect(() => {
        fetchNpcs()
    }, [fetchNpcs])

    const handleNpcClick = useCallback(
        (npc) => {
            const realmId = LOCATION_TO_REALM_ID[npc.location]
            if (!realmId) {
                showToast('无法定位该导师所在秘境', 'warning')
                return
            }
            navigate(`/npc/${realmId}`)
        },
        [navigate]
    )

    return (
        <div className={`${styles.container} page-container`}>
            <div className={styles.hero}>
                <div className={styles.heroContent}>
                    <h1 className={styles.heroTitle}>⛲ 知识之泉</h1>
                    <p className={styles.heroDesc}>与导师对话，领悟算法的奥秘</p>
                </div>
                <div className={styles.heroDecor} aria-hidden="true">
                    <span className={styles.star} style={{ '--delay': '0s' }}>✦</span>
                    <span className={styles.star} style={{ '--delay': '1s' }}>✦</span>
                    <span className={styles.star} style={{ '--delay': '2s' }}>✦</span>
                </div>
            </div>

            {loading && (
                <div className={styles.loadingState}>
                    <span className={styles.loadingIcon}>🔮</span>
                    <p className={styles.loadingText}>正在召唤导师...</p>
                </div>
            )}

            {error && !loading && (
                <div className={styles.errorState}>
                    <span className={styles.errorIcon}>⚠️</span>
                    <p className={styles.errorText}>加载失败: {error}</p>
                    <button className={styles.retryBtn} onClick={fetchNpcs}>
                        重新加载
                    </button>
                </div>
            )}

            {!loading && !error && npcs.length === 0 && (
                <div className={styles.emptyState}>
                    <span className={styles.emptyIcon}>🏜️</span>
                    <p className={styles.emptyText}>还没有可对话的导师</p>
                    <button className={styles.emptyBtn} onClick={() => navigate('/')}>
                        前往冒险地图
                    </button>
                </div>
            )}

            {!loading && !error && npcs.length > 0 && (
                <section className={styles.npcSection} aria-label="导师列表">
                    <h2 className={styles.sectionTitle}>
                        <span>🧙</span> 导师殿堂
                    </h2>

                    <div className={styles.npcGrid}>
                        {npcs.map((npc, index) => (
                            <GameCard
                                key={npc.id}
                                className={styles.npcCard}
                                glow
                                hoverable
                                onClick={() => handleNpcClick(npc)}
                                style={{ animationDelay: `${index * 100}ms` }}
                            >
                                <div className={styles.cardHeader}>
                                    <span className={styles.npcAvatar}>{npc.avatar}</span>
                                    <div className={styles.cardHeaderInfo}>
                                        <h3 className={styles.npcName}>{npc.name}</h3>
                                        <span className={styles.npcDomain}>{npc.domain}</span>
                                    </div>
                                </div>

                                <div className={styles.npcLocation}>
                                    <span>📍</span>
                                    <span>{npc.location}</span>
                                </div>

                                {npc.topics && npc.topics.length > 0 && (
                                    <div className={styles.topicsList}>
                                        {npc.topics.slice(0, 3).map((topic, i) => (
                                            <span key={i} className={styles.topicTag}>{topic}</span>
                                        ))}
                                        {npc.topics.length > 3 && (
                                            <span className={styles.topicMore}>+{npc.topics.length - 3}</span>
                                        )}
                                    </div>
                                )}

                                <div className={styles.cardAction}>
                                    <span>前往对话 →</span>
                                </div>
                            </GameCard>
                        ))}
                    </div>
                </section>
            )}

            {!loading && !error && npcs.length > 0 && (
                <section className={styles.statsSection} aria-label="快速统计">
                    <div className={styles.statCards}>
                        <GameCard className={styles.statCard}>
                            <span className={styles.statIcon}>🧙‍♂️</span>
                            <div className={styles.statInfo}>
                                <span className={styles.statValue}>{npcs.length}</span>
                                <span className={styles.statLabel}>可对话导师</span>
                            </div>
                        </GameCard>
                        <GameCard className={styles.statCard}>
                            <span className={styles.statIcon}>💬</span>
                            <div className={styles.statInfo}>
                                <span className={styles.statValue}>
                                    {npcs.reduce((sum, n) => sum + (n.topics?.length || 0), 0)}
                                </span>
                                <span className={styles.statLabel}>可探讨话题</span>
                            </div>
                        </GameCard>
                        <GameCard className={styles.statCard}>
                            <span className={styles.statIcon}>🗺️</span>
                            <div className={styles.statInfo}>
                                <span className={styles.statValue}>
                                    {new Set(npcs.map((n) => n.location)).size}
                                </span>
                                <span className={styles.statLabel}>覆盖秘境</span>
                            </div>
                        </GameCard>
                    </div>
                </section>
            )}
        </div>
    )
}
