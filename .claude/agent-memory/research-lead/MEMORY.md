# Research Lead Agent Memory

## Pipeline Design
- [pipeline_design.md](pipeline_design.md) - Sub-topic splits, batch sizes, ID collision prevention
- [source_reliability.md](source_reliability.md) - Comprehensive source reliability patterns
- [validation_gotchas.md](validation_gotchas.md) - Common validation pitfalls

## Tool Limitations
- The `Skill` tool does NOT work for custom agents defined in `.claude/agents/`
- Workaround: perform research directly using WebSearch/WebFetch, write files inline
- OneDrive: use Python scripts with os.replace(tmpfile, filepath) for reliable YAML writes
- ALWAYS check existing fact IDs immediately before writing -- other sessions may have added facts
- PyYAML default dump sorts fields alphabetically -- must use custom writer to preserve field order

## CRITICAL: yaml.safe_load/dump Corruption (2026-03-12)
- NEVER use yaml.safe_load() followed by yaml.dump() on 01_macro_context.yaml
- yaml.dump rewrites the entire file, destroying formatting AND dropping facts from other documents
- The safe_load/dump cycle lost DOC-007 through DOC-018 facts in one incident
- ALWAYS use text-level operations (cat append, sed, python string replacement) instead
- git checkout -- will restore committed state but LOSES ALL uncommitted work from other sessions

## research_api.py Behaviour (2026-03-13)
- The API ignores the `id` field in add-fact -- it always auto-assigns the next sequential ID
- Do NOT pre-specify IDs in fact JSON; let the API assign them
- source_date MUST be YYYY-MM or YYYY-MM-DD format; plain YYYY fails validation silently
- Batch adding facts via Python subprocess works well; loop over list and call add-fact per item
- The API handles ID collision prevention automatically

## Project State (as of 2026-03-13, updated)
- Committed state: 474 facts in 01_macro_context.yaml, DOC-001 through DOC-014
- DOC-014: "Critical Minerals Investment Landscape & Capital Flows" -- 50 verified facts (01-425 to 01-474)
- DOC-013: "Competing Supply Jurisdictions & Global Diversification Race" -- 47 verified facts (01-378 to 01-424)
- DOC-012: "Recycling, Circular Economy & Secondary Supply" -- 38 verified facts (01-340 to 01-377)
- DOC-011: "NWMP Regional Mineral Endowment Profile" -- 47 verified facts (01-293 to 01-339)
- DOC-010: "Critical Minerals Price Outlook & Investment Cycle" -- 44 verified facts (01-249 to 01-292)
- DOC-009: "AI & Data Centre Infrastructure Mineral Demand" -- 37 verified facts (01-212 to 01-248)
- DOC-008: "Allied Nation Supply Chain Diversification" -- 44 verified facts (01-168 to 01-211)
- Next safe fact ID: 01-475
- Next document ID: DOC-015
- Note: 01-167 was used for a test fact and archived; IDs jump from 01-166 to 01-168

## Source Reliability Notes (2026-03-13, updated)
### New in DOC-008 pipeline:
- ASPI Strategist: excellent for bilateral partnership analysis, freely accessible
- EEAS (EU External Action): good primary source for EU partnerships, freely accessible
- Austrade: good for Australian trade analysis, freely accessible
- Norton Rose Fulbright: good legal analysis of IRA/minerals, freely accessible
- CSEP (India): good for India-Australia partnership analysis, freely accessible
- Japan PM Office (kantei.go.jp): authoritative for Japan bilateral docs, freely accessible
- US Treasury press releases: authoritative for IRA guidance, freely accessible
- Modern Diplomacy: page rendering issues (CSS-only in WebFetch), use alternative sources
- US State Dept (2021-2025.state.gov): some pages showing technical difficulties, use IEA as alternative
- Australian minister.industry.gov.au: tends to timeout on WebFetch, use search result summaries

### Previously documented:
- CFR reports: excellent source, all quotes verifiable, freely accessible
- CSIS analysis: excellent source, detailed and freely accessible
- MWI West Point: good source for defence mineral facts, freely accessible
- The Oregon Group: good for defence/mineral statistics, freely accessible
- Al Jazeera: good for resource nationalism news, freely accessible
- White House/PM.gov.au: authoritative for bilateral agreement details, freely accessible
- East Asia Forum: good for Asia-Pacific analysis, freely accessible
- CEN (Chemical & Engineering News): accessible, but verify exact wording carefully
- Policy Options (IRPP): page rendering issues, CSS-only content in WebFetch
- ScienceDirect abstracts: useful for claims but paywalled for full text
- Discovery Alert: secondary source, should cross-reference

