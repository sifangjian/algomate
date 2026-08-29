// background.js — 默认点击工具栏图标即打开侧边栏(任意页面均可, 不受域名限制)
chrome.runtime.onInstalled.addListener(async () => {
  try {
    await chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });
  } catch (e) {
    console.warn('[AlgoMate] setPanelBehavior failed', e);
  }
});
