# Supply-Side Research Plan

## Overview

This plan covers 4 desk research workstreams to fill gaps in Section 3.5 (Supply-Side Analysis) and Section 3.8 (Pricing). These are independent of the 144 company research reports and can run in parallel.

## Gap Summary

| # | Gap | Feeds Into | Priority |
|---|-----|-----------|----------|
| 1 | Commercial lab provider profiles | Section 3.5 provider comparison, Section 3.6 gap evidence | High |
| 2 | University/government facility profiles | Section 3.5 facility profiles, Section 3.7 JKTech opportunity | High |
| 3 | Lab service pricing benchmarks | Section 3.8 pricing table, Figure 11 cost comparison | Medium |
| 4 | Transport & logistics cost data | Section 3.8 total cost comparison, Section 3.5 transport barriers | Medium |

---

## Workstream A: Commercial Lab Provider Profiles

### Scope
Profile the 5 major commercial lab providers serving the Australian mining sector.

### Providers
1. **ALS Limited** — largest global lab network, known Mt Isa collection point
2. **Bureau Veritas Minerals** — major assay and met testwork provider
3. **SGS Australia** — assay, met testwork, environmental
4. **Intertek Minerals** — assay and geochemistry
5. **Core Resources** (Brisbane) — specialist met testwork and pilot plant

### Data to collect per provider

| Field | Description |
|-------|------------|
| Company overview | Parent company, ownership, scale of Australian operations |
| Services offered | Assay/sample prep, met testwork, environmental, pilot processing, characterisation — tick each |
| Australian lab locations | City/town, state — list all labs |
| NQ/NWMP presence | Any labs, collection points, or offices in North Queensland or Mt Isa region |
| Mt Isa operations | Specific: what does the ALS Mt Isa point actually do? Sample collection only, or on-site prep? |
| Capacity information | Any public statements about capacity, turnaround times, backlogs |
| General pricing tier | If publicly available — otherwise mark "Pricing on request" |
| Key clients (if disclosed) | Any named mining company clients in NQ/NWMP |

### Execution
- **5 parallel agents** — one per provider
- Each agent searches the provider's Australian website, LinkedIn page, ASX filings (ALS is listed), and industry publications
- Output: `{PROVIDER_NAME}_Profile.md` saved to `Market Feasibility Section/Sections/05_Supply_Side/Provider_Profiles/`

### Search strategy per agent
- `"{provider name}" Australia minerals laboratory services`
- `"{provider name}" site:.com.au laboratory locations`
- `"{provider name}" Mount Isa OR "North Queensland" mining`
- `"{provider name}" metallurgical testwork Australia`
- For ALS: `"ALS" site:asx.com.au annual report` (ALS is ASX-listed as ALQ)

---

## Workstream B: University/Government Research Facility Profiles

### Scope
Profile 4 key non-commercial facilities that provide mineral processing research services.

### Facilities
1. **UQ Sustainable Minerals Institute (SMI) / JKTech** — Indooroopilly, QLD
2. **CSIRO Mineral Processing** — Brisbane and Perth facilities
3. **Townsville QRCUF** (Queensland Resources Common User Facility)
4. **ANSTO** (Australian Nuclear Science and Technology Organisation) — Lucas Heights, NSW

### Data to collect per facility

| Field | Description |
|-------|------------|
| Facility overview | Host institution, location, year established |
| Services offered | Which of the 7 MICMRC service types they cover |
| Commercial availability | Do they accept commercial work from mining companies? Pricing model? |
| Current capacity | Staff numbers, throughput indicators, utilisation if known |
| Operational status (2026) | Active, relocating, expanding, at capacity |
| JKTech-specific | Indooroopilly relocation status as of 2025-2026 — confirmed? Timeline? New location? |
| QRCUF-specific | Current utilisation, services actually operational vs planned |
| Relevance to MICMRC | Competitive overlap or potential collaboration partner |

### Execution
- **4 parallel agents** — one per facility
- Output: `{FACILITY_NAME}_Profile.md` saved to `Market Feasibility Section/Sections/05_Supply_Side/Facility_Profiles/`

### Search strategy per agent
- `"{facility name}" mineral processing services commercial`
- `"JKTech" OR "JK Mineral Research Centre" relocation 2025 2026`
- `"QRCUF" Townsville services operational`
- `"CSIRO" mineral processing Brisbane Perth mining`
- `"ANSTO" minerals characterisation mining services`

---

## Workstream C: Lab Service Pricing Benchmarks

### Scope
Collect indicative pricing for 5 key service categories to support Section 3.8 pricing analysis.

### Service categories and target data

| Service Type | Unit | Target Data |
|-------------|------|------------|
| Routine multi-element assay (ICP-OES/MS) | A$ per sample | Published rate card or industry benchmark |
| Metallurgical testwork program (flotation/leaching) | A$ per program or per day | Industry estimates, published quotes |
| Environmental water/soil analysis | A$ per sample | Published rate card or industry benchmark |
| Pilot-scale processing campaign | A$ per campaign | Industry estimates, typically $100K–$500K range |
| Ore characterisation / drop-weight testing | A$ per program | Industry estimates |

