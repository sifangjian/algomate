import { useEffect, useState } from 'react'
import { useHallStore } from '../../stores/hallStore'
import styles from './AlgorithmMap.module.css'

export default function AlgorithmMap() {
  const { npcs, cardGraph, learningPath, fetchCardGraph } = useHallStore()
  const [loading, setLoading] = useState(!cardGraph)

  useEffect(() => {
    if (!cardGraph && fetchCardGraph) {
      setLoading(true)
      Promise.resolve(fetchCardGraph()).finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [cardGraph, fetchCardGraph])

  if (loading || !cardGraph) {
    return <div className={styles.loading}>正在加载卡牌地图...</div>
  }

  const nodes = cardGraph.nodes || []
  const edges = cardGraph.edges || []

  const nodePositions = {}
  nodes.forEach((node, idx) => {
    nodePositions[node.id] = {
      x: 100 + (idx % 3) * 200,
      y: 80 + Math.floor(idx / 3) * 120,
      node,
    }
  })

  return (
    <div className={styles.algorithmMap}>
      <svg width="100%" height="400" viewBox="0 0 600 400">
        {edges.map((edge, idx) => {
          const source = nodePositions[edge.source]
          const target = nodePositions[edge.target]
          if (!source || !target) return null
          return (
            <line
              key={idx}
              x1={source.x}
              y1={source.y}
              x2={target.x}
              y2={target.y}
              className={styles.edge}
            />
          )
        })}
        {nodes.map((node) => {
          const pos = nodePositions[node.id] || { x: 100, y: 100 }
          return (
            <g key={node.id} className={styles.node}>
              <circle cx={pos.x} cy={pos.y} r="30" className={styles.nodeCircle} />
              <text x={pos.x} y={pos.y + 4} className={styles.nodeText} textAnchor="middle">
                {node.name}
              </text>
            </g>
          )
        })}
      </svg>
      <div className={styles.legend}>
        <div className={styles.legendItem}>
          <span className={`${styles.legendDot} ${styles.prerequisite}`}></span>
          <span>前置关联</span>
        </div>
        <div className={styles.legendItem}>
          <span className={`${styles.legendDot} ${styles.related}`}></span>
          <span>相关关联</span>
        </div>
        <div className={styles.legendItem}>
          <span className={`${styles.legendDot} ${styles.empty}`}></span>
          <span>空卡牌</span>
        </div>
      </div>
    </div>
  )
}
