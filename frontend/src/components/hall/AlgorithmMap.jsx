import { useMemo, useRef, useState, useEffect, useLayoutEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useHallStore } from '../../stores/hallStore'
import { forceSimulation, forceLink, forceManyBody, forceCenter, forceCollide } from 'd3-force'
import styles from './AlgorithmMap.module.css'

const NODE_WIDTH = 140
const NODE_HEIGHT = 52
const NODE_RX = 8
const GRID = 40

const COLORS = {
  nodeFill: '#303030',
  nodeBorder: '#8c8c8c',
  emptyNodeBorder: '#555555',
  emptyNodeFill: '#252525',
  nodeText: '#ffffff',
  emptyNodeText: '#888888',
  typeText: '#999999',
  link: '#555555',
  tipRelatedLink: '#60a5fa',
  grid: '#2a2a2a',
}

export default function AlgorithmMap() {
  const navigate = useNavigate()
  const { cardGraph } = useHallStore()
  const svgRef = useRef(null)
  const transformRef = useRef({ x: 0, y: 0, scale: 1 })
  const dragRef = useRef({ dragging: false, startX: 0, startY: 0, originX: 0, originY: 0 })
  const fitRef = useRef(false)

  const [transform, setTransform] = useState({ x: 0, y: 0, scale: 1 })
  const [isDragging, setIsDragging] = useState(false)
  const [hoveredNode, setHoveredNode] = useState(null)
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 })

  useEffect(() => { transformRef.current = transform }, [transform])

  const simulationData = useMemo(() => {
    if (!cardGraph?.nodes?.length) return null

    const nodes = cardGraph.nodes.map(n => ({
      id: n.id,
      name: n.name,
      algorithm_type: n.algorithm_type,
      durability: n.durability,
      review_level: n.review_level,
      is_empty: n.is_empty,
      x: 0,
      y: 0,
    }))

    const nodeMap = {}
    nodes.forEach(n => { nodeMap[n.id] = n })

    const links = (cardGraph.edges || [])
      .filter(e => nodeMap[e.source] && nodeMap[e.target])
      .map(e => ({
        source: e.source,
        target: e.target,
        link_type: e.link_type,
        source_card_name: e.source_card_name,
        target_card_name: e.target_card_name,
      }))

    const sim = forceSimulation(nodes)
      .force('link', forceLink(links).id(d => d.id).distance(180).strength(0.5))
      .force('charge', forceManyBody().strength(-400))
      .force('center', forceCenter(0, 0))
      .force('collide', forceCollide().radius(100))
      .stop()

    sim.tick(300)

    return { nodes, links }
  }, [cardGraph])

  const bounds = useMemo(() => {
    if (!simulationData?.nodes.length) return null
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
    simulationData.nodes.forEach(n => {
      minX = Math.min(minX, n.x - NODE_WIDTH / 2)
      maxX = Math.max(maxX, n.x + NODE_WIDTH / 2)
      minY = Math.min(minY, n.y - NODE_HEIGHT / 2)
      maxY = Math.max(maxY, n.y + NODE_HEIGHT / 2)
    })
    return { minX, minY, maxX, maxY, width: maxX - minX, height: maxY - minY }
  }, [simulationData])

  useLayoutEffect(() => {
    if (!bounds || fitRef.current) return
    const svg = svgRef.current
    if (!svg) return
    let raf
    const fit = () => {
      const rect = svg.getBoundingClientRect()
      if (rect.width === 0 || rect.height === 0) { raf = requestAnimationFrame(fit); return }
      const pad = 40
      const scaleX = (rect.width - 2 * pad) / bounds.width
      const scaleY = (rect.height - 2 * pad) / bounds.height
      const scale = Math.min(scaleX, scaleY, 1.0)
      const x = pad - bounds.minX * scale + ((rect.width - 2 * pad) - bounds.width * scale) / 2
      const y = pad - bounds.minY * scale + ((rect.height - 2 * pad) - bounds.height * scale) / 2
      setTransform({ x, y, scale })
      fitRef.current = true
    }
    raf = requestAnimationFrame(fit)
    return () => cancelAnimationFrame(raf)
  }, [bounds])

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
    if (e.target.closest('[data-node]')) return
    dragRef.current = { dragging: true, startX: e.clientX, startY: e.clientY, originX: transformRef.current.x, originY: transformRef.current.y }
    setIsDragging(true)
  }

  const handleNodeClick = useCallback((node) => {
    navigate(`/study/${node.id}`)
  }, [navigate])

  if (!cardGraph?.nodes?.length) {
    return (
      <div className={styles.mapContainer}>
        <div className={styles.emptyState}>正在加载卡牌地图...</div>
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

  const nodeMap = {}
  simulationData.nodes.forEach(n => { nodeMap[n.id] = n })

  return (
    <div className={styles.mapContainer}>
      <svg ref={svgRef} className={`${styles.mapSvg} ${isDragging ? styles.dragging : ''}`} onMouseDown={handleMouseDown}>
        <defs>
          <marker id="arrowRelated" markerWidth="8" markerHeight="8" refX="8" refY="4" orient="auto" markerUnits="userSpaceOnUse">
            <path d="M0,0 L8,4 L0,8 Z" fill={COLORS.link} />
          </marker>
          <marker id="arrowTipRelated" markerWidth="8" markerHeight="8" refX="8" refY="4" orient="auto" markerUnits="userSpaceOnUse">
            <path d="M0,0 L8,4 L0,8 Z" fill={COLORS.tipRelatedLink} />
          </marker>
        </defs>

        <g transform={`translate(${transform.x} ${transform.y}) scale(${transform.scale})`}>
          <g className={styles.grid}>{gridLines}</g>

          <g className={styles.links}>
            {simulationData.links.map((link, i) => {
              const s = nodeMap[link.source.id || link.source]
              const t = nodeMap[link.target.id || link.target]
              if (!s || !t) return null
              const dx = t.x - s.x
              const dy = t.y - s.y
              const dist = Math.sqrt(dx * dx + dy * dy)
              if (dist === 0) return null
              const ux = dx / dist
              const uy = dy / dist
              const sx = s.x + ux * (NODE_WIDTH / 2)
              const sy = s.y + uy * (NODE_HEIGHT / 2)
              const tx = t.x - ux * (NODE_WIDTH / 2)
              const ty = t.y - uy * (NODE_HEIGHT / 2)
              const isTipRelated = link.link_type === 'tip_related'
              return (
                <line
                  key={`link-${i}`}
                  x1={sx} y1={sy} x2={tx} y2={ty}
                  className={isTipRelated ? styles.tipRelatedLink : styles.relatedLink}
                  markerEnd={isTipRelated ? "url(#arrowTipRelated)" : "url(#arrowRelated)"}
                />
              )
            })}
          </g>

          <g className={styles.nodes}>
            {simulationData.nodes.map((node) => {
              const isEmpty = node.is_empty
              return (
                <g
                  key={`node-${node.id}`}
                  data-node
                  className={styles.nodeGroup}
                  transform={`translate(${node.x} ${node.y})`}
                  onClick={() => handleNodeClick(node)}
                  onMouseEnter={() => {
                    setHoveredNode(node)
                    const rect = svgRef.current.getBoundingClientRect()
                    const scale = transform.scale
                    const x = transform.x + node.x * scale
                    const y = transform.y + node.y * scale
                    setTooltipPos({ x: rect.left + x, y: rect.top + y - 10 })
                  }}
                  onMouseLeave={() => setHoveredNode(null)}
                >
                  <rect
                    className={`${styles.nodeRect} ${isEmpty ? styles.emptyNode : ''}`}
                    x={-NODE_WIDTH / 2}
                    y={-NODE_HEIGHT / 2}
                    width={NODE_WIDTH}
                    height={NODE_HEIGHT}
                    rx={NODE_RX}
                  />
                  <text
                    className={styles.nodeText}
                    x={0} y={-6}
                    textAnchor="middle"
                    dominantBaseline="middle"
                    fill={isEmpty ? COLORS.emptyNodeText : COLORS.nodeText}
                    fontSize="12"
                    fontWeight="500"
                  >
                    {node.name.length > 10 ? node.name.slice(0, 10) + '…' : node.name}
                  </text>
                  <text
                    className={styles.typeText}
                    x={0} y={10}
                    textAnchor="middle"
                    dominantBaseline="middle"
                    fill={COLORS.typeText}
                    fontSize="9"
                  >
                    {node.algorithm_type || '未分类'}
                  </text>
                </g>
              )
            })}
          </g>
        </g>
      </svg>

      <div className={styles.legend}>
        <div className={styles.legendItem}>
          <span className={styles.relatedLegend}></span>
          <span>题目关联</span>
        </div>
        <div className={styles.legendItem}>
          <span className={styles.tipRelatedLegend}></span>
          <span>技巧关联</span>
        </div>
        <div className={styles.legendItem}>
          <span className={styles.emptyLegend}></span>
          <span>空卡牌</span>
        </div>
        <div className={styles.hint}>拖拽移动 · 滚轮缩放</div>
      </div>
      {hoveredNode && (
        <div
          className={styles.nodeTooltip}
          style={{
            left: tooltipPos.x,
            top: tooltipPos.y,
            position: 'fixed',
            transform: 'translate(-50%, -100%)',
          }}
        >
          <div className={styles.tooltipTitle}>{hoveredNode.name}</div>
          <div className={styles.tooltipRow}>
            <span className={styles.tooltipLabel}>类型</span>
            <span className={styles.tooltipValue}>{hoveredNode.algorithm_type || '未分类'}</span>
          </div>
          {hoveredNode.durability != null && (
            <div className={styles.tooltipRow}>
              <span className={styles.tooltipLabel}>耐久</span>
              <span className={styles.tooltipValue}>{Math.round(hoveredNode.durability)}%</span>
            </div>
          )}
          {hoveredNode.review_level != null && (
            <div className={styles.tooltipRow}>
              <span className={styles.tooltipLabel}>等级</span>
              <span className={styles.tooltipValue}>Lv.{hoveredNode.review_level}</span>
            </div>
          )}
          {hoveredNode.is_empty && (
            <div className={styles.tooltipEmpty}>空卡牌</div>
          )}
        </div>
      )}
    </div>
  )
}
