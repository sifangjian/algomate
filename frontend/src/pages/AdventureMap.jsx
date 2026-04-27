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

const MOCK_REALMS = [
  {
    id: 'novice_forest',
    name: '新手森林',
    icon: '🌲',
    description: '算法之旅的起点，学习基础数据结构与查找算法',
    status: 'unlocked',
    order: 1,
    progress: 65,
    npcInfo: { id: 'npc_novice_teacher', name: '引导者艾琳', avatar: '🧙‍♀️' },
    bossInfo: null,
  },
  {
    id: 'mist_swamp',
    name: '迷雾沼泽',
    icon: '🌫️',
    description: '深入递归与回溯的领域，挑战迷雾史莱姆王',
    status: 'unlocked',
    order: 2,
    progress: 30,
    npcInfo: { id: 'npc_swamp_guide', name: '沼泽向导', avatar: '🧟' },
    bossInfo: { id: 'boss_slime_king', name: '迷雾史莱姆王', difficulty: 2 },
  },
  {
    id: 'crystal_cave',
    name: '水晶洞穴',
    icon: '💎',
    description: '动态规划的璀璨世界，用智慧照亮黑暗',
    status: 'partial',
    order: 3,
    progress: 10,
    unlockCondition: {
      type: 'card_count',
      requiredValue: 5,
      currentValue: 3,
      description: '需要5张熟练度≥60的卡牌',
    },
    npcInfo: { id: 'npc_crystal_sage', name: '水晶贤者', avatar: '🔮' },
    bossInfo: null,
  },
  {
    id: 'volcano_peak',
    name: '火山之巅',
    icon: '🌋',
    description: '图论与高级算法的终极试炼场',
    status: 'locked',
    order: 4,
    progress: 0,
    unlockCondition: {
      type: 'complete_realm',
      requiredValue: 1,
      currentValue: 0,
      description: '需要通关迷雾沼泽',
    },
    npcInfo: { id: 'npc_fire_lord', name: '炎之领主', avatar: '🔥' },
    bossInfo: { id: 'boss_dragon', name: '熔岩巨龙', difficulty: 3 },
  },
  {
    id: 'sky_garden',
    name: '天空花园',
    icon: '🏔️',
    description: '高级数据结构的圣域，触及算法的极限',
    status: 'locked',
    order: 5,
    progress: 0,
    unlockCondition: {
      type: 'level',
      requiredValue: 10,
      currentValue: 5,
      description: '需要达到等级10',
    },
    npcInfo: { id: 'npc_sky_keeper', name: '天空守护者', avatar: '👼' },
    bossInfo: null,
  },
]

export default function AdventureMap() {
  const navigate = useNavigate()
  const { realms, setRealms, setLoading, setError } = useGameStore()
  const { setUser } = useUserStore()
  const { setTaskSummary, addToast } = useUIStore()

  const fetchInitialData = useCallback(async () => {
    setLoading(true)
    try {
      const [realmsData] = await Promise.allSettled([
        realmService.getAll().catch(() => MOCK_REALMS),
        userService.getUser().catch(() => null),
      ])

      if (realmsData.status === 'fulfilled' && Array.isArray(realmsData.value)) {
        const sorted = [...(realmsData.value || MOCK_REALMS)].sort(
          (a, b) => (a.order || 0) - (b.order || 0)
        )
        setRealms(sorted)
      } else {
        const sorted = [...MOCK_REALMS].sort((a, b) => a.order - b.order)
        setRealms(sorted)
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
      showToast('加载失败，使用离线数据', 'warning')
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
      navigate(`/npc/${realm.id}`)
    },
    [navigate]
  )

  const displayRealms = realms.length > 0 ? realms : MOCK_REALMS

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
              className={`${styles.realmCard} ${styles[realm.status]}`}
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
                    {'★'.repeat(realm.bossInfo.difficulty)}{'☆'.repeat(3 - realm.bossInfo.difficulty)}
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
