# Market Feasibility Dashboard — Documentation

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Project Structure](#project-structure)
4. [Architecture](#architecture)
5. [Fact Database](#fact-database)
6. [Documents Database](#documents-database)
7. [Context Files](#context-files)
8. [Dashboard Features](#dashboard-features)
9. [Build System](#build-system)
10. [Workflows](#workflows)
11. [Data Schema Reference](#data-schema-reference)
12. [Extending the System](#extending-the-system)

---

## Overview

The Market Feasibility Dashboard is a research management tool for the Maven Libera Market Feasibility Study. It tracks every factual claim used in the study, links claims to their original sources for independent verification, and organises research documents across 10 study sections.

**Core purpose:** Ensure every number, statistic, and factual assertion in the feasibility study can be traced back to a primary source and independently verified.

**Key capabilities:**

- Track and verify factual claims with source quotes, URLs, and metadata
- Organise research across 10 feasibility study sections
- Cross-link facts to reference documents
- Search, filter, and sort facts by section, source type, verification status, and document
- Archive and restore facts
- Edit context/reference files directly in the browser
- Generate a fully self-contained offline HTML dashboard

**Tech stack:**

| Layer | Technology |
|-------|-----------|
| Data storage | YAML files (facts) + Markdown files (documents, context) |
| Build tool | Python 3 with PyYAML |
| Frontend | Single-file HTML with vanilla JavaScript and CSS |
| Markdown rendering | marked.js (embedded) |
| External dependencies | PyYAML only |

---

## Quick Start

### Prerequisites

- Python 3.8+
- PyYAML (`pip install pyyaml`)

### Build and open

```bash
cd "Market Feasibility Section"
python build_dashboard.py        # or .venv/bin/python build_dashboard.py
open dashboard.html              # macOS — or just open the file in any browser
```

The build script reads all YAML and Markdown files, injects the data into an HTML template, and writes `dashboard.html`. The output is a single self-contained file — no server required.

### Add a fact

1. Open the relevant YAML file in `Fact Database/` (e.g. `01_macro_context.yaml`)
2. Add a new entry following the schema (see [Data Schema Reference](#data-schema-reference))
3. Rebuild the dashboard

### Add a document

1. Create a `.md` file in `Documents/`
2. Add an entry to `Documents/documents_index.yaml`
3. Reference the document ID in any related facts using the `document` field
4. Rebuild the dashboard

---

## Project Structure

```
Market Feasibility Section/
│
├── build_dashboard.py              # Python build script (generates dashboard.html)
├── dashboard.html                  # Generated output — open in browser
│
├── Fact Database/                  # Core data: one YAML file per study section
│   ├── README.md
│   ├── SCHEMA.md                   # Field definitions and validation rules
│   ├── 01_macro_context.yaml       # Section 01 facts
│   ├── 02_regional_endowment.yaml  # Section 02 facts
│   ├── 03_market_definition.yaml   # Section 03 facts
│   ├── 04_demand_assessment.yaml   # Section 04 facts
│   ├── 05_supply_side.yaml         # Section 05 facts
│   ├── 06_gap_analysis.yaml        # Section 06 facts
│   ├── 07_growth_outlook.yaml      # Section 07 facts
│   ├── 08_pricing.yaml             # Section 08 facts
│   ├── 09_risk_factors.yaml        # Section 09 facts
│   ├── 10_conclusions.yaml         # Section 10 facts
│   └── _cross_section.yaml         # Facts used across multiple sections
│
├── Documents/                      # Research documents and reference sheets
│   ├── README.md
│   ├── documents_index.yaml        # Registry of all documents
│   └── *.md                        # Markdown content files
│
├── Context/                        # Editable context files for research agents
│   └── *.md                        # Background/reference markdown files
│
├── Sections/                       # Section-specific working directories
│   ├── 01_Macro_Context/
│   ├── 02_Regional_Endowment/
│   ├── 03_Market_Definition/
│   ├── 04_Demand_Assessment/
│   ├── 05_Supply_Side/
│   ├── 06_Gap_Analysis/
│   ├── 07_Growth_Outlook/
│   ├── 08_Pricing/
│   ├── 09_Risk_Factors/
│   └── 10_Conclusions/
│
├── Planning/                       # Planning documents
├── Expenditure Data/               # Raw data files
├── Visualisations/                 # Charts and graphs
├── Comparator Centre Research/     # Comparative research
├── New Miner Research Reports/     # Company research reports
├── Sourcing/                       # Source material
└── Other Data/                     # Supplementary data
```

---

## Architecture

### How it works

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Fact Database/  │     │   Documents/     │     │    Context/     │
│   *.yaml files   │     │  index.yaml +   │     │   *.md files    │
│                  │     │   *.md files     │     │                 │
└────────┬─────────┘     └────────┬─────────┘     └────────┬────────┘
         │                        │                         │
         └────────────┬───────────┘─────────────────────────┘
                      │
              ┌───────▼────────┐
              │  Python build  │
              │    script      │
              │ (build_dash..  │
              │   board.py)    │
              └───────┬────────┘
                      │
              ┌───────▼────────┐
              │ dashboard.html │
              │  (self-        │
              │   contained)   │
              └────────────────┘
```

1. **Data layer** — YAML files store structured fact entries; Markdown files store document content and context
2. **Build step** — `build_dashboard.py` reads all data, serialises it as JSON, and injects it into an HTML template containing all CSS and JavaScript
3. **Output** — A single `dashboard.html` file that can be opened directly in any modern browser with no server or internet connection required

### Frontend architecture

The dashboard is a single-page application (SPA) built with vanilla JavaScript:

- **Views** are `<div>` elements toggled via `display: none/block`
- **Navigation** is a fixed 260px sidebar with section links
- **Data** is embedded as JavaScript arrays: `FACTS`, `DOCUMENTS`, `CONTEXT_FILES`, `ARCHIVED`
- **State** uses `localStorage` for interactive changes (fact status, context file edits)
- **Markdown** is rendered client-side using the embedded `marked.js` library

### Data flow

```
YAML/Markdown files
    ↓ (Python build)
JSON embedded in HTML
    ↓ (browser loads)
JavaScript arrays (FACTS, DOCUMENTS, etc.)
    ↓ (user interactions)
localStorage (status changes, edits, archives)
```

**Important:** Changes made in the browser (status toggles, archives) are stored in `localStorage` only. They do not write back to the YAML files. To persist changes permanently, update the YAML files directly and rebuild.

---

## Fact Database

### Purpose

The Fact Database is the core of the system. Every factual claim, statistic, or assertion used in the market feasibility study has an entry here. Each entry links the claim to its original source with enough detail to allow independent verification.

### File organisation

One YAML file per feasibility study section, plus a cross-section file:

| File | Section |
|------|---------|
| `01_macro_context.yaml` | Macro Market Context |
| `02_regional_endowment.yaml` | Regional Resource Endowment |
| `03_market_definition.yaml` | Market Definition & Segmentation |
| `04_demand_assessment.yaml` | Demand Assessment |
| `05_supply_side.yaml` | Supply-Side Analysis |
| `06_gap_analysis.yaml` | Supply-Demand Gap Analysis |
| `07_growth_outlook.yaml` | Growth Outlook |
| `08_pricing.yaml` | Pricing Analysis |
| `09_risk_factors.yaml` | Risk Factors |
| `10_conclusions.yaml` | Conclusions |
| `_cross_section.yaml` | Facts used across multiple sections |

### Fact entry structure

```yaml
- id: "01-001"
  claim: >
    The Australian Government allocated A$566.1 million over 10 years
    from 2024-25 for data, maps and tools for the resources industry.
  source_quotes:
    - >
      A$566.1 million over 10 years from 2024–25 for geoscience data,
      maps and tools for the resources industry.
  source_excerpt: |
    The *Future Made in Australia* agenda includes significant
    investment in critical minerals infrastructure...
  source_name: "Future Made in Australia — Critical Minerals"
  source_author: "Department of Industry, Science and Resources"
  source_url: "https://www.industry.gov.au/..."
  source_type: government_publication
  source_date: "2024"
  source_page: ""
  document: "DOC-001"
  sections_used:
    - "01_Macro_Context"
  verified: false
  verification_notes: ""
  confidence: high
  date_added: "2026-03-09"
  added_by: "agent"
  notes: ""
```

### ID format

- Section facts: `{section_number}-{sequence}` — e.g. `01-001`, `05-012`
- Cross-section facts: `XX-{sequence}` — e.g. `XX-001`
- IDs are never reused. Deleted facts retire their IDs.

### Verification states

Facts progress through three states, managed in the dashboard:

| State | Meaning |
|-------|---------|
| **Unverified** | Fact has been entered but not independently checked |
| **Verified** | Someone has confirmed the source contains the claimed information |
| **Flagged** | Fact has been marked as needing attention (incorrect, outdated, or disputed) |

Facts can also be **archived**, which removes them from the active view but preserves them for reference.

---

## Documents Database

### Purpose

The Documents database organises research documents, reference sheets, and section drafts. Documents are cross-linked to facts, allowing you to see which facts came from or support a given document.

### Structure

- **Registry:** `Documents/documents_index.yaml` — metadata for every document
- **Content:** Individual `.md` files in the `Documents/` directory

### Document index entry

```yaml
- id: "DOC-001"
  title: "Macro Market Context — Data Sources & References"
  type: data_sources
  section: "01_Macro_Context"
  content_file: "macro_context_data_sources.md"
  description: >
    Collated reference sheet for Section 3.1 of the Market Feasibility Study.
  status: draft
  date_created: "2026-03-09"
  last_updated: "2026-03-09"
```

### Document types

| Type | Description |
|------|-------------|
| `section_draft` | Draft text for a feasibility study section |
| `data_sources` | Collated source/reference sheet |
| `research_plan` | Research methodology or execution plan |
| `research_report` | Company or facility research report |
| `source_reference` | External source document summary |

### Document statuses

| Status | Meaning |
|--------|---------|
| `stub` | Placeholder — no substantive content yet |
| `draft` | Work in progress |
| `in_review` | Content complete, under review |
| `complete` | Finalised |

### Linking facts to documents

Set the `document` field on a fact entry to the document's ID:

```yaml
# In a fact YAML file
- id: "01-003"
  document: "DOC-001"    # Links this fact to DOC-001
  # ...
```

In the dashboard, clicking a document opens a split-pane view showing the document content alongside all linked facts.

---

## Context Files

### Purpose

Context files are editable Markdown documents that provide background information for research agents and team members. They live in the `Context/` directory and can be viewed and edited directly in the dashboard.

### Usage

- Drop any `.md` file into `Context/` to make it available in the dashboard
- Files can be edited in the dashboard's built-in editor with live Markdown preview
- Edits are saved to `localStorage` (use the download button to export changes)

### Suggested content

- Research plans and execution guides
- Section structuring guides
- Market feasibility drafts
- Data source references
- Methodology notes

---

## Dashboard Features

### Sidebar navigation

The left sidebar provides access to all views:

- **Overview** — Summary statistics and charts
- **Fact Database** — Full searchable/filterable fact table
- **Documents** — Document registry with slide pane viewer
- **Context** — Editable context files
- **Section views** (01–10) — Filtered fact tables per section
- **Archive** — Archived facts with restore/delete options

### Overview page

Displays summary cards and two charts:

| Card | Shows |
|------|-------|
| Total Facts | Count of all active facts |
| Verified | Count with verified status |
| Unverified | Count still pending verification |

| Chart | Shows |
|-------|-------|
| Facts by Section | Horizontal bar chart — facts per study section |
| Facts by Source Type | Horizontal bar chart — distribution by source type |

### Fact Database view

The main working view for managing facts.

**Search:** Free-text search across fact IDs, claims, source names, and source quotes.

**Filters:**

| Filter | Options |
|--------|---------|
| Section | All sections + "All" |
| Status | Verified / Unverified / Flagged / All |
| Source Type | All source types + "All" |
| Document | All linked documents + "All" |

**Table columns:**

| Column | Content |
|--------|---------|
| ID | Fact identifier (e.g. `01-001`) |
| Status | Coloured badge — green (verified), orange (unverified), red (flagged) |
| Document | Linked document ID |
| Claim | The factual statement |
| Source | Source name (linked to URL) |
| Sections | Which study sections use this fact |
| Date Added | When the fact was entered |

**Row interactions:**

- Click a row to expand it, showing source quotes, source excerpts (rendered as Markdown), verification notes, and full metadata
- Use the status dropdown to change verification state
- Use the archive button to move a fact to the archive

### Documents view

**Table columns:** ID, Title, Type, Section, Status, Linked Facts (count), Last Updated

**Filters:** Status, Type, Section

**Slide pane:** Click any document row to open a split-pane view:

- **Left panel:** Document content rendered as Markdown, with text search
- **Right panel:** All facts linked to this document, with search
- **Text highlighting:** Select text in the document to search for matching facts

### Section views (01–10)

Each section has its own view showing only the facts assigned to that section via `sections_used`. The interface matches the Fact Database view but pre-filtered.

### Archive view

Shows all archived facts with:

- Previous verification status
- Date archived
- Restore button (returns fact to active state)
- Delete button (permanently removes from view)

### Context view

- File list with search
- Built-in Markdown editor with live preview toggle
- Unsaved changes indicator
- Save (to localStorage), download (as .md file), and delete controls

---

## Build System

### Build script: `build_dashboard.py`

The build script is a single Python file (~2,450 lines) that:

1. **Loads facts** — Parses all `*.yaml` files in `Fact Database/`
2. **Loads documents** — Parses `documents_index.yaml` and reads linked `.md` content files
3. **Loads context files** — Reads all `.md` files from `Context/`
4. **Computes statistics** — Aggregates counts by section, source type, and verification status
5. **Generates HTML** — Injects JSON data into an HTML template containing all CSS and JavaScript
6. **Writes output** — Saves the result as `dashboard.html`

### Running the build

```bash
# Using system Python
python build_dashboard.py

# Using a virtual environment
.venv/bin/python build_dashboard.py
```

### Build output

The build prints a summary to the console:

```
Building dashboard...
  Loaded 10 facts from 01_macro_context.yaml
  Loaded 0 facts from 02_regional_endowment.yaml
  ...
  Loaded 10 documents from documents_index.yaml
  Loaded 3 context files
Dashboard written to dashboard.html (142 KB)
```

### Template placeholders

The HTML template uses `%%PLACEHOLDER%%` markers that the build script replaces:

| Placeholder | Replaced with |
|-------------|---------------|
| `%%FACTS_JSON%%` | JSON array of all fact entries |
| `%%DOCUMENTS_JSON%%` | JSON array of all document entries |
| `%%CONTEXT_FILES_JSON%%` | JSON array of context file contents |
| `%%STATS_JSON%%` | JSON object with aggregated statistics |
| `%%SECTION_LABELS_JSON%%` | JSON mapping of section IDs to display names |
| `%%SOURCE_TYPE_LABELS_JSON%%` | JSON mapping of source types to display names |
| `%%BUILD_TIME%%` | ISO timestamp of the build |

---

## Workflows

### Research workflow

```
1. Research a topic
       ↓
2. Identify factual claims to include in the study
       ↓
3. For each claim:
   a. Find the primary source (government report, dataset, etc.)
   b. Copy a verbatim quote from the source
   c. Add an entry to the relevant section YAML file
   d. Link to a document if applicable
       ↓
4. Rebuild the dashboard
       ↓
5. Use the dashboard to review and verify facts
```

### Verification workflow

```
1. Open the dashboard → Fact Database view
       ↓
2. Filter by Status: "Unverified"
       ↓
3. For each unverified fact:
   a. Click the row to expand details
   b. Open the source URL
   c. Search for the verbatim quote in the source
   d. If confirmed: set status to "Verified", add verification notes
   e. If not found: set status to "Flagged", add notes explaining the issue
       ↓
4. Update the YAML file with permanent changes
```

### Adding a new section's facts

```
1. Open the stub YAML file (e.g. 05_supply_side.yaml)
       ↓
2. Replace the empty list with fact entries following the schema
       ↓
3. Create a corresponding document in Documents/ if needed
       ↓
4. Rebuild the dashboard
       ↓
5. Verify facts using the dashboard
```

---

## Data Schema Reference

### Fact fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `id` | Yes | string | Unique ID: `{section}-{seq}`, e.g. `01-001` |
| `claim` | Yes | string | The factual statement as it appears in the report |
| `source_quotes` | Yes | list[string] | Verbatim quotes from the original source |
| `source_name` | Yes | string | Full name of the publication or dataset |
| `source_author` | No | string | Author or publishing organisation |
| `source_url` | Yes | string | Direct URL to the source |
| `source_page` | No | string | Page number, section, or table reference |
| `source_type` | Yes | enum | Source classification (see below) |
| `source_date` | Yes | string | Publication date (`YYYY-MM` or `YYYY-MM-DD`) |
| `source_accessed` | No | string | Date the URL was last confirmed working |
| `source_excerpt` | No | string | Extended excerpt from source (Markdown supported) |
| `sections_used` | Yes | list[string] | Which report sections use this fact |
| `document` | No | string | Linked document ID (e.g. `DOC-001`) |
| `data_table` | No | string | Name of a data table this fact feeds into |
| `verified` | Yes | boolean | Has the source been independently confirmed? |
| `verification_notes` | No | string | Notes from the verification process |
| `confidence` | No | enum | `high`, `medium`, or `low` |
| `date_added` | Yes | string | Entry creation date (`YYYY-MM-DD`) |
| `added_by` | No | string | Who added the entry (name or `agent`) |
| `notes` | No | string | Additional context |

### Source types

| Value | Description |
|-------|-------------|
| `government_publication` | Government report, strategy document, or policy paper |
| `government_data` | Official statistics (ABS, Geoscience Australia, etc.) |
| `international_organisation` | IEA, World Bank, OECD, etc. |
| `academic_paper` | Peer-reviewed journal article |
| `industry_report` | Industry body report (AMEC, AusIMM, etc.) |
| `company_filing` | ASX announcement, annual report, quarterly report |
| `company_website` | Company webpage (not a formal filing) |
| `media` | News article or press release |
| `consultation` | Stakeholder interview or consultation transcript |
| `internal_data` | Our own collected/compiled data |
| `local_file` | Reference to a local file not available online |

### Section identifiers

Use these exact strings in `sections_used`:

| Identifier | Section |
|------------|---------|
| `01_Macro_Context` | Macro Market Context |
| `02_Regional_Endowment` | Regional Resource Endowment |
| `03_Market_Definition` | Market Definition & Segmentation |
| `04_Demand_Assessment` | Demand Assessment |
| `05_Supply_Side` | Supply-Side Analysis |
| `06_Gap_Analysis` | Supply-Demand Gap Analysis |
| `07_Growth_Outlook` | Growth Outlook |
| `08_Pricing` | Pricing Analysis |
| `09_Risk_Factors` | Risk Factors |
| `10_Conclusions` | Conclusions |

### Document index fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `id` | Yes | string | Unique ID: `DOC-{sequence}`, e.g. `DOC-001` |
| `title` | Yes | string | Document title |
| `type` | Yes | enum | `section_draft`, `data_sources`, `research_plan`, `research_report`, `source_reference` |
| `section` | Yes | string | Associated study section identifier |
| `content_file` | Yes | string | Filename of the `.md` content file in `Documents/` |
| `description` | No | string | Brief description of the document |
| `status` | Yes | enum | `stub`, `draft`, `in_review`, `complete` |
| `date_created` | Yes | string | Creation date (`YYYY-MM-DD`) |
| `last_updated` | Yes | string | Last modification date (`YYYY-MM-DD`) |

---

## Extending the System

### Adding facts

Edit the relevant YAML file in `Fact Database/`. Follow the schema, increment the ID sequence, and rebuild.

### Adding documents

1. Write a Markdown file and place it in `Documents/`
2. Add a registry entry to `documents_index.yaml`
3. Reference the document ID from related fact entries
4. Rebuild

### Adding context files

Drop any `.md` file into `Context/`. It will appear in the dashboard's Context view on the next build.

### Adding a new source type

1. Add the new type to `SOURCE_TYPE_LABELS` in `build_dashboard.py`
2. Add it to `SCHEMA.md` for documentation
3. Use it in fact YAML entries
4. Rebuild

### Adding a new document type

1. Add the new type to `DOC_TYPE_LABELS` in `build_dashboard.py`
2. Add it to `Documents/README.md`
3. Use it in `documents_index.yaml` entries
4. Rebuild

### Modifying the dashboard UI

All HTML, CSS, and JavaScript live inside the `HTML_TEMPLATE` string in `build_dashboard.py`. Edit the template and rebuild to see changes.

---

## Appendix: CLI Quick Reference

```bash
# Build the dashboard
python build_dashboard.py

# Find all unverified facts
grep -l "verified: false" "Fact Database"/*.yaml

# Find facts from a specific source
grep -A5 "source_name.*IEA" "Fact Database"/*.yaml

# Find all facts used in a specific section
grep -B10 "01_Macro_Context" "Fact Database"/*.yaml

# Count facts per file
for f in "Fact Database"/*.yaml; do
  echo "$(grep -c '^- id:' "$f") — $(basename "$f")"
done
```
