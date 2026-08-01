import { useMemo } from 'react'

// Python 关键字高亮
const KEYWORDS = new Set([
    'def', 'return', 'if', 'else', 'elif', 'for', 'while', 'in', 'not', 'and', 'or',
    'True', 'False', 'None', 'class', 'import', 'from', 'as', 'with', 'try', 'except',
    'finally', 'raise', 'pass', 'break', 'continue', 'lambda', 'yield', 'async', 'await',
    'global', 'nonlocal', 'del', 'assert', 'is', 'print',
])

// 简单 Python 语法高亮
function highlightPython(code) {
    // 按行处理，保留换行
    const lines = code.split('\n')
    return lines.map((line, lineIdx) => {
        const tokens = []
        let i = 0
        while (i < line.length) {
            // 注释
            if (line[i] === '#') {
                tokens.push(
                    <span key={`${lineIdx}-${i}`} style={{ color: '#6a9955' }}>
                        {line.slice(i)}
                    </span>
                )
                i = line.length
                break
            }

            // 字符串 - 单引号
            if (line[i] === "'" || line[i] === '"') {
                const quote = line[i]
                let j = i + 1
                while (j < line.length && line[j] !== quote) {
                    if (line[j] === '\\') j++
                    j++
                }
                j++ // 包含结束引号
                tokens.push(
                    <span key={`${lineIdx}-${i}`} style={{ color: '#ce9178' }}>
                        {line.slice(i, j)}
                    </span>
                )
                i = j
                continue
            }

            // 数字
            if (/\d/.test(line[i]) && (i === 0 || /[\s\(\)\[\]\{\}\+\-\*\/=,;:]/.test(line[i - 1]))) {
                let j = i
                while (j < line.length && /[\d\.]/.test(line[j])) j++
                tokens.push(
                    <span key={`${lineIdx}-${i}`} style={{ color: '#b5cea8' }}>
                        {line.slice(i, j)}
                    </span>
                )
                i = j
                continue
            }

            // 标识符（可能的关键字或函数名）
            if (/[a-zA-Z_]/.test(line[i])) {
                let j = i
                while (j < line.length && /[a-zA-Z0-9_]/.test(line[j])) j++
                const word = line.slice(i, j)
                if (KEYWORDS.has(word)) {
                    tokens.push(
                        <span key={`${lineIdx}-${i}`} style={{ color: '#569cd6' }}>
                            {word}
                        </span>
                    )
                } else if (j < line.length && line[j] === '(') {
                    // 函数调用
                    tokens.push(
                        <span key={`${lineIdx}-${i}`} style={{ color: '#dcdcaa' }}>
                            {word}
                        </span>
                    )
                } else {
                    tokens.push(word)
                }
                i = j
                continue
            }

            // 其他字符
            tokens.push(line[i])
            i++
        }
        return (
            <span key={lineIdx}>
                {tokens}
                {lineIdx < lines.length - 1 && '\n'}
            </span>
        )
    })
}

export default function CodeBlock({ code, language = 'python' }) {
    const highlighted = useMemo(() => {
        if (!code) return null
        return highlightPython(code)
    }, [code])

    if (!code) return null

    return (
        <pre
            style={{
                background: '#1e1e1e',
                borderRadius: 8,
                padding: '14px 16px',
                overflowX: 'auto',
                margin: 0,
                fontFamily: "'SF Mono', 'Fira Code', 'Consolas', monospace",
                fontSize: '0.82rem',
                lineHeight: 1.6,
                color: '#d4d4d4',
                border: '1px solid rgba(255,255,255,0.06)',
                whiteSpace: 'pre',
                wordBreak: 'normal',
            }}
        >
            <code style={{ background: 'none', padding: 0, color: 'inherit' }}>
                {highlighted}
            </code>
        </pre>
    )
}