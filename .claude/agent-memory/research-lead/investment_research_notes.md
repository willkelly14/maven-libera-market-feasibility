---
name: Investment Research Notes
description: Source reliability and validation notes from DOC-014 Critical Minerals Investment Landscape research
type: project
---

## Source Reliability (Investment Topics)
- **DFC (dfc.gov)**: Parseable, press releases confirmed. Individual partner contribution amounts NOT specified in CMC press release (only total $1.8B confirmed)
- **FTI Consulting**: Excellent, fully parseable. US government critical minerals playbook data all confirmed verbatim (OSC $4.5B, DFC $205B ceiling, China $57B benchmark)
- **ASPI Strategist**: Excellent for financing framework analysis, all 4 midstream/bankability quotes confirmed verbatim
- **NAIF (naif.gov.au)**: Parseable, portfolio totals confirmed ($4.4B not $4.3B, 32 projects, $500M critical minerals allocation)
- **EFA (exportfinance.gov.au)**: Parseable, Critical Minerals Facility $4B and individual project amounts confirmed
- **Columbia CGEP (energypolicy.columbia.edu)**: Commentary page HTML truncated on fetch; thematic bond figures ($15B, 0.3%) confirmed via search results
- **Mining SEE (miningsee.eu)**: Parseable, policy-bankability analysis confirmed but claims spread across multiple sentences
- **JBIC (jbic.go.jp)**: Parseable, MOU details confirmed verbatim
- **PR Newswire**: Parseable, ADQ-Orion JV details confirmed
- **National Observer (nationalobserver.com)**: Behind 403 paywall; use BNN Bloomberg for Canada fund data
- **The Market Bull**: Parseable, Arafura financing breakdown confirmed -- note $495M from CMF (not $500M)
- **PwC Mine 2025 report**: Full PDF not fetchable; use Oregon Group summary for headline figures ($689B revenue, $193B EBITDA)
- **UNEP press releases**: Returned 403 on direct fetch; $450B/$800B figures confirmed via search results

## ID Collision Severity (DOC-014 session)
- DOC-013 was added by another session after initial planning, causing facts 01-371 to 01-414 to be occupied
- DOC-015 was also added by another session during this pipeline, further extending the collision risk
- Had to renumber 38 facts from 01-371..01-408 to 01-415..01-452
- Additionally found 3 facts with duplicate IDs that needed manual resolution (01-378, 01-393, 01-403)
- Two existing facts (01-409, 01-410) had duplicate IDs from the parallel session and were renumbered to 01-453, 01-454
- LESSON: Read the YAML file AND documents_index.yaml immediately before writing facts, not during planning
