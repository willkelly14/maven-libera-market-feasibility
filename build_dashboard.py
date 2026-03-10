#!/usr/bin/env python3
"""
Builds a static HTML dashboard from the Fact Database YAML files
and the Documents database.

Usage:
    .venv/bin/python build_dashboard.py
    open dashboard.html
"""

import glob
import json
import os
import sys
from datetime import datetime

try:
    import yaml
except ImportError:
    print("PyYAML not found. Run: .venv/bin/pip install pyyaml")
    sys.exit(1)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FACT_DB_DIR = os.path.join(BASE_DIR, "Fact Database")
DOCS_DIR = os.path.join(BASE_DIR, "Documents")
OUTPUT_FILE = os.path.join(BASE_DIR, "dashboard.html")

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

DOC_TYPE_LABELS = {
    "section_draft": "Section Draft",
    "data_sources": "Data Sources",
    "research_plan": "Research Plan",
    "research_report": "Research Report",
    "source_reference": "Source Reference",
}

DOC_STATUS_LABELS = {
    "draft": "Draft",
    "stub": "Stub",
    "complete": "Complete",
    "in_review": "In Review",
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
            fact.setdefault("claim", "")
            fact.setdefault("source_quotes", [])
            fact.setdefault("source_excerpt", "")
            fact.setdefault("source_name", "")
            fact.setdefault("source_author", "")
            fact.setdefault("source_url", "")
            fact.setdefault("source_page", "")
            fact.setdefault("source_type", "")
            fact.setdefault("source_date", "")
            fact.setdefault("sections_used", [])
            fact.setdefault("document", "")
            fact.setdefault("data_table", "")
            fact.setdefault("verified", False)
            fact.setdefault("verification_notes", "")
            fact.setdefault("confidence", "")
            fact.setdefault("date_added", "")
            fact.setdefault("added_by", "")
            fact.setdefault("notes", "")
            fact["_file"] = fname
            # Clean whitespace in single-line fields
            for field in ["claim", "verification_notes", "notes"]:
                if isinstance(fact[field], str):
                    fact[field] = " ".join(fact[field].split())
            if isinstance(fact["source_quotes"], list):
                fact["source_quotes"] = [
                    " ".join(q.split()) if isinstance(q, str) else str(q)
                    for q in fact["source_quotes"]
                ]
            # Keep source_excerpt as-is (it's markdown, preserve formatting)
            if isinstance(fact["source_excerpt"], str):
                fact["source_excerpt"] = fact["source_excerpt"].strip()
            facts.append(fact)
    return facts


def load_documents():
    index_path = os.path.join(DOCS_DIR, "documents_index.yaml")
    if not os.path.exists(index_path):
        print("  WARN: documents_index.yaml not found")
        return []
    with open(index_path, "r", encoding="utf-8") as f:
        docs_index = yaml.safe_load(f.read())
    if not docs_index or not isinstance(docs_index, list):
        return []

    documents = []
    for doc in docs_index:
        if not isinstance(doc, dict) or "id" not in doc:
            continue
        doc.setdefault("title", "")
        doc.setdefault("type", "")
        doc.setdefault("section", "")
        doc.setdefault("content_file", "")
        doc.setdefault("description", "")
        doc.setdefault("status", "")
        doc.setdefault("date_created", "")
        doc.setdefault("last_updated", "")

        # Clean multi-line description
        if isinstance(doc["description"], str):
            doc["description"] = " ".join(doc["description"].split())

        # Load content file
        content = ""
        if doc["content_file"]:
            content_path = os.path.join(DOCS_DIR, doc["content_file"])
            if os.path.exists(content_path):
                with open(content_path, "r", encoding="utf-8") as f:
                    content = f.read()
            else:
                print(f"  WARN: Content file not found: {doc['content_file']}")
        doc["content"] = content
        documents.append(doc)
    return documents


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

    by_document = {}
    for f in facts:
        d = f["document"] or "Unassigned"
        by_document.setdefault(d, 0)
        by_document[d] += 1

    return {
        "total": total,
        "verified": verified,
        "unverified": unverified,
        "by_section": by_section,
        "by_source_type": by_source_type,
        "by_source": dict(sorted(by_source.items(), key=lambda x: -x[1])),
        "by_document": by_document,
    }


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Fact Database — Market Feasibility</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
:root {
  --bg: #0d1117;
  --surface: #161b22;
  --surface2: #21262d;
  --surface3: #2d333b;
  --border: #30363d;
  --text: #e6edf3;
  --text-muted: #8b949e;
  --accent: #58a6ff;
  --green: #3fb950;
  --red: #f85149;
  --orange: #d29922;
  --purple: #bc8cff;
  --sidebar-w: 260px;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
  background: var(--bg); color: var(--text); line-height: 1.5;
  display: flex; min-height: 100vh;
}

/* ===== SIDEBAR ===== */
.sidebar {
  width: var(--sidebar-w); min-width: var(--sidebar-w);
  background: var(--surface); border-right: 1px solid var(--border);
  display: flex; flex-direction: column; position: fixed;
  top: 0; left: 0; bottom: 0; z-index: 100;
  overflow-y: auto;
}
.sidebar-header {
  padding: 20px 16px 12px; border-bottom: 1px solid var(--border);
}
.sidebar-header h1 { font-size: 16px; font-weight: 700; }
.sidebar-header .subtitle { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
.sidebar-nav { padding: 8px 0; }
.nav-section-label {
  font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;
  color: var(--text-muted); padding: 12px 16px 4px; font-weight: 600;
}
.nav-item {
  display: flex; align-items: center; gap: 8px;
  padding: 7px 16px; font-size: 13px; cursor: pointer;
  color: var(--text-muted); border-left: 3px solid transparent;
  transition: all 0.15s;
}
.nav-item:hover { background: var(--surface2); color: var(--text); }
.nav-item.active {
  background: rgba(88, 166, 255, 0.08); color: var(--accent);
  border-left-color: var(--accent);
}
.nav-item .nav-icon { width: 16px; text-align: center; font-size: 14px; flex-shrink: 0; }
.nav-item .nav-count {
  margin-left: auto; background: var(--surface2); border-radius: 10px;
  padding: 1px 7px; font-size: 11px; min-width: 20px; text-align: center;
}
.nav-divider { height: 1px; background: var(--border); margin: 4px 16px; }

/* ===== MAIN CONTENT ===== */
.main { margin-left: var(--sidebar-w); flex: 1; padding: 24px 32px; max-width: 1400px; }

/* ===== CARDS ===== */
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-bottom: 20px; }
.card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; padding: 14px;
}
.card-label { font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }
.card-value { font-size: 28px; font-weight: 600; margin-top: 2px; }
.card-value.green { color: var(--green); }
.card-value.red { color: var(--red); }
.card-value.accent { color: var(--accent); }

