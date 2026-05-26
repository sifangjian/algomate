import { useEffect, useRef, useCallback, useState, memo } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import { useNavigate } from 'react-router-dom'
import styles from './KnowledgeGraph.module.css'

const ALGORITHM_COLORS = {
  'Sorting': '#ef4444',
  'Search': '#3b82f6',
  'Dynamic Programming': '#10b981',
  'Graph': '#8b5cf6',
  'Tree': '#f59e0b',
  'String': '#ec4899',
  'Math': '#14b8a6',
  'Greedy': '#f97316',
  'Backtracking': '#6366f1',
  'Divide and Conquer': '#84cc16',
  'Hash Table': '#06b6d4',
  'Stack': '#d946ef',
  'Queue': '#a855f7',
  'Heap': '#eab308',
  'Linked List': '#22d3ee',
}

function getNodeColor(node) {
  return ALGORITHM_COLORS[node.algorithm_type] || '#64748b'
}

const KnowledgeGraph = memo(function KnowledgeGraph({ data, onNodeClick, onClose }) {
  const containerRef = useRef(null)
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 })

  useEffect(() => {
    if (containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect()
      setDimensions({ width: rect.width, height: rect.height })
    }
  }, [])

  const handleNodeClick = useCallback((node) => {
    if (onNodeClick) onNodeClick(node)
  }, [onNodeClick])

  if (!data || !data.nodes || data.nodes.length === 0) {
    return (
      <div className={styles.empty}>
        <p>暂无卡牌数据，无法展示知识图谱</p>
      </div>
    )
  }

  const graphData = {
    nodes: data.nodes.map(n => ({ ...n, val: 8 })),
    links: (data.edges || []).map(e => ({
      source: e.source,
      target: e.target,
      link_type: e.link_type,
      source_keyword: e.source_keyword,
    })),
  }

  return (
    <div className={styles.container} ref={containerRef}>
      <div className={styles.header}>
        <h3 className={styles.title}>🕸️ 知识图谱</h3>
        {onClose && (
          <button className={styles.closeBtn} onClick={onClose}>✕</button>
        )}
      </div>
      <ForceGraph2D
        graphData={graphData}
        width={dimensions.width}
        height={dimensions.height - 50}
        nodeLabel="name"
        nodeColor={getNodeColor}
        nodeRelSize={6}
        linkDirectionalArrowLength={4}
        linkDirectionalArrowRelPos={1}
        linkCurvature={0.1}
        linkColor={() => 'rgba(148, 163, 184, 0.4)'}
        onNodeClick={handleNodeClick}
        backgroundColor="rgba(15, 15, 26, 0.8)"
        cooldownTicks={100}
      />
      <div className={styles.legend}>
        {Object.entries(ALGORITHM_COLORS).slice(0, 8).map(([type, color]) => (
          <span key={type} className={styles.legendItem}>
            <span className={styles.legendDot} style={{ background: color }} />
            {type}
          </span>
        ))}
      </div>
    </div>
  )
})

export default KnowledgeGraph
