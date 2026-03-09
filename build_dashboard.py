#!/usr/bin/env python3
"""
Builds a static HTML dashboard from the Fact Database YAML files.

Usage:
    python3 build_dashboard.py
    open dashboard.html
"""

import glob
import json
import os
import sys
from datetime import datetime

# Use PyYAML if available, otherwise fall back to a basic parser
try:
    import yaml
except ImportError:
    print("PyYAML not installed. Installing...")
    os.system(f"{sys.executable} -m pip install pyyaml")
    import yaml

FACT_DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Fact Database")
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard.html")

SECTION_LABELS = {
    "01_Macro_Context": "01 — Macro Context",
    "02_Regional_Endowment": "02 — Regional Endowment",
    "03_Market_Definition": "03 — Market Definition",
    "04_Demand_Assessment": "04 — Demand Assessment",
    "05_Supply_Side": "05 — Supply Side",
    "06_Gap_Analysis": "06 — Gap Analysis",
    "07_Growth_Outlook": "07 — Growth Outlook",
    "08_Pricing": "08 — Pricing",
    "09_Risk_Factors": "09 — Risk Factors",
    "10_Conclusions": "10 — Conclusions",
}

SOURCE_TYPE_LABELS = {
    "government_publication": "Government Publication",
    "government_data": "Government Data",
    "international_organisation": "International Organisation",
    "academic_paper": "Academic Paper",
    "industry_report": "Industry Report",
    "company_filing": "Company Filing",
    "company_website": "Company Website",
    "media": "Media",
    "consultation": "Consultation",
    "internal_data": "Internal Data",
    "local_file": "Local File",
}


def load_facts():
    facts = []
    yaml_files = sorted(glob.glob(os.path.join(FACT_DB_DIR, "*.yaml")))
    for fpath in yaml_files:
        fname = os.path.basename(fpath)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        try:
            docs = yaml.safe_load(content)
        except yaml.YAMLError as e:
            print(f"  WARN: YAML parse error in {fname}: {e}")
            continue
        if not docs or not isinstance(docs, list):
            continue
        for fact in docs:
            if not isinstance(fact, dict) or "id" not in fact:
                continue
            # Normalise fields
            fact.setdefault("claim", "")
            fact.setdefault("source_quotes", [])
            fact.setdefault("source_name", "")
            fact.setdefault("source_author", "")
            fact.setdefault("source_url", "")
            fact.setdefault("source_page", "")
            fact.setdefault("source_type", "")
            fact.setdefault("source_date", "")
            fact.setdefault("sections_used", [])
            fact.setdefault("data_table", "")
            fact.setdefault("verified", False)
            fact.setdefault("verification_notes", "")
            fact.setdefault("confidence", "")
            fact.setdefault("date_added", "")
            fact.setdefault("added_by", "")
            fact.setdefault("notes", "")
            fact["_file"] = fname
            # Clean up whitespace in multi-line strings
            if isinstance(fact["claim"], str):
                fact["claim"] = " ".join(fact["claim"].split())
            if isinstance(fact["source_quotes"], list):
                fact["source_quotes"] = [
                    " ".join(q.split()) if isinstance(q, str) else str(q)
                    for q in fact["source_quotes"]
                ]
            if isinstance(fact["verification_notes"], str):
                fact["verification_notes"] = " ".join(fact["verification_notes"].split())
            facts.append(fact)
    return facts


