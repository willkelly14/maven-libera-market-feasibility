# Fact Database — Market Feasibility Section

Every factual claim used in the market feasibility study is tracked here so it can be independently verified.

## Structure

One YAML file per section:

```
Fact Database/
├── README.md                          ← this file
├── SCHEMA.md                          ← field definitions and usage guide
├── 01_macro_context.yaml
├── 02_regional_endowment.yaml
├── 03_market_definition.yaml
├── 04_demand_assessment.yaml
├── 05_supply_side.yaml
├── 06_gap_analysis.yaml
├── 07_growth_outlook.yaml
├── 08_pricing.yaml
├── 09_risk_factors.yaml
├── 10_conclusions.yaml
└── _cross_section.yaml                ← facts used across multiple sections
```

## Quick Reference

Each fact entry has this structure:

```yaml
- id: "01-001"
  claim: "The exact quote or paraphrase as it appears in our report"
  source_quotes:
    - "Verbatim quote from the original source"
    - "Additional supporting quote if needed"
  source_name: "Australian Critical Minerals Strategy 2023-2030"
  source_url: "https://www.industry.gov.au/publications/critical-minerals-strategy-2023-2030"
  source_type: government_publication  # See SCHEMA.md for types
  source_date: "2023-06"
  sections_used:
    - "01_Macro_Context"
  verified: false
  verification_notes: ""
  date_added: "2026-03-09"
```

## Verification Workflow

1. **Add fact** — when writing or reviewing a section, add each factual claim
2. **Source it** — include the URL and a verbatim quote from the source
3. **Verify** — someone opens the source URL, confirms the quote exists, marks `verified: true`
4. **Review** — filter for `verified: false` to find unverified claims

## Searching

Find all unverified facts:
```bash
grep -l "verified: false" Fact\ Database/*.yaml
```

Find all facts from a specific source:
```bash
grep -A5 "source_name.*IEA" Fact\ Database/*.yaml
```

Find all facts used in a specific section:
```bash
grep -B10 "01_Macro_Context" Fact\ Database/*.yaml
```
