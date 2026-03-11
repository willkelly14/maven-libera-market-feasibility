# Research Validator Memory

## Source Reliability Patterns

### USGS Mineral Commodity Summaries PDFs
- PDFs at `pubs.usgs.gov/periodicals/mcs2025/` cannot be parsed by WebFetch but CAN be read natively via the Read tool once downloaded
- USGS MCS PDFs are 2-page documents per commodity: page 1 has US data/statistics, page 2 has Events/Trends/Issues + World Production table + World Resources
- Production tables use footnotes extensively (e.g., JORC reserves in footnotes for Australia)
- World totals are often "rounded" values
- Watch for agents citing MCS 2024 quotes but attributing them to MCS 2025 (the edition covering the PREVIOUS year's data)

### IEA Global Critical Minerals Outlook 2025
- Executive summary and overview pages are well-structured HTML, fetchable via WebFetch
- Some quotes may be truncated or slightly reformatted in the WebFetch output
- Multiple facts reference the same 2-3 IEA URLs; batch verification is efficient

### Geoscience Australia AIMR 2024
- Main page (`/aimr2024`) has Minister's Foreword with high-level claims
- Introduction (`/aimr2024/introduction`) has nickel ranking change details
- Resources page (`/aimr2024/australias-identified-mineral-resources`) has detailed tables
- World rankings page (`/aimr2024/world-rankings`) has ranking details
- Individual commodity pages exist (e.g., `/aimr2024/nickel`) but may 404

### Investing News Network
- Articles are frequently updated/revised, changing figures between versions
- WebFetch sometimes returns CSS/JS instead of article body text
- Secondary source reporting on USGS data - always verify against USGS primary

## Common Verification Issues Found (2026-03-11 batch)
1. **Fabricated source_quotes**: Research agents sometimes paraphrase or create quotes from data tables rather than copying verbatim text. Found in 01-008, 01-015, 01-021, 01-025, 01-029.
2. **Wrong edition cited**: 01-007 cited MCS 2025 but quote was from MCS 2024.
3. **Incorrect calculated percentages**: 01-008 claimed 46% market share but actual was 37%; 01-015 claimed 61.3% but actual was 59.5%; 01-021 claimed 18.1% but actual was 15.5%.
4. **Overstated figures from secondary sources**: 01-020 claimed 300kt+ cobalt but USGS shows 290kt.
5. **IEA quotes are generally reliable** when sourced from the correct page.
6. **Geoscience Australia quotes are reliable** but ensure correct sub-page URL.

## Project Structure
- Fact database YAML files in `Fact Database/` directory
- Schema at `Fact Database/SCHEMA.md`
- Section 01 covers Macro Market Context (36 facts as of 2026-03-11)