def build_stats(facts):
    total = len(facts)
    verified = sum(1 for f in facts if f["verified"])
    unverified = total - verified

    by_section = {}
    for f in facts:
        for s in f["sections_used"]:
            by_section.setdefault(s, {"total": 0, "verified": 0})
            by_section[s]["total"] += 1
            if f["verified"]:
                by_section[s]["verified"] += 1

    by_source_type = {}
    for f in facts:
        st = f["source_type"] or "unknown"
        by_source_type.setdefault(st, 0)
        by_source_type[st] += 1

    by_source = {}
    for f in facts:
        sn = f["source_name"] or "Unknown"
        by_source.setdefault(sn, 0)
        by_source[sn] += 1

    return {
        "total": total,
        "verified": verified,
        "unverified": unverified,
        "by_section": by_section,
        "by_source_type": by_source_type,
        "by_source": dict(sorted(by_source.items(), key=lambda x: -x[1])),
    }


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Fact Database — Market Feasibility</title>
<style>
  :root {
    --bg: #0d1117;
    --surface: #161b22;
    --surface2: #21262d;
    --border: #30363d;
    --text: #e6edf3;
    --text-muted: #8b949e;
    --accent: #58a6ff;
    --green: #3fb950;
    --red: #f85149;
    --orange: #d29922;
    --purple: #bc8cff;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.5;
    padding: 24px;
  }
  h1 { font-size: 24px; font-weight: 600; margin-bottom: 4px; }
  .subtitle { color: var(--text-muted); font-size: 14px; margin-bottom: 24px; }

  /* Summary cards */
  .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
  }
  .card-label { font-size: 12px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }
  .card-value { font-size: 32px; font-weight: 600; margin-top: 4px; }
  .card-value.green { color: var(--green); }
  .card-value.red { color: var(--red); }
  .card-value.accent { color: var(--accent); }

  /* Two-col layout for charts */
  .charts { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }
  @media (max-width: 900px) { .charts { grid-template-columns: 1fr; } }
  .chart-box {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
  }
  .chart-box h2 { font-size: 14px; font-weight: 600; margin-bottom: 12px; }

  /* Bar chart rows */
  .bar-row { display: flex; align-items: center; margin-bottom: 8px; font-size: 13px; }
  .bar-label { width: 180px; flex-shrink: 0; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .bar-track { flex: 1; height: 20px; background: var(--surface2); border-radius: 4px; overflow: hidden; position: relative; margin: 0 8px; }
  .bar-fill { height: 100%; border-radius: 4px; transition: width 0.3s; }
  .bar-fill.verified { background: var(--green); }
  .bar-fill.unverified { background: var(--red); opacity: 0.6; }
  .bar-fill.type-bar { background: var(--accent); }
  .bar-count { width: 50px; text-align: right; font-size: 12px; color: var(--text-muted); flex-shrink: 0; }

  /* Controls */
  .controls {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    align-items: center;
  }
  .controls input[type="text"] {
    flex: 1;
    min-width: 200px;
    padding: 8px 12px;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
    font-size: 14px;
    outline: none;
  }
  .controls input[type="text"]:focus { border-color: var(--accent); }
  .controls select {
    padding: 8px 12px;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
    font-size: 14px;
    outline: none;
    cursor: pointer;
  }

  /* Fact table */
  .fact-table-wrap {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
  }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  thead th {
    text-align: left;
    padding: 10px 12px;
    background: var(--surface2);
    border-bottom: 1px solid var(--border);
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    color: var(--text-muted);
    cursor: pointer;
    user-select: none;
    white-space: nowrap;
  }
  thead th:hover { color: var(--text); }
  thead th .sort-arrow { margin-left: 4px; font-size: 10px; }
  tbody td {
    padding: 10px 12px;
    border-bottom: 1px solid var(--border);
    vertical-align: top;
  }
  tbody tr:hover { background: rgba(88, 166, 255, 0.04); }
  tbody tr:last-child td { border-bottom: none; }

  .badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
  }
  .badge-verified { background: rgba(63, 185, 80, 0.15); color: var(--green); }
  .badge-unverified { background: rgba(248, 81, 73, 0.15); color: var(--red); }
  .badge-section {
    background: rgba(88, 166, 255, 0.1);
    color: var(--accent);
    margin: 1px 2px;
    font-weight: 500;
  }
  .badge-source-type {
    background: rgba(188, 140, 255, 0.1);
    color: var(--purple);
    font-weight: 500;
  }

  .claim-text { max-width: 350px; }
  .source-quotes { max-width: 300px; color: var(--text-muted); font-style: italic; }
  .source-link {
    color: var(--accent);
    text-decoration: none;
    word-break: break-all;
    font-size: 12px;
  }
  .source-link:hover { text-decoration: underline; }

  .expand-btn {
    background: none;
    border: 1px solid var(--border);
    border-radius: 4px;
    color: var(--text-muted);
    cursor: pointer;
    padding: 2px 6px;
    font-size: 11px;
    margin-top: 4px;
  }
  .expand-btn:hover { color: var(--text); border-color: var(--text-muted); }

  .empty-state {
    text-align: center;
    padding: 48px;
    color: var(--text-muted);
  }

  .results-count {
    font-size: 13px;
    color: var(--text-muted);
    padding: 8px 0;
  }
</style>
</head>
<body>

<h1>Fact Database</h1>
<p class="subtitle">Market Feasibility Section — Maven Libera &middot; Generated %%GENERATED_AT%%</p>

<div class="cards" id="cards"></div>
<div class="charts">
  <div class="chart-box">
    <h2>Facts by Section</h2>
    <div id="chart-sections"></div>
  </div>
  <div class="chart-box">
    <h2>Facts by Source Type</h2>
    <div id="chart-types"></div>
  </div>
</div>

<div class="controls">
  <input type="text" id="search" placeholder="Search claims, sources, quotes...">
  <select id="filter-section">
    <option value="">All Sections</option>
  </select>
  <select id="filter-verified">
    <option value="">All Status</option>
    <option value="true">Verified</option>
    <option value="false">Unverified</option>
  </select>
  <select id="filter-source-type">
    <option value="">All Source Types</option>
  </select>
</div>

<div class="results-count" id="results-count"></div>

