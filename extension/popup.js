// popup.js — 预览抓取内容、填写心得与技巧、提交导入
const BACKEND = 'http://localhost:8000/api/v1/import';

const $ = (id) => document.getElementById(id);
const statusEl = $('status');

function setStatus(msg, type) {
  statusEl.textContent = msg;
  statusEl.className = 'status' + (type ? ' ' + type : '');
}

function renderPreview(data) {
  $('f-title').textContent = data.title || '（未识别到标题）';
  $('f-difficulty').textContent = data.difficulty || '—';
  const tagsBox = $('f-tags');
  tagsBox.innerHTML = '';
  (data.tags || []).forEach((t) => {
    const s = document.createElement('span');
    s.textContent = t;
    tagsBox.appendChild(s);
  });
  if (!(data.tags || []).length) tagsBox.textContent = '（无标签）';
  $('f-code').value = data.code || '';
  $('f-lang').textContent = data.language ? '语言: ' + data.language : '（未识别语言）';
  $('btn-import').disabled = !(data.slug || data.title);
  if (!(data.slug || data.title)) {
    setStatus('未能从当前页面抓取题目，请确认在 LeetCode 题目页打开本插件。', 'warn');
  } else {
    setStatus('抓取完成，请核对后填写心得与技巧并导入。', 'ok');
  }
}

// 动态添加一条技巧输入框
function addTechniqueRow(name = '', summary = '') {
  const wrap = document.createElement('div');
  wrap.className = 'tech-item';
  wrap.innerHTML = `
    <button type="button" class="btn-del" title="删除">✕</button>
    <input type="text" class="tech-name" placeholder="技巧名称（如：哈希表存差值）" value="${name.replace(/"/g, '&quot;')}" />
    <textarea class="tech-summary" placeholder="一句话总结（可选）" style="min-height:38px;">${summary}</textarea>
  `;
  wrap.querySelector('.btn-del').addEventListener('click', () => wrap.remove());
  $('f-techniques').appendChild(wrap);
}

// 收集技巧列表
function collectTechniques() {
  const items = [];
  document.querySelectorAll('#f-techniques .tech-item').forEach((row) => {
    const name = row.querySelector('.tech-name').value.trim();
    const summary = row.querySelector('.tech-summary').value.trim();
    if (name) items.push({ name, summary });
  });
  return items;
}

// 通过 chrome.scripting 注入 collect.js 到当前题目页并取返回值
async function collect() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || !/leetcode\.(cn|com)/.test(tab.url || '')) {
    setStatus('请先打开 LeetCode 题目页（leetcode.cn / leetcode.com）。', 'warn');
    return;
  }
  try {
    const [result] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ['collect.js'],
    });
    if (result && result.result) {
      renderPreview(result.result);
      window.__collected = result.result;
    } else {
      setStatus('抓取返回为空，请刷新题目页后重试。', 'err');
    }
  } catch (e) {
    setStatus('抓取异常: ' + e.message + '（刷新题目页后重试）', 'err');
  }
}

// 提交导入
async function doImport() {
  const d = window.__collected;
  if (!d) return;
  const btn = $('btn-import');
  btn.disabled = true;
  setStatus('正在导入…');
  const payload = {
    slug: d.slug,
    title: d.title,
    difficulty: d.difficulty,
    description: d.description || '',
    leetcode_link: d.source || '',
    tags: d.tags || [],
    code: $('f-code').value,
    language: d.language || '',
    techniques: collectTechniques(),
    notes: $('f-notes').value,
  };
  try {
    const r = await fetch(BACKEND, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const j = await r.json();
    if (r.ok) {
      const extra = j.is_new_problem
        ? ''
        : `（已存在该题，本次追加第 ${j.existing_solution_count + 1} 条解法）`;
      setStatus(
        (j.is_new_problem ? '导入成功（新建题卡）' : '已存在该题，追加解法') +
          ` · 技巧卡 ${j.technique_ids.length} 张` + extra,
        'ok'
      );
      btn.textContent = '已导入 ✓';
      // 引导去系统补写突破口/思路（破题思路已由你填写，这里提示可继续完善）
      const tip = document.createElement('div');
      tip.className = 'hint';
      tip.style.marginTop = '6px';
      tip.innerHTML = '可在系统中为解法补充「突破口 / 思路 / 易错点」，让卡片更完整。';
      statusEl.parentNode.insertBefore(tip, statusEl.nextSibling);
    } else {
      setStatus('导入失败: ' + JSON.stringify(j), 'err');
      btn.disabled = false;
    }
  } catch (e) {
    setStatus('请求失败: ' + e.message + '（确认后端 http://localhost:8000 已启动）', 'err');
    btn.disabled = false;
  }
}

$('btn-add-tech').addEventListener('click', () => addTechniqueRow());
$('btn-import').addEventListener('click', doImport);
collect();
