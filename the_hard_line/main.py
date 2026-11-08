import os
import time
import re
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import asyncpg

DB_HOST = os.getenv("DB_HOST", "192.168.1.201")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "loay")
DB_PASS = os.getenv("DB_PASS", "2004")
DB_NAME = os.getenv("DB_NAME", "egypt_users")

pool: Optional[asyncpg.Pool] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    print(f"Connecting to database at {DB_HOST}:{DB_PORT}/{DB_NAME}...")
    pool = await asyncpg.create_pool(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        min_size=1,
        max_size=4,
        ssl=False,
        command_timeout=15.0
    )
    print("Database connection pool ready.")
    yield
    if pool:
        await pool.close()
        print("Database connection pool closed.")

app = FastAPI(title="The Hard Line", lifespan=lifespan)

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>THE HARD LINE // DATABASE</title>
  <style>
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }
    body {
      background-color: #050505;
      color: #ffffff;
      font-family: ui-monospace, "Cascadia Code", "SF Mono", "Source Code Pro", Menlo, Consolas, monospace;
      font-size: 13px;
      line-height: 1.5;
      letter-spacing: -0.01em;
      padding: 24px 20px 60px 20px;
    }
    a {
      color: #ffffff;
      text-decoration: underline;
      text-underline-offset: 3px;
    }
    a:hover {
      background-color: #ffffff;
      color: #000000;
      text-decoration: none;
    }
    .container {
      max-width: 1080px;
      margin: 0 auto;
    }
    /* Header */
    header {
      border: 1px solid #222222;
      background: #0a0a0a;
      padding: 16px 20px;
      margin-bottom: 24px;
    }
    .header-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      border-bottom: 1px solid #1a1a1a;
      padding-bottom: 12px;
      margin-bottom: 12px;
    }
    .title {
      font-size: 18px;
      font-weight: 700;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: #ffffff;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 11px;
      color: #888888;
      border: 1px solid #262626;
      padding: 3px 8px;
    }
    .status-dot {
      width: 7px;
      height: 7px;
      background: #00ff66;
      display: inline-block;
    }
    .header-meta {
      font-size: 11px;
      color: #777777;
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
    }
    .header-meta span strong {
      color: #cccccc;
    }

    /* Search Box */
    .search-panel {
      border: 1px solid #222222;
      background: #0a0a0a;
      padding: 20px;
      margin-bottom: 24px;
    }
    .mode-selector {
      display: flex;
      gap: 6px;
      margin-bottom: 14px;
      flex-wrap: wrap;
    }
    .mode-btn {
      background: #111111;
      border: 1px solid #262626;
      color: #888888;
      font-family: inherit;
      font-size: 11px;
      padding: 6px 12px;
      cursor: pointer;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .mode-btn:hover {
      color: #ffffff;
      border-color: #444444;
    }
    .mode-btn.active {
      background: #ffffff;
      color: #000000;
      border-color: #ffffff;
      font-weight: 700;
    }
    .search-row {
      display: flex;
      gap: 8px;
    }
    .search-input {
      flex: 1;
      background: #000000;
      border: 1px solid #333333;
      color: #ffffff;
      font-family: inherit;
      font-size: 14px;
      padding: 12px 14px;
      outline: none;
    }
    .search-input:focus {
      border-color: #ffffff;
    }
    .search-btn {
      background: #ffffff;
      color: #000000;
      border: 1px solid #ffffff;
      font-family: inherit;
      font-size: 13px;
      font-weight: 700;
      padding: 12px 24px;
      cursor: pointer;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .search-btn:hover {
      background: #cccccc;
      border-color: #cccccc;
    }
    .hint {
      font-size: 11px;
      color: #666666;
      margin-top: 10px;
    }

    /* Stats Line */
    .status-bar {
      display: flex;
      justify-content: space-between;
      font-size: 11px;
      color: #888888;
      padding: 4px 4px 12px 4px;
      border-bottom: 1px solid #1a1a1a;
      margin-bottom: 20px;
    }

    /* Results */
    .results-container {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .dossier-card {
      border: 1px solid #222222;
      background: #090909;
      padding: 16px;
    }
    .dossier-card:hover {
      border-color: #383838;
    }
    .dossier-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      flex-wrap: wrap;
      gap: 8px;
      border-bottom: 1px solid #1a1a1a;
      padding-bottom: 10px;
      margin-bottom: 14px;
    }
    .person-name {
      font-size: 16px;
      font-weight: 700;
      color: #ffffff;
    }
    .person-fbid {
      font-size: 12px;
      color: #aaaaaa;
      border: 1px solid #222222;
      padding: 2px 6px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 10px 16px;
    }
    .field-row {
      display: flex;
      font-size: 12px;
      border-bottom: 1px dashed #141414;
      padding-bottom: 4px;
    }
    .field-label {
      width: 120px;
      color: #777777;
      text-transform: uppercase;
      font-size: 10px;
      letter-spacing: 0.05em;
      flex-shrink: 0;
      padding-top: 1px;
    }
    .field-value {
      flex: 1;
      color: #e0e0e0;
      word-break: break-word;
    }
    .empty-state {
      border: 1px dashed #222222;
      padding: 40px 20px;
      text-align: center;
      color: #666666;
    }
    .error-box {
      border: 1px solid #aa2222;
      background: #1a0808;
      color: #ff6666;
      padding: 14px;
      margin-bottom: 20px;
    }
    .loading {
      color: #888888;
      text-align: center;
      padding: 30px;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="header-top">
        <div class="title">THE HARD LINE // INTELLIGENCE DIRECTORY</div>
        <div class="badge">
          <span class="status-dot"></span>
          <span>POSTGRES: ONLINE</span>
        </div>
      </div>
      <div class="header-meta">
        <span>DATASET: <strong>45,183,146 RECORDS</strong></span>
        <span>INDEXED: <strong>FBID, PHONE</strong></span>
        <span>NODE: <strong>192.168.1.201:5432</strong></span>
        <span>LATENCY: <strong>&lt; 5ms</strong></span>
      </div>
    </header>

    <div class="search-panel">
      <div class="mode-selector">
        <button class="mode-btn active" data-mode="auto" onclick="setMode('auto')">AUTO DETECT</button>
        <button class="mode-btn" data-mode="fbid" onclick="setMode('fbid')">FBID</button>
        <button class="mode-btn" data-mode="phone" onclick="setMode('phone')">PHONE</button>
        <button class="mode-btn" data-mode="name" onclick="setMode('name')">NAME</button>
      </div>

      <div class="search-row">
        <input 
          type="text" 
          id="queryInput" 
          class="search-input" 
          placeholder="ENTER FBID (e.g. 100008623627444), PHONE (+20... or 01...), OR NAME"
          autofocus
        >
        <button class="search-btn" id="searchBtn" onclick="performSearch()">SEARCH</button>
      </div>
      <div class="hint">
        Auto-detection recognizes numeric Facebook IDs (1000...), Egyptian phone formats (+201..., 01...), or text names. Press ENTER to search.
      </div>
    </div>

    <div class="status-bar" id="statusBar">
      <span id="statusMessage">AWAITING QUERY INPUT</span>
      <span id="statusTime"></span>
    </div>

    <div id="errorContainer"></div>
    <div id="resultsContainer" class="results-container">
      <div class="empty-state">NO QUERY SUBMITTED. ENTER SEARCH TARGET ABOVE.</div>
    </div>
  </div>

  <script>
    let currentMode = 'auto';

    function setMode(mode) {
      currentMode = mode;
      document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-mode') === mode);
      });
      const input = document.getElementById('queryInput');
      if (mode === 'fbid') input.placeholder = 'ENTER FACEBOOK ID (e.g. 100010734491831)';
      else if (mode === 'phone') input.placeholder = 'ENTER PHONE NUMBER (e.g. 010..., 011..., +201...)';
      else if (mode === 'name') input.placeholder = 'ENTER NAME (FIRST NAME, LAST NAME, OR FULL NAME)';
      else input.placeholder = 'ENTER FBID, PHONE NUMBER (+20... or 01...), OR NAME';
      input.focus();
    }

    document.getElementById('queryInput').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        performSearch();
      }
    });

    async function performSearch() {
      const q = document.getElementById('queryInput').value.trim();
      if (!q) return;

      const statusBar = document.getElementById('statusMessage');
      const statusTime = document.getElementById('statusTime');
      const resultsContainer = document.getElementById('resultsContainer');
      const errorContainer = document.getElementById('errorContainer');

      errorContainer.innerHTML = '';
      resultsContainer.innerHTML = '<div class="loading">[ EXECUTING INDEX LOOKUP... ]</div>';
      statusBar.textContent = `SEARCHING: "${q}" (MODE: ${currentMode.toUpperCase()})...`;
      statusTime.textContent = '';

      const t0 = performance.now();
      try {
        const resp = await fetch(`/api/search?q=${encodeURIComponent(q)}&mode=${currentMode}`);
        const data = await resp.json();
        const t1 = performance.now();

        if (!resp.ok) {
          throw new Error(data.detail || 'Search query failed');
        }

        const duration = (data.duration_ms !== undefined) ? data.duration_ms : Math.round(t1 - t0);
        statusBar.textContent = `COMPLETED: ${data.count} RECORD(S) FOUND [RESOLVED AS ${data.type.toUpperCase()}]`;
        statusTime.textContent = `SERVER: ${duration} ms | CLIENT: ${Math.round(t1 - t0)} ms`;

        if (!data.results || data.results.length === 0) {
          resultsContainer.innerHTML = `<div class="empty-state">NO MATCHING DOSSIER FOUND FOR: "${q}"</div>`;
          return;
        }

        let html = '';
        for (const item of data.results) {
          const displayName = item.full_name || `${item.fname || ''} ${item.sname || ''}`.trim() || 'UNKNOWN';
          const profileLink = item.fbaccount 
            ? `<a href="${item.fbaccount}" target="_blank" rel="noopener noreferrer">${item.fbaccount}</a>` 
            : (item.fbid ? `<a href="https://facebook.com/${item.fbid}" target="_blank" rel="noopener noreferrer">https://facebook.com/${item.fbid}</a>` : 'N/A');

          html += `
          <div class="dossier-card">
            <div class="dossier-header">
              <div class="person-name">${escapeHtml(displayName)}</div>
              <div class="person-fbid">FBID: <strong>${escapeHtml(item.fbid || 'N/A')}</strong></div>
            </div>
            <div class="grid">
              <div class="field-row">
                <div class="field-label">PHONE:</div>
                <div class="field-value">${escapeHtml(item.phone || 'N/A')}</div>
              </div>
              <div class="field-row">
                <div class="field-label">GENDER:</div>
                <div class="field-value">${escapeHtml(item.gender || 'N/A')}</div>
              </div>
              <div class="field-row">
                <div class="field-label">BIRTHDAY:</div>
                <div class="field-value">${escapeHtml(item.birthday || 'N/A')}</div>
              </div>
              <div class="field-row">
                <div class="field-label">LOCATION:</div>
                <div class="field-value">${escapeHtml(item.location || 'N/A')}</div>
              </div>
              <div class="field-row">
                <div class="field-label">HOMETOWN:</div>
                <div class="field-value">${escapeHtml(item.hometown || 'N/A')}</div>
              </div>
              <div class="field-row">
                <div class="field-label">RELATIONSHIP:</div>
                <div class="field-value">${escapeHtml(item.relationship || 'N/A')}</div>
              </div>
              <div class="field-row">
                <div class="field-label">WORKPLACE:</div>
                <div class="field-value">${escapeHtml(item.workplace || 'N/A')}</div>
              </div>
              <div class="field-row">
                <div class="field-label">JOB TITLE:</div>
                <div class="field-value">${escapeHtml(item.job_title || 'N/A')}</div>
              </div>
              <div class="field-row">
                <div class="field-label">EDUCATION:</div>
                <div class="field-value">${escapeHtml(item.education || 'N/A')}</div>
              </div>
              <div class="field-row">
                <div class="field-label">EMAIL:</div>
                <div class="field-value">${escapeHtml(item.email || 'N/A')}</div>
              </div>
              <div class="field-row" style="grid-column: 1 / -1;">
                <div class="field-label">FB URL:</div>
                <div class="field-value">${profileLink}</div>
              </div>
            </div>
          </div>
          `;
        }
        resultsContainer.innerHTML = html;
      } catch (err) {
        errorContainer.innerHTML = `<div class="error-box">ERROR: ${escapeHtml(err.message)}</div>`;
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

    // Support query in URL hash or param: ?q=123
    window.addEventListener('DOMContentLoaded', () => {
      const params = new URLSearchParams(window.location.search);
      const q = params.get('q');
      if (q) {
        document.getElementById('queryInput').value = q;
        performSearch();
      }
    });
  </script>
</body>
</html>
"""

def normalize_phone_variants(raw: str) -> List[str]:
    # Strip spaces, dashes, parentheses
    clean = re.sub(r'[\s\-\(\)]', '', raw)
    variants = {clean}
    
    # Egypt specific variants:
    # Standard DB format: +2010xxxxxxxx, +2011xxxxxxxx, +2012xxxxxxxx, +2015xxxxxxxx
    if clean.startswith('+20'):
        variants.add(clean)
        variants.add(clean[3:]) # without +20 -> 10xxxxxxxx
        variants.add('0' + clean[3:]) # 010xxxxxxxx
        variants.add('20' + clean[3:]) # 2010xxxxxxxx
    elif clean.startswith('20') and len(clean) >= 12:
        variants.add('+' + clean)
        variants.add(clean)
        variants.add(clean[2:])
        variants.add('0' + clean[2:])
    elif clean.startswith('01') and len(clean) == 11:
        variants.add('+2' + clean)
        variants.add('2' + clean)
        variants.add(clean)
        variants.add(clean[1:])
    elif clean.startswith('1') and len(clean) == 10:
        variants.add('+20' + clean)
        variants.add('20' + clean)
        variants.add('0' + clean)
        variants.add(clean)

    return list(variants)

def map_user_record(row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "fbid": row["fbid"],
        "phone": row["phone"],
        "fname": row["fname"],
        "sname": row["sname"],
        "full_name": row["unknown_7"] or f"{row['fname'] or ''} {row['sname'] or ''}".strip(),
        "gender": row["gender"],
        "birthday": row["unknown_4"],
        "fbaccount": row["fbaccount"],
        "workplace": row["unknown_9"],
        "job_title": row["unknown_10"],
        "location": row["unknown_11"],
        "hometown": row["unknown_12"],
        "education": row["unknown_13"],
        "email": row["email"],
        "relationship": row["unknown_19"]
    }

@app.get("/", response_class=HTMLResponse)
async def get_index():
    return HTMLResponse(content=HTML_PAGE, status_code=200)

@app.get("/api/search")
async def api_search(
    q: str = Query(..., min_length=1, max_length=100),
    mode: str = Query("auto", regex="^(auto|fbid|phone|name)$")
):
    global pool
    if not pool:
        raise HTTPException(status_code=503, detail="Database pool not initialized")

    query = q.strip()
    t0 = time.time()
    detected_type = mode

    # Auto detection logic
    if mode == "auto":
        clean_num = re.sub(r'[\s\-\(\)\+]', '', query)
        if query.startswith('+') or (clean_num.startswith('01') and len(clean_num) in (10, 11)) or (clean_num.startswith('201') and len(clean_num) in (12, 13)):
            detected_type = "phone"
        elif clean_num.isdigit() and len(clean_num) >= 12:
            detected_type = "fbid"
        elif clean_num.isdigit() and len(clean_num) in (9, 10, 11):
            detected_type = "phone"
        else:
            detected_type = "name"

    rows = []
    async with pool.acquire() as conn:
        if detected_type == "fbid":
            # Exact B-Tree index lookup on fbid
            sql = "SELECT * FROM users WHERE fbid = $1 LIMIT 50;"
            rows = await conn.fetch(sql, query)

            # If not found and user entered full URL, extract fbid from url
            if not rows and "facebook.com/" in query:
                extracted = query.rstrip("/").split("/")[-1]
                rows = await conn.fetch("SELECT * FROM users WHERE fbid = $1 OR fbaccount ILIKE $2 LIMIT 50;", extracted, f"%{extracted}%")

        elif detected_type == "phone":
            # Indexed search across phone variants (+201..., 01..., etc.)
            variants = normalize_phone_variants(query)
            sql = "SELECT * FROM users WHERE phone = ANY($1::text[]) LIMIT 50;"
            rows = await conn.fetch(sql, variants)

        elif detected_type == "name":
            # Fast B-Tree index pattern scan on lower(fname)
            lower_q = query.lower()
            sql = """
                SELECT * FROM users 
                WHERE lower(fname) LIKE $1 
                LIMIT 50;
            """
            rows = await conn.fetch(sql, f"{lower_q}%")

    t1 = time.time()
    duration_ms = round((t1 - t0) * 1000, 2)

    results = [map_user_record(r) for r in rows]
    return {
        "query": query,
        "type": detected_type,
        "count": len(results),
        "duration_ms": duration_ms,
        "results": results
    }

@app.get("/healthz")
async def health_check():
    return {"status": "ok", "app": "The Hard Line"}
