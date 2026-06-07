// dashboard.js — LAON VaultGuard frontend v0.1.1

const API = '';
let currentFilter = 'all';
let currentRepoId = '';
let selectedFindings = new Set();

// ── SSE ──
const evtSource = new EventSource('/api/events');
evtSource.addEventListener('connected', () => updateConnection(true));
evtSource.addEventListener('scan:started', () => { updateConnection(true); loadStatus(); });
evtSource.addEventListener('scan:completed', () => { loadStatus(); loadFindings(); });
evtSource.addEventListener('finding:new', () => { loadFindings(); loadStatus(); });
evtSource.addEventListener('finding:acknowledged', () => { loadFindings(); loadStatus(); });
evtSource.onerror = () => updateConnection(false);

function updateConnection(connected) {
  const dot = document.getElementById('status-dot');
  const status = document.getElementById('connection-status');
  dot.className = connected ? 'status-dot online' : 'status-dot offline';
  status.textContent = connected ? '연결됨' : '연결 끊김 (재연결 중...)';
}

// ── Status ──
async function loadStatus() {
  try {
    const res = await fetch(`${API}/api/status`);
    const data = await res.json();
    document.getElementById('open-count').textContent = data.open_findings;
    document.getElementById('scan-count').textContent = data.total_scans;
    document.getElementById('repo-count').textContent = data.registered_repos;
    document.getElementById('last-scan').textContent = data.last_scan
      ? new Date(data.last_scan).toLocaleString('ko-KR') : '없음';
  } catch (err) { console.error(err); }
}

// ── Findings ──
async function loadFindings() {
  const params = new URLSearchParams();
  params.set('limit', '200');
  if (currentFilter !== 'all') params.set('severity', currentFilter);
  if (currentRepoId) params.set('repo_id', currentRepoId);

  const dateFrom = document.getElementById('date-from')?.value;
  const dateTo = document.getElementById('date-to')?.value;
  if (dateFrom) params.set('from', dateFrom);
  if (dateTo) params.set('to', dateTo);

  try {
    const res = await fetch(`${API}/api/findings?${params}`);
    const data = await res.json();
    const tbody = document.getElementById('findings-body');

    if (data.total === 0) {
      tbody.innerHTML = '<tr><td colspan="9" class="empty-state">탐지된 시크릿이 없습니다 🎉</td></tr>';
      updateBulkBar();
      return;
    }

    tbody.innerHTML = data.findings.map(f => {
      const checked = selectedFindings.has(f.id) ? 'checked' : '';
      return `
      <tr class="${checked ? 'selected' : ''}" data-id="${f.id}">
        <td class="check-col"><input type="checkbox" ${checked} onchange="toggleFinding('${f.id}', this.checked)"></td>
        <td><span class="badge ${f.severity}">${f.severity}</span></td>
        <td style="font-size:12px;color:var(--muted)">${f.repo_name || '-'}</td>
        <td>${f.provider}</td>
        <td>${f.secret_type || f.secretType}</td>
        <td title="${f.file_path || f.filePath}">${shortenPath(f.file_path || f.filePath)}</td>
        <td><code>${f.masked_fingerprint || f.maskedFingerprint}</code></td>
        <td style="font-size:12px">${new Date(f.detected_at || f.detectedAt).toLocaleString('ko-KR')}</td>
        <td>
          ${f.acknowledged
            ? '<span style="color:var(--green)">✓ 확인됨</span>'
            : `<button class="btn" onclick="acknowledge('${f.id}')">확인</button>`
          }
        </td>
      </tr>`;
    }).join('');

    document.getElementById('select-all').checked = false;
    updateBulkBar();
  } catch (err) { console.error(err); }
}

async function acknowledge(id) {
  try {
    await fetch(`${API}/api/findings/${id}/acknowledge`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ note: 'Acknowledged via dashboard' }),
    });
    selectedFindings.delete(id);
    loadFindings();
    loadStatus();
  } catch (err) { console.error(err); }
}

// ── Bulk actions ──
function toggleFinding(id, checked) {
  if (checked) selectedFindings.add(id);
  else selectedFindings.delete(id);
  updateBulkBar();
}

function toggleSelectAll() {
  const checked = document.getElementById('select-all').checked;
  document.querySelectorAll('#findings-body input[type=checkbox]').forEach(cb => {
    cb.checked = checked;
    const id = cb.closest('tr')?.dataset.id;
    if (id) {
      if (checked) selectedFindings.add(id);
      else selectedFindings.delete(id);
    }
  });
  updateBulkBar();
}

function clearSelection() {
  selectedFindings.clear();
  document.querySelectorAll('#findings-body input[type=checkbox]').forEach(cb => cb.checked = false);
  document.getElementById('select-all').checked = false;
  updateBulkBar();
}

function updateBulkBar() {
  const bar = document.getElementById('bulk-bar');
  const count = document.getElementById('bulk-count');
  if (selectedFindings.size > 0) {
    bar.classList.remove('hidden');
    count.textContent = `${selectedFindings.size}개 선택`;
  } else {
    bar.classList.add('hidden');
  }
}

async function bulkAcknowledge() {
  if (selectedFindings.size === 0) return;
  const btn = document.querySelector('#bulk-bar .btn.primary');
  btn.disabled = true;
  btn.textContent = '처리 중...';

  try {
    await fetch(`${API}/api/findings/acknowledge/bulk`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids: [...selectedFindings], note: 'Bulk acknowledged via dashboard' }),
    });
    selectedFindings.clear();
    loadFindings();
    loadStatus();
  } catch (err) { console.error(err); }
  btn.disabled = false;
  btn.textContent = '✅ 선택 항목 확인';
}

// ── Filters ──
function setFilter(filter) {
  currentFilter = filter;
  document.querySelectorAll('.filter-bar > .btn').forEach(b => b.classList.remove('active'));
  document.querySelector(`.filter-bar > .btn:nth-child(${['all','critical','high','medium','info'].indexOf(filter) + 1})`)?.classList.add('active');
  loadFindings();
}

function setRepoFilter(repoId) {
  currentRepoId = repoId;
  loadFindings();
}

async function loadRepos() {
  try {
    const res = await fetch(`${API}/api/repos`);
    const data = await res.json();
    const select = document.getElementById('repo-filter');
    select.innerHTML = '<option value="">전체</option>' +
      data.repos.map(r => `<option value="${r.id}">${r.name} (${r.findings_open})</option>`).join('');
  } catch (err) { console.error(err); }
}

// ── Scan ──
async function triggerScan() {
  try {
    const btn = document.getElementById('scan-btn');
    btn.disabled = true;
    btn.textContent = '⏳ 스캔 중...';
    await fetch(`${API}/api/scan/trigger`, { method: 'POST' });
    setTimeout(() => {
      btn.disabled = false;
      btn.textContent = '🔄 지금 스캔';
      loadStatus();
      loadFindings();
    }, 5000);
  } catch (err) { console.error(err); }
}

function shortenPath(filePath) {
  if (!filePath) return '';
  if (filePath.length <= 40) return filePath;
  return '...' + filePath.slice(-37);
}

// ── Init ──
loadStatus();
loadFindings();
loadRepos();
