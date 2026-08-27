// content.js — LeetCode 题目页抓取脚本 (Manifest V3)
// 数据源优先级: __NEXT_DATA__ (Next.js state) -> DOM 兜底
// 通过 chrome.runtime.onMessage 把抓取结果传给 popup

(function () {
  'use strict';

  function readNextData() {
    try {
      const el = document.getElementById('__NEXT_DATA__');
      if (!el || !el.textContent) return null;
      return JSON.parse(el.textContent);
    } catch (e) {
      return null;
    }
  }

  // 从 __NEXT_DATA__ 里尽量抽取题目信息
  function parseFromNextData(nd) {
    const out = { ok: false, title: '', slug: '', difficulty: '', tags: [], description: '', code: '', language: '' };
    try {
      const q = nd?.props?.pageProps?.data?.question;
      if (!q) return out;
      out.title = q.title || '';
      out.slug = q.titleSlug || '';
      out.difficulty = (q.difficulty || '').toLowerCase();
      out.tags = (q.topicTags || []).map((t) => (t.name || '').trim()).filter(Boolean);
      out.description = q.content || '';
      // 题目翻译/题面可能有多语言，保留原文
      return out;
    } catch (e) {
      return out;
    }
  }

  // DOM 兜底：从可见页面补抓
  function parseFromDOM() {
    const out = { ok: false, title: '', slug: '', difficulty: '', tags: [], description: '', code: '', language: '' };

    // slug 从 URL
    const m = location.pathname.match(/\/problems\/([^/]+)/);
    if (m) out.slug = decodeURIComponent(m[1]);

    // 标题: [data-cy="question-title"] 或 h1
    const titleEl = document.querySelector('[data-cy="question-title"]') || document.querySelector('h1');
    if (titleEl) out.title = titleEl.textContent.trim();

    // 难度: 常见 class 含 "text-difficulty" 或含 easy/medium/hard 文本
    const diffEl = Array.from(document.querySelectorAll('div, span')).find((e) =>
      /^(easy|medium|hard)$/i.test((e.getAttribute('difficulty') || e.textContent || '').trim())
    );
    if (diffEl) out.difficulty = diffEl.textContent.trim().toLowerCase();

    // 标签
    document.querySelectorAll('a[href*="tag"], .tag, [data-cy="tag"]').forEach((a) => {
      const t = (a.textContent || '').trim();
      if (t && !out.tags.includes(t)) out.tags.push(t);
    });

    // 题面: [data-cy="question-content"] 或 .question-content
    const descEl = document.querySelector('[data-cy="question-content"]') || document.querySelector('.question-content');
    if (descEl) out.description = descEl.innerText.trim();

    return out;
  }

  // 抓取编辑器当前代码 (Monaco)
  function readEditorCode() {
    // Monaco 文本域 fallback: .monaco-editor textarea，或 .view-lines 文本
    const ta = document.querySelector('.monaco-editor textarea');
    if (ta && ta.value) return ta.value;
    const lines = Array.from(document.querySelectorAll('.monaco-editor .view-lines .view-line'))
      .map((l) => l.innerText)
      .join('\n');
    return lines.trim();
  }

  function detectLanguage() {
    // 从编辑器相关下拉 / 页面 state 推断
    const langEl = document.querySelector('[data-cy="lang-select"]') || document.querySelector('.lang-select');
    if (langEl && langEl.textContent) return langEl.textContent.trim().toLowerCase();
    return '';
  }

  function collect() {
    let data = parseFromNextData(readNextData());
    const dom = parseFromDOM();
    // 合并: __NEXT_DATA__ 优先，DOM 补缺
    data.title = data.title || dom.title;
    data.slug = data.slug || dom.slug;
    data.difficulty = data.difficulty || dom.difficulty;
    data.description = data.description || dom.description;
    data.tags = data.tags.length ? data.tags : dom.tags;
    data.code = readEditorCode();
    data.language = detectLanguage();
    data.ok = !!(data.slug || data.title);
    data.source = location.href;
    return data;
  }

  chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg && msg.type === 'COLLECT') {
      try {
        sendResponse({ success: true, data: collect() });
      } catch (e) {
        sendResponse({ success: false, error: String(e) });
      }
    }
    return true; // keep channel open for async
  });
})();
