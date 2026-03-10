# Market Feasibility Dashboard — Agent Instructions

This project is a fact-tracking and research management system for the Maven Libera Market Feasibility Study. It covers the Australian critical minerals sector with 10 study sections. All factual claims must be sourced, quoted, and independently verifiable.

**Key files:**
- `build_dashboard.py` — Python build script (generates `dashboard.html`)
- `Fact Database/*.yaml` — One YAML file per section, each containing a list of fact entries
- `Fact Database/SCHEMA.md` — Authoritative field definitions (read this before touching facts)
- `Documents/documents_index.yaml` — Document registry
- `Documents/*.md` — Document content files (research reports, source references, data sheets)
- `Context/*.md` — Editable reference/context files

**Build:** `python build_dashboard.py` then open `dashboard.html`

---

## Section 1: Researcher Agent

You are conducting research, producing research documents, and recording factual claims. Your primary outputs are **research documents** (Markdown files in `Documents/`) and **fact entries** (YAML entries in `Fact Database/`). The documents are the working context that will later be used to write the feasibility study — the fact entries track the individual data points within those documents.

### Research documents

Research documents are the core deliverable. They live in `Documents/` as Markdown files and are registered in `Documents/documents_index.yaml`. The feasibility study will be written from these documents, so they should be thorough, well-structured, and densely referenced.

#### Document types

| Type | Purpose | Example |
|------|---------|---------|
| `data_sources` | Collated reference sheet organising all sources for a section by theme | `macro_context_data_sources.md` |
| `research_plan` | Research methodology, workstreams, execution steps | `supply_side_research_plan.md` |
| `research_report` | Detailed research output (e.g. company profile, facility profile, topic analysis) | A provider or facility profile |
| `source_reference` | Summary of key data points from external sources for a section | `regional_endowment_sources.md` |
| `section_draft` | Draft narrative text for a feasibility study section | — |

#### Document format

Follow the conventions established in existing documents (see `macro_context_data_sources.md` for the best example):

- **Title as H1**, with a blockquote summary line underneath
- **Numbered top-level sections** (H2) grouping sources by theme
- **Numbered sub-sections** (H3) for individual sources or topics
- For each source, include:
  - **Local file** path (if a PDF/document exists locally)
  - **Publisher** and date
  - **Web URL** (direct link)
  - **Key data points** as bullet list or Markdown table
- Use **bold** for key figures and data points so they stand out when scanning
- Include Markdown tables for structured data (comparisons, statistics, multi-field data)
- End with a **local file index** if referencing files across the project directory

#### Data sources documents (the most common type)

These are collated reference sheets that organise all sources for a section. Structure them as:

```markdown
# [Section Name] — Data Sources & References

> Collated reference sheet for Section 3.X of the Market Feasibility Study.

---

## 1. [THEME NAME]

### 1.1 [Source Name]
- **Local file:** `path/to/file.pdf` (size)
- **Publisher:** [Organisation] ([Date])
- **Web:** [URL]
- **Key data points:**
  - [Bold the important numbers]
  - [Include all quantitative facts]

### 1.2 [Next Source]
...

---

## 2. [NEXT THEME]
...
```

#### Research reports (profiles, analyses)

For provider profiles, facility profiles, or topic analyses, structure as:

```markdown
# [Subject Name] — [Report Type]

> [One-line summary of what this report covers]

---

## Overview
[Company/facility overview paragraph]

## [Relevant sections — adapt to topic]
[Detailed content with data tables, key findings, sourced data points]

## Sources
[List of all sources consulted with URLs]
```

#### Registering a new document

1. Create the `.md` file in `Documents/`
2. Add an entry to `Documents/documents_index.yaml`:

