import { useRef, useEffect, useCallback } from 'react'
import { EditorView, keymap, placeholder as placeholderExt } from '@codemirror/view'
import { EditorState } from '@codemirror/state'
import { defaultKeymap, indentWithTab } from '@codemirror/commands'
import { python } from '@codemirror/lang-python'
import { syntaxHighlighting, defaultHighlightStyle } from '@codemirror/language'

// 暗色主题样式
const darkTheme = EditorView.theme({
    '&': {
        background: 'var(--color-bg-elevated)',
        color: '#d4d4d4',
        fontSize: '0.85rem',
        fontFamily: "'Fira Code', 'SF Mono', 'Consolas', monospace",
    },
    '&.cm-focused': {
        outline: 'none',
    },
    '.cm-content': {
        caretColor: '#d4d4d4',
        fontFamily: "'Fira Code', 'SF Mono', 'Consolas', monospace",
        lineHeight: 1.6,
        padding: '10px 12px',
    },
    '.cm-cursor': {
        borderLeftColor: '#d4d4d4',
    },
    '.cm-selectionBackground, .cm-focused .cm-selectionBackground': {
        background: 'rgba(114, 145, 255, 0.15)',
    },
    '.cm-gutters': {
        display: 'none',
    },
    '.cm-scroller': {
        fontFamily: "'Fira Code', 'SF Mono', 'Consolas', monospace",
        lineHeight: 1.6,
    },
    '&.cm-editor': {
        borderRadius: 'var(--radius-sm, 4px)',
        border: '1px solid var(--border-color)',
    },
    '&.cm-editor.cm-focused': {
        borderColor: 'var(--color-primary)',
    },
    '.cm-placeholder': {
        color: '#666',
        fontFamily: "'Fira Code', 'SF Mono', 'Consolas', monospace",
        fontSize: '0.85rem',
        padding: '10px 12px',
    },
})

export default function CodeEditor({ value = '', onChange, placeholder: placeholderText, rows = 5, readOnly = false }) {
    const containerRef = useRef(null)
    const viewRef = useRef(null)
    const onChangeRef = useRef(onChange)

    // 保持 onChange 引用最新
    useEffect(() => {
        onChangeRef.current = onChange
    }, [onChange])

    const minHeight = rows * 1.6 * 14 + 20

    useEffect(() => {
        if (!containerRef.current) return

        const updateListener = EditorView.updateListener.of((update) => {
            if (update.docChanged) {
                onChangeRef.current?.(update.state.doc.toString())
            }
        })

        const extensions = [
            python(),
            keymap.of([...defaultKeymap, indentWithTab]),
            darkTheme,
            syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
            updateListener,
            EditorView.lineWrapping,
            EditorView.contentAttributes.of({ 'aria-label': placeholderText || '代码编辑器' }),
        ]

        if (placeholderText) {
            extensions.push(placeholderExt(placeholderText))
        }

        if (readOnly) {
            extensions.push(EditorView.editable.of(false))
        }

        const state = EditorState.create({
            doc: value || '',
            extensions,
        })

        const view = new EditorView({
            state,
            parent: containerRef.current,
        })

        viewRef.current = view

        return () => {
            view.destroy()
            viewRef.current = null
        }
    }, []) // eslint-disable-line react-hooks/exhaustive-deps

    // 外部 value 变化时同步到编辑器（避免循环）
    useEffect(() => {
        const view = viewRef.current
        if (!view) return
        const current = view.state.doc.toString()
        if (value !== current) {
            view.dispatch({
                changes: { from: 0, to: current.length, insert: value || '' },
            })
        }
    }, [value])

    return (
        <div
            ref={containerRef}
            style={{
                minHeight: minHeight + 'px',
            }}
        />
    )
}