<div class="fact-table-wrap">
  <table>
    <thead>
      <tr>
        <th data-sort="id">ID <span class="sort-arrow"></span></th>
        <th data-sort="verified">Status <span class="sort-arrow"></span></th>
        <th data-sort="claim">Claim <span class="sort-arrow"></span></th>
        <th>Source Quotes</th>
        <th data-sort="source_name">Source <span class="sort-arrow"></span></th>
        <th>Sections</th>
        <th data-sort="date_added">Added <span class="sort-arrow"></span></th>
      </tr>
    </thead>
    <tbody id="fact-body"></tbody>
  </table>
</div>

<script>
const FACTS = %%FACTS_JSON%%;
const STATS = %%STATS_JSON%%;
const SECTION_LABELS = %%SECTION_LABELS_JSON%%;
const SOURCE_TYPE_LABELS = %%SOURCE_TYPE_LABELS_JSON%%;

// --- Summary Cards ---
function renderCards() {
  const el = document.getElementById('cards');
  const pct = STATS.total > 0 ? Math.round((STATS.verified / STATS.total) * 100) : 0;
  el.innerHTML = `
    <div class="card"><div class="card-label">Total Facts</div><div class="card-value accent">${STATS.total}</div></div>
    <div class="card"><div class="card-label">Verified</div><div class="card-value green">${STATS.verified}</div></div>
    <div class="card"><div class="card-label">Unverified</div><div class="card-value red">${STATS.unverified}</div></div>
    <div class="card"><div class="card-label">Verified %</div><div class="card-value ${pct >= 80 ? 'green' : pct >= 50 ? 'accent' : 'red'}">${pct}%</div></div>
    <div class="card"><div class="card-label">Sections</div><div class="card-value accent">${Object.keys(STATS.by_section).length}</div></div>
    <div class="card"><div class="card-label">Sources</div><div class="card-value accent">${Object.keys(STATS.by_source).length}</div></div>
  `;
}

// --- Bar Charts ---
function renderCharts() {
  const secEl = document.getElementById('chart-sections');
  const maxSec = Math.max(...Object.values(STATS.by_section).map(s => s.total), 1);
  let secHtml = '';
  const secKeys = Object.keys(SECTION_LABELS);
  for (const key of secKeys) {
    const data = STATS.by_section[key] || { total: 0, verified: 0 };
    const uv = data.total - data.verified;
    const vPct = (data.verified / maxSec) * 100;
    const uPct = (uv / maxSec) * 100;
    const label = SECTION_LABELS[key] || key;
    secHtml += `<div class="bar-row">
      <div class="bar-label" title="${label}">${label}</div>
      <div class="bar-track">
        <div style="display:flex;height:100%">
          <div class="bar-fill verified" style="width:${vPct}%"></div>
          <div class="bar-fill unverified" style="width:${uPct}%"></div>
        </div>
      </div>
      <div class="bar-count">${data.verified}/${data.total}</div>
    </div>`;
  }
  secEl.innerHTML = secHtml;

  const typeEl = document.getElementById('chart-types');
  const maxType = Math.max(...Object.values(STATS.by_source_type), 1);
  let typeHtml = '';
  const sortedTypes = Object.entries(STATS.by_source_type).sort((a, b) => b[1] - a[1]);
  for (const [type, count] of sortedTypes) {
    const pct = (count / maxType) * 100;
    const label = SOURCE_TYPE_LABELS[type] || type;
    typeHtml += `<div class="bar-row">
      <div class="bar-label" title="${label}">${label}</div>
      <div class="bar-track"><div class="bar-fill type-bar" style="width:${pct}%"></div></div>
      <div class="bar-count">${count}</div>
    </div>`;
  }
  typeEl.innerHTML = typeHtml;
}

// --- Filters ---
function populateFilters() {
  const secSelect = document.getElementById('filter-section');
  for (const [key, label] of Object.entries(SECTION_LABELS)) {
    const opt = document.createElement('option');
    opt.value = key;
    opt.textContent = label;
    secSelect.appendChild(opt);
  }
  const typeSelect = document.getElementById('filter-source-type');
  for (const [key, label] of Object.entries(SOURCE_TYPE_LABELS)) {
    const opt = document.createElement('option');
    opt.value = key;
    opt.textContent = label;
    typeSelect.appendChild(opt);
  }
}

// --- Table ---
let sortCol = 'id';
let sortAsc = true;

