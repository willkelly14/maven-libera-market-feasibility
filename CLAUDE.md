NEVER delete facts or documents that have previously been added to the dashboard, unless explicitly told
All fact entries must follow `Fact Database/SCHEMA.md` exactly
Use today's date (YYYY-MM-DD) for `date_added` and `source_accessed`
IDs are never reused — check the relevant YAML file for the next available sequence number

## Research Pipeline

When the user asks for research on a topic, launch the **research-lead** agent. It coordinates the full parallel pipeline:

1. **Planning** — breaks topic into 3-5 sub-topics, assigns ID ranges and staging files
2. **Source Discovery** — launches 1 `research-searcher` agent to broadly search the web and produce a structured source catalog
3. **Parallel Research** — launches N `research-writer` agents simultaneously, each receiving relevant sources from the catalog
4. **Assembly** — launches 1 `research-assembler` agent to merge staging files into the main YAML and create a cohesive document
5. **Parallel Validation** — launches N `research-validator` agents simultaneously, each verifying facts and finding alternative sources when originals are inaccessible
6. **Correction** — launches 1 `research-corrector` agent to apply corrections, archive unverifiable facts, update the document, and rebuild the dashboard
7. **Annotation** — launches 1 `research-annotator` agent to add inline fact ID references (e.g., `[01-001]`) after each factual sentence in the document

### Staging directories
- `Fact Database/staging/` — temporary fact, correction, and source catalog YAML files
- `Documents/staging/` — temporary document section files
- `Fact Database/archive.yaml` — permanent archive for facts that could not be verified from any source
- Staging files are cleaned up by the research-corrector at the end of the pipeline

### Agent team
| Agent | File | Role |
|-------|------|------|
| `research-lead` | `.claude/agents/research-lead.md` | Orchestrator — breaks work, launches agents, coordinates phases |
| `research-searcher` | `.claude/agents/research-searcher.md` | Broad source discovery — searches widely, produces source catalog for writers |
| `research-writer` | `.claude/agents/research-writer.md` | Parallel researcher — writes facts + doc section to staging |
| `research-assembler` | `.claude/agents/research-assembler.md` | Merges staging into main YAML + cohesive document |
| `research-validator` | `.claude/agents/research-validator.md` | Parallel validator — checks facts, finds alternative sources, writes corrections |
| `research-corrector` | `.claude/agents/research-corrector.md` | Applies corrections, archives failed facts, updates document, rebuilds dashboard |
| `research-annotator` | `.claude/agents/research-annotator.md` | Adds inline fact ID references to the final document for traceability |

## Rules for all research agents

- Every claim must have at least one verbatim `source_quote` copied directly from the source — do not paraphrase
- `source_url` must be a direct link to the source (not a search engine or aggregator page)
- Prefer primary sources (government data, company filings, peer-reviewed papers) over secondary sources (media, industry commentary), but you can use them if you have verified the information to be correct and the source reputable.
- Set `confidence` honestly: "high" only when the source is authoritative and the quote is unambiguous
- Set `verified` to `false` — verification is done separately by the validation phase
- When adding facts to a section YAML file, read the file first to avoid duplicate claims or IDs
- Link facts to existing documents in `documents_index.yaml` where applicable

## Rules for all validation agents

- For each unverified fact, open `source_url` and confirm the `source_quotes` appear in the source
- If the URL is broken or inaccessible, **search for alternative sources** that confirm the same claim — do not simply mark as failed because the URL didn't work
- If an alternative source confirms the claim, update the fact with the new source details and mark as `corrected`
- Only mark as `failed` if the claim cannot be verified from ANY source after thorough searching
- If verified, set `verified: true` and record confirmation in `verification_notes` (e.g. "Confirmed on p.12, accessed 2026-03-11")
- Flag any fact where the source date is more than 3 years old — note this in `verification_notes`
- When a fact has errors, **fix the errors** (correct the claim, find the right quote, update the URL) — don't just flag them
- Facts marked `failed` will be archived (moved to `Fact Database/archive.yaml`) and removed from the document by the corrector

## Git commit rules for the research pipeline

- The research-lead MUST commit at two checkpoints: after assembly (Phase 4.5) and after final verification (Phase 8.5)
- Commits only proceed AFTER data integrity verification passes — never commit inconsistent data
- If verification fails, the pipeline STOPS immediately
- Commit messages must include: fact count, document title, YAML file, and archived count (if applicable)
- Stage files explicitly by path — never use `git add .` or `git add -A`

If you are a developer agent, read this:
- The dashboard is a single-file HTML output generated by `build_dashboard.py` — all changes must work in that pipeline
- Do not add external dependencies — the dashboard must remain a self-contained HTML file (inline CSS/JS, embedded data)
- After making changes, run `python3 build_dashboard.py` and confirm the output `dashboard.html` opens correctly in a browser
- Preserve backward compatibility with existing YAML data — never change field names or remove fields from the schema without updating all YAML files
- Keep `serve_dashboard.py` API endpoints consistent with the dashboard's frontend expectations
- Read `DOCUMENTATION.md` for full system architecture before making structural changes
