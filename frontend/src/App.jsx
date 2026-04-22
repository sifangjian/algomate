import React from 'react'
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Notes from './pages/Notes'
import Practice from './pages/Practice'
import Progress from './pages/Progress'
import Settings from './pages/Settings'

function App() {
  return (
    <Router>
      <div className="app-container">
        <aside className="sidebar">
          <div className="sidebar-header">
            <h1>算法学习助手</h1>
          </div>
          <nav>
            <ul className="nav-list">
              <li className="nav-item">
                <NavLink to="/">首页</NavLink>
              </li>
              <li className="nav-item">
                <NavLink to="/notes">笔记</NavLink>
              </li>
              <li className="nav-item">
                <NavLink to="/practice">练习</NavLink>
              </li>
              <li className="nav-item">
                <NavLink to="/progress">进度</NavLink>
              </li>
              <li className="nav-item">
                <NavLink to="/settings">设置</NavLink>
              </li>
            </ul>
          </nav>
        </aside>
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/notes" element={<Notes />} />
            <Route path="/practice" element={<Practice />} />
            <Route path="/progress" element={<Progress />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
      <div className="status-bar">
        就绪
      </div>
    </Router>
  )
}

export default App
