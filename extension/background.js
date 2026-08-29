// background.js — 工具栏图标点击: 通知 content script 切换右侧面板
chrome.action.onClicked.addListener(async (tab) => {
  if (!tab?.id) return;
  try {
    await chrome.tabs.sendMessage(tab.id, { type: 'toggle-panel' });
  } catch (e) {
    // content script 未注入(非 LeetCode 页)时静默
    console.warn('[AlgoMate] toggle-panel failed (非 LeetCode 页?)', e);
  }
});