/* ===== CHARTS ===== */
.charts { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 20px; }
@media (max-width: 1000px) { .charts { grid-template-columns: 1fr; } }
.chart-box {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; padding: 14px;
}
.chart-box h2 { font-size: 13px; font-weight: 600; margin-bottom: 10px; }
.bar-row { display: flex; align-items: center; margin-bottom: 6px; font-size: 12px; }
.bar-label { width: 160px; flex-shrink: 0; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.bar-track { flex: 1; height: 16px; background: var(--surface2); border-radius: 3px; overflow: hidden; margin: 0 8px; }
.bar-fill { height: 100%; border-radius: 3px; }
.bar-fill.verified { background: var(--green); }
.bar-fill.unverified { background: var(--red); opacity: 0.6; }
.bar-fill.type-bar { background: var(--accent); }
.bar-count { width: 45px; text-align: right; font-size: 11px; color: var(--text-muted); flex-shrink: 0; }

/* ===== CONTROLS ===== */
.controls {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; padding: 12px 14px; margin-bottom: 12px;
  display: flex; gap: 10px; flex-wrap: wrap; align-items: center;
}
.controls input[type="text"] {
  flex: 1; min-width: 180px; padding: 7px 10px;
  background: var(--surface2); border: 1px solid var(--border);
  border-radius: 6px; color: var(--text); font-size: 13px; outline: none;
}
.controls input:focus { border-color: var(--accent); }
.controls select {
  padding: 7px 10px; background: var(--surface2); border: 1px solid var(--border);
  border-radius: 6px; color: var(--text); font-size: 13px; outline: none; cursor: pointer;
}

/* ===== TABLE ===== */
.results-count { font-size: 12px; color: var(--text-muted); padding: 6px 0; }
.fact-table-wrap {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; overflow: hidden;
}
table { width: 100%; border-collapse: collapse; font-size: 12px; }
thead th {
  text-align: left; padding: 8px 10px; background: var(--surface2);
  border-bottom: 1px solid var(--border); font-weight: 600; font-size: 11px;
  text-transform: uppercase; letter-spacing: 0.3px; color: var(--text-muted);
  cursor: pointer; user-select: none; white-space: nowrap;
}
thead th:hover { color: var(--text); }
thead th .sort-arrow { margin-left: 3px; font-size: 9px; }
tbody td { padding: 8px 10px; border-bottom: 1px solid var(--border); vertical-align: top; }
tbody tr:hover { background: rgba(88, 166, 255, 0.04); }
tbody tr:last-child td { border-bottom: none; }
tbody tr.expanded-row td { border-bottom: none; }

/* Badges */
.badge {
  display: inline-block; padding: 2px 7px; border-radius: 10px;
  font-size: 10px; font-weight: 600; white-space: nowrap;
}
.badge-verified { background: rgba(63, 185, 80, 0.15); color: var(--green); }
.badge-unverified { background: rgba(248, 81, 73, 0.15); color: var(--red); }
.badge-section { background: rgba(88, 166, 255, 0.1); color: var(--accent); margin: 1px 2px; font-weight: 500; }
.badge-source-type { background: rgba(188, 140, 255, 0.1); color: var(--purple); font-weight: 500; }
.badge-doc { background: rgba(210, 153, 34, 0.15); color: var(--orange); font-weight: 500; cursor: pointer; }
.badge-doc:hover { background: rgba(210, 153, 34, 0.25); }
.badge-status { font-weight: 500; }
.badge-status-draft { background: rgba(210, 153, 34, 0.15); color: var(--orange); }
.badge-status-stub { background: rgba(248, 81, 73, 0.12); color: var(--red); }
.badge-status-complete { background: rgba(63, 185, 80, 0.15); color: var(--green); }
.badge-status-in_review { background: rgba(188, 140, 255, 0.15); color: var(--purple); }
.badge-doc-type { background: rgba(88, 166, 255, 0.1); color: var(--accent); font-weight: 500; }

.claim-text { max-width: 300px; }
.source-link { color: var(--accent); text-decoration: none; word-break: break-all; font-size: 11px; }
.source-link:hover { text-decoration: underline; }

/* ===== EXPANDABLE EXCERPT ===== */
.expand-toggle {
  background: none; border: 1px solid var(--border); border-radius: 4px;
  color: var(--text-muted); cursor: pointer; padding: 2px 8px;
  font-size: 11px; margin-top: 4px; display: inline-block;
}
.expand-toggle:hover { color: var(--text); border-color: var(--text-muted); }
.excerpt-row { display: none; }
.excerpt-row.visible { display: table-row; }
.excerpt-cell {
  padding: 0 10px 12px 10px; background: var(--surface2);
  border-bottom: 1px solid var(--border);
}
.excerpt-content {
  padding: 12px 16px; background: var(--bg); border-radius: 6px;
  border: 1px solid var(--border); font-size: 13px; line-height: 1.65;
}
.excerpt-content table { margin: 8px 0; font-size: 12px; }
.excerpt-content th, .excerpt-content td {
  padding: 4px 10px; border: 1px solid var(--border); text-align: left;
}
.excerpt-content th { background: var(--surface2); font-weight: 600; }
.excerpt-content strong { color: var(--accent); font-weight: 600; }
.excerpt-content em { color: var(--text-muted); }
.excerpt-content p { margin: 6px 0; }
.excerpt-content ul, .excerpt-content ol { margin: 6px 0 6px 20px; }
.excerpt-label { font-size: 11px; color: var(--text-muted); text-transform: uppercase; margin-bottom: 6px; letter-spacing: 0.3px; }

/* ===== DOCUMENT VIEW ===== */
.doc-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 20px; }
@media (max-width: 1000px) { .doc-grid { grid-template-columns: 1fr; } }
.doc-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; padding: 16px; cursor: pointer; transition: all 0.15s;
}
.doc-card:hover { border-color: var(--accent); background: rgba(88, 166, 255, 0.04); }
.doc-card.active { border-color: var(--accent); }
.doc-card-title { font-size: 14px; font-weight: 600; margin-bottom: 4px; }
.doc-card-meta { font-size: 11px; color: var(--text-muted); display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-bottom: 6px; }
.doc-card-desc { font-size: 12px; color: var(--text-muted); }
.doc-card-facts { font-size: 11px; color: var(--accent); margin-top: 6px; }