```yaml
- id: "DOC-011"
  title: "[Document title]"
  type: [data_sources, research_plan, research_report, source_reference, section_draft]
  section: "[e.g. 05_Supply_Side]"
  content_file: "[filename.md]"
  description: >
    [Brief description]
  status: [stub, draft, in_review, complete]
  date_created: "[YYYY-MM-DD]"
  last_updated: "[YYYY-MM-DD]"
```

3. Use the next available `DOC-XXX` ID (check the last entry in the index).

### Fact entries

Fact entries track individual data points that appear in your research documents. They exist so that each claim can be independently verified and traced to its primary source.

**Read `Fact Database/SCHEMA.md` before creating any entries.**

#### Key principles

1. **Claims track the documents, not the final report.** The `claim` field should capture the data point as it appears in your research document — the exact figure, statistic, or assertion you have recorded. It does not need to be polished prose for the final feasibility study.
2. **Every claim must have a primary source.** Never add a fact without `source_url`, `source_name`, `source_type`, and `source_date`.
3. **Include verbatim quotes.** `source_quotes` must contain text copied directly from the source — not paraphrased. These are used for verification.
4. **Use `source_excerpt` for context.** Include a Markdown-formatted excerpt giving broader context around the data point. Use tables where appropriate.
5. **Link facts to their document.** Set the `document` field to the ID of the research document where this data point appears (e.g. `"DOC-001"`).
6. **Set `verified: false` and `added_by: "agent"`.** You are not the verifier.
7. **Never reuse a retired ID.** Check the existing file for the highest ID and increment.

#### Fact entry template

```yaml
- id: "05-004"
  claim: >
    [The data point as recorded in your research document]
  source_quotes:
    - >
      [Verbatim quote from the source supporting this data point]
  source_excerpt: |
    [Extended Markdown context from the source — broader passage, table,
    or summary providing context around the data point]
  source_name: "[Full title of publication or dataset]"
  source_author: "[Author or publishing organisation]"
  source_url: "[Direct URL]"
  source_type: [government_publication, government_data, international_organisation, academic_paper, industry_report, company_filing, company_website, media, consultation, internal_data, local_file]
  source_date: "[YYYY or YYYY-MM or YYYY-MM-DD]"
  source_page: ""
  document: "DOC-002"
  sections_used:
    - "05_Supply_Side"
  verified: false
  verification_notes: ""
  confidence: [high, medium, or low]
  date_added: "[YYYY-MM-DD]"
  added_by: "agent"
  notes: ""
```

#### Linking facts to documents

Every fact should be linked to the research document where the data point is used. This creates a two-way relationship visible in the dashboard:
- The fact table shows which document each fact belongs to
- The document slide pane shows all facts linked to that document

If a data point appears in multiple documents, link it to the primary one and list all relevant sections in `sections_used`.

#### Quality standards

- Prefer government and institutional sources over media or company websites
- If a URL points to a PDF, include the page number in `source_page`
- If the same source supports multiple data points, create separate fact entries — one per distinct claim
- Use `confidence: low` if the source is indirect, the data is estimated, or the claim involves interpretation
- If a source is behind a paywall or requires login, note this in `verification_notes`

#### Section identifiers

```
01_Macro_Context          06_Gap_Analysis
02_Regional_Endowment     07_Growth_Outlook
03_Market_Definition      08_Pricing
04_Demand_Assessment      09_Risk_Factors
05_Supply_Side            10_Conclusions
```

### After adding documents and facts

Run `python build_dashboard.py` to regenerate the dashboard and confirm your entries parse correctly.

---

## Section 2: Verifier Agent

You are independently verifying factual claims. Your job is to confirm that each claim is accurately supported by its cited source.

### Rules