### Sources to search
1. ALS, SGS, Bureau Veritas websites for published rate cards or price lists
2. Industry benchmarking reports (e.g., from AusIMM, AMIRA)
3. Government grant programs that list indicative lab costs (e.g., CRC bid documents)
4. Academic papers that cite lab costs as part of methodology
5. Interview evidence — KGL cited $600–1K/day for technical staff visits

### Execution
- **1 agent** (pricing data is sparse and interlinked — better handled by one comprehensive search)
- Agent searches broadly, then compiles findings into a single benchmark table
- Output: `Pricing_Benchmarks.md` saved to `Market Feasibility Section/Sections/05_Supply_Side/`

### Expected outcome
- Lab pricing is often confidential (provided on request). Expect:
  - Routine assays: likely findable (some labs publish)
  - Met testwork: likely ranges only from industry publications
  - Pilot processing: order-of-magnitude only
  - Environmental: likely findable (regulatory context means some transparency)
  - Characterisation: sparse
- Flag all entries as `Published`, `Industry Estimate`, or `Not Publicly Available`

---

## Workstream D: Transport & Logistics Cost Data

### Scope
Collect transport cost data to support Section 3.8 total cost comparison between using the Centre vs interstate labs.

### Data to collect

| Data Point | Unit | Sources |
|-----------|------|---------|
| Freight cost: Mount Isa → Brisbane (road) | A$ per kg | Toll, TNT, StarTrack websites |
| Freight cost: Mount Isa → Brisbane (air) | A$ per kg | Qantas Freight, Rex |
| Freight cost: Mount Isa → Perth (road) | A$ per kg | Toll, TNT |
| Freight cost: Mount Isa → Perth (air) | A$ per kg | Qantas Freight |
| Typical sample shipment weight | kg per batch | Industry standard (typically 5–50kg for assays, 200kg+ for met testwork) |
| Lab turnaround times (interstate) | business days | ALS, SGS, Bureau Veritas published turnaround pages |
| Accommodation cost: Mount Isa | A$ per night | Hotels/motels in Mt Isa (for FIFO technical staff) |
| FIFO all-in daily cost | A$ per day | Interview evidence (KGL: $600–1K/day) |

### Execution
- **1 agent** — searches freight and logistics providers, then compiles comparison table
- Output: `Transport_Costs.md` saved to `Market Feasibility Section/Sections/05_Supply_Side/`

### Search strategy
- `freight cost "Mount Isa" Brisbane per kg road`
- `sample transport mining laboratory Australia freight`
- `"ALS" OR "SGS" turnaround time assay Australia business days`
- `accommodation "Mount Isa" hotel rate per night 2025 2026`
- `site:toll.com.au OR site:startrack.com.au regional freight rates Queensland`

---

## Output Directory Structure

```
Market Feasibility Section/Sections/05_Supply_Side/
├── SUPPLY_SIDE_RESEARCH_PLAN.md          ← this file
├── Pricing_Benchmarks.md                  ← Workstream C output
├── Transport_Costs.md                     ← Workstream D output
├── Provider_Profiles/
│   ├── ALS_Profile.md
│   ├── Bureau_Veritas_Profile.md
│   ├── SGS_Profile.md
│   ├── Intertek_Profile.md
│   └── Core_Resources_Profile.md
└── Facility_Profiles/
    ├── UQ_SMI_JKTech_Profile.md
    ├── CSIRO_Mineral_Processing_Profile.md
    ├── QRCUF_Profile.md
    └── ANSTO_Profile.md
```

## Execution Timeline

All 4 workstreams can run in parallel. Recommended order of launch:

1. **Workstream A** (commercial labs) — highest priority, feeds 3.5 directly
2. **Workstream B** (uni/gov facilities) — high priority, feeds 3.5 + 3.7
3. **Workstream D** (transport costs) — medium, feeds 3.8
4. **Workstream C** (pricing) — medium, hardest to source, may have sparse results

Total: **11 agent runs** (5 + 4 + 1 + 1), all parallelisable within workstreams.

## Integration with Company Reports

Data from these workstreams feeds into the market feasibility section analysis, NOT into individual company reports. The connection point is:
- **Field 4 (Labs Currently Used)** in company reports → cross-referenced against provider profiles from Workstream A
- **Section 3.5** synthesises provider profiles + facility profiles into a supply-side landscape
- **Section 3.8** uses pricing benchmarks + transport costs to build the total cost comparison model

## Not Included (Deferred)

**Interview extraction (Gap 5)** — The 31+ stakeholder consultation transcripts in Notion need systematic extraction, but this is deferred. Focus on company reports and desk research first. When ready, interview extraction will provide:
- Demand statements → Section 3.4
- Pain points → Section 3.4 + 3.6
- Pricing references → Section 3.8
- Service gap citations → Section 3.6
- Risk concerns → Section 3.9
- Lab usage / provider references → Section 3.5
