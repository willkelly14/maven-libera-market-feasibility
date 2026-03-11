#!/usr/bin/env python3
"""
Builds a static HTML dashboard from the Fact Database YAML files
and the Documents database.

Usage:
    .venv/bin/python build_dashboard.py
    open dashboard.html
"""

import csv
import glob
import json
import os
import random
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
CONTEXT_DIR = os.path.join(BASE_DIR, "Context")
DATASETS_DIR = os.path.join(BASE_DIR, "Datasets")
OUTPUT_FILE = os.path.join(BASE_DIR, "dashboard.html")
DEFAULT_SAMPLE_SIZE = 15

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
        doc.setdefault("sections", [])
        # Migrate legacy single-section field
        if "section" in doc and doc["section"]:
            if not doc["sections"]:
                doc["sections"] = [doc["section"]]
            del doc["section"]
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


def load_context_files():
    """Load all markdown files from the Context directory."""
    context_files = []
    if not os.path.exists(CONTEXT_DIR):
        os.makedirs(CONTEXT_DIR, exist_ok=True)
        return context_files

    md_files = sorted(glob.glob(os.path.join(CONTEXT_DIR, "*.md")))
    for fpath in md_files:
        fname = os.path.basename(fpath)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        context_files.append({
            "filename": fname,
            "title": fname.replace(".md", "").replace("_", " ").replace("-", " "),
            "content": content,
            "size": len(content),
        })
    return context_files


def _parse_csv(path):
    """Parse a CSV file, return (headers, rows, total_rows)."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        rows = list(reader)
    if not rows:
        return [], [], 0
    headers = rows[0]
    data_rows = rows[1:]
    return headers, data_rows, len(data_rows)


def _parse_excel(path):
    """Parse an Excel file, return (headers, rows, total_rows).

    Handles multi-row headers by detecting a header region at the top
    (rows where most cells are non-numeric text) and merging them into
    composite column names. Empty data rows are filtered out.
    """
    try:
        import openpyxl
    except ImportError:
        print("  WARN: openpyxl not installed. Run: .venv/bin/pip install openpyxl")
        return [], [], 0
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    all_rows = []
    for row in ws.iter_rows(values_only=True):
        all_rows.append([str(c) if c is not None else "" for c in row])
    wb.close()
    if not all_rows:
        return [], [], 0

    # Detect header region: find the first row where most cells look like
    # data (numbers). All rows before that are part of the header.
    def _is_data_row(row):
        non_empty = [c for c in row if c.strip()]
        if len(non_empty) < 2:
            return False
        numeric = sum(1 for c in non_empty if c.replace(",", "").replace(".", "").replace("-", "").strip().isdigit())
        return numeric > len(non_empty) * 0.4

    header_end = 0
    for i, row in enumerate(all_rows):
        if _is_data_row(row):
            header_end = i
            break
    else:
        # No data rows found; treat row 0 as header
        header_end = 1

    if header_end == 0:
        header_end = 1  # at least one header row

    header_rows = all_rows[:header_end]
    data_rows = all_rows[header_end:]

    # Build composite headers by forward-filling group labels then joining
    ncols = len(all_rows[0]) if all_rows else 0
    composite = [""] * ncols
    for hrow in header_rows:
        filled = []
        last = ""
        for c in hrow:
            if c.strip():
                last = c.strip()
            filled.append(last)
        for j in range(ncols):
            part = filled[j] if j < len(filled) else ""
            if part and part != composite[j].split(" / ")[-1] if composite[j] else True:
                composite[j] = (composite[j] + " / " + part).strip(" / ") if composite[j] else part

    # De-duplicate: if a composite header equals its group prefix, keep it
    headers = [h if h else f"Col {i+1}" for i, h in enumerate(composite)]

    # Filter out empty rows
    data_rows = [r for r in data_rows if any(c.strip() for c in r)]

    return headers, data_rows, len(data_rows)


def _parse_json(path):
    """Parse a JSON array-of-objects file, return (headers, rows, total_rows)."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list) or not data:
        return [], [], 0
    headers = list(data[0].keys())
    data_rows = [[str(obj.get(h, "")) for h in headers] for obj in data]
    return headers, data_rows, len(data_rows)


def load_datasets():
    """Load datasets from Datasets/datasets_index.yaml with random sampling."""
    index_path = os.path.join(DATASETS_DIR, "datasets_index.yaml")
    if not os.path.exists(index_path):
        print("  WARN: datasets_index.yaml not found")
        return []
    with open(index_path, "r", encoding="utf-8") as f:
        ds_index = yaml.safe_load(f.read())
    if not ds_index or not isinstance(ds_index, list):
        return []

    parsers = {"csv": _parse_csv, "xlsx": _parse_excel, "json": _parse_json}
    datasets = []
    for ds in ds_index:
        if not isinstance(ds, dict) or "id" not in ds:
            continue
        ds.setdefault("title", "")
        ds.setdefault("description", "")
        ds.setdefault("file", "")
        ds.setdefault("format", "")
        ds.setdefault("sections", [])
        ds.setdefault("source_name", "")
        ds.setdefault("source_url", "")
        ds.setdefault("sample_size", DEFAULT_SAMPLE_SIZE)
        ds.setdefault("date_added", "")
        ds.setdefault("notes", "")

        if isinstance(ds["description"], str):
            ds["description"] = " ".join(ds["description"].split())

        file_path = os.path.join(DATASETS_DIR, ds["file"]) if ds["file"] else ""
        if not file_path or not os.path.exists(file_path):
            print(f"  WARN: Dataset file not found: {ds['file']}")
            ds["_headers"] = []
            ds["_sample_rows"] = []
            ds["_totals_row"] = None
            ds["_total_rows"] = 0
            ds["_column_count"] = 0
            datasets.append(ds)
            continue

        fmt = ds["format"].lower()
        parser = parsers.get(fmt)
        if not parser:
            print(f"  WARN: Unknown format '{fmt}' for dataset {ds['id']}")
            ds["_headers"] = []
            ds["_sample_rows"] = []
            ds["_totals_row"] = None
            ds["_total_rows"] = 0
            ds["_column_count"] = 0
            datasets.append(ds)
            continue

        headers, rows, total = parser(file_path)

        # Extract totals row if the last row contains "total" (case-insensitive)
        totals_row = None
        if rows and any("total" in c.lower() for c in rows[-1]):
            totals_row = rows[-1]
            rows = rows[:-1]
            total = len(rows)

        sample_size = min(ds["sample_size"], total)
        sample = random.sample(rows, sample_size) if rows else []
        ds["_headers"] = headers
        ds["_sample_rows"] = sample
        ds["_totals_row"] = totals_row
        ds["_total_rows"] = total
        ds["_column_count"] = len(headers)
        datasets.append(ds)
    return datasets


def load_claude_md():
    """Load the CLAUDE.md file for editing in the dashboard."""
    claude_path = os.path.join(BASE_DIR, "CLAUDE.md")
    if os.path.exists(claude_path):
        with open(claude_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


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
.sidebar-nav { padding: 8px 0; flex: 1; }
.sidebar-bottom {
  border-top: 1px solid var(--border); padding: 8px 0;
  flex-shrink: 0;
}
.nav-section-label {
  font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;
  color: var(--text-muted); padding: 12px 16px 4px; font-weight: 600;
  display: flex; align-items: center; justify-content: space-between;
  cursor: pointer; user-select: none;
}
.nav-section-label:hover { color: var(--text); }
.nav-section-label .chevron {
  font-size: 10px; transition: transform 0.2s;
}
.nav-section-label.collapsed .chevron { transform: rotate(-90deg); }
.nav-section-items { overflow: hidden; transition: max-height 0.2s ease; }
.nav-section-items.collapsed { max-height: 0 !important; }
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

/* Search input wrapper with clear button */
.search-wrap {
  position: relative; display: flex; align-items: center;
}
.controls .search-wrap { flex: 1; min-width: 180px; }
.search-wrap input { padding-right: 28px !important; width: 100%; }
.search-clear {
  position: absolute; right: 6px; top: 50%; transform: translateY(-50%);
  background: none; border: none; color: var(--text-muted); cursor: pointer;
  font-size: 15px; line-height: 1; padding: 2px 4px; border-radius: 4px;
  display: none;
}
.search-clear.visible { display: block; }
.search-clear:hover { color: var(--text); background: var(--surface2); }

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
.badge-unverified { background: rgba(210, 153, 34, 0.15); color: var(--orange); }
.badge-flagged { background: rgba(248, 81, 73, 0.15); color: var(--red); }

/* Status dropdown */
.status-select {
  appearance: none; -webkit-appearance: none;
  border: none; border-radius: 10px; padding: 2px 20px 2px 7px;
  font-size: 10px; font-weight: 600; cursor: pointer; outline: none;
  background-repeat: no-repeat; background-position: right 5px center; background-size: 10px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 6'%3E%3Cpath d='M1 1l4 4 4-4' stroke='%238b949e' stroke-width='1.5' fill='none'/%3E%3C/svg%3E");
}
.status-select.s-verified { background-color: rgba(63, 185, 80, 0.15); color: var(--green); }
.status-select.s-unverified { background-color: rgba(210, 153, 34, 0.15); color: var(--orange); }
.status-select.s-flagged { background-color: rgba(248, 81, 73, 0.15); color: var(--red); }
.status-select.s-archived { background-color: rgba(139, 148, 158, 0.15); color: var(--text-muted); }
.status-select.s-draft { background-color: rgba(210, 153, 34, 0.15); color: var(--orange); }
.status-select.s-stub { background-color: rgba(248, 81, 73, 0.15); color: var(--red); }
.status-select.s-complete { background-color: rgba(63, 185, 80, 0.15); color: var(--green); }
.status-select.s-in_review { background-color: rgba(188, 140, 255, 0.15); color: var(--purple); }
.status-select option { background: var(--surface); color: var(--text); }

/* Confirm dialog */
.confirm-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.6); z-index: 400;
  display: flex; align-items: center; justify-content: center;
}
.confirm-dialog {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 10px; padding: 24px; max-width: 400px; width: 90%;
  box-shadow: 0 8px 32px rgba(0,0,0,0.5);
}
.confirm-dialog h3 { font-size: 15px; font-weight: 600; margin-bottom: 8px; }
.confirm-dialog p { font-size: 13px; color: var(--text-muted); margin-bottom: 16px; line-height: 1.5; }
.confirm-dialog .confirm-claim {
  background: var(--surface2); border-radius: 6px; padding: 8px 12px;
  font-size: 12px; color: var(--text); margin-bottom: 16px;
  max-height: 80px; overflow-y: auto; border: 1px solid var(--border);
}
.confirm-btns { display: flex; gap: 8px; justify-content: flex-end; }
.confirm-btns button {
  padding: 7px 16px; border-radius: 6px; font-size: 13px;
  font-weight: 600; cursor: pointer; border: 1px solid var(--border);
}
.btn-cancel { background: var(--surface2); color: var(--text); }
.btn-cancel:hover { background: var(--surface3); }
.btn-danger { background: rgba(248, 81, 73, 0.15); color: var(--red); border-color: rgba(248, 81, 73, 0.3); }
.btn-danger:hover { background: rgba(248, 81, 73, 0.25); }
.btn-warn { background: rgba(210, 153, 34, 0.15); color: var(--orange); border-color: rgba(210, 153, 34, 0.3); }
.btn-warn:hover { background: rgba(210, 153, 34, 0.25); }

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

/* ===== SLIDE PANE (full-width split) ===== */
.slide-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5); z-index: 200; opacity: 0;
  pointer-events: none; transition: opacity 0.25s ease;
}
.slide-overlay.open { opacity: 1; pointer-events: auto; }

.slide-pane {
  position: fixed; top: 0; right: 0; bottom: 0;
  left: 60px;
  background: var(--bg); border-left: 1px solid var(--border);
  z-index: 201; transform: translateX(100%);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex; flex-direction: column;
  box-shadow: -8px 0 32px rgba(0,0,0,0.5);
}
.slide-pane.open { transform: translateX(0); }