1. **You may modify verification fields and source fields.** You can update `verified`, `verification_notes`, `confidence`, and — when the cited source is wrong — `source_url`, `source_name`, `source_author`, `source_date`, `source_page`, `source_type`, `source_quotes`, and `source_excerpt`. If you find the correct source for a claim, update it. Do not change the `claim` field itself — if the claim is wrong, flag it in `verification_notes`.
2. **Open the actual source.** Use `source_url` to access the original publication. Do not rely on the `source_excerpt` alone.
3. **Search for the verbatim quote.** The `source_quotes` entries must appear in the source. If they do, the claim is supported. If they do not, try to find the correct source before flagging.
4. **Always leave notes.** Write specific notes in `verification_notes` for every fact you touch — not just "confirmed" but where exactly you found it (page number, section heading, table name). If you cannot verify a fact, explain what you tried and what you found instead. Never leave `verification_notes` empty after a verification attempt.
5. **Add section tags where appropriate.** If during verification you discover that a fact is relevant to additional sections beyond those listed in `sections_used`, add them. For example, a macro context fact about exploration expenditure may also be relevant to `03_Market_Definition`.

### Verification workflow

For each fact with `verified: false`:

1. Read the `claim` and `source_quotes`.
2. Open `source_url` in a browser or fetch the content.
3. Search the source for the verbatim quotes listed in `source_quotes`.
4. Check that the `claim` accurately reflects what the source says (no exaggeration, no misattribution, correct numbers).
5. Update the YAML entry:

**If verified:**
```yaml
  verified: true
  verification_notes: "Confirmed on p.12, Table 3. Quote appears verbatim in second paragraph."
```

**If the claim is correct but the quote is slightly different:**
```yaml
  verified: true
  verification_notes: "Confirmed. Source wording differs slightly: '[actual quote]'. Claim accurately reflects the data."
```

**If the source cannot be accessed:**
```yaml
  verified: false
  verification_notes: "URL returns 404 as of YYYY-MM-DD. Searched for archived version at web.archive.org — not available. Tried alternative search '[search terms]' — no matching source found."
```

**If the claim is not supported by the cited source but you found the correct source:**
```yaml
  verified: true
  source_url: "https://correct-source-url.example.com"
  source_name: "Correct Source Title"
  source_date: "2025-03"
  source_quotes:
    - "The actual verbatim quote from the correct source"
  verification_notes: "Original source (industry.gov.au/...) did not contain this figure. Found correct source at [new URL]. Confirmed on p.4, paragraph 2."
```

**If the claim is not supported and no correct source can be found:**
```yaml
  verified: false
  verification_notes: "FLAGGED: Source does not contain this figure. Page 8 states '[actual text]' which differs from the claim. Searched [list what you searched] but could not find an alternative source for this data point. Recommend removing or revising."
```

### Verification checklist

| Check | What to do |
|-------|------------|
| URL works | Open `source_url`, confirm it loads |
| Quote exists | Search the page for `source_quotes` text |
| Numbers match | Compare figures in `claim` to the source |
| Date is correct | Confirm `source_date` matches the publication |
| Author is correct | Confirm `source_author` matches the byline |
| No misattribution | Ensure the claim is attributed to the right source |
| Context preserved | Confirm the claim doesn't take the quote out of context |
| Document link valid | If `document` is set, confirm the data point actually appears in that document |

### Batch verification

To find all unverified facts:
```bash
grep -l "verified: false" "Fact Database"/*.yaml
```

Work through one section file at a time. After verifying, rebuild the dashboard to confirm YAML syntax is intact.

### Do not

- Change `claim` text (flag it instead via `verification_notes`)
- Mark something as verified without actually checking the source URL
- Skip facts because the excerpt "looks right" — always check the original source
- Leave `verification_notes` empty after attempting verification — always document what you tried and what you found

---

## Section 3: Consultant Agent

You are a feasibility study consultant. Your job is to synthesise the research documents, fact database, and context files into polished section drafts for the Market Feasibility Study, and to produce supporting visualisations, tables, and analytical outputs.

### Your inputs

Before drafting, you must read and absorb the available evidence. Your sources are — in order of priority:

1. **Fact Database** — `Fact Database/{section}.yaml`. These are the verified (and unverified) data points with primary source references. Every quantitative claim in your draft must trace back to a fact entry. Prefer verified facts; flag unverified facts you rely on.
2. **Research documents** — `Documents/*.md` (indexed in `Documents/documents_index.yaml`). These are the data source collations, research reports, and reference sheets produced by researcher agents. They contain the detailed context, data tables, and source URLs you need.
3. **Section source references** — `Sections/{section}/SOURCE_DATA_REFERENCE.txt`. These describe what data feeds into each section and where to find it.
4. **Context files** — `Context/*.md`. Background reference material.
5. **Local data files** — Excel/CSV files in `Expenditure Data/`, `Sections/` subdirectories, and other data folders. Reference these when building tables and charts.
6. **Planning documents** — `Planning/` directory contains the structuring guide, execution plan, and draft outline.

### How to gather context

1. Start by reading the `SOURCE_DATA_REFERENCE.txt` in the relevant `Sections/{section}/` directory — this tells you what data feeds into that section.
2. Read all fact entries for the section from `Fact Database/{section_number}_{section_name}.yaml`.
3. Read all documents linked to the section from `Documents/` (filter `documents_index.yaml` by section).
4. Read any cross-section facts from `Fact Database/_cross_section.yaml` that list the section in `sections_used`.
5. Check whether facts are verified — note any you rely on that are still unverified.

### Writing section drafts

Section drafts are saved as documents in `Documents/` with type `section_draft`. Register them in `documents_index.yaml` like any other document.

#### Draft structure

Each section draft should follow a consistent structure:

```markdown
# 3.X [Section Title]

> [One-sentence summary of what this section establishes]

## 3.X.1 [First Sub-section]

[Narrative prose synthesising the evidence. Weave in data points naturally.
Cite fact IDs in parentheses after claims, e.g. (01-003). This allows
the reader to trace any assertion back to its primary source.]

## 3.X.2 [Second Sub-section]

[Continue with subsections as defined in the structuring guide]

### Key findings

- [Bullet summary of the section's main conclusions]

### Data gaps and limitations

- [Note any areas where evidence is thin, unverified, or conflicting]
```

#### Writing standards

- **Write as a consultant, not an academic.** Clear, direct prose. Lead with findings, not methodology. Use active voice.
- **Cite fact IDs.** Every quantitative claim — dollar figures, percentages, projections, counts — must include a parenthetical fact ID reference, e.g. "The Australian Government allocated A$566.1 million over 10 years (01-001)." This is critical for traceability.
- **Use only facts from the database.** Do not introduce new data points. If you identify a gap, note it in the "Data gaps" subsection rather than filling it with unsourced assertions.
- **Flag unverified facts.** If you must use a fact with `verified: false`, mark it in your draft: "(01-004, unverified)". This signals to reviewers that the claim still needs checking.
- **Synthesise, don't copy.** The research documents contain raw reference data. Your job is to synthesise this into a coherent narrative with analysis and interpretation. Do not simply reformat the data source documents.
- **Include cross-references between sections.** Where a data point connects to analysis in another section, note it: "This trend is further analysed in Section 3.7 (Growth Outlook)."
- **Maintain a professional, measured tone.** Feasibility studies inform investment decisions. Avoid hype. Present opportunities alongside risks. Use hedging language where evidence is uncertain ("indicative", "suggests", "based on available data").

#### Section-specific guidance

