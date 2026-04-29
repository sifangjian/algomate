import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { npcService, LOCATION_TO_REALM_ID } from '../services/npcService'
import GameCard from '../components/ui/Card/GameCard'
import { showToast } from '../components/ui/Toast/index'
import styles from './KnowledgeSpring.module.css'

export default function KnowledgeSpring() {
    const navigate = useNavigate()
    const [npcs, setNpcs] = useState([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState(null)

    const fetchNpcs = useCallback(async () => {
        setIsLoading(true)
        setError(null)
        try {
            const data = await npcService.getUnlockedNpcs()
            setNpcs(Array.isArray(data) ? data : [])
        } catch (err) {
            setError(err.message || '加载失败')
            showToast('加载NPC列表失败', 'error')
        } finally {
            setIsLoading(false)
        }
    }, [])

    useEffect(() => {
        fetchNpcs()
    }, [fetchNpcs])

    const handleNpcClick = useCallback((npc) => {
        const realmId = LOCATION_TO_REALM_ID[npc.location] || npc.id
        navigate(`/npc/${realmId}`)
    }, [navigate])

    if (isLoading) {
        return (
            <div className={`${styles.container} page-container`}>
                <div className={styles.loading}>
                    <span className={styles.loadingIcon}>🔮</span>
                    <p>正在召唤导师们...</p>
                </div>
            </div>
        )
    }

    if (error) {
        return (
            <div className={`${styles.container} page-container`}>
                <div className={styles.error}>
                    <span className={styles.errorIcon}>⚠️</span>
                    <p className={styles.errorMsg}>加载失败: {error}</p>
                    <button className={styles.retryBtn} onClick={fetchNpcs}>重新加载</button>
                </div>
            </div>
        )
    }

    if (npcs.length === 0) {
        return (
            <div className={`${styles.container} page-container`}>
                <div className={styles.empty}>
                    <span className={styles.emptyIcon}>🏜️</span>
                    <p className={styles.emptyMsg}>还没有解锁任何导师</p>
                    <p className={styles.emptyHint}>前往冒险地图学习算法，解锁更多导师</p>
                    <button className={styles.emptyBtn} onClick={() => navigate('/')}>🗺️ 前往冒险地图</button>
                </div>
            </div>
        )
    }

    return (
        <div className={`${styles.container} page-container`}>
            <div className={styles.hero}>
                <div className={styles.heroContent}>
                    <h1 className={styles.heroTitle}>💬 知识之泉</h1>
                    <p className={styles.heroDesc}>选择一位导师，开启你的算法学习之旅</p>
                </div>
                <div className={styles.heroDecor} aria-hidden="true">
                    <span className={styles.star} style={{ '--delay': '0s' }}>✦</span>
                    <span className={styles.star} style={{ '--delay': '1s' }}>✦</span>
                    <span className={styles.star} style={{ '--delay': '2s' }}>✦</span>
                </div>
            </div>

            <section aria-label="导师列表">
                <h2 className={styles.sectionTitle}>
                    <span>🧙</span> 可对话导师
                </h2>

                <div className={styles.npcGrid}>
                    {npcs.map((npc, index) => (
                        <GameCard
                            key={npc.id}
                            className={styles.npcCard}
                            hoverable
                            glow
                            onClick={() => handleNpcClick(npc)}
                            style={{ animationDelay: `${index * 80}ms` }}
                        >
                            <div className={styles.npcHeader}>
                                <span className={styles.npcAvatar}>{npc.avatar}</span>
                                <div className={styles.npcInfo}>
                                    <h3 className={styles.npcName}>{npc.name}</h3>
                                    <span className={styles.npcDomain}>{npc.domain}</span>
                                </div>
                            </div>
                            <div className={styles.npcLocation}>
                                <span>📍</span>
                                <span>{npc.location}</span>
                            </div>
                            {npc.topics && npc.topics.length > 0 && (
                                <div className={styles.topics}>
                                    {npc.topics.slice(0, 4).map((topic, i) => (
                                        <span key={i} className={styles.topicTag}>{topic}</span>
                                    ))}
                                    {npc.topics.length > 4 && (
                                        <span className={styles.topicMore}>+{npc.topics.length - 4}</span>
                                    )}
                                </div>
                            )}
                        </GameCard>
                    ))}
                </div>
            </section>
        </div>
    )
}