.doc-viewer {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; margin-bottom: 20px; overflow: hidden;
}
.doc-viewer-header {
  padding: 16px 20px; border-bottom: 1px solid var(--border);
  display: flex; justify-content: space-between; align-items: flex-start;
}
.doc-viewer-title { font-size: 16px; font-weight: 600; }
.doc-viewer-meta { font-size: 12px; color: var(--text-muted); margin-top: 4px; }
.doc-viewer-close {
  background: none; border: 1px solid var(--border); border-radius: 4px;
  color: var(--text-muted); cursor: pointer; padding: 4px 10px; font-size: 12px;
}
.doc-viewer-close:hover { color: var(--text); border-color: var(--text-muted); }
.doc-viewer-content {
  padding: 20px; font-size: 14px; line-height: 1.7; max-height: 70vh; overflow-y: auto;
}
.doc-viewer-content h1 { font-size: 20px; margin: 16px 0 8px; }
.doc-viewer-content h2 { font-size: 17px; margin: 14px 0 6px; color: var(--accent); }
.doc-viewer-content h3 { font-size: 14px; margin: 12px 0 4px; }
.doc-viewer-content p { margin: 6px 0; }
.doc-viewer-content ul, .doc-viewer-content ol { margin: 6px 0 6px 24px; }
.doc-viewer-content table { margin: 10px 0; border-collapse: collapse; font-size: 13px; }
.doc-viewer-content th, .doc-viewer-content td {
  padding: 6px 12px; border: 1px solid var(--border); text-align: left;
}
.doc-viewer-content th { background: var(--surface2); font-weight: 600; }
.doc-viewer-content code { background: var(--surface2); padding: 2px 5px; border-radius: 3px; font-size: 12px; }
.doc-viewer-content pre { background: var(--surface2); padding: 12px; border-radius: 6px; overflow-x: auto; font-size: 12px; margin: 8px 0; }
.doc-viewer-content pre code { background: none; padding: 0; }
.doc-viewer-content a { color: var(--accent); }
.doc-viewer-content strong { color: var(--accent); }
.doc-viewer-content hr { border: none; border-top: 1px solid var(--border); margin: 16px 0; }

