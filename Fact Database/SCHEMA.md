# Fact Database Schema

## Field Definitions

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `id` | Yes | string | Unique ID: `{section_number}-{sequence}`, e.g. `01-001` |
| `claim` | Yes | string | The fact as stated (or to be stated) in our report. Exact wording. |
| `source_quotes` | Yes | list of strings | Verbatim quote(s) from the original source that support the claim. Must be copy-pasteable for search verification. |
| `source_name` | Yes | string | Full name of the publication, report, or dataset |
| `source_author` | No | string | Author or publishing organisation |
| `source_url` | Yes | string | Direct URL to the source (or local file path if not online) |
| `source_page` | No | string | Page number, section, or table reference within the source |
| `source_type` | Yes | enum | See source types below |
| `source_date` | Yes | string | Publication date (YYYY-MM or YYYY-MM-DD) |
| `source_accessed` | No | string | Date the URL was last accessed and confirmed working |
| `sections_used` | Yes | list of strings | Which report section(s) use this fact |
| `data_table` | No | string | If the fact feeds into a specific data table, name it here |
| `verified` | Yes | boolean | Has someone independently confirmed the source contains this claim? |
| `verification_notes` | No | string | Notes from verification (e.g. "confirmed on p.12", "URL broken, archived at...") |
| `confidence` | No | enum | `high`, `medium`, `low` — confidence in the claim's accuracy |
| `date_added` | Yes | string | Date the entry was created (YYYY-MM-DD) |
| `added_by` | No | string | Who added the entry (human name or "agent") |
| `notes` | No | string | Any additional context |

## Source Types

| Value | Description |
|-------|-------------|
| `government_publication` | Government report, strategy document, or policy paper |
| `government_data` | Official statistics (ABS, Geoscience Australia, etc.) |
| `international_organisation` | IEA, World Bank, OECD, etc. |
| `academic_paper` | Peer-reviewed journal article |
| `industry_report` | Industry body report (AMEC, AusIMM, etc.) |
| `company_filing` | ASX announcement, annual report, quarterly report |
| `company_website` | Company webpage (not a formal filing) |
| `media` | News article, press release |
| `consultation` | Stakeholder interview or consultation transcript |
| `internal_data` | Our own collected/compiled data (e.g. explorerData.csv) |
| `local_file` | Reference to a local file not available online |

## Section Identifiers

Use these exact strings in `sections_used`:

- `01_Macro_Context`
- `02_Regional_Endowment`
- `03_Market_Definition`
- `04_Demand_Assessment`
- `05_Supply_Side`
- `06_Gap_Analysis`
- `07_Growth_Outlook`
- `08_Pricing`
- `09_Risk_Factors`
- `10_Conclusions`

## ID Format

- Section 01 facts: `01-001`, `01-002`, ...
- Cross-section facts: `XX-001`, `XX-002`, ...
- IDs are never reused. If a fact is deleted, its ID is retired.

## Multi-line Quotes

Use YAML block scalars for long quotes:

```yaml
- id: "01-005"
  claim: >
    Australia's Critical Minerals Strategy identifies 31 commodities
    as critical minerals, with nickel added in February 2024.
  source_quotes:
    - >
      The Australian Government has identified 31 minerals as critical
      to the economy, national security, and the clean energy transition.
    - >
      In February 2024, nickel was added to the critical minerals list
      following industry consultation.
  source_name: "Australian Critical Minerals Strategy 2023-2030"
  # ... rest of fields
```
