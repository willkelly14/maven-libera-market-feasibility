# Research Lead Agent Memory

## Pipeline Design
- Split topics into 3-5 independent sub-topics for parallel research
- Give each researcher a wide ID range (50 IDs) to prevent collisions
- Assembler re-numbers sequentially after all researchers complete
- Split validation batches at 8-12 facts each for parallel validators
- Macro overview facts (cross-cutting IEA data) should be a separate batch, placed first in sequence

## Tool Limitations (2026-03-11)
- The `Skill` tool does NOT work for custom agents defined in `.claude/agents/`
- Sub-agent orchestration via Skill("research-writer") fails with "Unknown skill" error
- Workaround: perform research directly using WebSearch/WebFetch, write files inline
- This means the "parallel agent" architecture is aspirational; actual work is sequential

## OneDrive Sync Issue (2026-03-11)
- Files written via the `Write` tool may not persist on OneDrive-synced folders
- Workaround: use `bash cat > file << 'EOF'` for critical files, verify with `ls` after writing
- CRITICAL: Heredoc writes to staging dirs also fail intermittently -- skip staging files entirely
- Best approach: write final content directly to target files using Python scripts
- ALWAYS check existing fact IDs before choosing new ID range -- other sessions may have added facts

## ID Collision Prevention (2026-03-11)
- ALWAYS read the FULL YAML file and check ALL existing IDs before assigning new ones
- The documents_index.yaml may have been updated by other sessions between reads
- DOC-006 was added by another session while this pipeline was running, with facts 01-046 to 01-080
- Had to renumber entire batch from 01-046..01-082 to 01-081..01-117 mid-pipeline

## Regex Replacement Pitfall (2026-03-11)
- When replacing IDs in documents, if old range overlaps with new range, double-replacement occurs
- Example: 01-046->01-081, then 01-081->01-116 (wrong!)
- Solution: replace in reverse order (highest first) or use a two-pass approach with temp placeholders

## Source Reliability Patterns
- **IEA pages (iea.org/reports)**: Highly parseable, verbatim quotes extractable. Best source.
- **IEA commentaries**: Parseable, excellent for REE export control data
- **Geoscience Australia (ga.gov.au/aimr)**: Excellent, parseable, all figures confirmed. Best for exploration data.
- **Geoscience Australia exploration statistics**: Parseable, confirmed all 2024 data
- **ABS website (abs.gov.au)**: Chart data renders as JSON config, NOT parseable. Use GA or media secondary sources.
- **Queensland ministerial statements (statements.qld.gov.au)**: Parseable, verbatim quotes confirmed
- **Queensland dept pages (nrmmrrd.qld.gov.au)**: Parseable, policy details confirmed
- **Business Queensland**: Parseable, CEI details confirmed
- **Mining.com.au**: Parseable, ABS data analysis articles well-sourced
- **Mining Weekly (miningweekly.com)**: Behind 403 paywall; use alternative sources
- **BDO (bdo.com.au)**: Behind 403 paywall
- **Discovery Alert**: Behind 403 paywall
- **AMEC (amec.org.au)**: Parseable, JMEI data confirmed
- **Process Online**: Parseable, CopperString data confirmed
- **QLD Statedevelopment pipeline page**: Parseable, all project data confirmed
- **USGS MCS PDFs**: not parseable by WebFetch
- **S&P Global press releases**: accessible via press.spglobal.com
- **Silver Institute**: WordPress CSS/JS only
- **Market research firms (Mordor, Grand View, R&M)**: use GlobeNewsWire press releases
- **Statista / ScienceDirect**: behind paywall
- **NRCan (natural-resources.canada.ca)**: Parseable, CanmetMINING pages confirmed
- **Innovation.ca (navigator.innovation.ca)**: Parseable, facility details confirmed
- **GTK Finland (gtk.fi)**: Excellent, parseable, all Mintec data confirmed
- **Finnish Government (valtioneuvosto.fi)**: Parseable, minister quotes confirmed
- **NETL (netl.doe.gov)**: Parseable, METALLIC program details confirmed
- **DOE (energy.gov)**: Parseable, CMI hub data confirmed
- **Ames Lab (ameslab.gov)**: Parseable, CMI partnership details confirmed
- **Mintek (mintek.co.za)**: Parseable, history/mandate/objectives confirmed
- **SGS (sgs.com)**: Behind 403 paywall; use mining.com coverage instead
- **BNamericas (bnamericas.com)**: JS-rendered, often not parseable
- **WIPO Magazine (wipo.int)**: JS-rendered, not parseable; claims confirmed via search metadata
- **SRC (src.sk.ca)**: Parseable, REE facility data confirmed
- **Saskatchewan.ca**: Parseable, government news releases confirmed
- **DevDiscourse**: Parseable, Chile geoscience ROI data confirmed

