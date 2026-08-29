// background.js — 处理工具栏图标点击, 打开 sidePanel(侧边栏常驻形态)
chrome.runtime.onInstalled.addListener(() => {
  // 默认所有站点都可打开侧边栏(用户点击图标时针对当前 tab 打开)
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch((e) => {
    console.warn('[AlgoMate] setPanelBehavior failed', e);
  });
});

// 兜底: 某些版本 openPanelOnActionClick 不生效时, 手动打开
chrome.action.onClicked.addListener(async (tab) => {
  if (!tab?.windowId) return;
  try {
    await chrome.sidePanel.open({ windowId: tab.windowId });
  } catch (e) {
    console.warn('[AlgoMate] sidePanel.open failed', e);
  }
});
