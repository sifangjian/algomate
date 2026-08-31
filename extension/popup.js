// popup.js — 预览抓取内容、填写心得与技巧、提交导入
// 后端地址可配置（设置面板），默认指向服务器，本地开发可改 localhost
// 默认用 http（8025 Vite dev server 无 SSL）。服务器部署如改 HTTPS(反代)则改这里。
// ⚠️ HSTS 坑（2026-08-31）：博客 www.fjsi.top 带 Strict-Transport-Security 头，
// 浏览器会把 http://www.fjsi.top:8025 自动升级为 https:// → 8025 无 TLS 必报
// ERR_SSL_PROTOCOL_ERROR。故默认必须用裸域 fjsi.top（HSTS 无 includeSubDomains，裸域不受影响）。
const DEFAULT_BASE = 'http://fjsi.top:8025';

// 从 storage 读取已保存的后端地址，未设置则用默认
// 防御性清洗: 去除 @url:/反引号/首尾空白, 确保 http(s):// 开头
async function getBase() {
  let stored = DEFAULT_BASE;
  try {
    const r = await chrome.storage.local.get('algomate_base');
    if (r.algomate_base) stored = r.algomate_base;
  } catch {
    stored = DEFAULT_BASE;
  }
  // 去掉 @url:`...` 这种 markdown 占位包装, 以及反引号
  stored = stored
    .replace(/@url:/gi, '')
    .replace(/`/g, '')
    .trim()
    .replace(/\/$/, '');
  // 若不是 http(s) 开头, 补 http:// (避免 https:// 到裸 http 端口报 SSL 错)
  if (!/^https?:\/\//i.test(stored)) {
    stored = 'http://' + stored;
  }
  return stored;
}
// 拼接：base + /api/v1...
async function apiUrl(path) {
  return (await getBase()) + '/api/v1' + path;
}

const $ = (id) => document.getElementById(id);
const statusEl = $('status');

function setStatus(msg, type) {
  statusEl.textContent = msg;
  statusEl.className = 'status' + (type ? ' ' + type : '');
}

// ===== 设置面板（独立，不干扰抓取内容）=====
function initSettings() {
  const panel = $('settings-panel');
  const openBtn = $('btn-settings');
  const saveBtn = $('btn-save-base');
  const input = $('input-base');
  const closeBtn = $('btn-settings-close');

  openBtn.addEventListener('click', async () => {
    input.value = await getBase();
    panel.classList.add('open');
  });
  closeBtn.addEventListener('click', () => panel.classList.remove('open'));
  saveBtn.addEventListener('click', async () => {
    let v = input.value.trim().replace(/`/g, '').replace(/@url:/gi, '').replace(/\/+$/, '');
    if (!v) return;
    if (!/^https?:\/\//i.test(v)) v = 'http://' + v;
    await chrome.storage.local.set({ algomate_base: v });
    panel.classList.remove('open');
    setStatus('后端地址已保存：' + v + '，正在测试连接…', 'ok');
    // 连通性探测：GET 健康端点；网络/协议/HSTS 问题都会在此暴露，不用等导入时才报错
    try {
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 6000);
      const r = await fetch(v + '/api/v1/progress/stats', { signal: ctrl.signal });
      clearTimeout(timer);
      setStatus(
        r.ok
          ? '✓ 后端连接正常：' + v
          : '已保存，但后端响应异常（HTTP ' + r.status + '）：' + v,
        r.ok ? 'ok' : 'err'
      );
    } catch (e) {
      setStatus(
        '已保存，但连接失败：' + e.message + '。若浏览器把 http 自动升级成 https（HSTS），' +
        '请把地址改为裸域 http://fjsi.top:8025（www.fjsi.top 的 http 请求会被强制升级为 https 而失败）',
        'err'
      );
    }
  });
}

