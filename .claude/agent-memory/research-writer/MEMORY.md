# Research Writer Agent Memory

## Project Structure
- Documents go in `Documents/` directory
- Documents index: `Documents/documents_index.yaml`
- Fact database files: `Fact Database/01_macro_context.yaml`, etc.
- Schema: `Fact Database/SCHEMA.md`

## Current State (as of 2026-03-11)
- DOC-001: "Global Critical Minerals Demand Outlook" (01_Macro_Context)
- Facts 01-001 through 01-036 populated in 01_macro_context.yaml
- Next available fact ID for section 01: 01-037
- Next available document ID: DOC-002

## Key Sources & Reliability
- IEA Global Critical Minerals Outlook 2025: Excellent primary source, web pages parseable
- IEA Global Critical Minerals Outlook 2024: Good for 2023 data points
- USGS Mineral Commodity Summaries 2025: PDFs cannot be parsed by WebFetch, but CAN be downloaded with `curl -L -o /tmp/mcs2025_mineral.pdf <url>` and read natively with the Read tool (`pages` parameter). This allows direct verbatim quote extraction and high confidence.
- Geoscience Australia AIMR 2024: Web pages parseable, reliable for Australia-specific data
- Investing News Network: Secondary source, useful for aggregated country-level data, mark as "media" type

## YAML Gotchas
- pyyaml not installed by default; needs `pip3 install --break-system-packages pyyaml`
- Use `>` for multi-line strings in YAML
- Ensure no duplicate IDs before writing

## Minerals Covered in NWMP Scope
Lithium, nickel, cobalt, rare earth elements, copper, manganese, vanadium, iron ore
