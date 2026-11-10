/**
 * The Hardline — Client Search Controller & Renderer
 */
let currentMode = 'url';

function setMode(mode) {
  currentMode = mode;
  document.querySelectorAll('.hardline-mode-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-mode') === mode);
  });
  const input = document.getElementById('queryInput');
  const hint = document.getElementById('modeHint');

  if (mode === 'url') {
    input.placeholder = 'PASTE FACEBOOK PROFILE URL (e.g. facebook.com/share/... or facebook.com/username)';
    if (hint) hint.textContent = 'Paste any Facebook profile URL (short share link, username link, or profile.php). Press ENTER to resolve.';
  } else if (mode === 'fbid') {
    input.placeholder = 'ENTER FACEBOOK ID (e.g. 100007438327407)';
    if (hint) hint.textContent = 'Search directly by numeric Facebook User ID. Instant B-Tree indexed scan.';
  } else if (mode === 'phone') {
    input.placeholder = 'ENTER PHONE NUMBER (e.g. 010..., 011..., 012..., +201...)';
    if (hint) hint.textContent = 'Accepts Egyptian local format (01X...) or international format (+201X...).';
  } else if (mode === 'name') {
    input.placeholder = 'ENTER NAME (e.g. Abraam Marcos, Mohamed Ahmed, etc.)';
    if (hint) hint.textContent = 'Supports first name, full name, or reversed name query with sub-millisecond execution.';
  } else {
    input.placeholder = 'ENTER FBID, PHONE NUMBER (+20... or 01...), PROFILE URL, OR NAME';
    if (hint) hint.textContent = 'Auto-detection recognizes URLs, numeric Facebook IDs, Egyptian phone numbers, or text names.';
  }
  input.focus();
}

async function performSearch() {
  const inputEl = document.getElementById('queryInput');
  const q = inputEl.value.trim();
  if (!q) return;

  const statusBar = document.getElementById('statusMessage');
  const statusTime = document.getElementById('statusTime');
  const resultsContainer = document.getElementById('resultsContainer');
  const errorContainer = document.getElementById('errorContainer');

  errorContainer.innerHTML = '';
  resultsContainer.innerHTML = '<div class="hardline-empty-state" style="color: #ffcf69;">EXECUTING QUERY...</div>';
  
  if (currentMode === 'url' || q.includes('facebook.com') || q.includes('fb.me')) {
    statusBar.textContent = `RESOLVING FACEBOOK PROFILE URL & DOSSIER FOR: "${q}"...`;
  } else {
    statusBar.textContent = `SEARCHING: "${q}" (MODE: ${currentMode.toUpperCase()})...`;
  }
  statusTime.textContent = '';

  const t0 = performance.now();
  try {
    const url = `/api/search?q=${encodeURIComponent(q)}&mode=${encodeURIComponent(currentMode)}`;
    const resp = await fetch(url);

    if (resp.status === 401) {
      window.location.href = '/login';
      return;
    }

    const data = await resp.json();
    const t1 = performance.now();

    if (!resp.ok) {
      throw new Error(data.detail || 'Search query failed');
    }

    const duration = (data.duration_ms !== undefined) ? data.duration_ms : Math.round(t1 - t0);
    statusBar.textContent = `COMPLETED: ${data.count} RECORD(S) FOUND [RESOLVED AS ${data.type.toUpperCase()}]`;
    statusTime.textContent = `SERVER: ${duration} ms | CLIENT: ${Math.round(t1 - t0)} ms`;

    if (!data.results || data.results.length === 0) {
      resultsContainer.innerHTML = `<div class="hardline-empty-state">NO MATCHING DOSSIER FOUND FOR: "${escapeHtml(q)}"</div>`;
      return;
    }

    let html = '';
    for (const item of data.results) {
      const displayName = item.full_name || `${item.fname || ''} ${item.sname || ''}`.trim() || 'UNKNOWN';
      const profileLink = item.fbaccount 
        ? `<a href="${item.fbaccount}" target="_blank" rel="noopener noreferrer">${escapeHtml(item.fbaccount)}</a>` 
        : (item.fbid ? `<a href="https://facebook.com/${item.fbid}" target="_blank" rel="noopener noreferrer">https://facebook.com/${item.fbid}</a>` : 'N/A');

      html += `
      <div class="hardline-card">
        <div class="hardline-card-header">
          <div class="hardline-person-name">${escapeHtml(displayName)}</div>
          <div class="hardline-person-fbid">FBID: <strong>${escapeHtml(item.fbid || 'N/A')}</strong></div>
        </div>
        <div class="hardline-grid">
          <div class="hardline-field-row">
            <div class="hardline-field-label">PHONE:</div>
            <div class="hardline-field-value">${escapeHtml(item.phone || 'N/A')}</div>
          </div>
          <div class="hardline-field-row">
            <div class="hardline-field-label">GENDER:</div>
            <div class="hardline-field-value">${escapeHtml(item.gender || 'N/A')}</div>
          </div>
          <div class="hardline-field-row">
            <div class="hardline-field-label">BIRTHDAY:</div>
            <div class="hardline-field-value">${escapeHtml(item.birthday || 'N/A')}</div>
          </div>
          <div class="hardline-field-row">
            <div class="hardline-field-label">LOCATION:</div>
            <div class="hardline-field-value">${escapeHtml(item.location || 'N/A')}</div>
          </div>
          <div class="hardline-field-row">
            <div class="hardline-field-label">HOMETOWN:</div>
            <div class="hardline-field-value">${escapeHtml(item.hometown || 'N/A')}</div>
          </div>
          <div class="hardline-field-row">
            <div class="hardline-field-label">RELATIONSHIP:</div>
            <div class="hardline-field-value">${escapeHtml(item.relationship || 'N/A')}</div>
          </div>
          <div class="hardline-field-row">
            <div class="hardline-field-label">WORKPLACE:</div>
            <div class="hardline-field-value">${escapeHtml(item.workplace || 'N/A')}</div>
          </div>
          <div class="hardline-field-row">
            <div class="hardline-field-label">JOB TITLE:</div>
            <div class="hardline-field-value">${escapeHtml(item.job_title || 'N/A')}</div>
          </div>
          <div class="hardline-field-row">
            <div class="hardline-field-label">EDUCATION:</div>
            <div class="hardline-field-value">${escapeHtml(item.education || 'N/A')}</div>
          </div>
          <div class="hardline-field-row">
            <div class="hardline-field-label">EMAIL:</div>
            <div class="hardline-field-value">${escapeHtml(item.email || 'N/A')}</div>
          </div>
          <div class="hardline-field-row" style="grid-column: 1 / -1;">
            <div class="hardline-field-label">FB URL:</div>
            <div class="hardline-field-value">${profileLink}</div>
          </div>
        </div>
      </div>
      `;
    }
    resultsContainer.innerHTML = html;
  } catch (err) {
    errorContainer.innerHTML = `<div class="hardline-error-box">ERROR: ${escapeHtml(err.message)}</div>`;
    resultsContainer.innerHTML = '';
    statusBar.textContent = 'SEARCH ABORTED ON ERROR';
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

document.addEventListener('DOMContentLoaded', () => {
  const queryInput = document.getElementById('queryInput');
  if (queryInput) {
    queryInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        performSearch();
      }
    });

    const params = new URLSearchParams(window.location.search);
    const q = params.get('q');
    const mode = params.get('mode');
    if (mode && ['url', 'auto', 'fbid', 'phone', 'name'].includes(mode)) {
      setMode(mode);
    } else {
      setMode('url');
    }
    if (q) {
      queryInput.value = q;
      performSearch();
    }
  }
});