// ===== 初始化 =====
function init() {
  $('btn-add-tech').addEventListener('click', () => addTechniqueRow());
  $('btn-import').addEventListener('click', () => doImport());
  $('btn-recrawl').addEventListener('click', () => {
    // 情况3：重新抓取 = 退出编辑模式，以新解法/新技巧导入
    window.__recrawl = true;
    resetEditState();
    collect();
  });
  setupComplexityToggle('f-time-select', 'f-time');
  setupComplexityToggle('f-space-select', 'f-space');
  initSettings();
  collect();
}
init();

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

function addTechniqueRow(name = '', use_cases = '', notes = '', code_template = '', id = null) {
  const wrap = document.createElement('div');
  wrap.className = 'tech-item';
  if (id != null) wrap.dataset.techId = id;
  wrap.innerHTML = `
    <button type="button" class="btn-del" title="删除">✕</button>
    <input type="text" class="tech-name" placeholder="技巧名称（如：哈希表存差值）" value="${name.replace(/"/g, '&quot;')}" />
    <textarea class="tech-use-cases" placeholder="使用场景/触发条件（可选）" style="min-height:38px;">${use_cases}</textarea>
    <textarea class="tech-notes" placeholder="注意事项（可选）" style="min-height:38px;">${notes}</textarea>
    <textarea class="tech-code" placeholder="标准代码模板（可选）" style="min-height:38px;">${code_template}</textarea>
  `;
  wrap.querySelector('.btn-del').addEventListener('click', () => wrap.remove());
  $('f-techniques').appendChild(wrap);
}

function collectTechniques() {
  const items = [];
  document.querySelectorAll('#f-techniques .tech-item').forEach((row) => {
    const name = row.querySelector('.tech-name').value.trim();
    const use_cases = row.querySelector('.tech-use-cases').value.trim();
    const notes = row.querySelector('.tech-notes').value.trim();
    const code_template = row.querySelector('.tech-code').value.trim();
    if (!name) return;
    const item = { name, use_cases, notes, code_template };
    if (row.dataset.techId) item.technique_id = parseInt(row.dataset.techId, 10);
    items.push(item);
  });
  return items;
}

// 复杂度: 下拉选择或手动填写, 二选一
function getComplexity(selectId, manualId) {
  const sel = $(selectId);
  const val = sel.value;
  if (val === '__manual__' || val === '') {
    return $(manualId).value.trim();
  }
  return val;
}

function setupComplexityToggle(selectId, manualId) {
  const sel = $(selectId);
  const manual = $(manualId);
  if (!sel || !manual) return;
  sel.addEventListener('change', () => {
    manual.classList.toggle('show', sel.value === '__manual__');
  });
}

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
      checkReviewCard(result.result.slug);
      loadSystemProblem(result.result.slug);
    } else {
      setStatus('抓取返回为空，请刷新题目页后重试。', 'err');
    }
  } catch (e) {
    setStatus('抓取异常: ' + e.message + '（刷新题目页后重试）', 'err');
  }
}

// [模块D] LeetCode 页内复习浮窗: 根据 slug 查找系统内题卡, 提供重做标记(AC/卡住)+边界遗漏笔记回传
async function checkReviewCard(slug) {
  if (!slug) return;
  try {
    const r = await fetch(await apiUrl(`/cards/by-slug/${encodeURIComponent(slug)}`));
    const j = await r.json();
    const data = j && j.data;
    if (!data || !data.card_id) return;
    renderReviewBox(data);
  } catch (e) {
    console.warn('[AlgoMate] 查询复习卡失败', e);
  }
}

