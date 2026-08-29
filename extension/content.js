// content.js — 在 LeetCode 页面右侧注入固定面板(iframe 加载 popup.html)
const PANEL_ID = 'algomate-side-panel-iframe';
const TOGGLE_ID = 'algomate-side-panel-toggle';

function createPanel() {
  if (document.getElementById(PANEL_ID) || document.getElementById(TOGGLE_ID)) return;

  const toggle = document.createElement('div');
  toggle.id = TOGGLE_ID;
  toggle.textContent = '📥 AlgoMate';
  toggle.style.cssText = 'position:fixed;right:0;top:160px;z-index:2147483646;' +
    'cursor:pointer;background:#0969da;color:#fff;font-size:12px;padding:8px 6px;' +
    'border-radius:6px 0 0 6px;writing-mode:vertical-rl;user-select:none;' +
    'box-shadow:-2px 0 8px rgba(0,0,0,.2)';

  const panel = document.createElement('div');
  panel.id = 'algomate-side-panel';
  panel.style.cssText = 'position:fixed;top:0;right:0;width:400px;height:100vh;z-index:2147483647;' +
    'background:#fff;box-shadow:-4px 0 16px rgba(0,0,0,.25);display:none;';

  const iframe = document.createElement('iframe');
  iframe.id = PANEL_ID;
  iframe.src = chrome.runtime.getURL('popup.html');
  iframe.style.cssText = 'width:100%;height:100%;border:none;';
  iframe.onerror = () => { panel.dataset.err = 'iframe 加载失败(检查 manifest web_accessible_resources)'; };
  panel.appendChild(iframe);

  toggle.addEventListener('click', () => {
    const show = panel.style.display === 'none' || !panel.style.display;
    panel.style.display = show ? 'block' : 'none';
    toggle.style.display = show ? 'none' : 'block';
  });

  document.body.appendChild(panel);
  document.body.appendChild(toggle);
  window.__algomatePanel = panel;
  window.__algomateToggle = toggle;
}

function togglePanel() {
  const panel = document.getElementById('algomate-side-panel');
  const toggle = document.getElementById(TOGGLE_ID);
  if (!panel || !toggle) { createPanel(); return; }
  const show = panel.style.display === 'none' || !panel.style.display;
  panel.style.display = show ? 'block' : 'none';
  toggle.style.display = show ? 'none' : 'block';
}

// 进入 LeetCode 任意页即创建(默认隐藏, 仅显示右侧竖条)
if (document.body) createPanel();
else document.addEventListener('DOMContentLoaded', createPanel);

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg && msg.type === 'toggle-panel') { togglePanel(); sendResponse({ ok: true }); }
});
