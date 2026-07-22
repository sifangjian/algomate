import { useMemo, useRef, useState, useEffect, useLayoutEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useHallStore } from '../../stores/hallStore'
import { tree, hierarchy } from 'd3-hierarchy'
import styles from './AlgorithmMap.module.css'

const NODE_WIDTH = 128
const NODE_HEIGHT = 38
const NODE_RX = 8
const V_GAP = 56
const H_GAP = 200
const DOT_RADIUS = 6
const GRID = 40

const COLORS = {
  nodeFill: '#303030',
  nodeBorder: '#8c8c8c',
  nodeText: '#ffffff',
  link: '#555555',
  crossLink: '#4a4a4a',
  grid: '#2a2a2a',
}

const DOT_COLORS = {
  core: '#60a5fa',
  important: '#a78bfa',
  extension: '#22d3ee',
}

const DOT_LABELS = {
  core: '基础',
  important: '进阶',
  extension: '拓展',
}

export default function AlgorithmMap() {
  const navigate = useNavigate()
  const { npcs, algorithmInfo } = useHallStore()
  const svgRef = useRef(null)
  const transformRef = useRef({ x: 0, y: 0, scale: 1 })
  const dragRef = useRef({ dragging: false, startX: 0, startY: 0, originX: 0, originY: 0 })
  const fitRef = useRef(false)

  const [transform, setTransform] = useState({ x: 0, y: 0, scale: 1 })
  const [isDragging, setIsDragging] = useState(false)
  const [collapsed, setCollapsed] = useState(new Set())

  useEffect(() => { transformRef.current = transform }, [transform])

  const topicImportance = useMemo(() => algorithmInfo?.topic_importance || {}, [algorithmInfo])
  const topicPrerequisites = useMemo(() => algorithmInfo?.topic_prerequisites || {}, [algorithmInfo])
  const topicProgress = useMemo(() => algorithmInfo?.topic_progress || {}, [algorithmInfo])
  const allTopics = useMemo(() => algorithmInfo?.algorithm_types || [], [algorithmInfo])

  // 构建严格树：每个节点只分配给其第一个前置依赖作为主父节点
  const fullTreeData = useMemo(() => {
    if (!allTopics.length) return null

    const childrenMap = {}
    allTopics.forEach(t => { childrenMap[t] = [] })

    const primaryParent = {}
    allTopics.forEach(topic => {
      const prereqs = topicPrerequisites[topic] || []
      if (prereqs.length > 0) {
        primaryParent[topic] = prereqs[0]
        childrenMap[prereqs[0]].push(topic)
      }
    })

    const roots = allTopics.filter(t => !primaryParent[t])

    const buildNode = (topic) => ({
      name: topic,
      children: childrenMap[topic].map(buildNode),
      importance: topicImportance[topic] || 'extension',
      learned: !!(topicProgress[topic]?.learned),
      hasChildren: childrenMap[topic].length > 0,
    })

    return { name: '__root__', children: roots.map(buildNode) }
  }, [allTopics, topicImportance, topicPrerequisites, topicProgress])

  // 应用折叠状态后计算布局
  const treeLayout = useMemo(() => {
    if (!fullTreeData) return null

    const applyCollapse = (node) => ({
      name: node.name,
      importance: node.importance,
      learned: node.learned,
      hasChildren: node.hasChildren,
      children: collapsed.has(node.name) ? [] : node.children.map(applyCollapse),
    })

    const visibleData = {
      name: '__root__',
      children: fullTreeData.children.map(applyCollapse),
    }

    const root = hierarchy(visibleData).sort((a, b) => {
      const order = { core: 0, important: 1, extension: 2 }
      return (order[a.data.importance] ?? 3) - (order[b.data.importance] ?? 3)
    })

    return tree().nodeSize([V_GAP, H_GAP])(root)
  }, [fullTreeData, collapsed])

  const nodes = useMemo(() => {
    if (!treeLayout) return []
    return treeLayout.descendants().filter(d => d.data.name !== '__root__')
  }, [treeLayout])

  const links = useMemo(() => {
    if (!treeLayout) return []
    return treeLayout.links().filter(l => l.source.data.name !== '__root__')
  }, [treeLayout])

  // 节点位置映射：name → {x, y}（横向布局：x=depth, y=breadth）
  const nodePositions = useMemo(() => {
    const map = new Map()
    nodes.forEach(n => map.set(n.data.name, { x: n.y, y: n.x }))
    return map
  }, [nodes])

  // 二级依赖边：非首要前置依赖的跨分支连接
  const crossEdges = useMemo(() => {
    const edges = []
    // 收集当前可见节点名（折叠的节点不在树中）
    const visibleNames = new Set(nodes.map(n => n.data.name))

    allTopics.forEach(topic => {
      const prereqs = topicPrerequisites[topic] || []
      // 跳过第一个前置依赖（那是树的主边），只取后续的
      for (let i = 1; i < prereqs.length; i++) {
        const from = prereqs[i]
        const to = topic
        // 两端节点都可见时才绘制
        if (visibleNames.has(from) && visibleNames.has(to)) {
          edges.push({ from, to })
        }
      }
    })
    return edges
  }, [allTopics, topicPrerequisites, nodes])

  const bounds = useMemo(() => {
    if (!nodes.length) return null
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
    nodes.forEach(n => {
      const x = n.y, y = n.x
      minX = Math.min(minX, x - NODE_WIDTH / 2)
      maxX = Math.max(maxX, x + NODE_WIDTH / 2)
      minY = Math.min(minY, y - NODE_HEIGHT / 2)
      maxY = Math.max(maxY, y + NODE_HEIGHT / 2)
    })
    return { minX, minY, maxX, maxY, width: maxX - minX, height: maxY - minY }
  }, [nodes])

  // 初始视图：scale=1 放大显示局部
  useLayoutEffect(() => {
    if (!bounds || fitRef.current) return
    const svg = svgRef.current
    if (!svg) return
    let raf
    const fit = () => {
      const rect = svg.getBoundingClientRect()
      if (rect.width === 0 || rect.height === 0) { raf = requestAnimationFrame(fit); return }
      const pad = 40
      const scale = 1.0
      const x = pad - bounds.minX * scale
      const y = pad - bounds.minY * scale + (rect.height - 2 * pad - bounds.height * scale) / 2
      setTransform({ x, y, scale })
      fitRef.current = true
    }
    raf = requestAnimationFrame(fit)
    return () => cancelAnimationFrame(raf)
  }, [bounds])

  // 滚轮缩放
  useEffect(() => {
    const svg = svgRef.current
    if (!svg) return
    const onWheel = (e) => {
      e.preventDefault()
      const t = transformRef.current
      const delta = -e.deltaY * 0.002
      let newScale = Math.max(0.2, Math.min(3, t.scale * (1 + delta)))
      const rect = svg.getBoundingClientRect()
      const mx = e.clientX - rect.left, my = e.clientY - rect.top
      const ratio = newScale / t.scale
      setTransform({ scale: newScale, x: mx - (mx - t.x) * ratio, y: my - (my - t.y) * ratio })
    }
    svg.addEventListener('wheel', onWheel, { passive: false })
    return () => svg.removeEventListener('wheel', onWheel)
  }, [])

  // 拖拽平移
  useEffect(() => {
    const onMove = (e) => {
      if (!dragRef.current.dragging) return
      setTransform(t => ({
        ...t,
        x: dragRef.current.originX + e.clientX - dragRef.current.startX,
        y: dragRef.current.originY + e.clientY - dragRef.current.startY,
      }))
    }
    const onUp = () => {
      if (dragRef.current.dragging) { dragRef.current.dragging = false; setIsDragging(false) }
    }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
    return () => { window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp) }
  }, [])

  const handleMouseDown = (e) => {
    if (e.target.closest('[data-toggle]') || e.target.closest('[data-node]')) return
    dragRef.current = { dragging: true, startX: e.clientX, startY: e.clientY, originX: transformRef.current.x, originY: transformRef.current.y }
    setIsDragging(true)
  }

  const toggleCollapse = useCallback((topic, e) => {
    e.stopPropagation()
    setCollapsed(prev => {
      const next = new Set(prev)
      next.has(topic) ? next.delete(topic) : next.add(topic)
      return next
    })
  }, [])

  const getNpcForTopic = (topic) => npcs.find(npc => npc.specialties?.includes(topic) || npc.topics?.includes(topic))

  const handleNodeClick = (topic) => {
    const npc = getNpcForTopic(topic)
    if (npc) navigate(`/npc/${npc.id}`)
  }

  if (!algorithmInfo) {
    return (
      <div className={styles.mapContainer}>
        <div className={styles.emptyState}>正在加载算法地图...</div>
      </div>
    )
  }

  const gridLines = []
  if (bounds) {
    const pad = 400
    const startX = Math.floor((bounds.minX - pad) / GRID) * GRID
    const endX = bounds.maxX + pad
    const startY = Math.floor((bounds.minY - pad) / GRID) * GRID
    const endY = bounds.maxY + pad
    for (let x = startX; x <= endX; x += GRID) gridLines.push(<line key={`v${x}`} x1={x} y1={startY} x2={x} y2={endY} className={styles.gridLine} />)
    for (let y = startY; y <= endY; y += GRID) gridLines.push(<line key={`h${y}`} x1={startX} y1={y} x2={endX} y2={y} className={styles.gridLine} />)
  }

  return (
    <div className={styles.mapContainer}>
      <svg ref={svgRef} className={`${styles.mapSvg} ${isDragging ? styles.dragging : ''}`} onMouseDown={handleMouseDown}>
        <defs>
          <marker id="arrowhead" markerWidth="8" markerHeight="8" refX="8" refY="4" orient="auto" markerUnits="userSpaceOnUse">
            <path d="M0,0 L8,4 L0,8 Z" fill={COLORS.link} />
          </marker>
          <marker id="cross-arrow" markerWidth="6" markerHeight="6" refX="6" refY="3" orient="auto" markerUnits="userSpaceOnUse">
            <path d="M0,0 L6,3 L0,6 Z" fill={COLORS.crossLink} />
          </marker>
        </defs>

        <g transform={`translate(${transform.x} ${transform.y}) scale(${transform.scale})`}>
          <g className={styles.grid}>{gridLines}</g>

          {/* 二级依赖边：跨分支虚线 */}
          <g className={styles.crossLinks}>
            {crossEdges.map((edge, i) => {
              const from = nodePositions.get(edge.from)
              const to = nodePositions.get(edge.to)
              if (!from || !to) return null
              // 从前置节点右边缘到目标节点左边缘的贝塞尔曲线
              const sx = from.x + NODE_WIDTH / 2
              const sy = from.y
              const tx = to.x - NODE_WIDTH / 2
              const ty = to.y
              const dx = (tx - sx) * 0.4
              return (
                <path
                  key={`cross-${i}`}
                  className={styles.crossLinkPath}
                  d={`M ${sx} ${sy} C ${sx + dx} ${sy} ${tx - dx} ${ty} ${tx} ${ty}`}
                  markerEnd="url(#cross-arrow)"
                />
              )
            })}
          </g>

          {/* 主树边：正交折线 */}
          <g className={styles.links}>
            {links.map((link, i) => {
              const sx = link.source.y + NODE_WIDTH / 2
              const sy = link.source.x
              const tx = link.target.y - NODE_WIDTH / 2
              const ty = link.target.x
              const midX = (sx + tx) / 2
              return (
                <path
                  key={i}
                  className={styles.linkPath}
                  d={`M ${sx} ${sy} L ${midX} ${sy} L ${midX} ${ty} L ${tx} ${ty}`}
                  markerEnd="url(#arrowhead)"
                />
              )
            })}
          </g>

          <g className={styles.nodes}>
            {nodes.map((node, i) => {
              const dotColor = DOT_COLORS[node.data.importance] || DOT_COLORS.extension
              const isCollapsed = collapsed.has(node.data.name)
              const hasChildren = node.data.hasChildren
              return (
                <g
                  key={`${node.data.name}-${i}`}
                  data-node
                  className={styles.nodeGroup}
                  transform={`translate(${node.y} ${node.x})`}
                  onClick={() => handleNodeClick(node.data.name)}
                >
                  <rect
                    className={styles.nodeRect}
                    x={-NODE_WIDTH / 2}
                    y={-NODE_HEIGHT / 2}
                    width={NODE_WIDTH}
                    height={NODE_HEIGHT}
                    rx={NODE_RX}
                  />
                  <circle cx={-NODE_WIDTH / 2 + 12} cy={0} r={DOT_RADIUS} fill={dotColor} />
                  <text className={styles.nodeText} x={6} y={0} textAnchor="middle" dominantBaseline="middle">
                    {node.data.name}
                  </text>
                  {node.data.learned && (
                    <text x={NODE_WIDTH / 2 - (hasChildren ? 26 : 10)} y={0} textAnchor="end" dominantBaseline="middle" fill="#22c55e" fontSize="13" style={{ pointerEvents: 'none' }}>
                      ✓
                    </text>
                  )}
                  {hasChildren && (
                    <g
                      data-toggle
                      className={styles.toggleBtn}
                      onClick={(e) => toggleCollapse(node.data.name, e)}
                    >
                      <circle cx={NODE_WIDTH / 2 + 2} cy={0} r={10} />
                      <text
                        x={NODE_WIDTH / 2 + 2}
                        y={1}
                        textAnchor="middle"
                        dominantBaseline="middle"
                        fill="#bfbfbf"
                        fontSize="14"
                        fontWeight="bold"
                      >
                        {isCollapsed ? '+' : '−'}
                      </text>
                    </g>
                  )}
                </g>
              )
            })}
          </g>
        </g>
      </svg>

      <div className={styles.legend}>
        <div className={styles.legendItem}>
          <span className={styles.legendLine}></span>
          <span>主依赖</span>
        </div>
        <div className={styles.legendItem}>
          <span className={styles.crossLegendLine}></span>
          <span>关联依赖</span>
        </div>
        {['core', 'important', 'extension'].map(k => (
          <div className={styles.legendItem} key={k}>
            <span className={`${styles.legendDot} ${styles[k]}`}></span>
            <span>{DOT_LABELS[k]}</span>
          </div>
        ))}
        <div className={styles.legendItem}>
          <span className={styles.legendCheck}>✓</span>
          <span>已学习</span>
        </div>
        <div className={styles.legendItem}>
          <span className={styles.toggleLegend}>+/−</span>
          <span>展开/折叠</span>
        </div>
        <div className={styles.hint}>拖拽移动 · 滚轮缩放</div>
      </div>
    </div>
  )
}
