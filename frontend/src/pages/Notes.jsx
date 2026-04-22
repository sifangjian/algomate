import React, { useState, useEffect } from 'react'

const ALGORITHM_TYPES = ['排序', '查找', '图论', '动态规划', '递归', '字符串', '树', '数组', '其他']
const DIFFICULTIES = ['简单', '中等', '困难']

function Notes() {
  const [notes, setNotes] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingNote, setEditingNote] = useState(null)
  const [searchKeyword, setSearchKeyword] = useState('')
  const [filterType, setFilterType] = useState('')
  const [filterDifficulty, setFilterDifficulty] = useState('')
  const [analyzingId, setAnalyzingId] = useState(null)
  const [selectedNote, setSelectedNote] = useState(null)
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    algorithm_type: '其他',
    difficulty: '中等'
  })

  useEffect(() => {
    fetchNotes()
  }, [filterType, filterDifficulty, searchKeyword])

  const fetchNotes = async () => {
    try {
      setLoading(true)
      let url = '/api/notes/'
      const params = new URLSearchParams()
      if (filterType) params.append('algorithm_type', filterType)
      if (filterDifficulty) params.append('difficulty', filterDifficulty)
      if (searchKeyword) params.append('keyword', searchKeyword)
      if (params.toString()) url += '?' + params.toString()

      const res = await fetch(url)
      const data = await res.json()
      setNotes(data.notes || [])
    } catch (error) {
      console.error('获取笔记失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!formData.title || !formData.content) {
      alert('请填写标题和内容')
      return
    }

    try {
      const method = editingNote ? 'PUT' : 'POST'
      const url = editingNote ? `/api/notes/${editingNote.id}` : '/api/notes/'
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })

      if (res.ok) {
        alert(editingNote ? '笔记更新成功' : '笔记创建成功')
        resetForm()
        fetchNotes()
      }
    } catch (error) {
      console.error('保存笔记失败:', error)
      alert('保存失败')
    }
  }

  const handleDelete = async (noteId) => {
    if (!confirm('确定要删除这条笔记吗？')) return

    try {
      const res = await fetch(`/api/notes/${noteId}`, { method: 'DELETE' })
      if (res.ok) {
        alert('删除成功')
        fetchNotes()
        if (selectedNote?.id === noteId) setSelectedNote(null)
      }
    } catch (error) {
      console.error('删除笔记失败:', error)
    }
  }

  const handleAnalyze = async (noteId) => {
    setAnalyzingId(noteId)
    try {
      const res = await fetch(`/api/notes/${noteId}/analyze`, { method: 'POST' })
      const data = await res.json()
      if (res.ok) {
        alert(`AI分析完成！\n算法类型: ${data.analysis.algorithm_type}\n难度: ${data.analysis.difficulty}\n摘要: ${data.analysis.summary}`)
        fetchNotes()
      } else {
        alert(data.error || 'AI分析失败')
      }
    } catch (error) {
      console.error('AI分析失败:', error)
      alert('AI分析失败')
    } finally {
      setAnalyzingId(null)
    }
  }

  const handleEdit = (note) => {
    setEditingNote(note)
    setFormData({
      title: note.title,
      content: note.content,
      algorithm_type: note.algorithm_type,
      difficulty: note.difficulty
    })
    setShowForm(true)
  }

  const resetForm = () => {
    setShowForm(false)
    setEditingNote(null)
    setFormData({ title: '', content: '', algorithm_type: '其他', difficulty: '中等' })
  }

  const getDifficultyColor = (difficulty) => {
    switch (difficulty) {
      case '简单': return '#4caf50'
      case '中等': return '#ff9800'
      case '困难': return '#f44336'
      default: return '#999'
    }
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return ''
    return new Date(dateStr).toLocaleDateString('zh-CN')
  }

  return (
    <div>
      <div className="page-header">
        <h2>笔记管理</h2>
      </div>

      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap' }}>
        <input
          type="text"
          placeholder="搜索笔记..."
          value={searchKeyword}
          onChange={(e) => setSearchKeyword(e.target.value)}
          style={{ flex: '1', minWidth: '200px', padding: '8px 12px', border: '1px solid #ddd', borderRadius: '4px' }}
        />
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          style={{ padding: '8px 12px', border: '1px solid #ddd', borderRadius: '4px' }}
        >
          <option value="">全部类型</option>
          {ALGORITHM_TYPES.map(type => (
            <option key={type} value={type}>{type}</option>
          ))}
        </select>
        <select
          value={filterDifficulty}
          onChange={(e) => setFilterDifficulty(e.target.value)}
          style={{ padding: '8px 12px', border: '1px solid #ddd', borderRadius: '4px' }}
        >
          <option value="">全部难度</option>
          {DIFFICULTIES.map(diff => (
            <option key={diff} value={diff}>{diff}</option>
          ))}
        </select>
        <button className="btn btn-primary" onClick={() => { resetForm(); setShowForm(true); }}>
          新建笔记
        </button>
      </div>

      {showForm && (
        <div className="card">
          <div className="card-title">{editingNote ? '编辑笔记' : '创建新笔记'}</div>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>标题</label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                placeholder="输入笔记标题"
                required
              />
            </div>
            <div className="form-group">
              <label>内容 (支持 Markdown)</label>
              <textarea
                value={formData.content}
                onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                placeholder="输入笔记内容，支持 Markdown 格式"
                style={{ minHeight: '150px' }}
                required
              />
            </div>
            <div style={{ display: 'flex', gap: '15px', flexWrap: 'wrap' }}>
              <div className="form-group" style={{ flex: '1', minWidth: '150px' }}>
                <label>算法类型</label>
                <select
                  value={formData.algorithm_type}
                  onChange={(e) => setFormData({ ...formData, algorithm_type: e.target.value })}
                >
                  {ALGORITHM_TYPES.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>
              <div className="form-group" style={{ flex: '1', minWidth: '150px' }}>
                <label>难度</label>
                <select
                  value={formData.difficulty}
                  onChange={(e) => setFormData({ ...formData, difficulty: e.target.value })}
                >
                  {DIFFICULTIES.map(diff => (
                    <option key={diff} value={diff}>{diff}</option>
                  ))}
                </select>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
              <button type="submit" className="btn btn-primary">
                {editingNote ? '保存修改' : '创建笔记'}
              </button>
              <button type="button" className="btn btn-secondary" onClick={resetForm}>
                取消
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="card">
        <div className="card-title">笔记列表</div>
        {loading ? (
          <p>加载中...</p>
        ) : notes.length === 0 ? (
          <p style={{ color: '#666' }}>暂无笔记</p>
        ) : (
          <div style={{ display: 'grid', gap: '10px' }}>
            {notes.map((note) => (
              <div
                key={note.id}
                style={{
                  padding: '15px',
                  border: '1px solid #eee',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  transition: 'box-shadow 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)'}
                onMouseLeave={(e) => e.currentTarget.style.boxShadow = 'none'}
                onClick={() => setSelectedNote(selectedNote?.id === note.id ? null : note)}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '5px' }}>
                      <h3 style={{ margin: 0, fontSize: '1.1rem' }}>{note.title}</h3>
                      <span style={{
                        backgroundColor: getDifficultyColor(note.difficulty),
                        color: 'white',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontSize: '0.75rem'
                      }}>
                        {note.difficulty}
                      </span>
                      <span style={{
                        backgroundColor: '#e3f2fd',
                        color: '#1976d2',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontSize: '0.75rem'
                      }}>
                        {note.algorithm_type}
                      </span>
                    </div>
                    <p style={{ color: '#666', fontSize: '0.9rem', margin: '5px 0' }}>
                      {note.content.substring(0, 150)}{note.content.length > 150 ? '...' : ''}
                    </p>
                    {note.summary && (
                      <p style={{ color: '#888', fontSize: '0.85rem', fontStyle: 'italic', marginTop: '5px' }}>
                        AI摘要: {note.summary}
                      </p>
                    )}
                    <div style={{ display: 'flex', gap: '15px', fontSize: '0.8rem', color: '#999', marginTop: '8px' }}>
                      <span>创建: {formatDate(note.created_at)}</span>
                      <span>更新: {formatDate(note.updated_at)}</span>
                      {note.mastery_level > 0 && <span>掌握度: {note.mastery_level}%</span>}
                      {note.review_count > 0 && <span>复习: {note.review_count}次</span>}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '5px', marginLeft: '10px' }} onClick={(e) => e.stopPropagation()}>
                    <button
                      className="btn btn-primary"
                      style={{ padding: '5px 10px', fontSize: '0.8rem' }}
                      onClick={() => handleAnalyze(note.id)}
                      disabled={analyzingId === note.id}
                    >
                      {analyzingId === note.id ? '分析中...' : 'AI分析'}
                    </button>
                    <button
                      className="btn btn-secondary"
                      style={{ padding: '5px 10px', fontSize: '0.8rem' }}
                      onClick={() => handleEdit(note)}
                    >
                      编辑
                    </button>
                    <button
                      className="btn btn-secondary"
                      style={{ padding: '5px 10px', fontSize: '0.8rem', backgroundColor: '#f44336' }}
                      onClick={() => handleDelete(note.id)}
                    >
                      删除
                    </button>
                  </div>
                </div>

                {selectedNote?.id === note.id && (
                  <div style={{ marginTop: '15px', paddingTop: '15px', borderTop: '1px solid #eee' }}>
                    <h4 style={{ marginBottom: '10px' }}>笔记详情</h4>
                    <pre style={{
                      backgroundColor: '#f5f5f5',
                      padding: '15px',
                      borderRadius: '4px',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                      fontSize: '0.9rem',
                      lineHeight: '1.6'
                    }}>
                      {note.content}
                    </pre>
                    {note.tags && note.tags.length > 0 && (
                      <div style={{ display: 'flex', gap: '5px', marginTop: '10px', flexWrap: 'wrap' }}>
                        {note.tags.map((tag, idx) => (
                          <span key={idx} style={{
                            backgroundColor: '#e8f5e9',
                            color: '#2e7d32',
                            padding: '2px 8px',
                            borderRadius: '4px',
                            fontSize: '0.8rem'
                          }}>
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Notes