.doc-facts-section {
  border-top: 1px solid var(--border); padding: 16px 20px;
}
.doc-facts-section h3 { font-size: 13px; font-weight: 600; margin-bottom: 10px; }

/* ===== VIEWS ===== */
.view { display: none; }
.view.active { display: block; }
.page-title { font-size: 20px; font-weight: 600; margin-bottom: 16px; }

/* hide scrollbar styling */
.sidebar::-webkit-scrollbar { width: 6px; }
.sidebar::-webkit-scrollbar-track { background: transparent; }
.sidebar::-webkit-scrollbar-thumb { background: var(--surface2); border-radius: 3px; }
</style>
</head>
<body>

<!-- SIDEBAR -->
<nav class="sidebar">
  <div class="sidebar-header">
    <h1>Market Feasibility</h1>
    <div class="subtitle">Maven Libera &middot; %%GENERATED_AT%%</div>
  </div>
  <div class="sidebar-nav">
    <div class="nav-section-label">Overview</div>
    <div class="nav-item active" data-view="dashboard">
      <span class="nav-icon">&#9632;</span> Dashboard
    </div>

    <div class="nav-divider"></div>
    <div class="nav-section-label">Databases</div>
    <div class="nav-item" data-view="facts">
      <span class="nav-icon">&#10003;</span> Fact Database
      <span class="nav-count" id="nav-fact-count">0</span>
    </div>
    <div class="nav-item" data-view="documents">
      <span class="nav-icon">&#9776;</span> Documents
      <span class="nav-count" id="nav-doc-count">0</span>
    </div>

    <div class="nav-divider"></div>
    <div class="nav-section-label">Sections</div>
    <div id="nav-sections"></div>
  </div>
</nav>

<!-- MAIN -->
<div class="main">

  <!-- DASHBOARD VIEW -->
  <div class="view active" id="view-dashboard">
    <div class="page-title">Dashboard</div>
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
  </div>

  <!-- FACTS VIEW -->
  <div class="view" id="view-facts">
    <div class="page-title">Fact Database</div>
    <div class="controls">
      <input type="text" id="search" placeholder="Search claims, sources, quotes...">
      <select id="filter-section"><option value="">All Sections</option></select>
      <select id="filter-verified">
        <option value="">All Status</option>
        <option value="true">Verified</option>
        <option value="false">Unverified</option>
      </select>
      <select id="filter-source-type"><option value="">All Source Types</option></select>
      <select id="filter-document"><option value="">All Documents</option></select>
    </div>
    <div class="results-count" id="results-count"></div>
    <div class="fact-table-wrap">
      <table>
        <thead>
          <tr>
            <th data-sort="id">ID <span class="sort-arrow"></span></th>
            <th data-sort="verified">Status <span class="sort-arrow"></span></th>
            <th data-sort="document">Doc <span class="sort-arrow"></span></th>
            <th data-sort="claim">Claim <span class="sort-arrow"></span></th>
            <th data-sort="source_name">Source <span class="sort-arrow"></span></th>
            <th>Sections</th>
            <th data-sort="date_added">Added <span class="sort-arrow"></span></th>
          </tr>
        </thead>
        <tbody id="fact-body"></tbody>
      </table>
    </div>
  </div>

  <!-- DOCUMENTS VIEW -->
  <div class="view" id="view-documents">
    <div class="page-title">Documents</div>
    <div class="doc-grid" id="doc-grid"></div>
    <div id="doc-viewer-container"></div>
  </div>

  <!-- SECTION-FILTERED FACTS VIEW -->
  <div class="view" id="view-section">
    <div class="page-title" id="section-view-title"></div>
    <div class="results-count" id="section-results-count"></div>
    <div class="fact-table-wrap">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Status</th>
            <th>Doc</th>
            <th>Claim</th>
            <th>Source</th>
            <th>Added</th>
          </tr>
        </thead>
        <tbody id="section-fact-body"></tbody>
      </table>
    </div>
  </div>

</div>

<script>
const FACTS = %%FACTS_JSON%%;
const DOCUMENTS = %%DOCUMENTS_JSON%%;
const STATS = %%STATS_JSON%%;
const SECTION_LABELS = %%SECTION_LABELS_JSON%%;
const SOURCE_TYPE_LABELS = %%SOURCE_TYPE_LABELS_JSON%%;
const DOC_TYPE_LABELS = %%DOC_TYPE_LABELS_JSON%%;
const DOC_STATUS_LABELS = %%DOC_STATUS_LABELS_JSON%%;