## Validation Gotchas
- IEA cobalt recycling: "20% for cobalt" not "over 20%" -- exact wording matters
- IEA STEPS quotes: some on exec summary, others on overview page -- check both URLs
- WGC gold central banks: 863t described as "falling short of 1,000t" not "reaching upper end"
- GlobeNewsWire press releases: contain market size but NOT all application details
- IEA geothermal/molybdenum claim: in search results but not confirmed on fetched pages

## Project State
- DOC-001: "Global Critical Minerals Demand Outlook" (01_Macro_Context) -- COMPLETE, 45 facts (01-001 to 01-045)
- DOC-002: "Exploration and Mining Investment Trends" (07_Growth_Outlook) -- COMPLETE, 35 facts all verified
- DOC-003: "Australian & Queensland Policy Alignment Analysis" (04_Demand_Assessment) -- COMPLETE, 37 facts all verified
- DOC-004: "Peer Nation Infrastructure Benchmarking" (07_Growth_Outlook) -- COMPLETE, 28 facts all verified
- DOC-005: "Energy Transition & Supply Chain Context" (01_Macro_Context) -- COMPLETE, 37 facts all verified (01-081 to 01-117)
- DOC-006: "Australian Testing & Research Infrastructure Audit" (01_Macro_Context) -- COMPLETE, 35 facts all verified (01-046 to 01-080)
- Facts 01-001 through 01-117 in 01_macro_context.yaml (01-046 to 01-080 = DOC-006)
- Facts 04-001 through 04-010, 04-050 through 04-060, 04-100 through 04-108, 04-150 through 04-156 in 04_policy_alignment.yaml
- Facts 07-001 through 07-035 in 07_growth_outlook.yaml
- Next available fact ID: 01-118 (section 01), 04-157 (section 04), 07-064 (section 07)
- Next available document ID: DOC-007

## Sub-topic Split That Worked Well (Confirmed)
- Macro overview + Copper | Zinc + Lead + Silver | Cobalt + Vanadium | REE + Molybdenum | Phosphate + Gold
- Good independence, minimal overlap; each batch produced 7-12 facts
- Policy alignment: Federal strategy | QLD strategy | Funding programs (CMFG+NAIF) | CRC + synthesis
- 4 sub-topics, 37 facts total, all verified

## Energy Transition Sub-topic Split (Confirmed)
- Battery/EVs | Grid/Renewables | Geopolitical risks | Western sovereign response
- 4 sub-topics, 37 facts total (10+10+10+7), all verified
- IEA sources dominated (33/37 facts), with 3 media and 1 industry report
- IRENA direct pages return 403; use search result snippets for capacity stats

## Infrastructure Audit Sub-topic Split (Confirmed)
- ANSTO/Synchrotron/R&D Hub | CSIRO/UQ SMI/JKTech | QRCUF/QLD regional | WA facilities + gap analysis
- 4 sub-topics, 35 facts total, all verified
- Source reliability: ANSTO pages highly parseable, CSIRO pages mostly parseable (some 404s on old unit pages), QLD ministerial statements excellent, Curtin/Murdoch university pages reliable
- Mining Technology (mining-technology.com): article content truncated during fetch, figures not independently verifiable
- CSIRO "rising stars" article: only confirmed ~100 researchers, not 300 employees -- be careful with search result summaries vs actual page content
- Adelaide ISER page: "only centre of its kind" claim NOT found despite appearing in search results -- always verify claims against actual fetched content
- African Security Analysis (DRC cobalt): partial content only, use INN for quota data
- CSIS: good for FORGE/MSP data, exact count is "55 delegations" not "54 countries"

## Policy Research Notes
- gov.au pages (industry.gov.au, minister.industry.gov.au) frequently timeout on WebFetch
- IEA policy database mirrors Australian strategy content well -- use as primary source
- ATO pages parseable for CMPTI details
- NAIF homepage parseable, all stats confirmed
- EFA criticalminerals page parseable
- CMCI CRC website is Wix-based, renders as JS only -- use InnovationAus or media coverage
- QLD ministerial statements parseable and reliable for verbatim quotes
- PyYAML default dump sorts fields alphabetically -- must use custom writer to preserve field order
- When batch-updating verified status, use Python script rather than manual edits
