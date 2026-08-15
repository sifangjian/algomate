import React, { useState, useEffect } from 'react';

// 此文件仅用于生成设计预览图，不参与实际项目构建

const PreviewFrame = () => {
  const [time, setTime] = useState('');

  useEffect(() => {
    const update = () => {
      const now = new Date();
      const h = now.getHours().toString().padStart(2, '0');
      const m = now.getMinutes().toString().padStart(2, '0');
      setTime(`${h}:${m}`);
    };
    update();
    const timer = setInterval(update, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div style={{
      width: '100vw',
      height: '100vh',
      background: '#141419',
      backgroundImage: `
        linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)
      `,
      backgroundSize: '24px 24px',
      color: '#e4e4ea',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
    }}>
      <div style={{ display: 'flex', flex: 1, minHeight: 0 }}>
        {/* ===== 侧边栏 ===== */}
        <aside style={{
          width: 220,
          background: '#191920',
          borderRight: '1px solid rgba(255,255,255,0.06)',
          display: 'flex',
          flexDirection: 'column',
          flexShrink: 0,
          padding: '12px 10px',
          gap: 12,
          overflow: 'hidden',
        }}>
          {/* 品牌头部 */}
          <div style={{ padding: '4px 4px 8px', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: '#e4e4ea', display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontSize: 16 }}>⚔️</span>
              AlgoMate
            </div>
            <div style={{ fontSize: 10, color: '#5c5c6c', fontFamily: "'JetBrains Mono', monospace", marginTop: 2 }}>
              v0.1.0 · 算法修习助手
            </div>
          </div>

          {/* 新建按钮 */}
          <button style={{
            width: '100%',
            height: 30,
            background: '#252532',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: 4,
            color: '#e4e4ea',
            fontSize: 13,
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 6,
          }}>+ 新建卡片</button>

          {/* 主导航 */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 2, marginTop: 4 }}>
            {[
              { icon: '🗺️', label: '图鉴', path: '/hall', active: true },
              { icon: '⚔️', label: '修炼', path: '/review' },
              { icon: '📝', label: '题目', path: '/problems' },
              { icon: '💡', label: '解法', path: '/solutions' },
              { icon: '⭐', label: '技巧', path: '/techniques' },
            ].map((item, i) => (
              <div key={i} style={{
                height: 36,
                padding: '6px 10px',
                borderRadius: 3,
                background: item.active ? 'rgba(129,140,248,0.08)' : 'transparent',
                borderLeft: item.active ? '2px solid #818cf8' : '2px solid transparent',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                gap: 1,
                cursor: 'pointer',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: item.active ? '#b8b8ff' : '#9898a8' }}>
                  <span style={{ fontSize: 14 }}>{item.icon}</span>
                  {item.label}
                </div>
                <div style={{ fontSize: 10, color: '#5c5c6c', fontFamily: "'JetBrains Mono', monospace", paddingLeft: 20 }}>
                  {item.path}
                </div>
              </div>
            ))}
          </div>

          {/* 修炼任务 */}
          <div style={{ marginTop: 8 }}>
            <div style={{ fontSize: 10, color: '#5c5c6c', fontFamily: "'JetBrains Mono', monospace", marginBottom: 6, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>今日修炼</span>
              <span style={{ background: '#facc15', color: '#141419', padding: '1px 6px', borderRadius: 3, fontSize: 10, fontWeight: 700 }}>8</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#9898a8' }}>
                <span style={{ width: 5, height: 5, borderRadius: '50%', background: '#facc15', flexShrink: 0 }} />
                待复习 <span style={{ color: '#facc15', marginLeft: 'auto' }}>5</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#9898a8' }}>
                <span style={{ width: 5, height: 5, borderRadius: '50%', background: '#f87171', flexShrink: 0 }} />
                濒危 <span style={{ color: '#f87171', marginLeft: 'auto' }}>2</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#9898a8' }}>
                <span style={{ width: 5, height: 5, borderRadius: '50%', background: '#4ade80', flexShrink: 0 }} />
                已完成 <span style={{ color: '#4ade80', marginLeft: 'auto' }}>1</span>
              </div>
            </div>
          </div>

          {/* 最近活动 */}
          <div style={{ marginTop: 8, flex: 1, minHeight: 0 }}>
            <div style={{ fontSize: 10, color: '#5c5c6c', fontFamily: "'JetBrains Mono', monospace", marginBottom: 6 }}>最近活动</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {[
                { time: '14:32', action: '新建技巧', name: '滑动窗口', color: '#4ade80' },
                { time: '13:05', action: '复习完成', name: 'DFS 遍历', color: '#4ade80' },
                { time: '11:48', action: '新建解法', name: '快速幂', color: '#facc15' },
                { time: '10:20', action: '濒危技巧', name: '回溯剪枝', color: '#f87171' },
                { time: '09:15', action: '新建题目', name: 'LC.209', color: '#4ade80' },
              ].map((item, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11 }}>
                  <span style={{ color: '#5c5c6c', fontFamily: "'JetBrains Mono', monospace", width: 32 }}>{item.time}</span>
                  <span style={{ color: item.color, fontWeight: 500 }}>{item.action}</span>
                  <span style={{ color: '#9898a8', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.name}</span>
                </div>
              ))}
            </div>
          </div>

          {/* 底部信息 */}
          <div style={{ borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: 8 }}>
            <div style={{ fontSize: 10, color: '#5c5c6c', fontFamily: "'JetBrains Mono', monospace" }}>
              #session-001
            </div>
            <div style={{ fontSize: 10, color: '#9898a8', marginTop: 2 }}>
              学习 <span style={{ color: '#4ade80', fontWeight: 600 }}>23</span> 天
            </div>
          </div>
        </aside>

        {/* ===== 主内容区 ===== */}
        <main style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, overflow: 'hidden' }}>
          {/* 顶部标签栏 */}
          <div style={{
            height: 40,
            background: '#191920',
            borderBottom: '1px solid rgba(255,255,255,0.06)',
            display: 'flex',
            alignItems: 'center',
            padding: '0 16px',
            gap: 4,
            flexShrink: 0,
          }}>
            {[
              { label: '工作台', active: true },
              { label: '修炼' },
              { label: '题目' },
              { label: '解法' },
              { label: '技巧' },
            ].map((tab, i) => (
              <div key={i} style={{
                height: '100%',
                padding: '0 16px',
                display: 'flex',
                alignItems: 'center',
                fontSize: 13,
                color: tab.active ? '#e4e4ea' : '#5c5c6c',
                borderBottom: tab.active ? '2px solid #818cf8' : '2px solid transparent',
                cursor: 'pointer',
                fontWeight: tab.active ? 600 : 400,
              }}>{tab.label}</div>
            ))}
            <div style={{ flex: 1 }} />
            <div style={{
              width: 200,
              height: 26,
              background: '#2a2a3a',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 4,
              display: 'flex',
              alignItems: 'center',
              padding: '0 10px',
              gap: 6,
              fontSize: 12,
              color: '#5c5c6c',
            }}>
              🔍 <span>搜索卡片...</span>
            </div>
          </div>

          {/* 内容滚动区 */}
          <div style={{ flex: 1, overflow: 'auto', padding: '20px 24px' }}>
            {/* 问候区 */}
            <div style={{ marginBottom: 20 }}>
              <h1 style={{ fontSize: 28, fontWeight: 800, color: '#e4e4ea', margin: 0, lineHeight: 1.2 }}>
                早上好，<br />开始今天的工作
              </h1>
              <div style={{
                marginTop: 8,
                fontSize: 11,
                color: '#5c5c6c',
                fontFamily: "'JetBrains Mono', monospace",
                display: 'flex',
                gap: 8,
                alignItems: 'center',
              }}>
                <span style={{ color: '#818cf8' }}>No.001</span>
                <span>·</span>
                <span>工作台</span>
                <span>·</span>
                <span>2026-08-15 · 周六 · 09:36 CST</span>
                <span>·</span>
                <span style={{ color: '#facc15' }}>8 个任务进行中</span>
                <span>·</span>
                <span style={{ color: '#4ade80' }}>0 个今日完成</span>
              </div>
            </div>

            {/* 新建卡片输入区 */}
            <div style={{
              background: '#1e1e27',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: 4,
              padding: 16,
              marginBottom: 20,
              boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
            }}>
              <div style={{ fontSize: 12, color: '#5c5c6c', fontFamily: "'JetBrains Mono', monospace", marginBottom: 10 }}>
                <span style={{ color: '#818cf8' }}># 01</span>{'  '}
                <span style={{ color: '#9898a8' }}>[输入]</span>{'  '}
                <span style={{ color: '#e4e4ea', fontWeight: 600 }}>新卡片</span>
              </div>
              <textarea
                placeholder="描述你想记录的内容，Enter 发送；Shift+Enter 换行..."
                style={{
                  width: '100%',
                  minHeight: 80,
                  background: '#141419',
                  border: '1px solid rgba(255,255,255,0.08)',
                  borderRadius: 4,
                  color: '#e4e4ea',
                  padding: 12,
                  fontSize: 13,
                  fontFamily: 'inherit',
                  resize: 'vertical',
                  outline: 'none',
                  boxSizing: 'border-box',
                }}
              />
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginTop: 10,
              }}>
                <div style={{ display: 'flex', gap: 8 }}>
                  {[
                    { icon: '+', label: '新建' },
                    { icon: '📁', label: '分类' },
                    { icon: '💬', label: '算法类型' },
                    { icon: '🧠', label: '思维链' },
                    { icon: '⌘', label: '命令' },
                  ].map((tool, i) => (
                    <button key={i} style={{
                      height: 26,
                      padding: '0 10px',
                      background: '#252532',
                      border: '1px solid rgba(255,255,255,0.08)',
                      borderRadius: 3,
                      color: '#9898a8',
                      fontSize: 12,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 4,
                    }}>
                      <span>{tool.icon}</span>
                      <span>{tool.label}</span>
                    </button>
                  ))}
                </div>
                <button style={{
                  height: 28,
                  padding: '0 16px',
                  background: '#818cf8',
                  border: 'none',
                  borderRadius: 3,
                  color: '#141419',
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                }}>
                  发送 <span>↵</span>
                </button>
              </div>
            </div>

            {/* 当前状态区 */}
            <div style={{ marginBottom: 20 }}>
              <div style={{ fontSize: 12, color: '#5c5c6c', fontFamily: "'JetBrains Mono', monospace", marginBottom: 4 }}>
                <span style={{ color: '#818cf8' }}># 02</span>{'  '}
                <span style={{ color: '#9898a8' }}>[状态]</span>{'  '}
                <span style={{ color: '#e4e4ea', fontWeight: 600 }}>当前状态</span>
              </div>
              <div style={{ fontSize: 11, color: '#5c5c6c', fontFamily: "'JetBrains Mono', monospace", marginBottom: 12 }}>
                2 项需要关注 · 6 项正常 · 1 项注意
              </div>

              {/* 状态卡片网格 */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: 10,
              }}>
                {[
                  { label: '总卡片', value: 47, unit: '', status: 'normal', sub: '15题 · 12解 · 20技' },
                  { label: '待复习', value: 5, unit: '', status: 'warning', sub: '今日到期' },
                  { label: '濒危技巧', value: 2, unit: '', status: 'critical', sub: '耐久度<30' },
                  { label: '连续学习', value: 23, unit: '天', status: 'normal', sub: '🔥' },
                  { label: '本周学习', value: 5, unit: '/7天', status: 'normal', sub: '坚持就是胜利' },
                  { label: '准确率', value: 87, unit: '%', status: 'normal', sub: '累计复习' },
                  { label: '累计复习', value: 156, unit: '次', status: 'normal', sub: '全部时间' },
                  { label: '今日新增', value: 3, unit: '', status: 'normal', sub: '1题 · 1解 · 1技' },
                  { label: '下一复习', value: 2, unit: '天后', status: 'warning', sub: '下周三到期' },
                ].map((card, i) => {
                  const statusColors = {
                    normal: { bg: 'rgba(74,222,128,0.12)', color: '#4ade80', label: '正常' },
                    warning: { bg: 'rgba(250,204,21,0.12)', color: '#facc15', label: '注意' },
                    critical: { bg: 'rgba(248,113,113,0.12)', color: '#f87171', label: '危险' },
                  };
                  const sc = statusColors[card.status];
                  return (
                    <div key={i} style={{
                      background: '#1e1e27',
                      border: '1px solid rgba(255,255,255,0.06)',
                      borderRadius: 4,
                      padding: '12px 14px',
                      boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                        <span style={{ fontSize: 12, color: '#9898a8' }}>{card.label}</span>
                        <span style={{
                          fontSize: 10,
                          color: sc.color,
                          background: sc.bg,
                          padding: '1px 6px',
                          borderRadius: 3,
                          fontWeight: 600,
                        }}>{sc.label}</span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
                        <span style={{ fontSize: 28, fontWeight: 800, color: '#e4e4ea', lineHeight: 1, fontFamily: "'JetBrains Mono', monospace" }}>
                          {card.value}
                        </span>
                        <span style={{ fontSize: 12, color: '#5c5c6c' }}>{card.unit}</span>
                      </div>
                      <div style={{ fontSize: 11, color: '#5c5c6c', marginTop: 4 }}>{card.sub}</div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* 今日修炼任务 */}
            <div>
              <div style={{ fontSize: 12, color: '#5c5c6c', fontFamily: "'JetBrains Mono', monospace", marginBottom: 4 }}>
                <span style={{ color: '#818cf8' }}># 03</span>{'  '}
                <span style={{ color: '#9898a8' }}>[修炼]</span>{'  '}
                <span style={{ color: '#e4e4ea', fontWeight: 600 }}>今日修炼任务</span>
              </div>
              <div style={{
                background: '#1e1e27',
                border: '1px solid rgba(255,255,255,0.06)',
                borderRadius: 4,
                overflow: 'hidden',
              }}>
                {[
                  { id: 1, name: '二分查找模板', type: '技巧', priority: 'critical', status: '未完成' },
                  { id: 2, name: '快速幂', type: '技巧', priority: 'high', status: '未完成' },
                  { id: 3, name: '滑动窗口最大值', type: '技巧', priority: 'medium', status: '进行中' },
                  { id: 4, name: 'LC.209 长度最小的子数组', type: '题目', priority: 'high', status: '已完成' },
                ].map((task, i) => {
                  const priorityColors = {
                    critical: '#f87171',
                    high: '#facc15',
                    medium: '#38bdf8',
                    low: '#4ade80',
                  };
                  const statusColors = {
                    '未完成': '#5c5c6c',
                    '进行中': '#facc15',
                    '已完成': '#4ade80',
                  };
                  return (
                    <div key={i} style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 12,
                      padding: '10px 14px',
                      borderBottom: i < 3 ? '1px solid rgba(255,255,255,0.04)' : 'none',
                      fontSize: 13,
                    }}>
                      <span style={{ color: '#5c5c6c', fontFamily: "'JetBrains Mono', monospace", fontSize: 11, width: 28 }}>
                        #{String(task.id).padStart(3, '0')}
                      </span>
                      <span style={{
                        width: 6,
                        height: 6,
                        borderRadius: '50%',
                        background: priorityColors[task.priority],
                        flexShrink: 0,
                      }} />
                      <span style={{ color: '#e4e4ea', flex: 1 }}>{task.name}</span>
                      <span style={{ color: '#5c5c6c', fontSize: 11 }}>{task.type}</span>
                      <span style={{
                        color: statusColors[task.status],
                        fontSize: 11,
                        padding: '1px 8px',
                        background: task.status === '已完成' ? 'rgba(74,222,128,0.1)' : task.status === '进行中' ? 'rgba(250,204,21,0.1)' : 'rgba(255,255,255,0.05)',
                        borderRadius: 3,
                        fontWeight: 600,
                      }}>{task.status}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </main>
      </div>

      {/* ===== 底部状态栏 ===== */}
      <footer style={{
        height: 24,
        background: '#111115',
        borderTop: '1px solid rgba(255,255,255,0.06)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 16px',
        fontSize: 11,
        fontFamily: "'JetBrains Mono', monospace",
        color: '#5c5c6c',
        flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#4ade80' }} />
            AlgoMate
          </span>
          <span>v0.1.0</span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <span style={{ color: '#4ade80' }}>API</span> ✅
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <span style={{ color: '#4ade80' }}>DB</span> ✅
          </span>
        </div>
        <div style={{ display: 'flex', gap: 16 }}>
          <span>今日完成: <span style={{ color: '#4ade80' }}>1</span></span>
          <span>总卡片: <span style={{ color: '#e4e4ea' }}>47</span></span>
          <span>总复习: <span style={{ color: '#e4e4ea' }}>156</span></span>
          <span>更新: {time}</span>
        </div>
      </footer>
    </div>
  );
};

export default PreviewFrame;
