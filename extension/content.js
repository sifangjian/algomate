// content.js — 在 LeetCode 页面右侧注入固定面板(iframe 加载 popup.html)
const PANEL_ID = 'algomate-side-panel-iframe';
const TOGGLE_ID = 'algomate-side-panel-toggle';

function createPanel() {
  if (document.getElementById(PANEL_ID)) return;

  const container = document.createElement('div');
  container.id = 'algomate-side-panel';
  container.style.cssText = [
    'position:fixed',
    'top:0',
    'right:0',
    'width:400px',
    'height:100vh',
    'z-index:2147483646',
    'background:#fff',
    'box-shadow:-2px 0 12px rgba(0,0,0,0.25)',
    'display:flex',
    'flex-direction:column',
    'font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif',
  ].join(';');

  const iframe = document.createElement('iframe');
  iframe.id = PANEL_ID;
  // 用 src 指向扩展内 popup.html
  iframe.src = chrome.runtime.getURL('popup.html');
  iframe.style.cssText = 'width:100%;height:100%;border:0;';

  container.appendChild(iframe);
  document.documentElement.appendChild(container);
}

function removePanel() {
  const c = document.getElementById('algomate-side-panel');
  if (c) c.remove();
}

function togglePanel() {
  if (document.getElementById('algomate-side-panel')) removePanel();
  else createPanel();
}

// 工具栏图标点击切换面板
chrome.runtime.onMessage.addListener((msg, _sender, _sendResponse) => {
  if (msg && msg.type === 'toggle-panel') togglePanel();
});

// 首次打开 LeetCode 题目页自动显示面板
if (window.location.href.includes('/problems/')) {
  createPanel();
}
