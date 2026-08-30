// collect.js — 注入到 LeetCode 题目页执行的抓取函数
// 由 popup 通过 chrome.scripting.executeScript 调用
// 调试: 打开题目页 F12 -> Console 搜 [AlgoMate]

(function () {
  'use strict';
  const DEBUG = true;
  function dbg(...a) { if (DEBUG) console.log('[AlgoMate]', ...a); }

  function readNextData() {
    try {
      const el = document.getElementById('__NEXT_DATA__');
      if (!el || !el.textContent) return null;
      return JSON.parse(el.textContent);
    } catch (e) { return null; }
  }

  function findQuestion(nd) {
    if (!nd) return null;
    const pp = nd.props && nd.props.pageProps;
    if (!pp) return null;
    if (pp.data && pp.data.question) return pp.data.question;
    const dss = pp.dehydratedState && pp.dehydratedState.queries;
    if (Array.isArray(dss)) {
      for (const q of dss) {
        const d = q && q.state && q.state.data;
        if (d && (d.titleSlug || d.title)) return d;
      }
    }
    if (pp.question) return pp.question;
    return null;
  }

  function cleanTitle(raw) {
    if (!raw) return raw;
    return raw
      // 去掉末尾站点后缀: " - 力扣（LeetCode）" / " - 力扣(LeetCode)" / " - LeetCode"
      .replace(/\s*[-–—|]\s*力扣\s*[（(]?\s*LeetCode\s*[）)]?\s*$/i, '')
      .replace(/\s*[-–—|]\s*LeetCode\s*$/i, '')
      // 去掉开头的序号 "1. "
      .replace(/^\s*\d+\.\s*/, '')
      .trim();
  }

  function parseFromNextData(nd) {
    const out = { ok: false, title: '', slug: '', difficulty: '', tags: [], description: '', code: '', language: '' };
    try {
      const q = findQuestion(nd);
      if (!q) { dbg('__NEXT_DATA__ 未找到题目对象'); return out; }
      out.title = cleanTitle(q.title || '');
      out.slug = q.titleSlug || '';
      out.difficulty = (q.difficulty || '').toLowerCase();
      out.tags = (q.topicTags || []).map((t) => (t.name || '').trim()).filter(Boolean);
      out.description = q.content || '';
      out.ok = !!(out.title || out.slug);
      dbg('__NEXT_DATA__ 解析成功', out.title, out.slug);
      return out;
    } catch (e) {
      dbg('__NEXT_DATA__ 解析异常', e);
      return out;
    }
  }

  function parseFromDOM() {
    const out = { ok: false, title: '', slug: '', difficulty: '', tags: [], description: '', code: '', language: '' };
    const m = location.pathname.match(/\/problems\/([^/]+)/);
    if (m) out.slug = decodeURIComponent(m[1]);

    let titleEl = document.querySelector('[data-cy="question-title"]')
      || document.querySelector('#question-title')
      || document.querySelector('.question-title');
    if (titleEl) {
      out.title = titleEl.textContent.trim();
    }
    if (!out.title && document.title) {
      // 兜底: 从 <title> 提取, 形如 "两数之和 - 力扣（LeetCode）" / "Two Sum - LeetCode"
      out.title = cleanTitle(document.title);
    }

    const diffEl = document.querySelector('[data-cy="difficulty"]')
      || document.querySelector('.text-difficulty-easy, .text-difficulty-medium, .text-difficulty-hard');
    if (diffEl) {
      const cls = diffEl.className || '';
      const txt = (diffEl.getAttribute('difficulty') || diffEl.textContent || '').trim().toLowerCase();
      if (/easy/.test(cls) || txt === 'easy') out.difficulty = 'easy';
      else if (/medium/.test(cls) || txt === 'medium') out.difficulty = 'medium';
      else if (/hard/.test(cls) || txt === 'hard') out.difficulty = 'hard';
    }

    const contentScope = document.querySelector('[data-cy="question-content"]')
      || document.querySelector('.question-content')
      || document.body;
    contentScope.querySelectorAll('a[href*="tag"], .tag, [data-cy="tag"]').forEach((a) => {
      const t = (a.textContent || '').trim();
      if (t && !out.tags.includes(t)) out.tags.push(t);
    });

    const descEl = document.querySelector('[data-cy="question-content"]') || document.querySelector('.question-content');
    if (descEl) out.description = descEl.innerText.trim();

    out.ok = !!(out.title && out.slug);
    return out;
  }

  function readEditorCode() {
    // Monaco 编辑器: 优先从隐藏 textarea(.inputarea) 读真实代码
    const ta = document.querySelector('.monaco-editor textarea.inputarea')
      || document.querySelector('.monaco-editor textarea');
    if (ta && ta.value) return ta.value;
    // 兜底: 拼接可见行 (.view-line), Monaco 用 div 渲染, innerText 近似原文
    const lines = Array.from(document.querySelectorAll('.monaco-editor .view-lines .view-line'))
      .map((l) => (l.innerText || l.textContent || ''))
      .join('\n');
    return lines.trim();
  }

  function detectLanguage() {
    // 1) Monaco 编辑器上挂载的 mode 属性
    const ed = document.querySelector('.monaco-editor');
    if (ed) {
      const mode = ed.getAttribute('data-mode-id') || ed.getAttribute('data-mode');
      if (mode) return mode.toLowerCase();
    }
    // 2) 顶部语言下拉/选择按钮 (LeetCode 在编辑器上方, 文本为语言名)
    const langCandidates = document.querySelectorAll(
      '[data-cy="lang-select"], .language-dropdown, button[class*="lang"], .css-1wy0on6, [role="combobox"]'
    );
    for (const el of langCandidates) {
      const t = (el.textContent || '').trim().toLowerCase();
      if (t && /python|java|cpp|c\+\+|javascript|golang|rust|cpp|mysql|typescript/.test(t)) return t;
    }
    // 3) 任何包含已知语言名的按钮
    const allBtns = Array.from(document.querySelectorAll('button, [class*="lang"], [class*="Lang"]'));
    for (const b of allBtns) {
      const t = (b.textContent || '').trim().toLowerCase();
      const m = t.match(/^(python3?|java|cpp|c\+\+|javascript|typescript|golang|go|rust|mysql|sql|scala|kotlin|swift)$/);
      if (m) return m[1];
    }
    return '';
  }

  function collect() {
    let data = parseFromNextData(readNextData());
    if (!data.ok) {
      dbg('回退 DOM 抓取');
      data = parseFromDOM();
    }
    // 无论走哪条路径, 代码与语言都从编辑器运行时读取
    data.code = readEditorCode();
    data.language = detectLanguage();
    data.ok = !!(data.slug || data.title);
    data.source = location.href;
    dbg('最终抓取', data);
    return data;
  }

  // 作为注入脚本执行时，把结果返回给调用方
  return collect();
})();
