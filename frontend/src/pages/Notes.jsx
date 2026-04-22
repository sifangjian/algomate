import React, { useState } from 'react'

function Notes() {
  const [notes, setNotes] = useState([])
  const [newNote, setNewNote] = useState({ title: '', content: '' })

  const handleCreateNote = () => {
    if (newNote.title && newNote.content) {
      setNotes([...notes, { ...newNote, id: Date.now(), createdAt: new Date().toISOString() }])
      setNewNote({ title: '', content: '' })
    }
  }

  return (
    <div>
      <div className="page-header">
        <h2>笔记管理</h2>
      </div>
      <div className="card">
        <div className="card-title">创建新笔记</div>
        <div className="form-group">
          <label>标题</label>
          <input
            type="text"
            value={newNote.title}
            onChange={(e) => setNewNote({ ...newNote, title: e.target.value })}
            placeholder="输入笔记标题"
          />
        </div>
        <div className="form-group">
          <label>内容</label>
          <textarea
            value={newNote.content}
            onChange={(e) => setNewNote({ ...newNote, content: e.target.value })}
            placeholder="输入笔记内容（支持 Markdown）"
          />
        </div>
        <button className="btn btn-primary" onClick={handleCreateNote}>创建笔记</button>
      </div>
      <div className="card">
        <div className="card-title">笔记列表</div>
        {notes.length === 0 ? (
          <p>暂无笔记</p>
        ) : (
          notes.map((note) => (
            <div key={note.id} style={{ padding: '10px 0', borderBottom: '1px solid #eee' }}>
              <h3>{note.title}</h3>
              <p style={{ color: '#666', fontSize: '0.9rem' }}>{note.content.substring(0, 100)}...</p>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default Notes
