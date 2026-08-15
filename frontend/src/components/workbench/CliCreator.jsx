import { useState, useRef, useEffect } from 'react'
import styles from './CliCreator.module.css'

const commandLog = [
    { type: 'system', text: 'algoMate-cli v0.1.0' },
    { type: 'system', text: '✓ 已加载 47 张卡片 · 5 项待复习' },
    { type: 'prompt', text: '/new technique' },
    { type: 'input', text: '› 卡片标题: 滑动窗口最大值模板' },
    { type: 'input', text: '› 选择分类: 1) 双指针 2) 二分查找 3) 滑动窗口 ...' },
    { type: 'input', text: '› 难度: 中等 · 标签: #模板 #双指针' },
    { type: 'success', text: '✓ 技巧卡片已创建 (id=20)' },
    { type: 'system', text: '输入 /help 查看命令...' },
]

export default function CliCreator({ onCreateCard }) {
    const [inputValue, setInputValue] = useState('')
    const logRef = useRef(null)

    useEffect(() => {
        if (logRef.current) {
            logRef.current.scrollTop = logRef.current.scrollHeight
        }
    }, [])

    const handleSubmit = (e) => {
        e.preventDefault()
        const val = inputValue.trim()
        if (!val) return

        if (val === '/new' || val.startsWith('/new ')) {
            if (onCreateCard) onCreateCard()
        }
        setInputValue('')
    }

    return (
        <div className={styles.cliContainer}>
            <div className={styles.cliLog} ref={logRef}>
                {commandLog.map((entry, idx) => (
                    <div key={idx} className={`${styles.logLine} ${styles[entry.type]}`}>
                        {entry.type === 'prompt' && <span className={styles.promptSymbol}>$</span>}
                        {entry.type !== 'prompt' && entry.type !== 'input' && <span className={styles.promptSymbol}>$</span>}
                        <span className={styles.logText}>{entry.text}</span>
                    </div>
                ))}
            </div>
            <form className={styles.cliInput} onSubmit={handleSubmit}>
                <span className={styles.inputPrompt}>$</span>
                <input
                    type="text"
                    className={styles.inputField}
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    placeholder="输入 /new 创建卡片，/help 查看命令..."
                />
            </form>
        </div>
    )
}