## Infrastructure Research Notes (2026-03-12)
- IEA Reliable Supply page: all 6 quotes confirmed verbatim
- IEA Exec Summary 2025: all 3 quotes confirmed verbatim
- IEA Overview 2025: both investment quotes confirmed
- WRI water article: all 4 quotes confirmed
- White House Lobito fact sheet: all 5 quotes confirmed
- QLD statements parseable and all quotes confirmed
- S&P Global article (17.9yr lead times): behind 403 paywall; confirmed via press release
- Arthur D. Little (desalination costs): behind 403; figures widely cited
- TAZARA: updated to US$1.4B (Sep 2024 deal, confirmed SCMP)
- BHP Cerro Colorado 44% claim: NOT confirmed; corrected to court-ordered cessation

## Pipeline Design Notes (2026-03-13, updated)
- read-staging-facts returns `{filename: [facts]}` format, NOT `{facts: [facts]}`
- For 37-44 fact documents, single-session direct research works well (no agent delegation needed)
- Sub-topic split for bilateral agreements: by partner nation works better than by theme
- Sub-topic split for mineral demand: by mineral type + demand pathway works well
- Validation is fastest when sources were already fetched during research phase
- dashboard.html is gitignored -- don't try to `git add` it
- Silver and rare earth per-GW data centre consumption: NOT publicly quantified at granular level
- Goldman Sachs article body doesn't render via WebFetch (CSS/JS only); verify via secondary sources
- WEF weforum.org/stories/ returns 403 on WebFetch; verify via search result snippets
- Silver Institute pages intermittently return 500; use secondary sources for verification
- BHP bhp.com/news tends to timeout on WebFetch; use corroboration from other articles

## DOC-011 Pipeline Notes (2026-03-13)
- NWMP mineral endowment: sub-topic split by (1) resource estimates, (2) production/operations, (3) national share, (4) pipeline, (5) mineralogy worked well
- 47 facts in single session, all verified -- direct research without agent delegation is efficient for regional profiles
- QLD State Development projects pipeline page: excellent primary source, all project data verified
- Glencore operational changes pages: all closure/smelter data verified, excellent primary source
- Evolution Mining FY25 Ernest Henry fact sheet PDF: all production data verified, excellent primary source
- iQ Industry Queensland: good for Dugald River, George Fisher, Cannington data -- all verified
- Richmond Vanadium website: all JORC data verified
- QEM Limited project page: all vanadium JORC data verified
- Mining Weekly: returns 403 on many articles but search result summaries reliable for cross-verification
- NS Energy Business: good for historical reserve figures, all verified
- Geoscience Australia AIMR 2025 preliminary tables: excellent authoritative source for EDR/reserve data
- South32 Cannington website: returns 403 on WebFetch
- Glencore R&R report 2024 PDF: binary/compressed, not readable via WebFetch
- Chinova Resources website: CSS/JS only rendering but key data confirmed in search results
- George Fisher concentrate grades (10.2% Zn, 5.3% Pb, 71g/t Ag): confirmed but may be concentrate grades not ore grades
- CopperString: original 840km figure confirmed but Powerlink website now shows split delivery (Eastern Link first)

## DOC-010 Pipeline Notes (2026-03-13)
- Price outlook research: sub-topic split by (1) price forecasts, (2) price cycles, (3) AU incentives, (4) intl incentives worked well
- IEA Global Critical Minerals Outlook 2025 exec summary: excellent, all quotes verifiable
- deVere Group nickel forecast: good secondary source, analyst consensus data confirmed
- Mining.com/Cobalt Institute: cobalt demand 222kt/400kt/7% CAGR confirmed, but 11%/4% split NOT in source
- Crux Investor (rare earths): good for NdPr price data, Pentagon pricing floor verified
- Core Consultants Group (tungsten): all tungsten data verified, accessible
- Quest Metals (antimony): all antimony price and production data verified
- Resource Capital Funds: mine count projections verified, but 73% correlation not in their article (from McKinsey)
- RBA Bulletin Oct 2025: excellent primary source for AU critical minerals context
- JPMorgan critical minerals page: all data points verified, excellent primary source
- industry.gov.au pages: WebFetch timeouts, use PwC/ATO mirrors instead
- Sprott.com: returns 403 on WebFetch
- Investing News Network: page structure returns CSS-only for article body; use search snippets
- For price outlook documents, batch adding 40+ facts via Python subprocess loop works well (~2 min)