function renderReviewBox(data) {
  if (document.getElementById('review-box')) return;
  const box = document.createElement('div');
  box.id = 'review-box';
  box.className = 'conflict-box';
  box.style.marginTop = '10px';
  box.style.borderColor = '#0969da';
  box.innerHTML = `
    <div class="hint" style="color:#0969da;font-weight:600;margin-bottom:6px;">🔁 系统内已导入该题，可在此标记重做结果</div>
    <div class="hint">题目：${data.title || ''}</div>
    <div class="field" style="margin-top:6px;">
      <label>边界遗漏 / 为什么卡住 / 注意点（可选，记录到本次复习笔记）</label>
      <textarea id="f-review-note" placeholder="重做时漏掉的边界条件 / 卡住的原因 / 下次要注意的点…"></textarea>
    </div>
    <div style="display:flex;gap:8px;margin-top:6px;">
      <button type="button" class="btn btn-primary" id="btn-redone-ac" style="background:#1f883d;">已 AC ✓</button>
      <button type="button" class="btn btn-primary" id="btn-redone-stuck" style="background:#cf222e;">卡住了</button>
    </div>
    <div class="status" id="review-status"></div>
  `;
  const importBtn = $('btn-import');
  importBtn.parentNode.insertBefore(box, importBtn);

  const note = () => $('f-review-note').value.trim();
  const setRS = (msg, type) => {
    const el = $('review-status');
    el.textContent = msg;
    el.className = 'status' + (type ? ' ' + type : '');
  };
  $('btn-redone-ac').addEventListener('click', async () => {
    await markReview(data.card_id, 'redone_ac', note(), setRS);
  });
  $('btn-redone-stuck').addEventListener('click', async () => {
    await markReview(data.card_id, 'redone_stuck', note(), setRS);
  });
}

async function markReview(cardId, action, note, setRS) {
  try {
    setRS('正在记录…');
    const r = await fetch(await apiUrl(`/reviews/${cardId}/complete`), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, note }),
    });
    if (r.ok) {
      setRS(action === 'redone_ac' ? '已记录：重做 AC ✓' : '已记录：重做卡住，已存入复习队列', 'ok');
      $('btn-redone-ac').disabled = true;
      $('btn-redone-stuck').disabled = true;
    } else {
      const j = await r.json().catch(() => ({}));
      setRS('记录失败: ' + JSON.stringify(j), 'err');
    }
  } catch (e) {
    setRS('请求失败: ' + e.message + '（确认后端地址已配置且服务可用）', 'err');
  }
}

// ===== 系统已有题目信息加载（重做编辑场景：展示+直接修改补充）=====
function resetEditState() {
  const oldBox = document.getElementById('system-info');
  if (oldBox) oldBox.remove();
  document.querySelectorAll('#f-techniques .tech-item').forEach((r) => r.remove());
  window.__editSolutionId = null;
  window.__systemTechniqueIds = null;
}

async function loadSystemProblem(slug) {
  if (!slug) return;
  try {
    const r = await fetch(await apiUrl(`/problems/by-slug/${encodeURIComponent(slug)}`));
    if (r.status === 404 || !r.ok) return; // 系统无此题，正常走新建
    const p = await r.json();
    if (window.__recrawl) {
      // 重新抓取后：只提示一行，不预填、不进入编辑模式
      showRecrawlHint(p.title);
      return;
    }
    renderSystemEdit(p);
  } catch (e) {
    console.warn('[AlgoMate] 加载系统题目信息失败', e);
  }
}

function showRecrawlHint(title) {
  const oldBox = document.getElementById('system-info');
  if (oldBox) oldBox.remove();
  const box = document.createElement('div');
  box.id = 'system-info';
  box.className = 'conflict-box';
  box.style.marginTop = '10px';
  box.style.borderColor = '#0969da';
  box.innerHTML = `<div class="hint" style="color:#0969da;font-weight:600;">↻ 已重新抓取页面「${title}」，本次将以新解法 / 新技巧导入（不更新系统已有内容）</div>`;
  $('btn-import').parentNode.insertBefore(box, $('btn-import'));
}

