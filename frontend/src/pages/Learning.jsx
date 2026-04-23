import React, { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

function Learning() {
    const [topics, setTopics] = useState([])
    const [selectedTopic, setSelectedTopic] = useState(null)
    const [selectedConcept, setSelectedConcept] = useState(null)
    const [messages, setMessages] = useState([])
    const [userInput, setUserInput] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [showQuiz, setShowQuiz] = useState(false)
    const [quizQuestions, setQuizQuestions] = useState([])
    const [noteContent, setNoteContent] = useState('')
    const [noteTitle, setNoteTitle] = useState('')
    const [savingNote, setSavingNote] = useState(false)
    const [topicCollapsed, setTopicCollapsed] = useState(false)
    const messagesEndRef = useRef(null)

    useEffect(() => {
        fetchTopics()
    }, [])

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    const fetchTopics = async () => {
        try {
            console.log('开始获取主题...')
            const res = await fetch('/api/learning/topics')
            console.log('API 响应状态:', res.status, res.statusText)
            if (!res.ok) {
                console.error('API 请求失败:', res.status)
                return
            }
            const data = await res.json()
            console.log('获取到的主题数据:', data)
            console.log('categories 字段:', data.categories)
            if (data.categories) {
                setTopics(data.categories)
            } else {
                console.error('数据格式错误：没有 categories 字段', data)
            }
        } catch (error) {
            console.error('获取主题失败:', error)
        }
    }

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    const handleTopicSelect = (category, topic) => {
        setSelectedTopic(topic)
        setSelectedConcept(null)
        setMessages([])
        setShowQuiz(false)
        setNoteContent('')
        setNoteTitle('')
        setTopicCollapsed(true)
    }

    const handleConceptClick = async (concept) => {
        setSelectedConcept(concept)
        setIsLoading(true)
        setMessages([])

        try {
            const res = await fetch(`/api/learning/explain-concept?topic=${encodeURIComponent(selectedTopic)}&concept=${encodeURIComponent(concept)}`)
            const data = await res.json()
            if (data.explanation) {
                setMessages([
                    { role: 'assistant', content: data.explanation }
                ])
            }
        } catch (error) {
            console.error('获取概念解释失败:', error)
            setMessages([
                { role: 'assistant', content: '抱歉，获取概念解释失败了。' }
            ])
        } finally {
            setIsLoading(false)
        }
    }

    const handleSendMessage = async () => {
        if (!userInput.trim() || isLoading) return

        const userMessage = userInput.trim()
        setUserInput('')
        setMessages(prev => [...prev, { role: 'user', content: userMessage }])
        setIsLoading(true)

        const assistantMessage = { role: 'assistant', content: '' }
        setMessages(prev => [...prev, assistantMessage])

        try {
            const res = await fetch('/api/learning/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    topic: selectedTopic,
                    question: userMessage,
                    history: messages.map(m => ({ role: m.role, content: m.content }))
                })
            })

            if (!res.ok) {
                throw new Error(`HTTP error: ${res.status}`)
            }

            const reader = res.body.getReader()
            const decoder = new TextDecoder()

            while (true) {
                const { done, value } = await reader.read()
                if (done) break

                const chunk = decoder.decode(value)
                const lines = chunk.split('\n')

                for (const line of lines) {
                    if (line.startsWith('data: ') && line !== 'data: [DONE]') {
                        try {
                            const data = JSON.parse(line.slice(6))
                            if (data.content) {
                                assistantMessage.content += data.content
                                setMessages(prev => {
                                    const newMessages = [...prev]
                                    newMessages[newMessages.length - 1] = { ...assistantMessage }
                                    return newMessages
                                })
                            }
                            if (data.error) {
                                assistantMessage.content = `错误: ${data.error}`
                                setMessages(prev => {
                                    const newMessages = [...prev]
                                    newMessages[newMessages.length - 1] = { ...assistantMessage }
                                    return newMessages
                                })
                            }
                        } catch (e) {
                            console.warn('Parse error:', e)
                        }
                    }
                }
            }
        } catch (error) {
            console.error('发送消息失败:', error)
            assistantMessage.content = '抱歉，发送消息失败了。'
            setMessages(prev => {
                const newMessages = [...prev]
                newMessages[newMessages.length - 1] = { ...assistantMessage }
                return newMessages
            })
        } finally {
            setIsLoading(false)
        }
    }

    const handleStartQuiz = async () => {
        setShowQuiz(true)
        setIsLoading(true)

        try {
            const res = await fetch('/api/learning/generate-quiz', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic: selectedTopic })
            })
            const data = await res.json()
            setQuizQuestions(data.questions || [])
        } catch (error) {
            console.error('生成测验失败:', error)
        } finally {
            setIsLoading(false)
        }
    }

    const handleSaveNote = async () => {
        if (!noteTitle.trim() || !noteContent.trim()) {
            alert('请填写笔记标题和内容')
            return
        }

        setSavingNote(true)
        try {
            const algorithmType = selectedTopic || '其他'
            const res = await fetch('/api/learning/save-note', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: noteTitle,
                    content: noteContent,
                    algorithm_type: algorithmType,
                    difficulty: '中等',
                    summary: noteContent.substring(0, 100)
                })
            })
            const data = await res.json()
            if (data.id) {
                alert('笔记保存成功！')
                setNoteTitle('')
                setNoteContent('')
            } else {
                alert(data.error || '保存失败')
            }
        } catch (error) {
            console.error('保存笔记失败:', error)
            alert('保存失败')
        } finally {
            setSavingNote(false)
        }
    }

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 40px)' }}>
            <div className="page-header" style={{ flexShrink: 0 }}>
                <h2>学习中心</h2>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', flex: 1, minHeight: 0 }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                    <div className="card" style={{ flexShrink: 0 }}>
                        {topicCollapsed ? (
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                    <span style={{ fontSize: '1.2rem' }}>📚</span>
                                    <span style={{ fontWeight: 'bold', color: '#667eea' }}>{selectedTopic}</span>
                                    <span style={{ fontSize: '0.85rem', color: '#888' }}>已选择</span>
                                </div>
                                <button
                                    onClick={() => setTopicCollapsed(false)}
                                    style={{
                                        padding: '6px 12px',
                                        fontSize: '0.85rem',
                                        background: '#667eea',
                                        color: 'white',
                                        border: 'none',
                                        borderRadius: '5px',
                                        cursor: 'pointer'
                                    }}
                                >
                                    ☰ 展开主题列表
                                </button>
                            </div>
                        ) : (
                            <>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <div className="card-title">选择学习主题</div>
                                    {selectedTopic && (
                                        <button
                                            onClick={() => setTopicCollapsed(true)}
                                            style={{
                                                padding: '4px 10px',
                                                fontSize: '0.8rem',
                                                background: '#f0f0f0',
                                                color: '#666',
                                                border: '1px solid #ddd',
                                                borderRadius: '5px',
                                                cursor: 'pointer'
                                            }}
                                        >
                                            折叠 ↑
                                        </button>
                                    )}
                                </div>
                                {topics.length === 0 ? (
                                    <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
                                        <p>加载中...</p>
                                        <p style={{ fontSize: '0.85rem' }}>请检查控制台是否有错误信息</p>
                                    </div>
                                ) : (
                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginTop: '10px' }}>
                                        {topics.map(category => (
                                            <div key={category.id} style={{ width: '100%', marginBottom: '10px' }}>
                                                <div style={{ fontWeight: 'bold', marginBottom: '5px', color: '#667eea' }}>
                                                    {category.icon} {category.name}
                                                </div>
                                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                                                    {category.topics.map(topic => (
                                                        <button
                                                            key={topic}
                                                            onClick={() => handleTopicSelect(category.name, topic)}
                                                            style={{
                                                                padding: '4px 10px',
                                                                fontSize: '0.85rem',
                                                                border: selectedTopic === topic ? '2px solid #667eea' : '1px solid #ddd',
                                                                borderRadius: '15px',
                                                                background: selectedTopic === topic ? '#667eea' : 'white',
                                                                color: selectedTopic === topic ? 'white' : '#333',
                                                                cursor: 'pointer'
                                                            }}
                                                        >
                                                            {topic}
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </>
                        )}
                    </div>

                    {selectedTopic && (
                        <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minHeight: 0 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                                <div className="card-title" style={{ margin: 0 }}>
                                    📚 {selectedTopic} - AI 讲解与问答
                                </div>
                                <button
                                    onClick={handleStartQuiz}
                                    style={{
                                        padding: '6px 12px',
                                        fontSize: '0.85rem',
                                        background: '#764ba2',
                                        color: 'white',
                                        border: 'none',
                                        borderRadius: '5px',
                                        cursor: 'pointer'
                                    }}
                                >
                                    生成小测验
                                </button>
                            </div>

                            {!showQuiz ? (
                                <>
                                    <div style={{ height: '450px', overflowY: 'auto', marginBottom: '15px', padding: '10px', background: '#f5f5f5', borderRadius: '8px' }}>
                                        {messages.length === 0 && !isLoading && (
                                            <div style={{ textAlign: 'center', color: '#666', padding: '40px 0' }}>
                                                <div style={{ fontSize: '48px', marginBottom: '10px' }}>🤔</div>
                                                <p>选择一个概念开始学习，或者直接问我问题</p>
                                                {selectedTopic && (
                                                    <div style={{ marginTop: '15px' }}>
                                                        <p style={{ fontSize: '0.9rem', color: '#888' }}>试试这样问：</p>
                                                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px', justifyContent: 'center' }}>
                                                            {['给我讲讲原理', '有什么应用场景', '代码怎么实现', '和XXX有什么区别'].map(q => (
                                                                <button
                                                                    key={q}
                                                                    onClick={() => setUserInput(q)}
                                                                    style={{
                                                                        padding: '4px 10px',
                                                                        fontSize: '0.8rem',
                                                                        border: '1px solid #ddd',
                                                                        borderRadius: '10px',
                                                                        background: 'white',
                                                                        cursor: 'pointer'
                                                                    }}
                                                                >
                                                                    {q}
                                                                </button>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                        {messages.map((msg, index) => (
                                            <div key={index} style={{ marginBottom: '15px' }}>
                                                <div style={{
                                                    display: 'flex',
                                                    justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start'
                                                }}>
                                                    <div style={{
                                                        maxWidth: '80%',
                                                        padding: '10px 15px',
                                                        borderRadius: '10px',
                                                        background: msg.role === 'user' ? '#818cf8' : 'white',
                                                        color: msg.role === 'user' ? '#ffffff' : '#333',
                                                        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                                                        overflowWrap: 'break-word',
                                                        wordBreak: 'break-word'
                                                    }}>
                                                        <div style={{ maxWidth: '100%', overflowX: 'auto' }}>
                                                            <ReactMarkdown
                                                                remarkPlugins={[remarkGfm]}
                                                                components={{
                                                                    h1: ({ children }) => (
                                                                        <h1 style={{ fontSize: '1.35rem', fontWeight: '600', marginBottom: '12px', marginTop: '16px', color: 'inherit', borderBottom: '2px solid #667eea', paddingBottom: '6px' }}>
                                                                            {children}
                                                                        </h1>
                                                                    ),
                                                                    h2: ({ children }) => (
                                                                        <h2 style={{ fontSize: '1.15rem', fontWeight: '600', marginBottom: '10px', marginTop: '14px', color: 'inherit', borderBottom: '1px solid #e8e8e8', paddingBottom: '4px' }}>
                                                                            {children}
                                                                        </h2>
                                                                    ),
                                                                    h3: ({ children }) => (
                                                                        <h3 style={{ fontSize: '1rem', fontWeight: '600', marginBottom: '8px', marginTop: '12px', color: 'inherit' }}>
                                                                            {children}
                                                                        </h3>
                                                                    ),
                                                                    h4: ({ children }) => (
                                                                        <h4 style={{ fontSize: '0.9rem', fontWeight: '600', marginBottom: '6px', marginTop: '10px', color: 'inherit' }}>
                                                                            {children}
                                                                        </h4>
                                                                    ),
                                                                    p: ({ children }) => (
                                                                        <p style={{ marginBottom: '10px', lineHeight: '1.7', color: 'inherit' }}>
                                                                            {children}
                                                                        </p>
                                                                    ),
                                                                    ul: ({ children }) => (
                                                                        <ul style={{ marginBottom: '10px', paddingLeft: '20px', color: 'inherit' }}>
                                                                            {children}
                                                                        </ul>
                                                                    ),
                                                                    ol: ({ children }) => (
                                                                        <ol style={{ marginBottom: '10px', paddingLeft: '20px', color: 'inherit' }}>
                                                                            {children}
                                                                        </ol>
                                                                    ),
                                                                    li: ({ children }) => (
                                                                        <li style={{ marginBottom: '4px', lineHeight: '1.6', color: 'inherit' }}>
                                                                            {children}
                                                                        </li>
                                                                    ),
                                                                    blockquote: ({ children }) => (
                                                                        <blockquote style={{ borderLeft: '3px solid #667eea', margin: '12px 0', padding: '10px 16px', background: '#f8f9fa', borderRadius: '0 4px 4px 0', color: '#555' }}>
                                                                            {children}
                                                                        </blockquote>
                                                                    ),
                                                                    table: ({ children }) => (
                                                                        <table style={{ borderCollapse: 'collapse', width: '100%', margin: '12px 0', fontSize: '0.9rem' }}>
                                                                            {children}
                                                                        </table>
                                                                    ),
                                                                    thead: ({ children }) => (
                                                                        <thead style={{ background: '#f5f5f7' }}>
                                                                            {children}
                                                                        </thead>
                                                                    ),
                                                                    th: ({ children }) => (
                                                                        <th style={{ border: '1px solid #e0e0e0', padding: '10px 14px', textAlign: 'left', fontWeight: '600', color: '#333' }}>
                                                                            {children}
                                                                        </th>
                                                                    ),
                                                                    td: ({ children }) => (
                                                                        <td style={{ border: '1px solid #e8e8e8', padding: '10px 14px', color: '#444' }}>
                                                                            {children}
                                                                        </td>
                                                                    ),
                                                                    tr: ({ children }) => (
                                                                        <tr style={{ background: '#fff' }}>
                                                                            {children}
                                                                        </tr>
                                                                    ),
                                                                    code: ({ node, inline, className, children, ...props }) => {
                                                                        if (inline) {
                                                                            return (
                                                                                <code style={{ background: '#f0f0f5', padding: '2px 6px', borderRadius: '3px', fontSize: '0.85em', color: '#667eea', fontFamily: "'Fira Code', monospace" }}>
                                                                                    {children}
                                                                                </code>
                                                                            )
                                                                        }
                                                                        return (
                                                                            <pre style={{ background: '#1e1e2e', color: '#e0e0e0', padding: '14px', borderRadius: '6px', overflow: 'auto', margin: '12px 0', fontSize: '0.85rem' }}>
                                                                                <code style={{ fontFamily: "'Fira Code', 'Consolas', monospace" }} {...props}>{children}</code>
                                                                            </pre>
                                                                        )
                                                                    },
                                                                    a: ({ children, href }) => (
                                                                        <a href={href} style={{ color: '#667eea', textDecoration: 'none', borderBottom: '1px dashed #667eea' }} target="_blank" rel="noopener noreferrer">
                                                                            {children}
                                                                        </a>
                                                                    ),
                                                                    hr: () => (
                                                                        <hr style={{ border: 'none', height: '1px', background: '#e0e0e0', margin: '16px 0' }} />
                                                                    ),
                                                                    strong: ({ children }) => (
                                                                        <strong style={{ fontWeight: '600' }}>
                                                                            {children}
                                                                        </strong>
                                                                    )
                                                                }}
                                                            >
                                                                {msg.content}
                                                            </ReactMarkdown>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                        {isLoading && (
                                            <div style={{ textAlign: 'center', padding: '20px' }}>
                                                <span style={{ color: '#667eea' }}>AI 正在思考...</span>
                                            </div>
                                        )}
                                        <div ref={messagesEndRef} />
                                    </div>

                                    <div style={{ display: 'flex', gap: '10px' }}>
                                        <input
                                            type="text"
                                            value={userInput}
                                            onChange={(e) => setUserInput(e.target.value)}
                                            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                                            placeholder="输入你的问题..."
                                            style={{
                                                flex: 1,
                                                padding: '10px 15px',
                                                border: '1px solid #ddd',
                                                borderRadius: '20px',
                                                fontSize: '0.95rem',
                                                outline: 'none'
                                            }}
                                        />
                                        <button
                                            onClick={handleSendMessage}
                                            disabled={isLoading || !userInput.trim()}
                                            style={{
                                                padding: '10px 20px',
                                                background: '#667eea',
                                                color: 'white',
                                                border: 'none',
                                                borderRadius: '20px',
                                                cursor: isLoading || !userInput.trim() ? 'not-allowed' : 'pointer',
                                                opacity: isLoading || !userInput.trim() ? 0.6 : 1
                                            }}
                                        >
                                            发送
                                        </button>
                                    </div>
                                </>
                            ) : (
                                <div style={{ flex: 1, overflowY: 'auto' }}>
                                    <div style={{ marginBottom: '15px' }}>
                                        <button
                                            onClick={() => setShowQuiz(false)}
                                            style={{
                                                padding: '5px 10px',
                                                fontSize: '0.85rem',
                                                border: '1px solid #ddd',
                                                borderRadius: '5px',
                                                background: 'white',
                                                cursor: 'pointer'
                                            }}
                                        >
                                            ← 返回对话
                                        </button>
                                    </div>
                                    {quizQuestions.length === 0 && !isLoading && (
                                        <p style={{ color: '#666', textAlign: 'center' }}>暂无测验题目</p>
                                    )}
                                    {quizQuestions.map((q, index) => (
                                        <div key={index} style={{ marginBottom: '20px', padding: '15px', background: '#f5f5f5', borderRadius: '8px' }}>
                                            <div style={{ fontWeight: 'bold', marginBottom: '10px' }}>
                                                [{q.question_type}] {q.content}
                                            </div>
                                            {q.question_type === '选择题' && q.options && (
                                                <div style={{ marginLeft: '20px' }}>
                                                    {Object.entries(q.options).map(([key, val]) => (
                                                        <div key={key} style={{ marginBottom: '5px' }}>
                                                            {key}. {val}
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                            {q.answer && (
                                                <div style={{ marginTop: '10px', padding: '10px', background: '#e8f5e9', borderRadius: '5px' }}>
                                                    <strong>答案：</strong>{q.answer}
                                                </div>
                                            )}
                                            {q.explanation && (
                                                <div style={{ marginTop: '10px', fontSize: '0.9rem', color: '#666' }}>
                                                    <strong>解析：</strong>{q.explanation}
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                    {isLoading && <p style={{ textAlign: 'center', color: '#667eea' }}>生成中...</p>}
                                </div>
                            )}
                        </div>
                    )}
                </div>

                <div className="card" style={{ display: 'flex', flexDirection: 'column', minHeight: 0 }}>
                    <div className="card-title">📝 笔记区</div>
                    <p style={{ fontSize: '0.85rem', color: '#666', marginTop: '5px' }}>
                        在这里记录学习心得、重点内容和代码片段
                    </p>

                    <input
                        type="text"
                        value={noteTitle}
                        onChange={(e) => setNoteTitle(e.target.value)}
                        placeholder="笔记标题"
                        style={{
                            padding: '10px',
                            border: '1px solid #ddd',
                            borderRadius: '5px',
                            marginBottom: '10px',
                            fontSize: '0.95rem'
                        }}
                    />

                    <textarea
                        value={noteContent}
                        onChange={(e) => setNoteContent(e.target.value)}
                        placeholder="在这里记录笔记...

可以包括：
- 核心原理理解
- 自己的思考
- 代码实现要点
- 常见错误和注意事项
- 相关知识点对比"
                        style={{
                            flex: 1,
                            padding: '10px',
                            border: '1px solid #ddd',
                            borderRadius: '5px',
                            fontSize: '0.95rem',
                            fontFamily: 'monospace',
                            resize: 'none',
                            minHeight: '200px'
                        }}
                    />

                    <button
                        onClick={handleSaveNote}
                        disabled={savingNote || !noteTitle.trim() || !noteContent.trim()}
                        style={{
                            marginTop: '10px',
                            padding: '12px',
                            background: savingNote ? '#ccc' : '#4caf50',
                            color: 'white',
                            border: 'none',
                            borderRadius: '5px',
                            fontSize: '1rem',
                            cursor: savingNote ? 'not-allowed' : 'pointer'
                        }}
                    >
                        {savingNote ? '保存中...' : '💾 保存笔记'}
                    </button>

                    {selectedTopic && (
                        <div style={{ marginTop: '15px', padding: '10px', background: '#fff3e0', borderRadius: '5px', fontSize: '0.85rem' }}>
                            <strong>💡 当前学习主题：</strong>{selectedTopic}
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

export default Learning