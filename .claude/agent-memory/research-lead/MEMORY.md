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

## Uncommitted Work Risk (2026-03-12)
- Multiple sessions' work exists only as uncommitted working tree changes
- git checkout -- or git stash on any shared file can destroy other sessions' uncommitted facts
- The committed 01_macro_context.yaml has only 117 facts (DOC-001 to DOC-006)
- Other sessions added DOC-007 through DOC-020 but never committed
- My DOC-021 infrastructure facts (01-692 to 01-749) are appended to the committed+DOC-021 state

## Project State (as of 2026-03-12)
- Committed state: 117 facts in 01_macro_context.yaml, DOC-001 through DOC-006
- My additions: DOC-021 "Infrastructure Constraints" with 58 verified facts (01-692 to 01-749)
- documents_index.yaml has DOC-001 through DOC-021 (DOC-007 to DOC-020 from other uncommitted sessions)
- Next safe fact ID: 01-750 (IDs 01-118 to 01-691 reserved for uncommitted session work)
- Next document ID: DOC-022

## Infrastructure Research Notes (2026-03-12)
- IEA Reliable Supply page: all 6 quotes confirmed verbatim (16yr lead time, ore grades, water stress)
- IEA Exec Summary 2025: all 3 quotes confirmed verbatim (30% copper shortfall, 5% investment, 7% flood risk)
- IEA Overview 2025: both investment quotes confirmed ($500B STEPS, $600B APS)
- WRI water article: all 4 quotes confirmed (16% water stress, 8% arid, 20% by 2050, 65% Atacama)
- White House Lobito fact sheet: all 5 quotes confirmed ($6B, 1300km, 800km, 300k tonnes, 170k tonnes)
- QLD statements parseable and all quotes confirmed (CopperString, rail subsidy, freight investigation)
- Sunwater Julius Dam: location/date/ROL/allocation confirmed; cost comparison NOT on this page
- MIWB FAQ: "approximately twice as much" confirmed on dedicated FAQ page
- QLD NWMP pipeline: all 6 project details confirmed (CopperString, Eva, Saint Elmo, Julia Creek, Mt James, Sybella)
- S&P Global article (17.9yr lead times): behind 403 paywall; confirmed via press release
- Arthur D. Little (desalination costs): behind 403; figures widely cited in Chile mining literature
- TAZARA: original claim was US$1B (Feb 2024); updated to US$1.4B (Sep 2024 deal, confirmed SCMP)
- BHP Cerro Colorado 44% claim: NOT confirmed; corrected to court-ordered cessation + Los Bronces 24% decline