function renderSystemEdit(p) {
  // 幂等：移除旧框
  const oldBox = document.getElementById('system-info');
  if (oldBox) oldBox.remove();

  // 预填题卡突破口（用户尚未填写时）
  if (!$('f-breakthrough').value) $('f-breakthrough').value = p.breakthrough || '';

  const sols = p.solutions || [];
  const box = document.createElement('div');
  box.id = 'system-info';
  box.className = 'conflict-box';
  box.style.marginTop = '10px';
  box.style.borderColor = '#0969da';
  const rows = sols
    .map((s) => `<div class="sol-row" data-id="${s.id}" style="padding:4px 8px;margin:2px 0;border:1px solid #d0d7de;border-radius:4px;cursor:pointer;font-size:12px;">📄 ${s.name}（${s.language || '未知语言'}）</div>`)
    .join('');
  box.innerHTML = `
    <div class="hint" style="color:#0969da;font-weight:600;margin-bottom:6px;">📋 系统中已有该题「${p.title}」，突破口已预填</div>
    <div class="hint" style="margin-bottom:6px;">默认新增一条解法；点击下方已有解法可展开其内容进行编辑（改完点导入即更新该解法）。删除已有技巧条目会同步删除系统技巧卡。</div>
    ${sols.length > 0
      ? `<div class="hint" style="margin-bottom:4px;">系统已有 ${sols.length} 条解法（点击展开编辑）：</div><div id="sol-list">${rows}</div>`
      : '<div class="hint">系统暂无解法，本次将新建第一条解法</div>'}
  `;
  const importBtn = $('btn-import');
  importBtn.parentNode.insertBefore(box, importBtn);

  // 系统已有技巧卡渲染为可编辑条目（去重，带 technique_id 供更新）
  const seen = new Set();
  const sysTechIds = [];
  sols.forEach((s) => (s.techniques || []).forEach((t) => {
    if (seen.has(t.id)) return;
    seen.add(t.id);
    sysTechIds.push(t.id);
    addTechniqueRow(t.name, t.use_cases || '', t.notes || '', t.code_template || '', t.id);
  }));
  window.__systemTechniqueIds = sysTechIds;

  window.__editSolutionId = null;
  // 解法名称列表：点击展开编辑该解法；再点同一行取消（回到新增）
  document.querySelectorAll('#sol-list .sol-row').forEach((row) => {
    row.addEventListener('click', () => {
      const id = parseInt(row.dataset.id, 10);
      const isActive = window.__editSolutionId === id;
      document.querySelectorAll('#sol-list .sol-row').forEach((r) => { r.style.outline = 'none'; });
      window.__editSolutionId = null;
      if (isActive) return; // 再点同一行 = 取消编辑，回到新增
      const sol = sols.find((s) => s.id === id);
      if (!sol) return;
      window.__editSolutionId = id;
      row.style.outline = '2px solid #0969da';
      $('f-name').value = sol.name || '';
      $('f-notes').value = sol.notes || '';
      fillComplexity('f-time-select', 'f-time', sol.time_complexity || '');
      fillComplexity('f-space-select', 'f-space', sol.space_complexity || '');
      $('f-pitfalls').value = (sol.pitfalls || []).join('\n');
      // 代码保留本次抓取的新代码，不覆盖
    });
  });
}

function fillComplexity(selectId, manualId, value) {
  if (!value) return;
  const sel = $(selectId);
  const manual = $(manualId);
  const matched = Array.from(sel.options).some((o) => o.value === value);
  if (matched) {
    sel.value = value;
  } else {
    sel.value = '__manual__';
    manual.value = value;
  }
  manual.classList.toggle('show', sel.value === '__manual__');
}