function truncate(text, max) {
  if (!text) return '';
  return text.length > max ? text.slice(0, max) + '...' : text;
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function getFilteredFacts() {
  const search = document.getElementById('search').value.toLowerCase();
  const section = document.getElementById('filter-section').value;
  const verified = document.getElementById('filter-verified').value;
  const sourceType = document.getElementById('filter-source-type').value;

  return FACTS.filter(f => {
    if (section && !(f.sections_used || []).includes(section)) return false;
    if (verified !== '' && String(f.verified) !== verified) return false;
    if (sourceType && f.source_type !== sourceType) return false;
    if (search) {
      const haystack = [
        f.id, f.claim, f.source_name, f.source_author, f.source_url,
        f.verification_notes, f.notes,
        ...(f.source_quotes || [])
      ].join(' ').toLowerCase();
      if (!haystack.includes(search)) return false;
    }
    return true;
  }).sort((a, b) => {
    let va = a[sortCol] ?? '';
    let vb = b[sortCol] ?? '';
    if (typeof va === 'boolean') { va = va ? 1 : 0; vb = vb ? 1 : 0; }
    if (typeof va === 'string') { va = va.toLowerCase(); vb = vb.toLowerCase(); }
    if (va < vb) return sortAsc ? -1 : 1;
    if (va > vb) return sortAsc ? 1 : -1;
    return 0;
  });
}

function renderTable() {
  const facts = getFilteredFacts();
  const tbody = document.getElementById('fact-body');
  document.getElementById('results-count').textContent = `Showing ${facts.length} of ${FACTS.length} facts`;

  if (facts.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No facts match your filters.</td></tr>';
    return;
  }

  tbody.innerHTML = facts.map(f => {
    const statusBadge = f.verified
      ? '<span class="badge badge-verified">Verified</span>'
      : '<span class="badge badge-unverified">Unverified</span>';

    const quotes = (f.source_quotes || []).map(q => escapeHtml(q)).join('<br><br>');

    const sections = (f.sections_used || []).map(s =>
      `<span class="badge badge-section">${s.replace('_', ' ')}</span>`
    ).join(' ');

    const sourceTypeLabel = SOURCE_TYPE_LABELS[f.source_type] || f.source_type || '';
    const sourceLink = f.source_url
      ? `<a class="source-link" href="${escapeHtml(f.source_url)}" target="_blank" rel="noopener">${escapeHtml(truncate(f.source_name || f.source_url, 60))}</a>`
      : escapeHtml(f.source_name || '');

    const verNotes = f.verification_notes
      ? `<br><span style="font-size:11px;color:var(--orange)">Note: ${escapeHtml(f.verification_notes)}</span>`
      : '';

    return `<tr>
      <td style="white-space:nowrap;font-family:monospace;font-size:12px">${escapeHtml(f.id)}</td>
      <td>${statusBadge}${verNotes}</td>
      <td class="claim-text">${escapeHtml(f.claim)}</td>
      <td class="source-quotes">${quotes || '<span style="color:var(--text-muted)">—</span>'}</td>
      <td>${sourceLink}<br><span class="badge badge-source-type">${escapeHtml(sourceTypeLabel)}</span>
        ${f.source_date ? `<br><span style="font-size:11px;color:var(--text-muted)">${escapeHtml(f.source_date)}</span>` : ''}</td>
      <td>${sections}</td>
      <td style="white-space:nowrap;font-size:12px;color:var(--text-muted)">${escapeHtml(f.date_added || '')}</td>
    </tr>`;
  }).join('');
}

// --- Sort ---
document.querySelectorAll('thead th[data-sort]').forEach(th => {
  th.addEventListener('click', () => {
    const col = th.dataset.sort;
    if (sortCol === col) { sortAsc = !sortAsc; }
    else { sortCol = col; sortAsc = true; }
    // Update arrows
    document.querySelectorAll('thead th .sort-arrow').forEach(s => s.textContent = '');
    th.querySelector('.sort-arrow').textContent = sortAsc ? ' ▲' : ' ▼';
    renderTable();
  });
});

// --- Events ---
document.getElementById('search').addEventListener('input', renderTable);
document.getElementById('filter-section').addEventListener('change', renderTable);
document.getElementById('filter-verified').addEventListener('change', renderTable);
document.getElementById('filter-source-type').addEventListener('change', renderTable);

// --- Init ---
renderCards();
renderCharts();
populateFilters();
renderTable();
</script>
</body>
</html>"""


def main():
    print("Loading facts from YAML files...")
    facts = load_facts()
    print(f"  Found {len(facts)} facts")

    stats = build_stats(facts)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = HTML_TEMPLATE
    html = html.replace("%%FACTS_JSON%%", json.dumps(facts, default=str))
    html = html.replace("%%STATS_JSON%%", json.dumps(stats, default=str))
    html = html.replace("%%SECTION_LABELS_JSON%%", json.dumps(SECTION_LABELS))
    html = html.replace("%%SOURCE_TYPE_LABELS_JSON%%", json.dumps(SOURCE_TYPE_LABELS))
    html = html.replace("%%GENERATED_AT%%", generated_at)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  Dashboard written to: {OUTPUT_FILE}")
    print(f"  Open it with: open dashboard.html")


if __name__ == "__main__":
    main()
