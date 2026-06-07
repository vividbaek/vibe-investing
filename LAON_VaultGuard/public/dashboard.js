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
        <td title="Click for detail" style="cursor:pointer;color:var(--medium);text-decoration:underline" onclick="showFindingDetail('${f.id}')">${shortenPath(f.file_path || f.filePath)}</td>
        <td><code>${f.masked_fingerprint || f.maskedFingerprint}</code></td>
        <td style="font-size:12px">${new Date(f.detected_at || f.detectedAt).toLocaleString('ko-KR')}</td>
        <td>
          ${f.acknowledged
            ? '<span style="color:var(--green);font-size:12px">Done</span> <button class="btn" onclick="unacknowledge(\'' + f.id + '\')" style="margin-left:4px">Undo</button>'
            : '<button class="btn" onclick="acknowledge(\'' + f.id + '\')">Confirm</button>'
          }
          <button class="btn" onclick="addComment('${f.id}')" style="margin-left:4px" title="Add note">Note</button>
        </td>
      </tr>`;
    }).join('');

    document.getElementById('select-all').checked = false;
    updateBulkBar();
  } catch (err) { console.error(err); }
}

async function acknowledge(id) {
  // fetch current finding to check for existing note
  var existingNote = '';
  try {
    var r = await fetch(API + '/api/findings/' + id);
    var f = await r.json();
    existingNote = f.acknowledged_note || f.acknowledgedNote || '';
  } catch(e) {}

  var note = existingNote;
  if (!note) {
    note = prompt('Review required: How was this resolved?\n\n(example: Rotated key, regenerated token, false positive, added to .gitignore, etc.)');
    if (!note || !note.trim()) { alert('A comment is required to acknowledge. Please describe how this was resolved.'); return; }
    note = note.trim();
  }

  try {
    await fetch(`${API}/api/findings/${id}/acknowledge`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ note: note }),
    });
    selectedFindings.delete(id);
    loadFindings();
    loadStatus();
  } catch (err) { console.error(err); }
}

async function unacknowledge(id) {
  try {
    await fetch(`${API}/api/findings/${id}/unacknowledge`, { method: 'PUT' });
    loadFindings();
    loadStatus();
  } catch (err) { console.error(err); }
}

async function addComment(id) {
  const comment = prompt('Add comment:');
  if (!comment) return;
  try {
    await fetch(`${API}/api/findings/${id}/comment`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ comment }),
    });
    loadFindings();
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
loadRepoScanList();
loadOAuthStatus();
loadAlertConfig();

// ── Alert Config ──
async function loadAlertConfig() {
  try {
    const res = await fetch(`${API}/api/alerts/config`);
    const data = await res.json();
    document.getElementById('ch-slack').checked = data.slack;
    document.getElementById('ch-telegram').checked = data.telegram;
    document.getElementById('ch-email').checked = data.email;
    document.getElementById('ch-teams').checked = data.teams || false;
    document.getElementById('ch-discord').checked = data.discord || false;
    document.getElementById('report-freq').value = data.frequency;
  } catch (err) { console.error(err); }
}

async function saveAlertConfig() {
  const config = {
    slack: document.getElementById('ch-slack').checked,
    telegram: document.getElementById('ch-telegram').checked,
    email: document.getElementById('ch-email').checked,
    teams: document.getElementById('ch-teams').checked,
    discord: document.getElementById('ch-discord').checked,
    frequency: document.getElementById('report-freq').value,
  };
  try {
    await fetch(`${API}/api/alerts/config`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
  } catch (err) { console.error(err); }
}

function exportReport() {
  window.open(API + '/api/report', '_blank');
}

function setupAlerts() {
  window.open('/alert-setup.html', 'alert-setup');
}

function toggleAlerts() {
  const panel = document.getElementById('alert-panel');
  panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
  if (panel.style.display === 'block') loadAlertConfig();
}

// ── GitHub OAuth ──
async function loadOAuthStatus() {
  try {
    const res = await fetch(`${API}/api/oauth/status`);
    const data = await res.json();
    const btn = document.getElementById('github-btn');
    const connectBtn = document.getElementById('github-connect-btn');
    const disconnectBtn = document.getElementById('github-disconnect-btn');
    const status = document.getElementById('github-status');

    btn.style.display = 'inline-block';
    if (data.connected) {
      status.innerHTML = `<span style="color:var(--green)">✓</span> ${data.user}`;
      connectBtn.style.display = 'none';
      disconnectBtn.style.display = 'inline-block';
    } else {
      status.textContent = data.clientIdConfigured ? '' : '';
      connectBtn.style.display = 'inline-block';
      disconnectBtn.style.display = 'none';
    }
  } catch (err) { console.error(err); }
}

function toggleGithub() {
  const panel = document.getElementById('github-panel');
  panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
  if (panel.style.display === 'block') loadGithubRepos();
}

function connectGithub() {
  fetch(`${API}/api/oauth/github`)
    .then(r => r.json())
    .then(data => {
      if (data.error) {
        alert('GitHub OAuth not configured.\n\n' + data.message + '\n\nSee: ' + data.docs);
        return;
      }
      window.open(`${API}/api/oauth/github`, 'github-oauth', 'width=600,height=700');
      let attempts = 0;
      const poll = setInterval(async () => {
        try {
          const res = await fetch(`${API}/api/oauth/status`);
          const d = await res.json();
          if (d.connected) { clearInterval(poll); loadOAuthStatus(); loadGithubRepos(); }
          if (++attempts > 60) clearInterval(poll);
        } catch {}
      }, 2000);
    });
}

async function disconnectGithub() {
  await fetch(`${API}/api/oauth/disconnect`, { method: 'POST' });
  loadOAuthStatus();
  document.getElementById('github-repo-list').innerHTML = '';
}

async function loadGithubRepos() {
  try {
    const res = await fetch(`${API}/api/github/repos`);
    if (!res.ok) {
      document.getElementById('github-repo-list').innerHTML =
        '<div style="color:var(--muted);padding:20px;text-align:center">GitHub 연동이 필요합니다</div>';
      return;
    }
    const data = await res.json();
    const list = document.getElementById('github-repo-list');
    list.innerHTML = data.repos.map(r => `
      <div style="display:flex;justify-content:space-between;align-items:center;padding:8px;border-bottom:1px solid var(--border)">
        <span>${r.private ? '🔒' : '📁'} ${r.full_name}</span>
        <button class="btn" onclick="addGithubRepo('${r.full_name}','${r.html_url}')">+ 등록</button>
      </div>
    `).join('');
  } catch (err) { console.error(err); }
}

async function addGithubRepo(fullName, htmlUrl) {
  const [owner, name] = fullName.split('/');
  try {
    await fetch(`${API}/api/repos`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: fullName,
        type: 'github',
        pathOrUrl: htmlUrl,
        branch: 'main',
      }),
    });
    loadRepos();
loadRepoScanList();
    loadGithubRepos();
  } catch (err) { console.error(err); }
}

// Scan History
function toggleHistory() {
  const panel = document.getElementById('history-panel');
  panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
  if (panel.style.display === 'block') loadScanHistory();
}

async function loadScanHistory() {
  try {
    const res = await fetch(API + '/api/scans');
    const data = await res.json();
    const list = document.getElementById('scan-history-list');
    if (data.scans.length === 0) {
      list.innerHTML = '<div style="color:var(--muted);padding:20px;text-align:center">No scan history</div>';
      return;
    }
    list.innerHTML = data.scans.map(s => {
      const time = new Date(s.startedAt).toLocaleString('ko-KR');
      const statusColor = s.status === 'completed' ? 'var(--green)' : s.status === 'failed' ? 'var(--red)' : 'var(--high)';
      const typeLabel = s.repoType === 'github' ? '[GitHub]' : s.repoType === 'gitlab' ? '[GitLab]' : '[Local]';
      const url = s.repoType !== 'local' ? '<br><span style="font-size:11px;color:var(--muted)">' + s.repoUrl + '</span>' : '';
      return '<div style="display:flex;justify-content:space-between;align-items:center;padding:10px;border-bottom:1px solid var(--border)">' +
        '<div>' +
          '<span style="color:' + statusColor + ';font-weight:bold">' + s.status.toUpperCase() + '</span> ' +
          '<span>' + typeLabel + ' ' + s.repoName + '</span>' +
          url +
          '<br><span style="font-size:11px;color:var(--muted)">' +
            'ID: ' + s.id.slice(0,8) + ' | ' + time +
            (s.status === 'completed' ? ' | scanned: ' + s.filesScanned + ' files, findings: ' +
              (s.findingsCritical + s.findingsHigh + s.findingsMedium + s.findingsInfo) +
              ' (C:' + s.findingsCritical + ' H:' + s.findingsHigh + ' M:' + s.findingsMedium + ' I:' + s.findingsInfo + ')' : '') +
            (s.errorMessage ? ' | error: ' + s.errorMessage.slice(0,60) : '') +
          '</span>' +
        '</div>' +
        '<span style="font-size:11px;color:var(--muted)">' + (s.llmProvidersUsed || []).join(', ') + '</span>' +
      '</div>';
    }).join('');
  } catch (err) { console.error(err); }
}

// Finding detail modal
function showFindingDetail(id) {
  fetch(API + '/api/findings/' + id).then(r => r.json()).then(f => {
    var fp = f.masked_fingerprint || f.maskedFingerprint;
    var path = f.file_path || f.filePath;
    var note = f.acknowledged_note || f.acknowledgedNote || '';
    var line = f.line || 0;
    var repoId = f.repoId || f.repo_id || '';
    var repoName = f.repo_name || '-';
    var severity = (f.severity || '').toUpperCase();
    var provider = f.provider || '';
    var secretType = f.secret_type || f.secretType || '';
    var evidence = f.evidence_note || f.evidenceNote || '-';
    var remediation = f.remediation || '-';
    var detected = new Date(f.detected_at || f.detectedAt).toLocaleString();
    var sources = (f.llmSources || f.llm_sources || []).join(', ') || '-';

    var detailHtml =
      '<p><strong>File:</strong> <code>' + path + (line ? ':' + line : '') + '</code>' +
      ' <a href="#" onclick="openFileView(\'' + repoId + '\',\'' + path + '\',' + line + ');return false" style="color:var(--accent);font-size:12px">(view)</a>' +
      ' <button class="btn" onclick="copyDetail()" style="margin-left:8px;font-size:11px">Copy</button>' +
      ' <button class="btn" onclick="downloadMD()" style="font-size:11px">MD</button></p>' +
      '<p><strong>Repo:</strong> ' + repoName + '</p>' +
      '<p><strong>Confidence:</strong> ' + f.confidence + '</p>' +
      '<p><strong>Fingerprint:</strong> <code>' + fp + '</code></p>' +
      '<p><strong>Evidence:</strong> ' + evidence + '</p>' +
      '<p><strong>Remediation:</strong> ' + remediation + '</p>' +
      '<p><strong>Detected:</strong> ' + detected + '</p>' +
      (note ? '<p><strong>Resolution note:</strong> <em>' + note + '</em></p>' : '') +
      '<p><strong>LLM Sources:</strong> ' + sources + '</p>';

    document.getElementById('modal-title').textContent = '[' + severity + '] ' + provider + ' — ' + secretType;
    document.getElementById('modal-body').innerHTML = detailHtml;

    // store for copy/download
    window._modalFinding = {
      severity, provider, secretType, path, line, fp, repoName, evidence, remediation, note, detected, sources
    };

    document.getElementById('finding-modal').style.display = 'flex';
  }).catch(err => console.error(err));
}

function copyDetail() {
  var f = window._modalFinding;
  if (!f) return;
  var text = '[' + f.severity + '] ' + f.provider + ' — ' + f.secretType + '\n' +
    'File: ' + f.path + (f.line ? ':' + f.line : '') + '\n' +
    'Repo: ' + f.repoName + '\n' +
    'Fingerprint: ' + f.fp + '\n' +
    'Evidence: ' + f.evidence + '\n' +
    'Remediation: ' + f.remediation + '\n' +
    'Detected: ' + f.detected + '\n' +
    (f.note ? 'Resolution: ' + f.note + '\n' : '');
  navigator.clipboard.writeText(text).then(function() {
    alert('Copied to clipboard');
  }).catch(function() {
    prompt('Copy manually:', text);
  });
}

function downloadMD() {
  var f = window._modalFinding;
  if (!f) return;
  var md = '# [' + f.severity + '] ' + f.provider + ' — ' + f.secretType + '\n\n' +
    '| Field | Value |\n|-------|-------|\n' +
    '| File | `' + f.path + (f.line ? ':' + f.line : '') + '` |\n' +
    '| Repo | ' + f.repoName + ' |\n' +
    '| Fingerprint | `' + f.fp + '` |\n' +
    '| Confidence | ' + (window._modalFinding.confidence || '') + ' |\n' +
    '| Evidence | ' + f.evidence + ' |\n' +
    '| Remediation | ' + f.remediation + ' |\n' +
    '| Detected | ' + f.detected + ' |\n' +
    (f.note ? '| Resolution | ' + f.note + ' |\n' : '') +
    '\n---\n';
  var blob = new Blob([md], { type: 'text/markdown' });
  var a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'finding-' + f.path.replace(/[^a-zA-Z0-9]/g, '_') + '.md';
  a.click();
}

function closeModal() {
  document.getElementById('finding-modal').style.display = 'none';
}

// Close modal on background click
document.addEventListener('click', function(e) {
  if (e.target.id === 'finding-modal') closeModal();
});

// File viewer
function openFileView(repoId, filePath, line) {
  var url = API + '/api/file?repo_id=' + repoId + '&path=' + encodeURIComponent(filePath) + '&line=' + line;
  window.open(url, 'file-view', 'width=900,height=600');
}