// 提交导入 (updateSolutionId 仅在冲突时显式传入; 首次导入不传)
async function doImport(updateSolutionId) {
  const d = window.__collected;
  if (!d) return;
  const btn = $('btn-import');
  btn.disabled = true;
  setStatus('正在导入…');

  const pitfalls = $('f-pitfalls').value
    .split('\n').map((s) => s.trim()).filter(Boolean);
  const techItems = collectTechniques();
  // 编辑模式：系统已有技巧中不在本次列表里的 → 提交删除
  const sysTechIds = window.__systemTechniqueIds || [];
  const keptIds = techItems.filter((i) => i.technique_id).map((i) => i.technique_id);
  const deletedTechIds = sysTechIds.filter((id) => !keptIds.includes(id));

  const payload = {
    slug: d.slug,
    title: d.title,
    difficulty: d.difficulty,
    description: d.description || '',
    leetcode_link: d.source || '',
    tags: d.tags || [],
    code: $('f-code').value,
    language: d.language || '',
    name: $('f-name').value,
    notes: $('f-notes').value,
    breakthrough: $('f-breakthrough').value,
    time_complexity: getComplexity('f-time-select', 'f-time'),
    space_complexity: getComplexity('f-space-select', 'f-space'),
    pitfalls,
    techniques: techItems,
  };
  if (updateSolutionId != null) {
    payload.update_solution_id = updateSolutionId;
  } else if (window.__editSolutionId != null) {
    payload.update_solution_id = window.__editSolutionId;
  }
  if (deletedTechIds.length) payload.deleted_technique_ids = deletedTechIds;

  try {
    const r = await fetch(await apiUrl('/import'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const j = await r.json();
    if (r.ok) {
      if (j.already_exists) {
        setStatus('已存在相同解法（代码与语言一致），未重复创建。', 'ok');
        btn.textContent = '已存在 ✓';
        return;
      }
      if (j.conflict) {
        showConflictChoice(j);
        return;
      }
      const extra = j.is_new_problem
        ? ''
        : `（已存在该题，本次追加第 ${j.existing_solution_count + 1} 条解法）`;
      const editing = payload.update_solution_id != null;
      setStatus(
        (editing ? '已更新该解法及题卡信息' : (j.is_new_problem ? '导入成功（新建题卡）' : '已存在该题，追加解法')) +
          ` · 技巧卡 ${j.technique_ids.length} 张` + extra,
        'ok'
      );
      btn.textContent = '已导入 ✓';
      const tip = document.createElement('div');
      tip.className = 'hint';
      tip.style.marginTop = '6px';
      tip.innerHTML = '下次重做时打开插件即可再次修改补充（题卡突破口 / 解法破题思路 / 技巧卡）。';
      statusEl.parentNode.insertBefore(tip, statusEl.nextSibling);

      const base = await getBase();
      const viewBtn = document.createElement('a');
      viewBtn.className = 'btn btn-view';
      viewBtn.textContent = '在 AlgoMate 中查看 →';
      viewBtn.href = `${base}/card/problem/${j.problem_id}`;
      viewBtn.target = '_blank';
      viewBtn.rel = 'noopener noreferrer';
      viewBtn.style.marginTop = '8px';
      viewBtn.style.display = 'inline-block';
      statusEl.parentNode.insertBefore(viewBtn, tip.nextSibling);
    } else {
      setStatus('导入失败: ' + JSON.stringify(j), 'err');
      btn.disabled = false;
    }
  } catch (e) {
    setStatus('请求失败: ' + e.message + '（确认后端地址已配置且服务可用）', 'err');
    btn.disabled = false;
  }
}

function showConflictChoice(j) {
  const box = document.createElement('div');
  box.className = 'conflict-box';
  box.innerHTML = '<div class="hint">该题已有解法，请选择：</div>';
  j.existing_solutions.forEach((sol) => {
    const row = document.createElement('div');
    row.className = 'conflict-row';
    row.innerHTML = `<span>解法 #${sol.id}（${sol.language || '未知语言'}）${sol.notes ? ' · ' + sol.notes : ''}</span>`;
    const upd = document.createElement('button');
    upd.className = 'btn btn-add';
    upd.textContent = '更新此解法';
    upd.addEventListener('click', () => {
      box.remove();
      doImport(sol.id);
    });
    row.appendChild(upd);
    box.appendChild(row);
  });
  const addNew = document.createElement('button');
  addNew.className = 'btn btn-primary';
  addNew.textContent = '仍要新增一条解法';
  addNew.addEventListener('click', () => {
    box.remove();
    doImport(null);
  });
  box.appendChild(addNew);

  const btn = $('btn-import');
  btn.disabled = false;
  statusEl.parentNode.insertBefore(box, statusEl.nextSibling);
}