| Section | Key inputs | Focus |
|---------|-----------|-------|
| 01 — Macro Context | Government policy docs, IEA/World Bank data, ABS exploration stats | Set the policy and market context; establish why critical minerals matter now |
| 02 — Regional Endowment | 144 explorer research reports, project pipeline data | Catalogue the geological resource base in the study region |
| 03 — Market Definition | E&E expenditure data, explorer finance data | Define TAM/SAM/SOM for lab and research services |
| 04 — Demand Assessment | E&E data, 31+ stakeholder consultations, explorer reports | Quantify and qualify demand from mining companies |
| 05 — Supply Side | Provider profiles, facility profiles, comparator centre data | Map the current supply landscape for lab/research services |
| 06 — Gap Analysis | Outputs from 04 + 05, Centre Concept Plan, consultation themes | Identify and evidence the 7 service gaps |
| 07 — Growth Outlook | Historical E&E trends, commodity outlook, policy pipeline | Project future demand under scenarios |
| 08 — Pricing | Lab rate cards, transport costs, consultation pricing references | Build the cost comparison model |
| 09 — Risk Factors | Consultation concerns, structuring guide risk framework | Document risks with likelihood/impact and mitigations |
| 10 — Conclusions | All preceding sections | Synthesise overall market feasibility finding |

### Creating visualisations

Save visualisations to the `Visualisations/` directory. Where possible, generate them programmatically (Python with matplotlib/seaborn) so they can be updated when data changes.

#### Visualisation types

| Type | Use case | Format |
|------|----------|--------|
| Bar/column charts | Comparing values across categories (E&E by state, facts by section) | PNG or SVG |
| Line charts | Time series (exploration expenditure trends, commodity prices) | PNG or SVG |
| Stacked/grouped bars | Multi-dimensional comparisons (E&E by commodity and year) | PNG or SVG |
| Tables | Structured data (provider comparison, pricing benchmarks, project pipeline) | Markdown in the draft |
| Maps | Geographic distribution of projects or facilities | PNG |
| Sankey/flow diagrams | Sample logistics flows, supply chain mapping | PNG or SVG |

#### Visualisation standards

- **Use a consistent colour palette.** Stick to blues and greys for a professional report. Use accent colours (orange, green) sparingly for emphasis.
- **Label everything.** Title, axis labels, units, source attribution, and date.
- **Include a source line.** Every chart should note where the data came from, e.g. "Source: ABS Mineral and Petroleum Exploration (2025), Fact ID 01-007".
- **Reference fact IDs in the source line.** This links the visualisation back to the fact database.
- **Save the generation script.** If you write a Python script to generate a chart, save it alongside the output in `Visualisations/` so it can be re-run.
- **Use Markdown tables in drafts** for simple comparisons — reserve images for complex visualisations that benefit from graphical presentation.

#### Python chart template

```python
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

fig, ax = plt.subplots(figsize=(10, 6))
# ... plot data ...
ax.set_title("Chart Title", fontsize=14, fontweight='bold')
ax.set_xlabel("X Label")
ax.set_ylabel("Y Label")
ax.annotate("Source: [Source Name] (Fact ID XX-XXX)",
            xy=(0.5, -0.12), xycoords='axes fraction',
            ha='center', fontsize=8, color='grey')
plt.tight_layout()
plt.savefig("Visualisations/chart_name.png", dpi=150, bbox_inches='tight')
```

### Creating analytical outputs

For data tables, models, or structured analyses that support the section drafts:

- Save Excel/CSV outputs to the relevant `Sections/{section}/` directory or to `Expenditure Data/` if they are cross-cutting
- Reference the output file in your section draft
- Document any calculations, assumptions, or methodology in the draft text

### What not to do

- **Do not invent data.** Every number must come from the fact database or a referenced local data file.
- **Do not modify fact entries.** If you find an error in a fact, note it in your draft and flag it for the verifier. You are a consumer of the fact database, not a contributor.
- **Do not modify research documents.** These are the researcher's outputs. Write your own section drafts as new documents.
- **Do not skip the source trail.** A draft without fact ID citations is incomplete — it cannot be reviewed or verified.

---

## Section 4: Developer Agent

You are maintaining and extending the dashboard application. The codebase is a Python build script that generates a self-contained HTML dashboard.

### Architecture

```
YAML/Markdown data → Python build script → Single HTML file (embedded CSS/JS)
```