## DOC-012 Pipeline Notes (2026-03-13)
- Recycling/circular economy: sub-topic split by (1) recycling rates by mineral, (2) projections & investment impact, (3) battery recycling industry, (4) tailings reprocessing, (5) QLD policy worked well
- 38 facts in single session, all verified -- direct research continues to be efficient
- IEA Recycling of Critical Minerals exec summary: excellent, nearly all quotes confirmed verbatim
- IEA news page (policy momentum): confirmed 70%+ China market share but NOT 80% (exec summary uses different figure)
- EUR-Lex summary page: gives less precise targets than the IEA policy page -- use IEA for EU Battery Regulation
- Battery Council International: 99% recycling rate confirmed but detailed stats (160M batteries, 80% recycled content) need BCI press release not just the news page
- QLD Circular Economy Research Alliance: department page reports $5.5M, UQ SMI reports $8M -- discrepancy documented in fact
- QLD NWMP Tailings Audit PDF: binary/not readable via WebFetch, but is authoritative government source
- Cobalt Blue MOU: confirmed on Mount Isa City Council website (December 9, 2024), good primary source
- QLD ministerial statements (statements.qld.gov.au): excellent primary source, all quotes confirmed verbatim
- CSIRO battery recycling page: all key stats confirmed; the $603M-$3.1B figure is on a different CSIRO page (2021 article)
- recovery-worldwide.com: zinc 30% claim NOT found on the cited page -- had to find alternative source (galvanizeit.org)
- ScienceDirect vanadium paper: paywalled, 44% EU recycling rate widely cited but couldn't verify directly
- McKinsey REE recycling article: timed out on WebFetch, verified via secondary sources and search snippets
- Python boolean gotcha: `false` in JSON dict literal is invalid Python -- must use `False`

## DOC-013 Pipeline Notes (2026-03-13)
- Competing supply jurisdictions: sub-topic split by (1) global overview/IEA data, (2) Canada, (3) Indonesia, (4) Chile/Argentina, (5) Saudi Arabia/Morocco, (6) DRC/Zambia, (7) India, (8) EU/Central Asia, (9) Australia competitive position
- 47 facts in single session, all verified -- direct research most efficient for multi-jurisdiction survey
- IEA Global Critical Minerals Outlook 2025 exec summary: excellent primary source, ALL 10+ quotes confirmed verbatim
- IEA news/policy pages: also excellent, all quotes verbatim
- Canada.ca government pages: excellent, all facts confirmed; Budget 2025 chapter page has authoritative sovereign fund data
- Breakbulk (Indonesia nickel article): excellent, all 6 data points confirmed verbatim
- Argus Media: 862,000 t/yr HPAL confirmed but Pomalaa detail comes from Mining Technology/Indonesia Miner
- CNBC: returns CSS-only on WebFetch (paywall), use secondary sources for Saudi Arabia
- SWP Berlin (Saudi Arabia analysis): returned 403 on WebFetch, but data widely confirmed across multiple sources
- PwC Aussie Mine 2025: excellent, all 7 claims confirmed on press release page
- Allens (critical minerals 2026 article): excellent, all government support figures confirmed
- Buenos Aires Herald: rendering issues but key Argentina lithium data confirmed via search snippets
- New America (DRC cobalt): excellent, all 5 claims confirmed verbatim
- Eurasianet (Central Asia): returned 403 on WebFetch, data confirmed via search result summaries
- resourcegovernance.org (NRGI Saudi Arabia): returned 403 on WebFetch
- For multi-jurisdiction surveys, doing all research in a single session without sub-agent delegation is most efficient

## DOC-014 Pipeline Notes (2026-03-13)
- Investment landscape/capital flows: no sub-topic split needed, single session with 50 facts covering 7 themes
- DFC press releases: excellent primary source, all amounts confirmed verbatim
- FTI Consulting playbook article: excellent, all 8+ data points confirmed verbatim
- EIB press releases: excellent, all amounts and quotes confirmed
- ASPI Strategist financing frameworks article: excellent, all 5+ quotes confirmed verbatim
- Norton Rose Fulbright private capital article: all quotes confirmed, excellent for PE structural analysis
- Columbia CGEP thematic bonds: PDF body not renderable via WebFetch, but key figures ($15B, 0.3%) confirmed via search
- HSF offtake agreements article: returns 403 on WebFetch, but bankability quotes widely confirmed across search results
- S&P Global PE mining articles: behind 403 paywall, confirmed via search result snippets and secondary coverage
- Export Finance Australia pages: all amounts confirmed, excellent primary source
- NAIF project pages: all amounts confirmed, detailed project data available
- Mining.com/RBC coverage: excellent for Canada capital gap analysis, all data confirmed
- SFA Oxford ESG article: CSS-only rendering, ICMA Green Enabling Projects claim verified via ISS Corporate instead
- PIIE bankability article: returns 403 on WebFetch
- Mining SEE articles: good for sovereign wealth fund analysis, confirmed quotes
- source_quotes list must not be empty -- API rejects facts with empty source_quotes array
