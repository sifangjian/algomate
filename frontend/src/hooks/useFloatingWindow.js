import { useState, useRef, useCallback, useEffect } from 'react'

const PADDING = { top: 8, right: 8, bottom: 8, left: 8 }

function clamp(val, min, max) {
    return Math.max(min, Math.min(val, max))
}

function clampPosition(pos, size, vw, vh) {
    return {
        x: clamp(pos.x, PADDING.left, vw - size.width - PADDING.right),
        y: clamp(pos.y, PADDING.top, vh - size.height - PADDING.bottom),
    }
}

function clampSize(newSize, newPos, vw, vh, minSize) {
    return {
        width: clamp(newSize.width, minSize.width, vw - newPos.x - PADDING.right),
        height: clamp(newSize.height, minSize.height, vh - newPos.y - PADDING.bottom),
    }
}

/**
 * @param {object} options
 * @param {{ x: number, y: number }} options.defaultPosition
 * @param {{ width: number, height: number }} options.defaultSize
 * @param {{ width: number, height: number }} [options.minSize]
 * @param {boolean} [options.enabled]
 */
export default function useFloatingWindow({
    defaultPosition,
    defaultSize,
    minSize = { width: 360, height: 300 },
    enabled = true,
}) {
    const panelRef = useRef(null)
    const [position, setPosition] = useState(defaultPosition)
    const [size, setSize] = useState(defaultSize)
    const [isDragging, setIsDragging] = useState(false)
    const [isResizing, setIsResizing] = useState(false)

    // 用 ref 存储拖拽/resize 的中间状态，避免每个 mousemove 都触发 React setState
    const dragState = useRef(null)
    const resizeState = useRef(null)

    // 同步 defaultPosition/defaultSize 变化
    const prevDefaultRef = useRef({ pos: defaultPosition, size: defaultSize })
    useEffect(() => {
        const prev = prevDefaultRef.current
        if (
            prev.pos.x !== defaultPosition.x || prev.pos.y !== defaultPosition.y ||
            prev.size.width !== defaultSize.width || prev.size.height !== defaultSize.height
        ) {
            setPosition(defaultPosition)
            setSize(defaultSize)
            prevDefaultRef.current = { pos: defaultPosition, size: defaultSize }
        }
    }, [defaultPosition, defaultSize])

    // 窗口 resize 时重新约束位置
    useEffect(() => {
        const handleResize = () => {
            const vw = window.innerWidth
            const vh = window.innerHeight
            setPosition(prev => clampPosition(prev, size, vw, vh))
        }
        window.addEventListener('resize', handleResize)
        return () => window.removeEventListener('resize', handleResize)
    }, [size])

    // 窗口失焦时取消操作
    useEffect(() => {
        const handleBlur = () => {
            if (dragState.current) finishDrag()
            if (resizeState.current) finishResize()
        }
        window.addEventListener('blur', handleBlur)
        return () => window.removeEventListener('blur', handleBlur)
    }, [])

    // ---- 拖拽逻辑 ----
    const finishDrag = useCallback(() => {
        const st = dragState.current
        if (!st) return
        const el = panelRef.current
        if (el) {
            const x = parseInt(el.style.left) || st.startPos.x
            const y = parseInt(el.style.top) || st.startPos.y
            setPosition({ x, y })
        }
        dragState.current = null
        setIsDragging(false)
        document.body.style.userSelect = ''
        document.body.style.cursor = ''
    }, [])

    const handleDragStart = useCallback((e) => {
        if (!enabled) return
        e.preventDefault()
        const clientX = e.touches ? e.touches[0].clientX : e.clientX
        const clientY = e.touches ? e.touches[0].clientY : e.clientY

        const el = panelRef.current
        if (!el) return
        const startPos = { x: parseInt(el.style.left), y: parseInt(el.style.top) }

        dragState.current = { startMouse: { x: clientX, y: clientY }, startPos }
        setIsDragging(true)
        document.body.style.userSelect = 'none'
        document.body.style.cursor = 'grabbing'
    }, [enabled])

    // ---- Resize 逻辑 ----
    const finishResize = useCallback(() => {
        const st = resizeState.current
        if (!st) return
        const el = panelRef.current
        if (el) {
            setSize({
                width: parseInt(el.style.width) || st.startSize.width,
                height: parseInt(el.style.height) || st.startSize.height,
            })
            setPosition({
                x: parseInt(el.style.left) || st.startPos.x,
                y: parseInt(el.style.top) || st.startPos.y,
            })
        }
        resizeState.current = null
        setIsResizing(false)
        document.body.style.userSelect = ''
        document.body.style.cursor = ''
    }, [])

    const createResizeStart = useCallback((direction) => (e) => {
        if (!enabled) return
        e.preventDefault()
        e.stopPropagation()
        const clientX = e.touches ? e.touches[0].clientX : e.clientX
        const clientY = e.touches ? e.touches[0].clientY : e.clientY

        const el = panelRef.current
        if (!el) return
        const startPos = { x: parseInt(el.style.left), y: parseInt(el.style.top) }
        const startSize = { width: parseInt(el.style.width), height: parseInt(el.style.height) }

        resizeState.current = { direction, startMouse: { x: clientX, y: clientY }, startPos, startSize }
        setIsResizing(true)
        document.body.style.userSelect = 'none'

        const cursors = { nw: 'nw-resize', ne: 'ne-resize', sw: 'sw-resize', se: 'se-resize' }
        document.body.style.cursor = cursors[direction] || 'se-resize'
    }, [enabled])

    // ---- 全局 mousemove/mouseup ----
    useEffect(() => {
        const handleMove = (e) => {
            const clientX = e.touches ? e.touches[0].clientX : e.clientX
            const clientY = e.touches ? e.touches[0].clientY : e.clientY

            if (dragState.current) {
                const { startMouse, startPos } = dragState.current
                const dx = clientX - startMouse.x
                const dy = clientY - startMouse.y
                const vw = window.innerWidth
                const vh = window.innerHeight
                const el = panelRef.current
                if (!el) return
                const w = parseInt(el.style.width) || size.width
                const h = parseInt(el.style.height) || size.height
                const newPos = clampPosition({ x: startPos.x + dx, y: startPos.y + dy }, { width: w, height: h }, vw, vh)
                el.style.left = `${newPos.x}px`
                el.style.top = `${newPos.y}px`
                return
            }

            if (resizeState.current) {
                const { direction, startMouse, startPos, startSize } = resizeState.current
                const dx = clientX - startMouse.x
                const dy = clientY - startMouse.y
                const vw = window.innerWidth
                const vh = window.innerHeight
                const el = panelRef.current
                if (!el) return

                let newW = startSize.width
                let newH = startSize.height
                let newX = startPos.x
                let newY = startPos.y

                if (direction.includes('e')) newW = startSize.width + dx
                if (direction.includes('s')) newH = startSize.height + dy
                if (direction.includes('w')) {
                    newW = startSize.width - dx
                    newX = startPos.x + dx
                }
                if (direction.includes('n')) {
                    newH = startSize.height - dy
                    newY = startPos.y + dy
                }

                // 约束最小尺寸
                if (newW < minSize.width) {
                    if (direction.includes('w')) newX = startPos.x + startSize.width - minSize.width
                    newW = minSize.width
                }
                if (newH < minSize.height) {
                    if (direction.includes('n')) newY = startPos.y + startSize.height - minSize.height
                    newH = minSize.height
                }

                // 约束不超出视口
                const clamped = clampSize({ width: newW, height: newH }, { x: newX, y: newY }, vw, vh, minSize)
                if (direction.includes('w')) {
                    newX = newX + (newW - clamped.width)
                }
                if (direction.includes('n')) {
                    newY = newY + (newH - clamped.height)
                }

                el.style.width = `${clamped.width}px`
                el.style.height = `${clamped.height}px`
                el.style.left = `${newX}px`
                el.style.top = `${newY}px`
            }
        }

        const handleUp = () => {
            if (dragState.current) finishDrag()
            if (resizeState.current) finishResize()
        }

        document.addEventListener('mousemove', handleMove)
        document.addEventListener('mouseup', handleUp)
        document.addEventListener('touchmove', handleMove, { passive: false })
        document.addEventListener('touchend', handleUp)
        return () => {
            document.removeEventListener('mousemove', handleMove)
            document.removeEventListener('mouseup', handleUp)
            document.removeEventListener('touchmove', handleMove)
            document.removeEventListener('touchend', handleUp)
        }
    }, [finishDrag, finishResize, size, minSize])

    return {
        position,
        size,
        isDragging,
        isResizing,
        panelRef,
        bindDrag: {
            onMouseDown: handleDragStart,
            onTouchStart: handleDragStart,
        },
        createResizeStart,
    }
}