// Build doc lookup
const DOC_MAP = {};
DOCUMENTS.forEach(d => DOC_MAP[d.id] = d);

// --- NAV ---
function initNav() {
  document.getElementById('nav-fact-count').textContent = FACTS.length;
  document.getElementById('nav-doc-count').textContent = DOCUMENTS.length;

  const navSections = document.getElementById('nav-sections');
  for (const [key, label] of Object.entries(SECTION_LABELS)) {
    const count = (STATS.by_section[key] || {}).total || 0;
    navSections.innerHTML += `<div class="nav-item" data-view="section" data-section="${key}">
      <span class="nav-icon" style="font-size:11px">${key.split('_')[0]}</span>
      ${label.split(' — ')[1]}
      <span class="nav-count">${count}</span>
    </div>`;
  }

  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
      document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
      item.classList.add('active');
      const view = item.dataset.view;
      document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
      document.getElementById('view-' + view).classList.add('active');

      if (view === 'section') {
        showSectionView(item.dataset.section);
      }
    });
  });
}

// --- DASHBOARD ---
function renderCards() {
  const el = document.getElementById('cards');
  const pct = STATS.total > 0 ? Math.round((STATS.verified / STATS.total) * 100) : 0;
  el.innerHTML = `
    <div class="card"><div class="card-label">Total Facts</div><div class="card-value accent">${STATS.total}</div></div>
    <div class="card"><div class="card-label">Verified</div><div class="card-value green">${STATS.verified}</div></div>
    <div class="card"><div class="card-label">Unverified</div><div class="card-value red">${STATS.unverified}</div></div>
    <div class="card"><div class="card-label">Verified %</div><div class="card-value ${pct>=80?'green':pct>=50?'accent':'red'}">${pct}%</div></div>
    <div class="card"><div class="card-label">Documents</div><div class="card-value accent">${DOCUMENTS.length}</div></div>
    <div class="card"><div class="card-label">Sources</div><div class="card-value accent">${Object.keys(STATS.by_source).length}</div></div>
  `;
}

