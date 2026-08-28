import { useState, useRef, useEffect, useCallback } from 'react'
import { activityLogService } from '../../services/activityLogService'
import styles from './ActivityLog.module.css'

/**
 * 格式化日期为 YYYY-MM-DD
 */
function formatDate(date) {
    const y = date.getFullYear()
    const m = String(date.getMonth() + 1).padStart(2, '0')
    const d = String(date.getDate()).padStart(2, '0')
    return `${y}-${m}-${d}`
}

/**
 * 解析后端返回的 naive datetime 字符串（上海时区）为 Date 对象
 * 后端设置 TZ=Asia/Shanghai，datetime.now() 返回上海时间
 * 直接按年月日时分秒构造 Date，避免 new Date() 误当作 UTC 解析
 */
function parseBackendTime(dateStr) {
    if (!dateStr) return new Date()
    const [datePart, timePart] = dateStr.split('T')
    const [y, m, d] = datePart.split('-').map(Number)
    const [h, mi, s] = (timePart || '00:00:00').split(':').map(Number)
    return new Date(y, m - 1, d, h, mi, s)
}

/**
 * 格式化完整时间 HH:MM:SS
 */
function formatFullTime(dateStr) {
    const d = parseBackendTime(dateStr)
    const h = String(d.getHours()).padStart(2, '0')
    const m = String(d.getMinutes()).padStart(2, '0')
    const s = String(d.getSeconds()).padStart(2, '0')
    return `${h}:${m}:${s}`
}

/**
 * 获取日志类型标签文本
 */
function getTypeLabel(type) {
    const labels = {
        auto_create: '创建',
        auto_view: '查看',
        auto_update: '修改',
        manual_note: '随笔',
    }
    return labels[type] || type
}

/**
 * 获取日志类型对应的 CSS 类名
 */
function getTypeClass(type) {
    const map = {
        auto_create: 'autoCreate',
        auto_view: 'autoView',
        auto_update: 'autoUpdate',
        manual_note: 'manualNote',
    }
    return map[type] || ''
}

/**
 * 卡片类型中文标签映射
 */
function getCardTypeLabel(cardType) {
    const labels = {
        problem: '题目',
        solution: '解法',
        technique: '技巧',
    }
    return labels[cardType] || cardType || ''
}

/**
 * 字段名中文标签映射
 */
function getFieldLabel(fieldKey) {
    const labels = {
        title: '标题',
        difficulty: '难度',
        leetcode_link: 'LeetCode 链接',
        tags: '标签',
        notes: '备注',
        video_demo_link: '视频链接',
        name: '名称',
        time_complexity: '时间复杂度',
        space_complexity: '空间复杂度',
        breakthrough: '突破口',
        approach: '思路',
        code: '代码',
        pitfalls: '易错点',
        use_cases: '适用场景',
        code_template: '代码模板',
        memory_anchors: '记忆锚点',
    }
    return labels[fieldKey] || fieldKey
}

/**
 * 渲染修改字段详情
 */
function ChangedFields({ details }) {
    if (!details?.changed_fields) return null
    const fields = details.changed_fields
    const entries = Object.entries(fields)
    if (entries.length === 0) return null

    return (
        <div className={styles.changedFields}>
            {entries.map(([key, change]) => {
                const oldVal = Array.isArray(change.old) ? change.old.join(', ') : String(change.old ?? '(空)')
                const newVal = Array.isArray(change.new) ? change.new.join(', ') : String(change.new ?? '(空)')
                const label = getFieldLabel(key)
                return (
                    <div key={key} className={styles.changedField}>
                        <span className={styles.fieldName}>{label}</span>
                        <span className={styles.fieldOld}>{oldVal}</span>
                        <span className={styles.fieldArrow}>&rarr;</span>
                        <span className={styles.fieldNew}>{newVal}</span>
                    </div>
                )
            })}
        </div>
    )
}