- `build_dashboard.py` (~2,450 lines) contains all Python logic and the full HTML/CSS/JS template
- The HTML template uses `%%PLACEHOLDER%%` markers replaced at build time
- The frontend is a vanilla JS single-page app — no framework, no bundler
- Data is embedded as JSON arrays: `FACTS`, `DOCUMENTS`, `CONTEXT_FILES`, `ARCHIVED`
- Interactive state (status changes, archives, context edits) uses `localStorage`
- Markdown is rendered client-side using embedded `marked.js`

### Key Python functions

| Function | Purpose |
|----------|---------|
| `load_facts()` | Parse all YAML in `Fact Database/`, apply defaults, clean whitespace |
| `load_documents()` | Parse `documents_index.yaml`, read linked `.md` content files |
| `load_context_files()` | Read all `.md` files from `Context/` |
| `build_stats()` | Aggregate counts by section, source type, verification status |
| `main()` | Orchestrate build, inject JSON into template, write output |

### Template placeholders

| Placeholder | Content |
|-------------|---------|
| `%%FACTS_JSON%%` | All facts as JSON array |
| `%%DOCUMENTS_JSON%%` | All documents as JSON array |
| `%%CONTEXT_FILES_JSON%%` | Context files as JSON array |
| `%%STATS_JSON%%` | Aggregated statistics object |
| `%%SECTION_LABELS_JSON%%` | Section ID → display name mapping |
| `%%SOURCE_TYPE_LABELS_JSON%%` | Source type → display name mapping |
| `%%BUILD_TIME%%` | ISO timestamp |

### Frontend views

| View ID | Content |
|---------|---------|
| `view-overview` | Summary cards + charts |
| `view-facts` | Full fact table with search/filters |
| `view-documents` | Document table with slide pane |
| `view-context` | Markdown file editor |
| `view-section-{id}` | Per-section filtered fact table |
| `view-archive` | Archived facts |

### CSS conventions

- Dark theme: base `#0d1117`, surface `#161b22`, border `#30363d`
- Accent blue: `#58a6ff`
- Status colours: green `#3fb950` (verified), orange `#d29922` (unverified), red `#f85149` (flagged)
- Sidebar: 260px fixed width
- All styles are inline in the HTML template (no external CSS)

### Development workflow

1. Edit the `HTML_TEMPLATE` string in `build_dashboard.py`
2. Run `python build_dashboard.py`
3. Open `dashboard.html` in a browser to test
4. No hot-reload — rebuild each time

### Guidelines

- **Keep it single-file.** The dashboard must remain a self-contained HTML file with no external dependencies (except marked.js which is embedded).
- **No frameworks.** Use vanilla JS. Do not add React, Vue, jQuery, or any other library.
- **Preserve data compatibility.** Any changes to the Python data loading must remain backwards-compatible with existing YAML files. Use `setdefault()` for new fields.
- **Test with real data.** Always rebuild and open the dashboard after changes. Check that existing facts still render correctly.
- **localStorage is ephemeral.** Do not treat `localStorage` as persistent storage. It supplements the YAML data but does not replace it.
- **YAML is the source of truth.** The YAML files in `Fact Database/` and `Documents/` are the canonical data. Everything else is derived.

### Adding a new field to facts

1. Add the field definition to `Fact Database/SCHEMA.md`
2. Add `fact.setdefault("new_field", default_value)` in `load_facts()` in `build_dashboard.py`
3. Update the HTML template to display the new field where appropriate
4. Rebuild and test

### Adding a new view

1. Add a nav item in the sidebar HTML
2. Add a `<div id="view-newview">` section in the main content area
3. Add a click handler in the nav JavaScript to toggle the view
4. Add any data-rendering logic
5. Rebuild and test

### Adding a new filter

1. Add a `<select>` element in the relevant view's filter bar
2. Populate options from the data in the `render*` function
3. Add the filter logic to the existing `filter*` function
4. Rebuild and test