/* Header bar spanning full width */
.slide-pane-topbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 20px; border-bottom: 1px solid var(--border);
  background: var(--surface); flex-shrink: 0;
}
.slide-pane-topbar-left { display: flex; align-items: center; gap: 12px; min-width: 0; flex: 1; }
.slide-pane-title { font-size: 16px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.slide-pane-meta { font-size: 11px; color: var(--text-muted); display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.slide-pane-close {
  background: none; border: none; color: var(--text-muted);
  cursor: pointer; padding: 4px; font-size: 20px; line-height: 1;
  border-radius: 4px; width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.slide-pane-close:hover { background: var(--surface2); color: var(--text); }

/* Split layout */
.slide-pane-split {
  display: flex; flex: 1; overflow: hidden;
}

/* Left: Document */
.slide-pane-doc {
  flex: 1; display: flex; flex-direction: column;
  border-right: 1px solid var(--border); min-width: 0;
}
.slide-pane-doc-header {
  padding: 8px 16px; border-bottom: 1px solid var(--border);
  font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;
  color: var(--text-muted); font-weight: 600; background: var(--surface);
  flex-shrink: 0;
  display: flex; align-items: center; gap: 10px;
}
.slide-pane-doc-header .panel-label { flex-shrink: 0; }
.doc-content-search {
  flex: 1; padding: 5px 8px; background: var(--surface2);
  border: 1px solid var(--border); border-radius: 5px;
  color: var(--text); font-size: 12px; outline: none;
  text-transform: none; letter-spacing: normal; font-weight: 400;
}
.doc-content-search:focus { border-color: var(--accent); }
.doc-search-count {
  font-size: 11px; color: var(--text-muted); white-space: nowrap;
  text-transform: none; letter-spacing: normal; font-weight: 400;
  min-width: 50px; text-align: center;
}
.doc-search-nav {
  background: var(--surface2); border: 1px solid var(--border);
  color: var(--text-muted); cursor: pointer; padding: 3px 8px;
  font-size: 13px; line-height: 1; border-radius: 4px;
  display: none;
}
.doc-search-nav.visible { display: inline-block; }
.doc-search-nav:hover { background: var(--border); color: var(--text); }
.doc-search-clear {
  background: none; border: none; color: var(--text-muted); cursor: pointer;
  font-size: 16px; line-height: 1; padding: 2px 4px; border-radius: 4px;
  display: none;
}
.doc-search-clear.visible { display: inline-block; }
.doc-search-clear:hover { color: var(--text); background: var(--surface2); }
.doc-search-match {
  background: rgba(255, 200, 50, 0.3); border-radius: 2px;
}
.doc-search-match.current {
  background: rgba(255, 160, 0, 0.5);
  outline: 2px solid rgba(255, 160, 0, 0.7); outline-offset: 1px;
}
.slide-pane-doc-body {
  flex: 1; overflow-y: auto; padding: 24px;
  font-size: 14px; line-height: 1.7; position: relative;
}
.slide-pane-doc-body h1 { font-size: 20px; margin: 16px 0 8px; }
.slide-pane-doc-body h2 { font-size: 17px; margin: 14px 0 6px; color: var(--accent); }
.slide-pane-doc-body h3 { font-size: 14px; margin: 12px 0 4px; }
.slide-pane-doc-body p { margin: 6px 0; }
.slide-pane-doc-body ul, .slide-pane-doc-body ol { margin: 6px 0 6px 24px; }
.slide-pane-doc-body table { margin: 10px 0; border-collapse: collapse; font-size: 13px; width: 100%; }
.slide-pane-doc-body th, .slide-pane-doc-body td {
  padding: 6px 12px; border: 1px solid var(--border); text-align: left;
}
.slide-pane-doc-body th { background: var(--surface2); font-weight: 600; }
.slide-pane-doc-body code { background: var(--surface2); padding: 2px 5px; border-radius: 3px; font-size: 12px; }
.slide-pane-doc-body pre { background: var(--surface2); padding: 12px; border-radius: 6px; overflow-x: auto; font-size: 12px; margin: 8px 0; }
.slide-pane-doc-body pre code { background: none; padding: 0; }
.slide-pane-doc-body a { color: var(--accent); }
.slide-pane-doc-body strong { color: var(--accent); }
.slide-pane-doc-body hr { border: none; border-top: 1px solid var(--border); margin: 16px 0; }
.doc-highlight-mark {
  background: rgba(88, 166, 255, 0.25); border-radius: 2px;
  outline: 2px solid rgba(88, 166, 255, 0.5); outline-offset: 1px;
  transition: background 0.3s;
}
.doc-highlight-mark.fading { background: transparent; outline-color: transparent; }

/* Right: Facts */
.slide-pane-facts {
  flex: 1; display: flex; flex-direction: column; min-width: 0;
}
.slide-pane-facts-header {
  padding: 8px 16px; border-bottom: 1px solid var(--border);
  background: var(--surface); flex-shrink: 0;
  display: flex; align-items: center; gap: 10px;
}
.slide-pane-facts-header .panel-label {
  font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;
  color: var(--text-muted); font-weight: 600; flex-shrink: 0;
}
.slide-pane-facts-header .fact-count {
  font-size: 11px; color: var(--accent); flex-shrink: 0;
}
.slide-pane-facts-search {
  padding: 5px 8px; background: var(--surface2);
  border: 1px solid var(--border); border-radius: 5px;
  color: var(--text); font-size: 12px; outline: none;
}
.slide-pane-facts-search:focus { border-color: var(--accent); }
.slide-pane-facts-body {
  flex: 1; overflow-y: auto;
}
.slide-pane-facts-body table { width: 100%; border-collapse: collapse; font-size: 12px; }
.slide-pane-facts-body thead th {
  text-align: left; padding: 6px 10px; background: var(--surface2);
  border-bottom: 1px solid var(--border); font-weight: 600; font-size: 10px;
  text-transform: uppercase; letter-spacing: 0.3px; color: var(--text-muted);
  position: sticky; top: 0; z-index: 1;
}
.slide-pane-facts-body tbody td {
  padding: 8px 10px; border-bottom: 1px solid var(--border); vertical-align: top;
}
.slide-pane-facts-body tbody tr { transition: background 0.15s; }
.slide-pane-facts-body tbody tr:hover { background: rgba(88, 166, 255, 0.04); }
.slide-pane-facts-body tbody tr.fact-highlight {
  background: rgba(88, 166, 255, 0.15);
  outline: 2px solid var(--accent);
  outline-offset: -2px;
}
.slide-pane-facts-body tbody tr.fact-highlight td { border-bottom-color: var(--accent); }
.pane-fact-claim { max-width: 280px; }
.pane-excerpt-row { display: none; }
.pane-excerpt-row.visible { display: table-row; }
.pane-excerpt-cell {
  padding: 0 10px 10px; background: var(--surface2);
  border-bottom: 1px solid var(--border);
}

/* Selection popup */
.selection-popup {
  position: fixed; z-index: 300;
  background: var(--accent); color: #fff; border-radius: 6px;
  padding: 5px 12px; font-size: 12px; font-weight: 600;
  cursor: pointer; box-shadow: 0 4px 16px rgba(0,0,0,0.4);
  pointer-events: auto; user-select: none;
  display: none; white-space: nowrap;
}
.selection-popup::after {
  content: ''; position: absolute; top: 100%; left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent; border-top-color: var(--accent);
}
.selection-popup:hover { filter: brightness(1.15); }

/* Doc table row highlight */
.doc-table-row { cursor: pointer; }
.doc-table-row:hover { background: rgba(88, 166, 255, 0.06); }
.doc-table-row.active { background: rgba(88, 166, 255, 0.1); }

/* ===== VIEWS ===== */
.view { display: none; }
.view.active { display: block; }
.page-title { font-size: 20px; font-weight: 600; margin-bottom: 16px; }

/* hide scrollbar styling */
.sidebar::-webkit-scrollbar { width: 6px; }
.sidebar::-webkit-scrollbar-track { background: transparent; }
.sidebar::-webkit-scrollbar-thumb { background: var(--surface2); border-radius: 3px; }

/* ===== CONTEXT PAGE ===== */
.context-layout { display: flex; gap: 0; height: calc(100vh - 80px); }
.context-file-list {
  width: 280px; min-width: 280px; border-right: 1px solid var(--border);
  display: flex; flex-direction: column; overflow: hidden;
  background: var(--surface); border-radius: 8px 0 0 8px;
  border: 1px solid var(--border);
}
.context-file-list-header {
  padding: 12px 14px; border-bottom: 1px solid var(--border);
  display: flex; flex-direction: column; gap: 8px; flex-shrink: 0;
}
.context-file-list-header .search-wrap { width: 100%; }
.context-file-list-header input {
  width: 100%; padding: 7px 10px; background: var(--surface2);
  border: 1px solid var(--border); border-radius: 6px;
  color: var(--text); font-size: 13px; outline: none;
}
.context-file-list-header input:focus { border-color: var(--accent); }
.context-file-items { flex: 1; overflow-y: auto; }
.context-file-item {
  padding: 10px 14px; cursor: pointer; border-bottom: 1px solid var(--border);
  transition: background 0.15s;
}
.context-file-item:hover { background: var(--surface2); }
.context-file-item.active { background: rgba(88, 166, 255, 0.08); border-left: 3px solid var(--accent); }
.context-file-item .ctx-title { font-size: 13px; font-weight: 600; }
.context-file-item .ctx-meta { font-size: 11px; color: var(--text-muted); margin-top: 2px; }

.context-editor-area {
  flex: 1; display: flex; flex-direction: column; min-width: 0;
  background: var(--surface); border-radius: 0 8px 8px 0;
  border: 1px solid var(--border); border-left: none;
}
.context-editor-toolbar {
  display: flex; align-items: center; gap: 8px; padding: 8px 14px;
  border-bottom: 1px solid var(--border); flex-shrink: 0;
  background: var(--surface);
}
.context-editor-toolbar .ctx-filename {
  font-size: 14px; font-weight: 600; flex: 1; min-width: 0;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.ctx-toolbar-btn {
  padding: 0 12px; background: var(--surface2); border: 1px solid var(--border);
  border-radius: 6px; color: var(--text); font-size: 12px; font-weight: 600;
  cursor: pointer; white-space: nowrap; height: 28px;
  display: flex; align-items: center; justify-content: center;
}
.ctx-toolbar-btn:hover { background: var(--surface3); }
.ctx-toolbar-btn.save-btn {
  background: rgba(63, 185, 80, 0.15); color: var(--green); border-color: rgba(63, 185, 80, 0.3);
  display: none;
}
.ctx-toolbar-btn.save-btn.visible { display: flex; }
.ctx-toolbar-btn.save-btn:hover { background: rgba(63, 185, 80, 0.25); }
.ctx-unsaved { font-size: 11px; color: var(--orange); font-weight: 600; display: none; }
.ctx-unsaved.visible { display: inline; }

/* Toggle switch */
.ctx-toggle {
  display: flex; background: var(--surface2); border-radius: 6px;
  border: 1px solid var(--border); overflow: hidden; height: 28px;
}
.ctx-toggle-opt {
  padding: 0 12px; font-size: 12px; font-weight: 600; cursor: pointer;
  color: var(--text-muted); border: none; background: none;
  transition: all 0.15s; user-select: none;
  display: flex; align-items: center; justify-content: center;
}
.ctx-toggle-opt:first-child { border-right: 1px solid var(--border); }
.ctx-toggle-opt:hover { color: var(--text); }
.ctx-toggle-opt.active {
  background: rgba(88, 166, 255, 0.15); color: var(--accent);
}

/* Three-dot menu */
.ctx-menu-wrap { position: relative; }
.ctx-dots-btn {
  background: var(--surface2); border: 1px solid var(--border); border-radius: 6px;
  color: var(--text-muted); cursor: pointer; font-size: 16px;
  line-height: 1; display: flex; align-items: center; justify-content: center;
  width: 28px; height: 28px;
}
.ctx-dots-btn:hover { background: var(--surface3); color: var(--text); }
.ctx-dropdown {
  position: absolute; top: calc(100% + 4px); right: 0;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; min-width: 160px; padding: 4px 0;
  box-shadow: 0 8px 24px rgba(0,0,0,0.4); z-index: 50;
  display: none;
}
.ctx-dropdown.open { display: block; }
.ctx-dropdown-item {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 14px; font-size: 13px; cursor: pointer;
  color: var(--text); border: none; background: none; width: 100%;
  text-align: left;
}
.ctx-dropdown-item:hover { background: var(--surface2); }
.ctx-dropdown-item.danger { color: var(--red); }
.ctx-dropdown-item.danger:hover { background: rgba(248, 81, 73, 0.1); }
.context-editor-body { flex: 1; display: flex; overflow: hidden; position: relative; }
.context-textarea {
  width: 100%; height: 100%; resize: none; border: none; outline: none;
  background: var(--bg); color: var(--text); font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
  font-size: 13px; line-height: 1.6; padding: 20px 24px; tab-size: 2;
}
.context-textarea::placeholder { color: var(--text-muted); }
.context-preview {
  width: 100%; height: 100%; overflow-y: auto; padding: 20px 24px;
  font-size: 14px; line-height: 1.7; display: none;
}
.context-preview.active { display: block; }
.context-textarea.hidden { display: none; }
.context-preview h1 { font-size: 20px; margin: 16px 0 8px; }
.context-preview h2 { font-size: 17px; margin: 14px 0 6px; color: var(--accent); }
.context-preview h3 { font-size: 14px; margin: 12px 0 4px; }
.context-preview p { margin: 6px 0; }
.context-preview ul, .context-preview ol { margin: 6px 0 6px 24px; }
.context-preview table { margin: 10px 0; border-collapse: collapse; font-size: 13px; width: 100%; }
.context-preview th, .context-preview td { padding: 6px 12px; border: 1px solid var(--border); text-align: left; }
.context-preview th { background: var(--surface2); font-weight: 600; }
.context-preview code { background: var(--surface2); padding: 2px 5px; border-radius: 3px; font-size: 12px; }
.context-preview pre { background: var(--surface2); padding: 12px; border-radius: 6px; overflow-x: auto; font-size: 12px; margin: 8px 0; }
.context-preview pre code { background: none; padding: 0; }
.context-preview a { color: var(--accent); }
.context-preview strong { color: var(--accent); }
.context-preview hr { border: none; border-top: 1px solid var(--border); margin: 16px 0; }
.context-empty {
  display: flex; align-items: center; justify-content: center;
  flex: 1; width: 100%; color: var(--text-muted); font-size: 14px;
  flex-direction: column; gap: 8px;
}
.context-empty .ctx-empty-icon { font-size: 32px; opacity: 0.5; }
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
    <div class="nav-section-label" onclick="toggleSection(this)">Overview <span class="chevron">&#9660;</span></div>
    <div class="nav-section-items">
      <div class="nav-item active" data-view="dashboard">
        <span class="nav-icon">&#9632;</span> Dashboard
      </div>
    </div>

    <div class="nav-divider"></div>
    <div class="nav-section-label" onclick="toggleSection(this)">Databases <span class="chevron">&#9660;</span></div>
    <div class="nav-section-items">
      <div class="nav-item" data-view="facts">
        <span class="nav-icon">&#10003;</span> Fact Database
        <span class="nav-count" id="nav-fact-count">0</span>
      </div>
      <div class="nav-item" data-view="documents">
        <span class="nav-icon">&#9776;</span> Documents
        <span class="nav-count" id="nav-doc-count">0</span>
      </div>
      <div class="nav-item" data-view="context">
        <span class="nav-icon"><svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 1h8a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1z"/><path d="M5.5 5h5M5.5 8h5M5.5 11h3"/></svg></span> Context
        <span class="nav-count" id="nav-context-count">0</span>
      </div>
      <div class="nav-item" data-view="datasets">
        <span class="nav-icon"><svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="3" width="14" height="11" rx="1"/><path d="M1 6.5h14M1 10h14M5.5 6.5V14"/></svg></span> Datasets
        <span class="nav-count" id="nav-dataset-count">0</span>
      </div>
    </div>

    <div class="nav-divider"></div>
    <div class="nav-section-label" onclick="toggleSection(this)">Sections <span class="chevron">&#9660;</span></div>
    <div class="nav-section-items" id="nav-sections"></div>
  </div>
  <div class="sidebar-bottom">
    <div class="nav-item" data-view="claude-instructions">
      <span class="nav-icon"><svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-linecap="round" stroke-width="1.6"><line x1="8" y1="0.8" x2="8" y2="4.5"/><line x1="8" y1="11.5" x2="8" y2="15.2"/><line x1="0.8" y1="8" x2="3.5" y2="8"/><line x1="12.5" y1="8" x2="15.2" y2="8"/><line x1="2.9" y1="2.9" x2="5.2" y2="5.2"/><line x1="10.8" y1="10.8" x2="13.1" y2="13.1"/><line x1="13.1" y1="2.9" x2="11.5" y2="4.5"/><line x1="4.5" y1="11.5" x2="2.9" y2="13.1"/></svg></span> Claude Instructions
    </div>
    <div class="nav-item" data-view="archive">
      <span class="nav-icon"><svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="1" width="14" height="4" rx="1"/><path d="M2 5v9a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V5"/><path d="M6 8.5h4"/></svg></span> Archive
      <span class="nav-count" id="nav-archive-count">0</span>
    </div>
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
      <div class="search-wrap">
        <input type="text" id="search" placeholder="Search claims, sources, quotes...">
        <button class="search-clear" id="search-clear" onclick="clearSearchInput('search')" title="Clear search">&times;</button>
      </div>
      <select id="filter-section"><option value="">All Sections</option></select>
      <select id="filter-verified">
        <option value="">All Status</option>
        <option value="verified">Verified</option>
        <option value="unverified">Unverified</option>
        <option value="flagged">Flagged</option>
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
    <div class="controls">
      <div class="search-wrap">
        <input type="text" id="doc-search" placeholder="Search documents by title, description, section, content...">
        <button class="search-clear" id="doc-search-table-clear" onclick="clearSearchInput('doc-search')" title="Clear search">&times;</button>
      </div>
      <select id="filter-doc-status">
        <option value="">All Statuses</option>
        <option value="draft">Draft</option>
        <option value="stub">Stub</option>
        <option value="complete">Complete</option>
        <option value="in_review">In Review</option>
      </select>
      <select id="filter-doc-type"><option value="">All Types</option></select>
      <select id="filter-doc-section"><option value="">All Sections</option></select>
    </div>
    <div class="results-count" id="doc-results-count"></div>
    <div class="fact-table-wrap">
      <table>
        <thead>
          <tr>
            <th data-doc-sort="id" style="width:80px">ID <span class="sort-arrow"></span></th>
            <th data-doc-sort="title">Title <span class="sort-arrow"></span></th>
            <th data-doc-sort="type">Type <span class="sort-arrow"></span></th>
            <th data-doc-sort="sections">Sections <span class="sort-arrow"></span></th>
            <th data-doc-sort="status">Status <span class="sort-arrow"></span></th>
            <th style="width:55px">Facts</th>
            <th data-doc-sort="last_updated" style="width:90px">Updated <span class="sort-arrow"></span></th>
          </tr>
        </thead>
        <tbody id="doc-table-body"></tbody>
      </table>
    </div>
  </div>

  <!-- SLIDE PANE -->
  <div class="slide-overlay" id="slide-overlay" onclick="closeSlidePane()"></div>
  <div class="slide-pane" id="slide-pane">
    <div class="slide-pane-topbar">
      <div class="slide-pane-topbar-left">
        <div class="slide-pane-title" id="slide-pane-title"></div>
        <div class="slide-pane-meta" id="slide-pane-meta"></div>
      </div>
      <button class="slide-pane-close" onclick="closeSlidePane()">&times;</button>
    </div>
    <div class="slide-pane-split">
      <div class="slide-pane-doc">
        <div class="slide-pane-doc-header">
          <span class="panel-label">Document</span>
          <input type="text" class="doc-content-search" id="doc-content-search" placeholder="Search in document...">
          <span class="doc-search-count" id="doc-search-count"></span>
          <button class="doc-search-nav" id="doc-search-prev" onclick="docSearchNav(-1)" title="Previous match">&uarr;</button>
          <button class="doc-search-nav" id="doc-search-next" onclick="docSearchNav(1)" title="Next match">&darr;</button>
          <button class="doc-search-clear" id="doc-search-clear" onclick="clearDocSearch()" title="Clear search">&times;</button>
        </div>
        <div class="slide-pane-doc-body" id="slide-pane-doc-body"></div>
      </div>
      <div class="slide-pane-facts">
        <div class="slide-pane-facts-header">
          <span class="panel-label">Linked Facts</span>
          <span class="fact-count" id="pane-fact-count"></span>
          <div class="search-wrap" style="flex:1">
            <input type="text" class="slide-pane-facts-search" id="pane-fact-search" placeholder="Search facts...">
            <button class="search-clear" id="pane-fact-search-clear" onclick="clearSearchInput('pane-fact-search')" title="Clear search">&times;</button>
          </div>
        </div>
        <div class="slide-pane-facts-body" id="slide-pane-facts-body"></div>
      </div>
    </div>
  </div>
  <div class="selection-popup" id="selection-popup" onclick="findFactFromSelection()">Find Fact &rarr;</div>
  <div id="confirm-container"></div>

  <!-- DATASETS VIEW -->
  <div class="view" id="view-datasets">
    <div class="page-title">Datasets</div>
    <div class="controls">
      <div class="search-wrap">
        <input type="text" id="ds-search" placeholder="Search datasets by title, description, format...">
        <button class="search-clear" id="ds-search-clear" onclick="clearSearchInput('ds-search')" title="Clear search">&times;</button>
      </div>
      <select id="filter-ds-section"><option value="">All Sections</option></select>
      <select id="filter-ds-format">
        <option value="">All Formats</option>
        <option value="csv">CSV</option>
        <option value="xlsx">Excel</option>
        <option value="json">JSON</option>
      </select>
    </div>
    <div class="results-count" id="ds-results-count"></div>
    <div class="fact-table-wrap">
      <table>
        <thead>
          <tr>
            <th data-ds-sort="id" style="width:80px">ID <span class="sort-arrow"></span></th>
            <th data-ds-sort="title">Title <span class="sort-arrow"></span></th>
            <th data-ds-sort="format" style="width:70px">Format <span class="sort-arrow"></span></th>
            <th data-ds-sort="sections">Sections <span class="sort-arrow"></span></th>
            <th data-ds-sort="_total_rows" style="width:80px">Rows <span class="sort-arrow"></span></th>
            <th style="width:65px">Sample</th>
            <th data-ds-sort="date_added" style="width:90px">Added <span class="sort-arrow"></span></th>
          </tr>
        </thead>
        <tbody id="ds-table-body"></tbody>
      </table>
    </div>
  </div>

  <!-- DATASET SLIDE PANE -->
  <div class="slide-overlay" id="ds-slide-overlay" onclick="closeDsSlidePane()"></div>
  <div class="slide-pane" id="ds-slide-pane">
    <div class="slide-pane-topbar">
      <div class="slide-pane-topbar-left">
        <div class="slide-pane-title" id="ds-slide-title"></div>
        <div class="slide-pane-meta" id="ds-slide-meta"></div>
      </div>
      <button class="slide-pane-close" onclick="closeDsSlidePane()">&times;</button>
    </div>
    <div style="padding:20px;overflow:auto;flex:1">
      <div id="ds-slide-desc" style="margin-bottom:12px;color:var(--text-muted);font-size:13px"></div>
      <div id="ds-slide-source" style="margin-bottom:12px;font-size:12px;color:var(--text-muted)"></div>
      <div id="ds-slide-sample-info" style="margin-bottom:12px;font-size:12px;color:var(--accent)"></div>
      <div id="ds-slide-notes" style="margin-bottom:16px;font-size:12px;color:var(--text-muted);font-style:italic"></div>
      <div class="fact-table-wrap" style="overflow-x:auto">
        <table id="ds-slide-table">
          <thead id="ds-slide-thead"></thead>
          <tbody id="ds-slide-tbody"></tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- ARCHIVE VIEW -->
  <div class="view" id="view-archive">
    <div class="page-title">Archive</div>
    <div class="results-count" id="archive-results-count"></div>
    <div class="fact-table-wrap">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Claim</th>
            <th>Source</th>
            <th>Previous Status</th>
            <th>Archived</th>
            <th style="width:80px"></th>
          </tr>
        </thead>
        <tbody id="archive-body"></tbody>
      </table>
    </div>
  </div>

  <!-- CONTEXT VIEW -->
  <div class="view" id="view-context">
    <div class="page-title">Context Files</div>
    <div class="context-layout">
      <div class="context-file-list">
        <div class="context-file-list-header">
          <div class="search-wrap">
            <input type="text" id="context-search" placeholder="Search files...">
            <button class="search-clear" id="context-search-clear" onclick="clearSearchInput('context-search')" title="Clear search">&times;</button>
          </div>
          <button class="ctx-toolbar-btn" onclick="createContextFile()" style="width:100%;justify-content:center;gap:4px"><span style="font-size:15px">+</span> New File</button>
        </div>
        <div class="context-file-items" id="context-file-items"></div>
      </div>
      <div class="context-editor-area">
        <div class="context-editor-toolbar" id="context-toolbar" style="display:none">
          <span class="ctx-filename" id="ctx-filename"></span>
          <span class="ctx-unsaved" id="ctx-unsaved">Unsaved changes</span>
          <button class="ctx-toolbar-btn save-btn" id="ctx-save-btn" onclick="saveContextFile()">Save</button>
          <div class="ctx-toggle">
            <button class="ctx-toggle-opt active" id="ctx-mode-edit" onclick="setContextMode('edit')">Edit</button>
            <button class="ctx-toggle-opt" id="ctx-mode-preview" onclick="setContextMode('preview')">Preview</button>
          </div>
          <div class="ctx-menu-wrap">
            <button class="ctx-dots-btn" id="ctx-dots-btn" onclick="toggleCtxMenu(event)">&middot;&middot;&middot;</button>
            <div class="ctx-dropdown" id="ctx-dropdown">
              <button class="ctx-dropdown-item" onclick="renameContextFile()">&#9998; Rename</button>
              <button class="ctx-dropdown-item" onclick="downloadContextFile()">&#8615; Download</button>
              <button class="ctx-dropdown-item danger" onclick="deleteContextFile()">&#10005; Delete</button>
            </div>
          </div>
        </div>
        <div class="context-editor-body" id="context-editor-body">
          <div class="context-empty">
            <div class="ctx-empty-icon">&#128196;</div>
            <div>Select a file to view or edit</div>
            <div style="font-size:12px">Or click <b>+ New File</b> to create one</div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- CLAUDE INSTRUCTIONS VIEW -->
  <div class="view" id="view-claude-instructions">
    <div class="page-title">Claude Instructions</div>
    <div style="font-size:13px;color:var(--text-muted);margin-bottom:12px">
      Edit the CLAUDE.md file that configures agent behaviour. Download the file to save changes to disk.
    </div>
    <div class="context-layout">
      <div class="context-editor-area" style="flex:1">
        <div class="context-editor-toolbar" id="claude-toolbar">
          <span class="ctx-filename">CLAUDE.md</span>
          <span class="ctx-unsaved" id="claude-unsaved">Unsaved changes</span>
          <button class="ctx-toolbar-btn save-btn" id="claude-save-btn" onclick="saveClaudeMd()">Save</button>
          <div class="ctx-toggle">
            <button class="ctx-toggle-opt active" id="claude-mode-edit" onclick="setClaudeMode('edit')">Edit</button>
            <button class="ctx-toggle-opt" id="claude-mode-preview" onclick="setClaudeMode('preview')">Preview</button>
          </div>
        </div>
        <div class="context-editor-body" id="claude-editor-body">
          <textarea class="context-textarea" id="claude-textarea" placeholder="No CLAUDE.md found..."></textarea>
          <div class="context-preview" id="claude-preview"></div>
        </div>
      </div>
    </div>
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
const CONTEXT_FILES = %%CONTEXT_FILES_JSON%%;
const CLAUDE_MD_CONTENT = %%CLAUDE_MD_JSON%%;
const DATASETS = %%DATASETS_JSON%%;
const DS_MAP = {};
DATASETS.forEach(d => DS_MAP[d.id] = d);

// Build doc lookup
const DOC_MAP = {};
DOCUMENTS.forEach(d => DOC_MAP[d.id] = d);

// Normalize fact status: support both boolean `verified` and string `verification_status`
function getFactStatus(f) {
  if (f.verification_status) return f.verification_status;
  return f.verified ? 'verified' : 'unverified';
}
function setFactStatus(f, status) {
  f.verification_status = status;
  f.verified = (status === 'verified');
}
// Initialize all facts
FACTS.forEach(f => { if (!f.verification_status) f.verification_status = getFactStatus(f); });

// --- ARCHIVE ---
const ARCHIVED = [];

function statusBadgeHtml(f, clickable) {
  const s = getFactStatus(f);
  if (clickable) {
    const sel = (v) => v === s ? ' selected' : '';
    return `<select class="status-select s-${s}" onchange="event.stopPropagation();changeFactStatus('${esc(f.id)}',this.value,this)" onclick="event.stopPropagation()">
      <option value="unverified"${sel('unverified')}>Unverified</option>
      <option value="verified"${sel('verified')}>Verified</option>
      <option value="flagged"${sel('flagged')}>Flagged</option>
      <option value="archive">Archive...</option>
    </select>`;
  }
  const cls = 'badge badge-' + s;
  const label = s === 'verified' ? 'Verified' : s === 'flagged' ? 'Flagged' : 'Unverified';
  return `<span class="${cls}">${label}</span>`;
}

function changeFactStatus(factId, newStatus, selectEl) {
  const f = FACTS.find(x => x.id === factId);
  if (!f) return;
  const oldStatus = getFactStatus(f);

  if (newStatus === 'flagged') {
    showConfirm(
      'Flag this fact?',
      'This will mark the fact as flagged for review.',
      f.claim,
      'Flag', 'btn-danger',
      () => { applyStatus(f, 'flagged'); },
      () => { revertSelect(selectEl, oldStatus); }
    );
  } else if (newStatus === 'archive') {
    showConfirm(
      'Archive this fact?',
      'This will remove the fact from all views and move it to the archive.',
      f.claim,
      'Archive', 'btn-warn',
      () => { archiveFact(f); },
      () => { revertSelect(selectEl, oldStatus); }
    );
  } else {
    applyStatus(f, newStatus);
  }
}

function revertSelect(selectEl, oldStatus) {
  if (selectEl) selectEl.value = oldStatus;
}

function applyStatus(f, status) {
  setFactStatus(f, status);
  refreshAllViews();
  // Persist to disk
  if (f._file) {
    fetch('/api/save-fact-status', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({id: f.id, status: status, file: f._file})
    }).catch(err => console.error('Save fact status failed:', err));
  }
}

function archiveFact(f) {
  const idx = FACTS.indexOf(f);
  if (idx === -1) return;
  f._archivedFrom = getFactStatus(f);
  f._archivedDate = new Date().toISOString().slice(0, 10);
  FACTS.splice(idx, 1);
  ARCHIVED.push(f);
  // Update doc fact counts
  if (f.document && DOC_FACT_COUNTS[f.document]) {
    DOC_FACT_COUNTS[f.document]--;
  }
  // Update pane facts if open
  if (currentPaneDocId) {
    currentPaneFacts = FACTS.filter(x => x.document === currentPaneDocId);
    document.getElementById('pane-fact-count').textContent = '(' + currentPaneFacts.length + ')';
  }
  refreshAllViews();
  renderArchive();
}

function deleteArchivedFact(archivedIdx) {
  const f = ARCHIVED[archivedIdx];
  if (!f) return;
  showConfirm(
    'Permanently delete this fact?',
    'This cannot be undone. The fact will be removed entirely.',
    f.claim,
    'Delete', 'btn-danger',
    () => { ARCHIVED.splice(archivedIdx, 1); renderArchive(); updateArchiveCount(); },
    () => {}
  );
}

function restoreArchivedFact(archivedIdx) {
  const f = ARCHIVED[archivedIdx];
  if (!f) return;
  ARCHIVED.splice(archivedIdx, 1);
  setFactStatus(f, f._archivedFrom || 'unverified');
  delete f._archivedFrom;
  delete f._archivedDate;
  FACTS.push(f);
  if (f.document) {
    DOC_FACT_COUNTS[f.document] = (DOC_FACT_COUNTS[f.document] || 0) + 1;
  }
  refreshAllViews();
  renderArchive();
}

function renderArchive() {
  const tbody = document.getElementById('archive-body');
  updateArchiveCount();
  document.getElementById('archive-results-count').textContent = ARCHIVED.length + ' archived fact' + (ARCHIVED.length !== 1 ? 's' : '');
  if (ARCHIVED.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:40px;color:var(--text-muted)">No archived facts.</td></tr>';
    return;
  }
  tbody.innerHTML = ARCHIVED.map((f, i) => {
    const prevStatus = f._archivedFrom || 'unverified';
    const prevLabel = prevStatus === 'verified' ? 'Verified' : prevStatus === 'flagged' ? 'Flagged' : 'Unverified';
    const prevCls = 'badge badge-' + prevStatus;
    return `<tr>
      <td style="font-family:monospace;font-size:11px;color:var(--text-muted)">${esc(f.id)}</td>
      <td style="font-size:12px">${esc(truncate(f.claim, 120))}</td>
      <td style="font-size:11px;color:var(--text-muted)">${esc(truncate(f.source_name || '', 40))}</td>
      <td><span class="${prevCls}">${prevLabel}</span></td>
      <td style="font-size:11px;color:var(--text-muted);white-space:nowrap">${esc(f._archivedDate || '')}</td>
      <td style="white-space:nowrap">
        <button class="expand-toggle" onclick="restoreArchivedFact(${i})" style="margin-right:4px">Restore</button>
        <button class="expand-toggle" onclick="deleteArchivedFact(${i})" style="color:var(--red);border-color:rgba(248,81,73,0.3)">Delete</button>
      </td>
    </tr>`;
  }).join('');
}

function updateArchiveCount() {
  document.getElementById('nav-archive-count').textContent = ARCHIVED.length;
}

function refreshAllViews() {
  renderTable();
  renderCards();
  renderDocTable();
  updateArchiveCount();
  if (currentPaneDocId) renderPaneFacts();
  const secView = document.getElementById('view-section');
  if (secView.classList.contains('active')) {
    const activeNav = document.querySelector('.nav-item.active[data-section]');
    if (activeNav) showSectionView(activeNav.dataset.section);
  }
}

// --- CONFIRM DIALOG ---
function showConfirm(title, message, claimText, actionLabel, actionClass, onConfirm, onCancel) {
  const container = document.getElementById('confirm-container');
  container.innerHTML = `<div class="confirm-overlay" id="confirm-overlay">
    <div class="confirm-dialog">
      <h3>${esc(title)}</h3>
      <p>${esc(message)}</p>
      ${claimText ? `<div class="confirm-claim">${esc(truncate(claimText, 200))}</div>` : ''}
      <div class="confirm-btns">
        <button class="btn-cancel" id="confirm-cancel">Cancel</button>
        <button class="${actionClass}" id="confirm-action">${esc(actionLabel)}</button>
      </div>
    </div>
  </div>`;
  document.getElementById('confirm-cancel').onclick = () => { container.innerHTML = ''; onCancel(); };
  document.getElementById('confirm-action').onclick = () => { container.innerHTML = ''; onConfirm(); };
  document.getElementById('confirm-overlay').onclick = (e) => {
    if (e.target === e.currentTarget) { container.innerHTML = ''; onCancel(); }
  };
}

// --- NAV ---
function toggleSection(label) {
  const items = label.nextElementSibling;
  if (!items || !items.classList.contains('nav-section-items')) return;
  label.classList.toggle('collapsed');
  if (items.classList.contains('collapsed')) {
    items.style.maxHeight = items.scrollHeight + 'px';
    items.classList.remove('collapsed');
  } else {
    items.style.maxHeight = items.scrollHeight + 'px';
    requestAnimationFrame(() => { items.classList.add('collapsed'); items.style.maxHeight = '0'; });
  }
}

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

  // Set initial max-height for all section item containers
  document.querySelectorAll('.nav-section-items').forEach(el => {
    el.style.maxHeight = el.scrollHeight + 'px';
  });
}

// --- DASHBOARD ---
function renderCards() {
  const el = document.getElementById('cards');
  const vCount = FACTS.filter(f => getFactStatus(f) === 'verified').length;
  const fCount = FACTS.filter(f => getFactStatus(f) === 'flagged').length;
  const uCount = FACTS.length - vCount - fCount;
  const pct = FACTS.length > 0 ? Math.round((vCount / FACTS.length) * 100) : 0;
  el.innerHTML = `
    <div class="card"><div class="card-label">Total Facts</div><div class="card-value accent">${FACTS.length}</div></div>
    <div class="card"><div class="card-label">Verified</div><div class="card-value green">${vCount}</div></div>
    <div class="card"><div class="card-label">Unverified</div><div class="card-value" style="color:var(--orange)">${uCount}</div></div>
    <div class="card"><div class="card-label">Flagged</div><div class="card-value red">${fCount}</div></div>
    <div class="card"><div class="card-label">Verified %</div><div class="card-value ${pct>=80?'green':pct>=50?'accent':'red'}">${pct}%</div></div>
    <div class="card"><div class="card-label">Documents</div><div class="card-value accent">${DOCUMENTS.length}</div></div>
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
    if (verified && getFactStatus(f) !== verified) return false;
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
  const statusBadge = statusBadgeHtml(f, true);
  const verNotes = f.verification_notes
    ? `<br><span style="font-size:10px;color:var(--orange)">Note: ${esc(f.verification_notes)}</span>` : '';

  const docBadge = f.document && DOC_MAP[f.document]
    ? `<span class="badge badge-doc" onclick="navigateToDoc('${esc(f.document)}')" title="${esc(f.document)}">${esc(DOC_MAP[f.document].title)}</span>`
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

// --- DOCUMENT STATUS EDITING ---
function docStatusSelectHtml(doc) {
  const s = (!doc.status || doc.status === 'stub') ? 'draft' : doc.status;
  const sel = (v) => v === s ? ' selected' : '';
  return `<select class="status-select s-${s}" onchange="event.stopPropagation();changeDocStatus('${esc(doc.id)}',this.value,this)" onclick="event.stopPropagation()">
    <option value="draft"${sel('draft')}>Draft</option>
    <option value="in_review"${sel('in_review')}>In Review</option>
    <option value="complete"${sel('complete')}>Complete</option>
  </select>`;
}

function changeDocStatus(docId, newStatus, selectEl) {
  const doc = DOC_MAP[docId];
  if (!doc) return;
  doc.status = newStatus;
  // Update select styling in-place
  if (selectEl) {
    selectEl.className = 'status-select s-' + newStatus;
  }
  // Re-render doc table to reflect change (also updates slide pane status if open)
  renderDocTable();
  // If the slide pane is open for this doc, update the pane's status dropdown too
  if (currentPaneDocId === docId) {
    openSlidePane(docId);
  }
  // Persist to disk
  fetch('/api/save-doc-status', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({id: docId, status: newStatus})
  }).catch(err => console.error('Save doc status failed:', err));
}

// --- DOCUMENT TABLE VIEW ---
let docSortCol = 'id', docSortAsc = true;

// Precompute fact counts per document
const DOC_FACT_COUNTS = {};
FACTS.forEach(f => {
  if (f.document) DOC_FACT_COUNTS[f.document] = (DOC_FACT_COUNTS[f.document] || 0) + 1;
});

function getFilteredDocs() {
  const search = document.getElementById('doc-search').value.toLowerCase();
  const status = document.getElementById('filter-doc-status').value;
  const type = document.getElementById('filter-doc-type').value;
  const section = document.getElementById('filter-doc-section').value;

  return DOCUMENTS.filter(d => {
    if (status && d.status !== status) return false;
    if (type && d.type !== type) return false;
    if (section && !(d.sections || []).includes(section)) return false;
    if (search) {
      const hay = [d.id, d.title, d.description,
        ...(d.sections || []).map(s => s + ' ' + (SECTION_LABELS[s] || '')),
        DOC_TYPE_LABELS[d.type] || '',
        DOC_STATUS_LABELS[d.status] || '', d.content || ''
      ].join(' ').toLowerCase();
      if (!hay.includes(search)) return false;
    }
    return true;
  }).sort((a, b) => {
    let va = a[docSortCol] ?? '', vb = b[docSortCol] ?? '';
    if (docSortCol === 'sections') { va = (a.sections || [])[0] || ''; vb = (b.sections || [])[0] || ''; }
    if (docSortCol === 'facts') { va = DOC_FACT_COUNTS[a.id] || 0; vb = DOC_FACT_COUNTS[b.id] || 0; }
    if (typeof va === 'string') { va = va.toLowerCase(); vb = vb.toLowerCase(); }
    return docSortAsc ? (va < vb ? -1 : va > vb ? 1 : 0) : (va > vb ? -1 : va < vb ? 1 : 0);
  });
}

function renderDocTable() {
  const docs = getFilteredDocs();
  const tbody = document.getElementById('doc-table-body');
  document.getElementById('doc-results-count').textContent = `Showing ${docs.length} of ${DOCUMENTS.length} documents`;
  if (docs.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:40px;color:var(--text-muted)">No documents match your filters.</td></tr>';
    return;
  }
  tbody.innerHTML = docs.map(d => {
    const typeLabel = DOC_TYPE_LABELS[d.type] || d.type;
    const secTags = (d.sections || []).map(s =>
      `<span class="badge badge-section">${esc(SECTION_LABELS[s] || s)}</span>`
    ).join(' ');
    const factCount = DOC_FACT_COUNTS[d.id] || 0;
    return `<tr class="doc-table-row" onclick="openSlidePane('${esc(d.id)}')" id="doc-row-${esc(d.id)}">
      <td style="font-family:monospace;font-size:11px;color:var(--accent);white-space:nowrap">${esc(d.id)}</td>
      <td>
        <div style="font-weight:600;font-size:13px">${esc(d.title)}</div>
        <div style="font-size:11px;color:var(--text-muted);margin-top:2px">${esc(truncate(d.description, 80))}</div>
      </td>
      <td style="font-size:12px;color:var(--text-muted)">${esc(typeLabel)}</td>
      <td>${secTags || '<span style="color:var(--text-muted);font-size:11px">—</span>'}</td>
      <td>${docStatusSelectHtml(d)}</td>
      <td style="text-align:center;font-size:12px;color:${factCount > 0 ? 'var(--accent)' : 'var(--text-muted)'}">${factCount}</td>
      <td style="white-space:nowrap;font-size:11px;color:var(--text-muted)">${esc(d.last_updated || d.date_created || '')}</td>
    </tr>`;
  }).join('');
}

function populateDocFilters() {
  const typeSelect = document.getElementById('filter-doc-type');
  for (const [key, label] of Object.entries(DOC_TYPE_LABELS)) {
    typeSelect.innerHTML += `<option value="${key}">${label}</option>`;
  }
  const secSelect = document.getElementById('filter-doc-section');
  for (const [key, label] of Object.entries(SECTION_LABELS)) {
    secSelect.innerHTML += `<option value="${key}">${label}</option>`;
  }
}

// --- SLIDE PANE ---
let currentPaneDocId = null;
let currentPaneFacts = [];
let selectedText = '';

function openSlidePane(docId) {
  const doc = DOC_MAP[docId];
  if (!doc) return;
  currentPaneDocId = docId;

  // Highlight table row
  document.querySelectorAll('.doc-table-row').forEach(r => r.classList.remove('active'));
  const row = document.getElementById('doc-row-' + docId);
  if (row) row.classList.add('active');

  const typeLabel = DOC_TYPE_LABELS[doc.type] || doc.type;
  const secTags = (doc.sections || []).map(s =>
    `<span class="badge badge-section">${esc(SECTION_LABELS[s] || s)}</span>`
  ).join(' ');

  document.getElementById('slide-pane-title').textContent = doc.title;
  document.getElementById('slide-pane-meta').innerHTML = `
    <span style="font-size:12px;color:var(--text-muted)">${esc(typeLabel)}</span>
    ${docStatusSelectHtml(doc)}
    <span style="color:var(--text-muted)">${esc(doc.id)}</span>
    ${secTags}
    ${doc.last_updated ? `<span style="color:var(--text-muted)">&middot; Updated ${esc(doc.last_updated)}</span>` : ''}
  `;

  // Clear document search
  document.getElementById('doc-content-search').value = '';
  clearDocSearchHighlights();

  // Document content
  document.getElementById('slide-pane-doc-body').innerHTML = doc.content
    ? marked.parse(doc.content)
    : '<p style="color:var(--text-muted)">No content yet.</p>';

  // Linked facts
  currentPaneFacts = FACTS.filter(f => f.document === docId);
  document.getElementById('pane-fact-count').textContent = `(${currentPaneFacts.length})`;
  document.getElementById('pane-fact-search').value = '';
  renderPaneFacts();

  // Open pane
  document.getElementById('slide-overlay').classList.add('open');
  document.getElementById('slide-pane').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function renderPaneFacts(highlightFactId) {
  const search = document.getElementById('pane-fact-search').value.toLowerCase();
  const filtered = currentPaneFacts.filter(f => {
    if (!search) return true;
    const hay = [f.id, f.claim, f.source_name, f.source_excerpt,
      ...(f.source_quotes || []), f.verification_notes, f.notes
    ].join(' ').toLowerCase();
    return hay.includes(search);
  });

  const body = document.getElementById('slide-pane-facts-body');
  if (filtered.length === 0) {
    body.innerHTML = `<div style="padding:40px 20px;text-align:center;color:var(--text-muted);font-size:13px">
      ${currentPaneFacts.length === 0 ? 'No linked facts.' : 'No facts match your search.'}
    </div>`;
    return;
  }

  body.innerHTML = `<table>
    <thead><tr>
      <th>ID</th><th>Status</th><th>Claim</th><th>Source</th>
    </tr></thead>
    <tbody>${filtered.map(f => {
      const badge = statusBadgeHtml(f, true);
      const hl = highlightFactId === f.id ? ' fact-highlight' : '';
      const hasExcerpt = f.source_excerpt && f.source_excerpt.trim();
      const excerptBtn = hasExcerpt
        ? `<br><button class="expand-toggle" onclick="event.stopPropagation();togglePaneExcerpt('${esc(f.id)}')">Source excerpt</button>` : '';
      const sourceLink = f.source_url
        ? `<a class="source-link" href="${esc(f.source_url)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">${esc(truncate(f.source_name || f.source_url, 35))}</a>`
        : esc(truncate(f.source_name || '', 35));

      let rows = `<tr id="pane-fact-${esc(f.id)}" class="${hl}" style="cursor:pointer"
          onclick="scrollToClaimInDoc('${esc(f.id)}')"
          title="Click to find in document">
        <td style="font-family:monospace;font-size:11px;color:var(--accent);white-space:nowrap">${esc(f.id)}</td>
        <td>${badge}</td>
        <td class="pane-fact-claim">${esc(f.claim)}${excerptBtn}</td>
        <td>${sourceLink}
          ${f.source_date ? `<br><span style="font-size:10px;color:var(--text-muted)">${esc(f.source_date)}</span>` : ''}</td>
      </tr>`;
      if (hasExcerpt) {
        rows += `<tr class="pane-excerpt-row" id="pane-excerpt-${esc(f.id)}">
          <td colspan="4" class="pane-excerpt-cell">
            <div class="excerpt-label">Source Excerpt</div>
            <div class="excerpt-content">${marked.parse(f.source_excerpt)}</div>
          </td>
        </tr>`;
      }
      return rows;
    }).join('')}</tbody>
  </table>`;

  // Scroll to highlighted fact
  if (highlightFactId) {
    setTimeout(() => {
      const el = document.getElementById('pane-fact-' + highlightFactId);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 50);
  }
}

function togglePaneExcerpt(id) {
  const row = document.getElementById('pane-excerpt-' + id);
  if (row) row.classList.toggle('visible');
}

function scrollToClaimInDoc(factId) {
  const f = FACTS.find(x => x.id === factId) || ARCHIVED.find(x => x.id === factId);
  if (!f || !f.claim) return;

  const docBody = document.getElementById('slide-pane-doc-body');
  if (!docBody) return;

  // Clear search highlights first to avoid DOM conflicts
  document.getElementById('doc-content-search').value = '';
  clearDocSearchHighlights();

  // Remove any previous highlights
  docBody.querySelectorAll('.doc-highlight-mark').forEach(el => {
    const parent = el.parentNode;
    parent.replaceChild(document.createTextNode(el.textContent), el);
    parent.normalize();
  });

  // Try to find the claim text (or significant substrings) in the document
  const claim = f.claim;
  const found = highlightTextInElement(docBody, claim);

  if (!found) {
    const words = claim.split(/\s+/);
    let partialFound = false;
    for (let fraction of [0.6, 0.4]) {
      const partial = words.slice(0, Math.max(Math.ceil(words.length * fraction), 4)).join(' ');
      if (partial.length >= 10 && highlightTextInElement(docBody, partial)) {
        partialFound = true;
        break;
      }
    }
    if (!partialFound) {
      for (const q of (f.source_quotes || [])) {
        if (q && q.length >= 10 && highlightTextInElement(docBody, q)) break;
      }
    }
  }

  const mark = docBody.querySelector('.doc-highlight-mark');
  if (mark) {
    mark.scrollIntoView({ behavior: 'smooth', block: 'center' });
    const factRow = document.getElementById('pane-fact-' + factId);
    if (factRow) { factRow.classList.add('fact-highlight'); setTimeout(() => factRow.classList.remove('fact-highlight'), 2000); }
    setTimeout(() => {
      docBody.querySelectorAll('.doc-highlight-mark').forEach(el => el.classList.add('fading'));
      setTimeout(() => {
        docBody.querySelectorAll('.doc-highlight-mark').forEach(el => {
          const parent = el.parentNode;
          parent.replaceChild(document.createTextNode(el.textContent), el);
          parent.normalize();
        });
      }, 500);
    }, 4000);
  } else {
    // No match found — briefly flash the fact row red
    const factRow = document.getElementById('pane-fact-' + factId);
    if (factRow) {
      factRow.style.background = 'rgba(248, 81, 73, 0.15)';
      setTimeout(() => { factRow.style.background = ''; }, 1500);
    }
  }
}

// Normalize text: collapse whitespace, normalize dashes/quotes/unicode
function normText(s) {
  return s.toLowerCase()
    .replace(/[\u2013\u2014\u2015]/g, '-')  // en-dash, em-dash -> hyphen
    .replace(/[\u2018\u2019\u201A\u201B]/g, "'")  // smart single quotes
    .replace(/[\u201C\u201D\u201E\u201F]/g, '"')  // smart double quotes
    .replace(/\u2026/g, '...')
    .replace(/\s+/g, ' ')
    .trim();
}

function highlightTextInElement(root, searchText) {
  if (!searchText || searchText.length < 3) return false;

  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
  const textNodes = [];
  while (walker.nextNode()) textNodes.push(walker.currentNode);

  // Build full text with character mapping back to original positions
  let fullText = '';
  const nodeMap = [];
  for (const node of textNodes) {
    const start = fullText.length;
    fullText += node.textContent;
    nodeMap.push({ node, start, end: fullText.length });
  }

  const normFull = normText(fullText);
  const normSearch = normText(searchText);
  const normIdx = normFull.indexOf(normSearch);
  if (normIdx === -1) return false;

  // Map normalized index back to original text index
  // Build a mapping: for each char in normFull, what's the original index
  const origLower = fullText.toLowerCase()
    .replace(/[\u2013\u2014\u2015]/g, '-')
    .replace(/[\u2018\u2019\u201A\u201B]/g, "'")
    .replace(/[\u201C\u201D\u201E\u201F]/g, '"')
    .replace(/\u2026/g, '...');
  // Since normText collapses whitespace, we need a char-by-char map
  const normToOrig = [];
  let oi = 0;
  const rawNorm = fullText
    .replace(/[\u2013\u2014\u2015]/g, '-')
    .replace(/[\u2018\u2019\u201A\u201B]/g, "'")
    .replace(/[\u201C\u201D\u201E\u201F]/g, '"')
    .replace(/\u2026/g, '...');
  // Simpler approach: find the search text using a regex that treats any whitespace as flexible
  const escaped = normSearch.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const flexPattern = escaped.replace(/ /g, '\\s+');
  const origForSearch = fullText
    .replace(/[\u2013\u2014\u2015]/g, '-')
    .replace(/[\u2018\u2019\u201A\u201B]/g, "'")
    .replace(/[\u201C\u201D\u201E\u201F]/g, '"');
  const re = new RegExp(flexPattern, 'i');
  const m = re.exec(origForSearch);
  if (!m) return false;

  const idx = m.index;
  const matchLen = m[0].length;
  const matchEnd = idx + matchLen;

  // Find which text nodes this spans and wrap them
  for (let i = nodeMap.length - 1; i >= 0; i--) {
    const nm = nodeMap[i];
    if (nm.end <= idx || nm.start >= matchEnd) continue;

    const node = nm.node;
    const nodeStart = Math.max(idx - nm.start, 0);
    const nodeEnd = Math.min(matchEnd - nm.start, node.textContent.length);

    if (nodeStart === 0 && nodeEnd === node.textContent.length) {
      const mark = document.createElement('span');
      mark.className = 'doc-highlight-mark';
      node.parentNode.replaceChild(mark, node);
      mark.appendChild(node);
    } else {
      const text = node.textContent;
      const before = text.slice(0, nodeStart);
      const match = text.slice(nodeStart, nodeEnd);
      const after = text.slice(nodeEnd);
      const frag = document.createDocumentFragment();
      if (before) frag.appendChild(document.createTextNode(before));
      const mark = document.createElement('span');
      mark.className = 'doc-highlight-mark';
      mark.textContent = match;
      frag.appendChild(mark);
      if (after) frag.appendChild(document.createTextNode(after));
      node.parentNode.replaceChild(frag, node);
    }
  }
  return true;
}

// Pane facts search
document.getElementById('pane-fact-search').addEventListener('input', () => renderPaneFacts());

// --- IN-DOCUMENT CONTENT SEARCH ---
let docSearchMatches = [];
let docSearchCurrentIdx = -1;
let docSearchDebounce = null;

document.getElementById('doc-content-search').addEventListener('input', () => {
  clearTimeout(docSearchDebounce);
  docSearchDebounce = setTimeout(performDocContentSearch, 200);
});

document.getElementById('doc-content-search').addEventListener('keydown', e => {
  if (e.key === 'Enter') {
    e.preventDefault();
    docSearchNav(e.shiftKey ? -1 : 1);
  }
  if (e.key === 'Escape') {
    e.target.value = '';
    clearDocSearchHighlights();
  }
});

function performDocContentSearch() {
  clearDocSearchHighlights();
  const query = document.getElementById('doc-content-search').value.trim();
  if (!query || query.length < 2) return;

  const docBody = document.getElementById('slide-pane-doc-body');
  if (!docBody) return;

  // Collect text nodes
  const walker = document.createTreeWalker(docBody, NodeFilter.SHOW_TEXT, null);
  const textNodes = [];
  while (walker.nextNode()) textNodes.push(walker.currentNode);

  // Build full text with node mapping
  let fullText = '';
  const nodeMap = [];
  for (const node of textNodes) {
    const start = fullText.length;
    fullText += node.textContent;
    nodeMap.push({ node, start, end: fullText.length });
  }

  // Find all matches (case-insensitive)
  const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const re = new RegExp(escaped, 'gi');
  const allMatches = [];
  let m;
  while ((m = re.exec(fullText)) !== null) {
    allMatches.push({ index: m.index, length: m[0].length });
  }

  if (allMatches.length === 0) {
    updateDocSearchUI();
    return;
  }

  // Wrap matches in reverse order to preserve indices
  for (let mi = allMatches.length - 1; mi >= 0; mi--) {
    const match = allMatches[mi];
    const matchEnd = match.index + match.length;

    for (let i = nodeMap.length - 1; i >= 0; i--) {
      const nm = nodeMap[i];
      if (nm.end <= match.index || nm.start >= matchEnd) continue;

      const node = nm.node;
      if (!node.parentNode) continue;

      const nodeStart = Math.max(match.index - nm.start, 0);
      const nodeEnd = Math.min(matchEnd - nm.start, node.textContent.length);

      if (nodeStart === 0 && nodeEnd === node.textContent.length) {
        const mark = document.createElement('span');
        mark.className = 'doc-search-match';
        mark.dataset.matchIndex = mi;
        node.parentNode.replaceChild(mark, node);
        mark.appendChild(node);
      } else {
        const text = node.textContent;
        const before = text.slice(0, nodeStart);
        const mid = text.slice(nodeStart, nodeEnd);
        const after = text.slice(nodeEnd);
        const frag = document.createDocumentFragment();
        if (before) frag.appendChild(document.createTextNode(before));
        const mark = document.createElement('span');
        mark.className = 'doc-search-match';
        mark.dataset.matchIndex = mi;
        mark.textContent = mid;
        frag.appendChild(mark);
        if (after) frag.appendChild(document.createTextNode(after));
        node.parentNode.replaceChild(frag, node);
      }
    }
  }

  docSearchMatches = docBody.querySelectorAll('.doc-search-match');
  docSearchCurrentIdx = 0;
  updateDocSearchUI();
  // Scroll to first match
  if (docSearchMatches.length > 0) {
    docSearchMatches[0].classList.add('current');
    docSearchMatches[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
}

function docSearchNav(dir) {
  if (docSearchMatches.length === 0) return;
  docSearchMatches[docSearchCurrentIdx]?.classList.remove('current');
  docSearchCurrentIdx = (docSearchCurrentIdx + dir + docSearchMatches.length) % docSearchMatches.length;
  docSearchMatches[docSearchCurrentIdx].classList.add('current');
  docSearchMatches[docSearchCurrentIdx].scrollIntoView({ behavior: 'smooth', block: 'center' });
  updateDocSearchUI();
}

function updateDocSearchUI() {
  const count = docSearchMatches.length;
  const hasQuery = document.getElementById('doc-content-search').value.trim().length > 0;
  document.getElementById('doc-search-count').textContent = count > 0
    ? `${docSearchCurrentIdx + 1} / ${count}`
    : (hasQuery ? '0 results' : '');
  document.getElementById('doc-search-prev').classList.toggle('visible', count > 1);
  document.getElementById('doc-search-next').classList.toggle('visible', count > 1);
  document.getElementById('doc-search-clear').classList.toggle('visible', hasQuery);
}

function clearDocSearch() {
  document.getElementById('doc-content-search').value = '';
  clearDocSearchHighlights();
  document.getElementById('doc-content-search').focus();
}

function clearDocSearchHighlights() {
  const docBody = document.getElementById('slide-pane-doc-body');
  if (!docBody) return;
  docBody.querySelectorAll('.doc-search-match').forEach(el => {
    const parent = el.parentNode;
    parent.replaceChild(document.createTextNode(el.textContent), el);
    parent.normalize();
  });
  docSearchMatches = [];
  docSearchCurrentIdx = -1;
  document.getElementById('doc-search-count').textContent = '';
  document.getElementById('doc-search-prev').classList.remove('visible');
  document.getElementById('doc-search-next').classList.remove('visible');
  document.getElementById('doc-search-clear').classList.remove('visible');
}

function closeSlidePane() {
  document.getElementById('slide-overlay').classList.remove('open');
  document.getElementById('slide-pane').classList.remove('open');
  document.body.style.overflow = '';
  document.querySelectorAll('.doc-table-row').forEach(r => r.classList.remove('active'));
  hideSelectionPopup();
  currentPaneDocId = null;
}

// Close on Escape
document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && currentPaneDocId) closeSlidePane();
});

// --- SELECTION POPUP (highlight text -> find fact) ---
const selPopup = document.getElementById('selection-popup');

function hideSelectionPopup() {
  selPopup.style.display = 'none';
  selectedText = '';
}

document.addEventListener('mouseup', e => {
  if (!currentPaneDocId) return;
  // Only trigger inside the doc body
  const docBody = document.getElementById('slide-pane-doc-body');
  if (!docBody || !docBody.contains(e.target)) {
    if (!selPopup.contains(e.target)) hideSelectionPopup();
    return;
  }

  const sel = window.getSelection();
  const text = sel.toString().trim();
  if (text.length < 3) { hideSelectionPopup(); return; }

  selectedText = text;
  const range = sel.getRangeAt(0);
  const rect = range.getBoundingClientRect();

  selPopup.style.left = (rect.left + rect.width / 2 - 50) + 'px';
  selPopup.style.top = (rect.top - 40) + 'px';
  selPopup.style.display = 'block';
});

function findFactFromSelection() {
  if (!selectedText || !currentPaneDocId) return;
  const query = selectedText.toLowerCase();

  // Score each fact by how well it matches the selected text
  let bestFact = null;
  let bestScore = 0;

  currentPaneFacts.forEach(f => {
    const fields = [f.claim, ...(f.source_quotes || []), f.source_excerpt, f.notes].join(' ').toLowerCase();
    if (fields.includes(query)) {
      // Exact substring match gets high score
      const score = query.length;
      if (score > bestScore) { bestScore = score; bestFact = f; }
    } else {
      // Word overlap scoring
      const queryWords = query.split(/\s+/).filter(w => w.length > 2);
      const matchCount = queryWords.filter(w => fields.includes(w)).length;
      const score = matchCount / Math.max(queryWords.length, 1);
      if (score > bestScore && score > 0.3) { bestScore = score; bestFact = f; }
    }
  });

  hideSelectionPopup();

  if (bestFact) {
    // Clear search, render with highlight
    document.getElementById('pane-fact-search').value = '';
    renderPaneFacts(bestFact.id);
    // Remove highlight after a few seconds
    setTimeout(() => {
      const el = document.getElementById('pane-fact-' + bestFact.id);
      if (el) el.classList.remove('fact-highlight');
    }, 4000);
  } else {
    // No match found — ask user before creating a flagged fact
    const capturedDocId = currentPaneDocId;
    const capturedText = selectedText;
    showConfirm(
      'No matching fact found',
      'Would you like to add this as a flagged fact for review?',
      capturedText,
      'Add as Flagged', 'btn-danger',
      () => {
        const doc = DOC_MAP[capturedDocId];
        const section = doc ? doc.section : '';
        const newId = 'FLAG-' + Date.now().toString(36).toUpperCase();
        const newFact = {
          id: newId,
          claim: capturedText,
          source_quotes: [],
          source_excerpt: '',
          source_name: '',
          source_author: '',
          source_url: '',
          source_page: '',
          source_type: '',
          source_date: '',
          sections_used: section ? [section] : [],
          document: capturedDocId,
          data_table: '',
          verified: false,
          verification_status: 'flagged',
          verification_notes: 'Flagged: no matching fact found for highlighted text',
          confidence: '',
          date_added: new Date().toISOString().slice(0, 10),
          added_by: 'dashboard',
          notes: '',
          _file: 'flagged'
        };
        FACTS.push(newFact);
        if (currentPaneDocId === capturedDocId) {
          currentPaneFacts.push(newFact);
          document.getElementById('pane-fact-count').textContent = '(' + currentPaneFacts.length + ')';
          document.getElementById('pane-fact-search').value = '';
          renderPaneFacts(newId);
          setTimeout(() => {
            const el = document.getElementById('pane-fact-' + newId);
            if (el) el.classList.remove('fact-highlight');
          }, 4000);
        }
        DOC_FACT_COUNTS[capturedDocId] = (DOC_FACT_COUNTS[capturedDocId] || 0) + 1;
        refreshAllViews();
      },
      () => {}
    );
  }
}

// --- CROSS-NAVIGATION ---
function navigateToDoc(docId) {
  // Switch to documents view and open the slide pane
  document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
  document.querySelector('[data-view="documents"]').classList.add('active');
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.getElementById('view-documents').classList.add('active');
  openSlidePane(docId);
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
    const badge = statusBadgeHtml(f, true);
    const verNotes = f.verification_notes
      ? `<br><span style="font-size:10px;color:var(--orange)">Note: ${esc(f.verification_notes)}</span>` : '';
    const docBadge = f.document && DOC_MAP[f.document]
      ? `<span class="badge badge-doc" onclick="navigateToDoc('${esc(f.document)}')" title="${esc(f.document)}">${esc(DOC_MAP[f.document].title)}</span>` : '—';
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

// --- DOC TABLE SORT ---
document.querySelectorAll('#view-documents thead th[data-doc-sort]').forEach(th => {
  th.addEventListener('click', () => {
    const col = th.dataset.docSort;
    if (docSortCol === col) docSortAsc = !docSortAsc;
    else { docSortCol = col; docSortAsc = true; }
    document.querySelectorAll('#view-documents thead th .sort-arrow').forEach(s => s.textContent = '');
    th.querySelector('.sort-arrow').textContent = docSortAsc ? ' \u25B2' : ' \u25BC';
    renderDocTable();
  });
});

// --- GENERIC SEARCH CLEAR ---
function toggleSearchClear(inputId) {
  const input = document.getElementById(inputId);
  const btn = input.parentElement.querySelector('.search-clear');
  if (btn) btn.classList.toggle('visible', input.value.length > 0);
}

function clearSearchInput(inputId) {
  const input = document.getElementById(inputId);
  input.value = '';
  input.dispatchEvent(new Event('input', { bubbles: true }));
  input.focus();
}

// --- EVENTS ---
['search','filter-section','filter-verified','filter-source-type','filter-document'].forEach(id => {
  const el = document.getElementById(id);
  el.addEventListener(el.tagName === 'INPUT' ? 'input' : 'change', renderTable);
});
['doc-search','filter-doc-status','filter-doc-type','filter-doc-section'].forEach(id => {
  const el = document.getElementById(id);
  el.addEventListener(el.tagName === 'INPUT' ? 'input' : 'change', renderDocTable);
});

// Toggle clear buttons on all search inputs
['search','doc-search','pane-fact-search'].forEach(id => {
  document.getElementById(id).addEventListener('input', () => toggleSearchClear(id));
});

// --- DATASETS PAGE ---
let dsSortCol = 'id', dsSortAsc = true;

function getFilteredDatasets() {
  const search = document.getElementById('ds-search').value.toLowerCase();
  const section = document.getElementById('filter-ds-section').value;
  const format = document.getElementById('filter-ds-format').value;

  return DATASETS.filter(d => {
    if (section && !(d.sections || []).includes(section)) return false;
    if (format && d.format !== format) return false;
    if (search) {
      const hay = [d.id, d.title, d.description, d.format, d.source_name,
        ...(d.sections || []).map(s => s + ' ' + (SECTION_LABELS[s] || ''))
      ].join(' ').toLowerCase();
      if (!hay.includes(search)) return false;
    }
    return true;
  }).sort((a, b) => {
    let va = a[dsSortCol] ?? '', vb = b[dsSortCol] ?? '';
    if (dsSortCol === 'sections') { va = (a.sections || [])[0] || ''; vb = (b.sections || [])[0] || ''; }
    if (typeof va === 'string') { va = va.toLowerCase(); vb = vb.toLowerCase(); }
    return dsSortAsc ? (va < vb ? -1 : va > vb ? 1 : 0) : (va > vb ? -1 : va < vb ? 1 : 0);
  });
}

function renderDsTable() {
  const dsets = getFilteredDatasets();
  const tbody = document.getElementById('ds-table-body');
  document.getElementById('ds-results-count').textContent = `Showing ${dsets.length} of ${DATASETS.length} datasets`;
  if (dsets.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:40px;color:var(--text-muted)">No datasets match your filters.</td></tr>';
    return;
  }
  tbody.innerHTML = dsets.map(d => {
    const secTags = (d.sections || []).map(s =>
      `<span class="badge badge-section">${esc(SECTION_LABELS[s] || s)}</span>`
    ).join(' ');
    const fmtUpper = (d.format || '').toUpperCase();
    return `<tr style="cursor:pointer" onclick="openDsSlidePane('${esc(d.id)}')">
      <td style="font-family:monospace;font-size:11px;color:var(--accent);white-space:nowrap">${esc(d.id)}</td>
      <td>
        <div style="font-weight:600;font-size:13px">${esc(d.title)}</div>
        <div style="font-size:11px;color:var(--text-muted);margin-top:2px">${esc(truncate(d.description, 80))}</div>
      </td>
      <td><span class="badge" style="background:var(--surface3);color:var(--text)">${esc(fmtUpper)}</span></td>
      <td>${secTags || '<span style="color:var(--text-muted);font-size:11px">\u2014</span>'}</td>
      <td style="text-align:right;font-size:12px">${d._total_rows.toLocaleString()}</td>
      <td style="text-align:right;font-size:12px;color:var(--text-muted)">${d._sample_rows.length}</td>
      <td style="white-space:nowrap;font-size:11px;color:var(--text-muted)">${esc(d.date_added || '')}</td>
    </tr>`;
  }).join('');
}

function openDsSlidePane(dsId) {
  const ds = DS_MAP[dsId];
  if (!ds) return;
  const secTags = (ds.sections || []).map(s =>
    `<span class="badge badge-section">${esc(SECTION_LABELS[s] || s)}</span>`
  ).join(' ');
  const fmtUpper = (ds.format || '').toUpperCase();

  document.getElementById('ds-slide-title').textContent = ds.title;
  document.getElementById('ds-slide-meta').innerHTML = `
    <span class="badge" style="background:var(--surface3);color:var(--text)">${esc(fmtUpper)}</span>
    <span style="color:var(--text-muted)">${esc(ds.id)}</span>
    ${secTags}
  `;
  document.getElementById('ds-slide-desc').textContent = ds.description || '';
  document.getElementById('ds-slide-source').innerHTML = ds.source_name
    ? `Source: ${ds.source_url ? `<a href="${esc(ds.source_url)}" target="_blank" style="color:var(--accent)">${esc(ds.source_name)}</a>` : esc(ds.source_name)}`
    : '';
  document.getElementById('ds-slide-sample-info').textContent =
    `Showing ${ds._sample_rows.length} of ${ds._total_rows.toLocaleString()} rows (random sample) \u00B7 ${ds._column_count} columns`;
  document.getElementById('ds-slide-notes').textContent = ds.notes || '';

  // Build data table
  const thead = document.getElementById('ds-slide-thead');
  const tbody = document.getElementById('ds-slide-tbody');
  thead.innerHTML = '<tr>' + (ds._headers || []).map(h =>
    `<th style="white-space:nowrap">${esc(h)}</th>`
  ).join('') + '</tr>';
  let bodyHtml = (ds._sample_rows || []).map(row =>
    '<tr>' + row.map(cell =>
      `<td style="white-space:nowrap;max-width:300px;overflow:hidden;text-overflow:ellipsis">${esc(String(cell))}</td>`
    ).join('') + '</tr>'
  ).join('');
  if (ds._totals_row) {
    bodyHtml += `<tr><td colspan="${ds._column_count}" style="padding:0;border-bottom:none"><div style="border-top:2px solid var(--border);margin:8px 0"></div></td></tr>`;
    bodyHtml += '<tr style="font-weight:700;background:var(--surface2)">' + ds._totals_row.map(cell =>
      `<td style="white-space:nowrap;max-width:300px;overflow:hidden;text-overflow:ellipsis">${esc(String(cell))}</td>`
    ).join('') + '</tr>';
  }
  tbody.innerHTML = bodyHtml;

  document.getElementById('ds-slide-overlay').classList.add('open');
  document.getElementById('ds-slide-pane').classList.add('open');
}

function closeDsSlidePane() {
  document.getElementById('ds-slide-overlay').classList.remove('open');
  document.getElementById('ds-slide-pane').classList.remove('open');
}

function populateDsFilters() {
  const secSelect = document.getElementById('filter-ds-section');
  for (const [key, label] of Object.entries(SECTION_LABELS)) {
    secSelect.innerHTML += `<option value="${key}">${label}</option>`;
  }
}

// Dataset table sort
document.querySelectorAll('#view-datasets thead th[data-ds-sort]').forEach(th => {
  th.addEventListener('click', () => {
    const col = th.dataset.dsSort;
    if (dsSortCol === col) dsSortAsc = !dsSortAsc;
    else { dsSortCol = col; dsSortAsc = true; }
    document.querySelectorAll('#view-datasets thead th .sort-arrow').forEach(s => s.textContent = '');
    th.querySelector('.sort-arrow').textContent = dsSortAsc ? ' \u25B2' : ' \u25BC';
    renderDsTable();
  });
});

// Dataset filter/search events
['ds-search','filter-ds-section','filter-ds-format'].forEach(id => {
  const el = document.getElementById(id);
  el.addEventListener(el.tagName === 'INPUT' ? 'input' : 'change', renderDsTable);
});
document.getElementById('ds-search').addEventListener('input', () => toggleSearchClear('ds-search'));

// --- CONTEXT PAGE ---
let currentContextIdx = -1;
let contextMode = 'edit';
// Track in-memory edits
const contextEdits = {};

function createContextFile() {
  const name = prompt('Enter filename (e.g. my_notes.md):');
  if (!name) return;
  const filename = name.endsWith('.md') ? name : name + '.md';
  // Check for duplicate
  if (CONTEXT_FILES.some(f => f.filename.toLowerCase() === filename.toLowerCase())) {
    alert('A file named "' + filename + '" already exists.');
    return;
  }
  const newFile = {
    filename: filename,
    title: filename.replace('.md', '').replace(/_/g, ' ').replace(/-/g, ' '),
    content: '',
    size: 0,
  };
  CONTEXT_FILES.push(newFile);
  const newIdx = CONTEXT_FILES.length - 1;
  renderContextFileList();
  openContextFile(newIdx);
  // Mark as edited so download/save are available
  contextEdits[newIdx] = '';
  updateCtxUnsaved();
  // Persist to disk
  fetch('/api/create-context', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({filename: filename, content: ''})
  }).catch(err => console.error('Create context failed:', err));
}

function renderContextFileList() {
  const search = document.getElementById('context-search').value.toLowerCase();
  const container = document.getElementById('context-file-items');
  document.getElementById('nav-context-count').textContent = CONTEXT_FILES.length;

  const filtered = CONTEXT_FILES.filter((f, i) => {
    if (!search) return true;
    return f.filename.toLowerCase().includes(search) ||
           f.title.toLowerCase().includes(search) ||
           (contextEdits[i] !== undefined ? contextEdits[i] : f.content).toLowerCase().includes(search);
  });

  if (filtered.length === 0) {
    container.innerHTML = '<div style="padding:30px 14px;text-align:center;color:var(--text-muted);font-size:13px">' +
      (CONTEXT_FILES.length === 0 ? 'No context files.<br><span style="font-size:11px">Click <b>+ New File</b> above to create one.</span>' : 'No files match your search.') +
      '</div>';
    return;
  }

  container.innerHTML = filtered.map((f, i) => {
    const realIdx = CONTEXT_FILES.indexOf(f);
    const content = contextEdits[realIdx] !== undefined ? contextEdits[realIdx] : f.content;
    const lines = content.split('\n').length;
    const edited = contextEdits[realIdx] !== undefined && contextEdits[realIdx] !== f.content;
    return '<div class="context-file-item' + (realIdx === currentContextIdx ? ' active' : '') +
      '" onclick="openContextFile(' + realIdx + ')">' +
      '<div class="ctx-title">' + esc(f.title) + (edited ? ' <span style="color:var(--orange)">*</span>' : '') + '</div>' +
      '<div class="ctx-meta">' + esc(f.filename) + ' &middot; ' + lines + ' lines</div>' +
      '</div>';
  }).join('');
}

function openContextFile(idx) {
  currentContextIdx = idx;
  const f = CONTEXT_FILES[idx];
  const content = contextEdits[idx] !== undefined ? contextEdits[idx] : f.content;

  document.getElementById('context-toolbar').style.display = 'flex';
  document.getElementById('ctx-filename').textContent = f.filename;
  updateCtxUnsaved();

  const body = document.getElementById('context-editor-body');
  body.innerHTML = '<textarea class="context-textarea" id="ctx-textarea" placeholder="Start writing...">' +
    esc(content) + '</textarea>' +
    '<div class="context-preview" id="ctx-preview"></div>';

  const textarea = document.getElementById('ctx-textarea');
  textarea.addEventListener('input', () => {
    contextEdits[currentContextIdx] = textarea.value;
    updateCtxUnsaved();
    renderContextFileList();
    if (contextMode === 'preview') {
      document.getElementById('ctx-preview').innerHTML = marked.parse(textarea.value);
    }
  });

  // Support tab key in textarea
  textarea.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      textarea.value = textarea.value.substring(0, start) + '  ' + textarea.value.substring(end);
      textarea.selectionStart = textarea.selectionEnd = start + 2;
      textarea.dispatchEvent(new Event('input'));
    }
  });

  setContextMode(contextMode);
  renderContextFileList();
}

function setContextMode(mode) {
  contextMode = mode;
  const textarea = document.getElementById('ctx-textarea');
  const preview = document.getElementById('ctx-preview');
  const editBtn = document.getElementById('ctx-mode-edit');
  const previewBtn = document.getElementById('ctx-mode-preview');
  if (!textarea || !preview) return;

  editBtn.classList.toggle('active', mode === 'edit');
  previewBtn.classList.toggle('active', mode === 'preview');

  if (mode === 'edit') {
    textarea.classList.remove('hidden');
    preview.classList.remove('active');
    textarea.focus();
  } else {
    textarea.classList.add('hidden');
    preview.classList.add('active');
    preview.innerHTML = marked.parse(textarea.value);
  }
}

function updateCtxUnsaved() {
  const el = document.getElementById('ctx-unsaved');
  const saveBtn = document.getElementById('ctx-save-btn');
  if (currentContextIdx < 0) { el.classList.remove('visible'); saveBtn.classList.remove('visible'); return; }
  const f = CONTEXT_FILES[currentContextIdx];
  const edited = contextEdits[currentContextIdx] !== undefined && contextEdits[currentContextIdx] !== f.content;
  el.classList.toggle('visible', edited);
  saveBtn.classList.toggle('visible', edited);
}

function saveContextFile() {
  if (currentContextIdx < 0) return;
  const f = CONTEXT_FILES[currentContextIdx];
  const content = contextEdits[currentContextIdx] !== undefined ? contextEdits[currentContextIdx] : f.content;
  // Update the source-of-truth so unsaved indicator clears
  f.content = content;
  f.size = content.length;
  delete contextEdits[currentContextIdx];
  updateCtxUnsaved();
  renderContextFileList();
  // Persist to disk
  fetch('/api/save-context', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({filename: f.filename, content: content})
  }).catch(err => console.error('Save context failed:', err));
}

function renameContextFile() {
  closeCtxMenu();
  if (currentContextIdx < 0) return;
  const f = CONTEXT_FILES[currentContextIdx];
  const oldName = f.filename;
  const input = prompt('Rename file:', oldName);
  if (!input || input === oldName) return;
  const newName = input.endsWith('.md') ? input : input + '.md';
  if (CONTEXT_FILES.some((cf, i) => i !== currentContextIdx && cf.filename.toLowerCase() === newName.toLowerCase())) {
    alert('A file named "' + newName + '" already exists.');
    return;
  }
  f.filename = newName;
  f.title = newName.replace('.md', '').replace(/_/g, ' ').replace(/-/g, ' ');
  document.getElementById('ctx-filename').textContent = newName;
  renderContextFileList();
  fetch('/api/rename-context', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({old_filename: oldName, new_filename: newName})
  }).catch(err => console.error('Rename context failed:', err));
}

function downloadContextFile() {
  closeCtxMenu();
  if (currentContextIdx < 0) return;
  const f = CONTEXT_FILES[currentContextIdx];
  const content = contextEdits[currentContextIdx] !== undefined ? contextEdits[currentContextIdx] : f.content;
  const blob = new Blob([content], { type: 'text/markdown' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = f.filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function deleteContextFile() {
  closeCtxMenu();
  if (currentContextIdx < 0) return;
  const f = CONTEXT_FILES[currentContextIdx];
  showConfirm(
    'Delete this context file?',
    'This will permanently delete "' + f.filename + '" from the dashboard and from disk.',
    '',
    'Delete', 'btn-danger',
    () => {
      const filename = f.filename;
      CONTEXT_FILES.splice(currentContextIdx, 1);
      delete contextEdits[currentContextIdx];
      currentContextIdx = -1;
      document.getElementById('context-toolbar').style.display = 'none';
      document.getElementById('context-editor-body').innerHTML =
        '<div class="context-empty"><div class="ctx-empty-icon">&#128196;</div>' +
        '<div>Select a file to view or edit</div>' +
        '<div style="font-size:12px">Or click <b>+ New File</b> to create one</div></div>';
      renderContextFileList();
      // Persist to disk
      fetch('/api/delete-context', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({filename: filename})
      }).catch(err => console.error('Delete context failed:', err));
    },
    () => {}
  );
}

function toggleCtxMenu(e) {
  e.stopPropagation();
  const dd = document.getElementById('ctx-dropdown');
  dd.classList.toggle('open');
}

function closeCtxMenu() {
  document.getElementById('ctx-dropdown').classList.remove('open');
}

// Close dropdown when clicking anywhere else
document.addEventListener('click', (e) => {
  const dd = document.getElementById('ctx-dropdown');
  if (dd && !dd.contains(e.target) && e.target.id !== 'ctx-dots-btn') {
    dd.classList.remove('open');
  }
});

document.getElementById('context-search').addEventListener('input', () => {
  toggleSearchClear('context-search');
  renderContextFileList();
});

// --- CLAUDE INSTRUCTIONS EDITOR ---
let claudeMode = 'edit';
let claudeOriginal = CLAUDE_MD_CONTENT;
let claudeEdited = null;

function initClaudeEditor() {
  const textarea = document.getElementById('claude-textarea');
  textarea.value = CLAUDE_MD_CONTENT;
  textarea.addEventListener('input', () => {
    claudeEdited = textarea.value;
    updateClaudeUnsaved();
    if (claudeMode === 'preview') {
      document.getElementById('claude-preview').innerHTML = marked.parse(textarea.value);
    }
  });
  textarea.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      textarea.value = textarea.value.substring(0, start) + '  ' + textarea.value.substring(end);
      textarea.selectionStart = textarea.selectionEnd = start + 2;
      textarea.dispatchEvent(new Event('input'));
    }
  });
  updateClaudeUnsaved();
}

function setClaudeMode(mode) {
  claudeMode = mode;
  const textarea = document.getElementById('claude-textarea');
  const preview = document.getElementById('claude-preview');
  document.getElementById('claude-mode-edit').classList.toggle('active', mode === 'edit');
  document.getElementById('claude-mode-preview').classList.toggle('active', mode === 'preview');
  if (mode === 'edit') {
    textarea.classList.remove('hidden');
    preview.classList.remove('active');
    textarea.focus();
  } else {
    textarea.classList.add('hidden');
    preview.classList.add('active');
    preview.innerHTML = marked.parse(textarea.value);
  }
}

function updateClaudeUnsaved() {
  const el = document.getElementById('claude-unsaved');
  const saveBtn = document.getElementById('claude-save-btn');
  const edited = claudeEdited !== null && claudeEdited !== claudeOriginal;
  el.classList.toggle('visible', edited);
  saveBtn.classList.toggle('visible', edited);
}

function saveClaudeMd() {
  const textarea = document.getElementById('claude-textarea');
  claudeOriginal = textarea.value;
  claudeEdited = null;
  updateClaudeUnsaved();
  // Persist to disk
  fetch('/api/save-claude', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({content: claudeOriginal})
  }).catch(err => console.error('Save CLAUDE.md failed:', err));
}

initClaudeEditor();

// --- INIT ---
initNav();
renderCards();
renderCharts();
populateFilters();
populateDocFilters();
populateDsFilters();
renderTable();
renderDocTable();
renderDsTable();
renderArchive();
renderContextFileList();
document.getElementById('nav-dataset-count').textContent = DATASETS.length;
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

    print("Loading context files...")
    context_files = load_context_files()
    print(f"  {len(context_files)} context files")

    print("Loading datasets...")
    datasets = load_datasets()
    print(f"  {len(datasets)} datasets")

    print("Loading CLAUDE.md...")
    claude_md = load_claude_md()
    print(f"  {len(claude_md)} chars")

    stats = build_stats(facts)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = HTML_TEMPLATE
    html = html.replace("%%FACTS_JSON%%", json.dumps(facts, default=str))
    html = html.replace("%%DOCUMENTS_JSON%%", json.dumps(documents, default=str))
    html = html.replace("%%CONTEXT_FILES_JSON%%", json.dumps(context_files, default=str))
    html = html.replace("%%DATASETS_JSON%%", json.dumps(datasets, default=str))
    html = html.replace("%%CLAUDE_MD_JSON%%", json.dumps(claude_md))
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