function renderCharts() {
  const secEl = document.getElementById('chart-sections');
  const maxSec = Math.max(...Object.values(STATS.by_section).map(s => s.total), 1);
  let secHtml = '';
  for (const [key, label] of Object.entries(SECTION_LABELS)) {
    const data = STATS.by_section[key] || { total: 0, verified: 0 };
    const uv = data.total - data.verified;
    const vPct = (data.verified / maxSec) * 100;
    const uPct = (uv / maxSec) * 100;
    secHtml += `<div class="bar-row">
      <div class="bar-label" title="${label}">${label}</div>
      <div class="bar-track"><div style="display:flex;height:100%">
        <div class="bar-fill verified" style="width:${vPct}%"></div>
        <div class="bar-fill unverified" style="width:${uPct}%"></div>
      </div></div>
      <div class="bar-count">${data.verified}/${data.total}</div>
    </div>`;
  }
  secEl.innerHTML = secHtml;

  const typeEl = document.getElementById('chart-types');
  const maxType = Math.max(...Object.values(STATS.by_source_type), 1);
  let typeHtml = '';
  for (const [type, count] of Object.entries(STATS.by_source_type).sort((a,b) => b[1]-a[1])) {
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

// --- FACT TABLE ---
let sortCol = 'id', sortAsc = true;

function esc(str) {
  if (!str) return '';
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function truncate(text, max) {
  if (!text) return '';
  return text.length > max ? text.slice(0, max) + '...' : text;
}

function getFilteredFacts() {
  const search = document.getElementById('search').value.toLowerCase();
  const section = document.getElementById('filter-section').value;
  const verified = document.getElementById('filter-verified').value;
  const sourceType = document.getElementById('filter-source-type').value;
  const docFilter = document.getElementById('filter-document').value;

  return FACTS.filter(f => {
    if (section && !(f.sections_used || []).includes(section)) return false;
    if (verified !== '' && String(f.verified) !== verified) return false;
    if (sourceType && f.source_type !== sourceType) return false;
    if (docFilter && f.document !== docFilter) return false;
    if (search) {
      const hay = [f.id, f.claim, f.source_name, f.source_author, f.source_url,
        f.verification_notes, f.notes, f.source_excerpt, ...(f.source_quotes||[])
      ].join(' ').toLowerCase();
      if (!hay.includes(search)) return false;
    }
    return true;
  }).sort((a, b) => {
    let va = a[sortCol] ?? '', vb = b[sortCol] ?? '';
    if (typeof va === 'boolean') { va = va ? 1 : 0; vb = vb ? 1 : 0; }
    if (typeof va === 'string') { va = va.toLowerCase(); vb = vb.toLowerCase(); }
    return sortAsc ? (va < vb ? -1 : va > vb ? 1 : 0) : (va > vb ? -1 : va < vb ? 1 : 0);
  });
}

function renderFactRow(f, colCount) {
  const statusBadge = f.verified
    ? '<span class="badge badge-verified">Verified</span>'
    : '<span class="badge badge-unverified">Unverified</span>';
  const verNotes = f.verification_notes
    ? `<br><span style="font-size:10px;color:var(--orange)">Note: ${esc(f.verification_notes)}</span>` : '';

  const docBadge = f.document && DOC_MAP[f.document]
    ? `<span class="badge badge-doc" onclick="navigateToDoc('${esc(f.document)}')" title="${esc(DOC_MAP[f.document].title)}">${esc(f.document)}</span>`
    : '<span style="color:var(--text-muted);font-size:11px">—</span>';

  const sections = (f.sections_used || []).map(s =>
    `<span class="badge badge-section">${s.replace('_',' ')}</span>`
  ).join(' ');

  const sourceLink = f.source_url
    ? `<a class="source-link" href="${esc(f.source_url)}" target="_blank" rel="noopener">${esc(truncate(f.source_name || f.source_url, 50))}</a>`
    : esc(f.source_name || '');
  const sourceTypeLabel = SOURCE_TYPE_LABELS[f.source_type] || f.source_type || '';

  const hasExcerpt = f.source_excerpt && f.source_excerpt.trim();
  const excerptBtn = hasExcerpt
    ? `<button class="expand-toggle" onclick="toggleExcerpt('${esc(f.id)}')">Source excerpt</button>` : '';

  let rows = `<tr class="${hasExcerpt ? 'expanded-row' : ''}" id="row-${esc(f.id)}">
    <td style="white-space:nowrap;font-family:monospace;font-size:11px">${esc(f.id)}</td>
    <td>${statusBadge}${verNotes}</td>
    <td>${docBadge}</td>
    <td class="claim-text">${esc(f.claim)}${excerptBtn ? '<br>'+excerptBtn : ''}</td>
    <td>${sourceLink}<br><span class="badge badge-source-type">${esc(sourceTypeLabel)}</span>
      ${f.source_date ? `<br><span style="font-size:10px;color:var(--text-muted)">${esc(f.source_date)}</span>` : ''}</td>
    <td>${sections}</td>
    <td style="white-space:nowrap;font-size:11px;color:var(--text-muted)">${esc(f.date_added||'')}</td>
  </tr>`;

  if (hasExcerpt) {
    rows += `<tr class="excerpt-row" id="excerpt-${esc(f.id)}">
      <td colspan="${colCount}" class="excerpt-cell">
        <div class="excerpt-label">Source Excerpt</div>
        <div class="excerpt-content" id="excerpt-content-${esc(f.id)}">${marked.parse(f.source_excerpt)}</div>
      </td>
    </tr>`;
  }
  return rows;
}

function toggleExcerpt(id) {
  const row = document.getElementById('excerpt-' + id);
  if (row) row.classList.toggle('visible');
}

function renderTable() {
  const facts = getFilteredFacts();
  const tbody = document.getElementById('fact-body');
  document.getElementById('results-count').textContent = `Showing ${facts.length} of ${FACTS.length} facts`;
  if (facts.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:40px;color:var(--text-muted)">No facts match your filters.</td></tr>';
    return;
  }
  tbody.innerHTML = facts.map(f => renderFactRow(f, 7)).join('');
}

function populateFilters() {
  const secSelect = document.getElementById('filter-section');
  for (const [key, label] of Object.entries(SECTION_LABELS)) {
    secSelect.innerHTML += `<option value="${key}">${label}</option>`;
  }
  const typeSelect = document.getElementById('filter-source-type');
  for (const [key, label] of Object.entries(SOURCE_TYPE_LABELS)) {
    typeSelect.innerHTML += `<option value="${key}">${label}</option>`;
  }
  const docSelect = document.getElementById('filter-document');
  DOCUMENTS.forEach(d => {
    docSelect.innerHTML += `<option value="${d.id}">${d.id} — ${esc(truncate(d.title, 40))}</option>`;
  });
}

// --- DOCUMENT VIEW ---
function renderDocGrid() {
  const grid = document.getElementById('doc-grid');
  grid.innerHTML = DOCUMENTS.map(d => {
    const factCount = FACTS.filter(f => f.document === d.id).length;
    const typeLabel = DOC_TYPE_LABELS[d.type] || d.type;
    const statusLabel = DOC_STATUS_LABELS[d.status] || d.status;
    const statusClass = 'badge-status-' + (d.status || 'stub');
    const secLabel = SECTION_LABELS[d.section] || d.section || '';
    return `<div class="doc-card" onclick="openDocument('${esc(d.id)}')" id="doc-card-${esc(d.id)}">
      <div class="doc-card-title">${esc(d.title)}</div>
      <div class="doc-card-meta">
        <span class="badge badge-doc-type">${esc(typeLabel)}</span>
        <span class="badge badge-status ${statusClass}">${esc(statusLabel)}</span>
        ${secLabel ? `<span style="color:var(--text-muted)">${esc(secLabel)}</span>` : ''}
      </div>
      <div class="doc-card-desc">${esc(d.description)}</div>
      <div class="doc-card-facts">${factCount} linked fact${factCount !== 1 ? 's' : ''}</div>
    </div>`;
  }).join('');
}

function openDocument(docId) {
  const doc = DOC_MAP[docId];
  if (!doc) return;

  // Highlight card
  document.querySelectorAll('.doc-card').forEach(c => c.classList.remove('active'));
  const card = document.getElementById('doc-card-' + docId);
  if (card) card.classList.add('active');

  // Find linked facts
  const linkedFacts = FACTS.filter(f => f.document === docId);

  const container = document.getElementById('doc-viewer-container');
  const typeLabel = DOC_TYPE_LABELS[doc.type] || doc.type;
  const statusLabel = DOC_STATUS_LABELS[doc.status] || doc.status;
  const statusClass = 'badge-status-' + (doc.status || 'stub');

  let factsHtml = '';
  if (linkedFacts.length > 0) {
    factsHtml = `<div class="doc-facts-section">
      <h3>Linked Facts (${linkedFacts.length})</h3>
      <table style="width:100%;border-collapse:collapse;font-size:12px">
        <thead><tr>
          <th style="text-align:left;padding:6px 8px;background:var(--surface2);border-bottom:1px solid var(--border);font-size:11px;text-transform:uppercase;color:var(--text-muted)">ID</th>
          <th style="text-align:left;padding:6px 8px;background:var(--surface2);border-bottom:1px solid var(--border);font-size:11px;text-transform:uppercase;color:var(--text-muted)">Status</th>
          <th style="text-align:left;padding:6px 8px;background:var(--surface2);border-bottom:1px solid var(--border);font-size:11px;text-transform:uppercase;color:var(--text-muted)">Claim</th>
          <th style="text-align:left;padding:6px 8px;background:var(--surface2);border-bottom:1px solid var(--border);font-size:11px;text-transform:uppercase;color:var(--text-muted)">Source</th>
        </tr></thead>
        <tbody>${linkedFacts.map(f => {
          const badge = f.verified
            ? '<span class="badge badge-verified">Verified</span>'
            : '<span class="badge badge-unverified">Unverified</span>';
          return `<tr style="cursor:pointer" onclick="navigateToFact('${esc(f.id)}')">
            <td style="padding:6px 8px;border-bottom:1px solid var(--border);font-family:monospace;font-size:11px;color:var(--accent)">${esc(f.id)}</td>
            <td style="padding:6px 8px;border-bottom:1px solid var(--border)">${badge}</td>
            <td style="padding:6px 8px;border-bottom:1px solid var(--border);max-width:300px">${esc(truncate(f.claim, 120))}</td>
            <td style="padding:6px 8px;border-bottom:1px solid var(--border);font-size:11px;color:var(--text-muted)">${esc(truncate(f.source_name, 40))}</td>
          </tr>`;
        }).join('')}</tbody>
      </table>
    </div>`;
  }

  container.innerHTML = `<div class="doc-viewer">
    <div class="doc-viewer-header">
      <div>
        <div class="doc-viewer-title">${esc(doc.title)}</div>
        <div class="doc-viewer-meta">
          <span class="badge badge-doc-type">${esc(typeLabel)}</span>
          <span class="badge badge-status ${statusClass}">${esc(statusLabel)}</span>
          &nbsp; ${esc(doc.id)} &middot; Updated ${esc(doc.last_updated || doc.date_created || '')}
        </div>
      </div>
      <button class="doc-viewer-close" onclick="closeDocument()">Close</button>
    </div>
    <div class="doc-viewer-content">${doc.content ? marked.parse(doc.content) : '<p style="color:var(--text-muted)">No content yet.</p>'}</div>
    ${factsHtml}
  </div>`;

  container.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function closeDocument() {
  document.getElementById('doc-viewer-container').innerHTML = '';
  document.querySelectorAll('.doc-card').forEach(c => c.classList.remove('active'));
}

// --- CROSS-NAVIGATION ---
function navigateToDoc(docId) {
  // Switch to documents view and open the document
  document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
  document.querySelector('[data-view="documents"]').classList.add('active');
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.getElementById('view-documents').classList.add('active');
  openDocument(docId);
}

function navigateToFact(factId) {
  // Switch to facts view, search for the fact
  document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
  document.querySelector('[data-view="facts"]').classList.add('active');
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.getElementById('view-facts').classList.add('active');
  document.getElementById('search').value = factId;
  renderTable();
  // Open the excerpt if it exists
  setTimeout(() => {
    const excerptRow = document.getElementById('excerpt-' + factId);
    if (excerptRow) excerptRow.classList.add('visible');
    const row = document.getElementById('row-' + factId);
    if (row) row.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, 100);
}

// --- SECTION VIEW ---
function showSectionView(sectionKey) {
  const label = SECTION_LABELS[sectionKey] || sectionKey;
  document.getElementById('section-view-title').textContent = label;
  const facts = FACTS.filter(f => (f.sections_used || []).includes(sectionKey));
  document.getElementById('section-results-count').textContent = `${facts.length} facts`;
  const tbody = document.getElementById('section-fact-body');
  if (facts.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:40px;color:var(--text-muted)">No facts yet for this section.</td></tr>';
    return;
  }
  tbody.innerHTML = facts.map(f => {
    const badge = f.verified
      ? '<span class="badge badge-verified">Verified</span>'
      : '<span class="badge badge-unverified">Unverified</span>';
    const verNotes = f.verification_notes
      ? `<br><span style="font-size:10px;color:var(--orange)">Note: ${esc(f.verification_notes)}</span>` : '';
    const docBadge = f.document && DOC_MAP[f.document]
      ? `<span class="badge badge-doc" onclick="navigateToDoc('${esc(f.document)}')">${esc(f.document)}</span>` : '—';
    const sourceLink = f.source_url
      ? `<a class="source-link" href="${esc(f.source_url)}" target="_blank">${esc(truncate(f.source_name || f.source_url, 50))}</a>`
      : esc(f.source_name || '');
    const hasExcerpt = f.source_excerpt && f.source_excerpt.trim();
    const excerptBtn = hasExcerpt
      ? `<br><button class="expand-toggle" onclick="toggleExcerpt('s-${esc(f.id)}')">Source excerpt</button>` : '';

    let rows = `<tr id="row-s-${esc(f.id)}">
      <td style="font-family:monospace;font-size:11px;cursor:pointer;color:var(--accent)" onclick="navigateToFact('${esc(f.id)}')">${esc(f.id)}</td>
      <td>${badge}${verNotes}</td>
      <td>${docBadge}</td>
      <td class="claim-text">${esc(f.claim)}${excerptBtn}</td>
      <td>${sourceLink}</td>
      <td style="white-space:nowrap;font-size:11px;color:var(--text-muted)">${esc(f.date_added||'')}</td>
    </tr>`;
    if (hasExcerpt) {
      rows += `<tr class="excerpt-row" id="excerpt-s-${esc(f.id)}">
        <td colspan="6" class="excerpt-cell">
          <div class="excerpt-label">Source Excerpt</div>
          <div class="excerpt-content">${marked.parse(f.source_excerpt)}</div>
        </td>
      </tr>`;
    }
    return rows;
  }).join('');
}

// --- SORT ---
document.querySelectorAll('#view-facts thead th[data-sort]').forEach(th => {
  th.addEventListener('click', () => {
    const col = th.dataset.sort;
    if (sortCol === col) sortAsc = !sortAsc;
    else { sortCol = col; sortAsc = true; }
    document.querySelectorAll('#view-facts thead th .sort-arrow').forEach(s => s.textContent = '');
    th.querySelector('.sort-arrow').textContent = sortAsc ? ' \u25B2' : ' \u25BC';
    renderTable();
  });
});

// --- EVENTS ---
['search','filter-section','filter-verified','filter-source-type','filter-document'].forEach(id => {
  const el = document.getElementById(id);
  el.addEventListener(el.tagName === 'INPUT' ? 'input' : 'change', renderTable);
});

// --- INIT ---
initNav();
renderCards();
renderCharts();
populateFilters();
renderTable();
renderDocGrid();
</script>
</body>
</html>"""


def main():
    print("Loading facts...")
    facts = load_facts()
    print(f"  {len(facts)} facts")

    print("Loading documents...")
    documents = load_documents()
    print(f"  {len(documents)} documents")

    stats = build_stats(facts)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = HTML_TEMPLATE
    html = html.replace("%%FACTS_JSON%%", json.dumps(facts, default=str))
    html = html.replace("%%DOCUMENTS_JSON%%", json.dumps(documents, default=str))
    html = html.replace("%%STATS_JSON%%", json.dumps(stats, default=str))
    html = html.replace("%%SECTION_LABELS_JSON%%", json.dumps(SECTION_LABELS))
    html = html.replace("%%SOURCE_TYPE_LABELS_JSON%%", json.dumps(SOURCE_TYPE_LABELS))
    html = html.replace("%%DOC_TYPE_LABELS_JSON%%", json.dumps(DOC_TYPE_LABELS))
    html = html.replace("%%DOC_STATUS_LABELS_JSON%%", json.dumps(DOC_STATUS_LABELS))
    html = html.replace("%%GENERATED_AT%%", generated_at)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  Dashboard: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
