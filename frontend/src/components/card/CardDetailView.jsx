import { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, useSearchParams, useNavigate } from 'react-router-dom'
import { cardService } from '../../services/cardService'
import CardPanel from './CardPanel'
import CreateCardModal from './CreateCardModal'
import styles from './CardDetailView.module.css'

export default function CardDetailView() {
  const { type, id } = useParams()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const [mainData, setMainData] = useState(null)
  const [compareData, setCompareData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [splitRatio, setSplitRatio] = useState(50)
  const [isDragging, setIsDragging] = useState(false)
  const containerRef = useRef(null)
  const [editModalOpen, setEditModalOpen] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)

  const compareParam = searchParams.get('compare')
  const [compareType, compareId] = compareParam ? compareParam.split('/') : [null, null]
  const isSplitMode = !!(compareType && compareId)

  const fetchData = useCallback(async (type, id) => {
    switch (type) {
      case 'problem':
        return await cardService.getProblem(id)
      case 'solution':
        return await cardService.getSolution(id)
      case 'technique':
        return await cardService.getTechnique(id)
      default:
        throw new Error(`Unknown card type: ${type}`)
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    async function load() {
      setLoading(true)
      setError(null)
      setMainData(null)
      setCompareData(null)

      try {
        const main = await fetchData(type, id)
        if (cancelled) return
        setMainData(main)

        if (compareType && compareId) {
          try {
            const compare = await fetchData(compareType, compareId)
            if (!cancelled) setCompareData(compare)
          } catch (err) {
            // 如果对比卡片加载失败，忽略错误，继续显示主卡片
            console.error('Failed to load compare card:', err)
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message || '加载卡片失败')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => { cancelled = true }
  }, [type, id, compareType, compareId, fetchData])

  const handleNavigate = useCallback((newType, newId) => {
    if (isSplitMode) {
      // 在 split 模式下，旧的主卡变左，新卡变右
      navigate(`/card/${newType}/${newId}?compare=${type}/${id}`)
    } else {
      // 在单卡模式下，点击链接时：旧卡变成对比卡，新卡成为主卡
      navigate(`/card/${newType}/${newId}?compare=${type}/${id}`)
    }
  }, [navigate, isSplitMode, type, id])

  const handleCloseCompare = useCallback(() => {
    navigate(`/card/${type}/${id}`)
  }, [navigate, type, id])

  const handleBack = useCallback(() => {
    navigate(-1)
  }, [navigate])

  const handleDelete = useCallback(async () => {
    try {
      await cardService.deleteCard(type, id)
      navigate(-1)
    } catch (err) {
      console.error('Delete failed:', err)
    }
  }, [type, id, navigate])

  const handleEditClick = useCallback(() => {
    setEditModalOpen(true)
  }, [])

  const handleEditClose = useCallback(() => {
    setEditModalOpen(false)
  }, [])

  const handleEditSaved = useCallback(async (result) => {
    setEditModalOpen(false)
    // 重新加载当前卡片数据
    setLoading(true)
    try {
      const fresh = await fetchData(type, id)
      setMainData(fresh)
    } catch (err) {
      console.error('Failed to reload card after edit:', err)
    } finally {
      setLoading(false)
    }
  }, [fetchData, type, id])

  const handleRefresh = useCallback(async () => {
    try {
      const fresh = await fetchData(type, id)
      setMainData(fresh)
    } catch (err) {
      console.error('Failed to refresh card:', err)
    }
  }, [fetchData, type, id])

  // 拖拽分隔线逻辑
  const handleMouseDown = useCallback((e) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  useEffect(() => {
    if (!isDragging) return

    const handleMouseMove = (e) => {
      if (!containerRef.current) return
      const rect = containerRef.current.getBoundingClientRect()
      const x = e.clientX - rect.left
      const ratio = Math.max(20, Math.min(80, (x / rect.width) * 100))
      setSplitRatio(ratio)
    }

    const handleMouseUp = () => {
      setIsDragging(false)
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isDragging])

  if (loading) {
    return (
      <div className={styles.detailPage}>
        <div className={styles.toolbar}>
          <button className={styles.backButton} onClick={handleBack}>← 返回</button>
        </div>
        <div className={styles.loadingState}>加载中...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={styles.detailPage}>
        <div className={styles.toolbar}>
          <button className={styles.backButton} onClick={handleBack}>← 返回</button>
        </div>
        <div className={styles.errorState}>
          <div className={styles.errorTitle}>卡片未找到</div>
          <div className={styles.errorMessage}>{error}</div>
          <button className={styles.backButton} onClick={handleBack}>返回首页</button>
        </div>
      </div>
    )
  }

  if (!mainData) {
    return (
      <div className={styles.detailPage}>
        <div className={styles.toolbar}>
          <button className={styles.backButton} onClick={handleBack}>← 返回</button>
        </div>
        <div className={styles.errorState}>
          <div className={styles.errorTitle}>卡片未找到</div>
          <div className={styles.errorMessage}>404 - 该卡片不存在</div>
          <button className={styles.backButton} onClick={handleBack}>返回首页</button>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.detailPage}>
      <div className={styles.toolbar}>
        <button className={styles.backButton} onClick={handleBack}>← 返回</button>
        {!isSplitMode && mainData && (
          <button className={styles.editButton} onClick={handleEditClick}>
            ✏️ 编辑
          </button>
        )}
        {!isSplitMode && mainData && (
          <button className={styles.deleteButton} onClick={() => setShowDeleteConfirm(true)}>
            🗑️ 删除
          </button>
        )}
        {isSplitMode && (
          <>
            <span className={styles.compareInfo}>
              对比模式: {type} / {compareType}
            </span>
            <button className={styles.closeCompare} onClick={handleCloseCompare}>
              ✕ 关闭对比
            </button>
          </>
        )}
      </div>

      <CreateCardModal
        open={editModalOpen}
        onClose={handleEditClose}
        onCreated={handleEditSaved}
        editType={type}
        editData={mainData}
      />

      {showDeleteConfirm && (
        <div className={styles.deleteOverlay}>
          <div className={styles.deleteDialog}>
            <h3>确认删除</h3>
            <p>确定要删除这个{type === 'problem' ? '题目' : type === 'solution' ? '解法' : '技巧'}卡片吗？此操作不可撤销。</p>
            <div className={styles.deleteDialogButtons}>
              <button className={styles.backButton} onClick={() => setShowDeleteConfirm(false)}>取消</button>
              <button className={styles.deleteConfirmBtn} onClick={handleDelete}>确认删除</button>
            </div>
          </div>
        </div>
      )}

      {isSplitMode ? (
        <div className={styles.splitView} ref={containerRef}>
          <div className={styles.panelLeft} style={{ flex: `${splitRatio}%` }}>
            <CardPanel type={type} data={mainData} onNavigate={handleNavigate} onRefresh={handleRefresh} />
          </div>
          <div
            className={`${styles.divider} ${isDragging ? styles.dividerActive : ''}`}
            onMouseDown={handleMouseDown}
          />
          <div className={styles.panelRight} style={{ flex: `${100 - splitRatio}%` }}>
            {compareData ? (
              <CardPanel type={compareType} data={compareData} onNavigate={handleNavigate} onRefresh={handleRefresh} />
            ) : (
              <div className={styles.loadingState}>加载对比卡片...</div>
            )}
          </div>
        </div>
      ) : (
        <div className={styles.singleCard}>
          <CardPanel type={type} data={mainData} onNavigate={handleNavigate} onRefresh={handleRefresh} />
        </div>
      )}
    </div>
  )
}