export default function ActivityLog() {
    const [logs, setLogs] = useState([])
    const [loading, setLoading] = useState(true)
    const [currentDate, setCurrentDate] = useState(new Date())
    const [sortOrder, setSortOrder] = useState('asc') // 默认正序：最早在上，最晚在下
    const [inputValue, setInputValue] = useState('')
    const [error, setError] = useState(null)
    const logRef = useRef(null)
    const inputRef = useRef(null)

    // 获取日志数据
    const fetchLogs = useCallback(async () => {
        setLoading(true)
        setError(null)
        try {
            const data = await activityLogService.getLogs({
                dateStr: formatDate(currentDate),
                sortOrder,
            })
            setLogs(data || [])
        } catch (err) {
            setError(err.message || '加载日志失败')
            setLogs([])
        } finally {
            setLoading(false)
        }
    }, [currentDate, sortOrder])

    // 组件挂载和日期/排序变化时重新加载
    useEffect(() => {
        fetchLogs()
    }, [fetchLogs])

    // 自动滚动到底部（显示最新日志）
    useEffect(() => {
        if (logRef.current) {
            logRef.current.scrollTop = logRef.current.scrollHeight
        }
    }, [logs])

    // 日期切换
    const goToPrevDay = () => {
        const prev = new Date(currentDate)
        prev.setDate(prev.getDate() - 1)
        setCurrentDate(prev)
    }

    const goToNextDay = () => {
        const next = new Date(currentDate)
        next.setDate(next.getDate() + 1)
        const today = new Date()
        if (next > today) return
        setCurrentDate(next)
    }

    const goToToday = () => {
        setCurrentDate(new Date())
    }

    // 排序切换
    const toggleSortOrder = () => {
        setSortOrder(prev => prev === 'desc' ? 'asc' : 'desc')
    }

    // 手动添加日志
    const handleSubmit = async (e) => {
        e.preventDefault()
        const val = inputValue.trim()
        if (!val) return

        setInputValue('')
        try {
            await activityLogService.createManualLog(val)
            await fetchLogs()
        } catch (err) {
            setError(err.message || '添加日志失败')
        }
    }

    // 判断是否今天
    const isToday = formatDate(currentDate) === formatDate(new Date())

    return (
        <div className={styles.container}>
            {/* 工具栏：日期导航 + 排序 */}
            <div className={styles.toolbar}>
                <div className={styles.dateNav}>
                    <button className={styles.navBtn} onClick={goToPrevDay}>&lt; 前一天</button>
                    <button className={styles.navBtn} onClick={goToToday} disabled={isToday}>
                        今天
                    </button>
                    <button
                        className={styles.navBtn}
                        onClick={goToNextDay}
                        disabled={isToday}
                    >
                        后一天 &gt;
                    </button>
                    <span className={styles.dateLabel}>
                        {formatDate(currentDate)}
                        {isToday && ' (今天)'}
                    </span>
                </div>
                <button className={styles.sortBtn} onClick={toggleSortOrder}>
                    {sortOrder === 'asc' ? '顺序 &darr;' : '倒序 &uarr;'}
                </button>
            </div>

            {/* 日志列表 */}
            <div className={styles.logList} ref={logRef}>
                {loading ? (
                    <div className={styles.loading}>加载中...</div>
                ) : error ? (
                    <div className={styles.emptyState}>
                        <div>✗ {error}</div>
                        <div style={{ marginTop: 8, fontSize: 11, color: 'var(--text-muted)', cursor: 'pointer' }} onClick={fetchLogs}>
                            点击重试
                        </div>
                    </div>
                ) : logs.length === 0 ? (
                    <div className={styles.emptyState}>
                        <div>暂无日志记录</div>
                        <div style={{ marginTop: 8, color: 'var(--text-muted)' }}>
                            {isToday ? '今天还没有任何操作，开始你的学习之旅吧' : '这一天没有活动记录'}
                        </div>
                    </div>
                ) : (
                    <div className={styles.timeline}>
                        {logs.map((entry) => (
                            <div key={entry.id} className={`${styles.logEntry} ${styles[getTypeClass(entry.type)]}`}>
                                <div className={styles.logDot} />
                                <span className={styles.logTime}>{formatFullTime(entry.created_at)}</span>
                                <div className={styles.logContent}>
                                    <div className={styles.logHeader}>
                                        <span className={`${styles.logTypeTag} ${styles[getTypeClass(entry.type)]}`}>
                                            {getTypeLabel(entry.type)}
                                        </span>
                                        {entry.card_type && entry.card_name && (
                                            <span className={styles.logCardInfo}>
                                                [{getCardTypeLabel(entry.card_type)}] {entry.card_name}
                                            </span>
                                        )}
                                    </div>
                                    <div className={styles.logText}>
                                        {entry.type === 'manual_note'
                                            ? entry.content
                                            : entry.content
                                        }
                                    </div>
                                    {entry.type === 'auto_update' && <ChangedFields details={entry.details} />}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* 输入框 */}
            <div className={styles.inputWrapper}>
                <form className={styles.cliInput} onSubmit={handleSubmit}>
                    <span className={styles.inputPrompt}>$</span>
                    <input
                        ref={inputRef}
                        type="text"
                        className={styles.inputField}
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder="输入日志内容，回车添加..."
                        autoFocus
                        autoComplete="off"
                    />
                </form>
            </div>
        </div>
    )
}