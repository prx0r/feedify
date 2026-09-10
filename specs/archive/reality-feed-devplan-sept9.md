# Reality Feed Development Plan

## Architecture

```
                   RAW WORLD
                       │
        ┌──────────────┼───────────────┐
        │              │               │
     filings        physical        frontier
        │              │               │
 SEC/TWSE/DART   grid/permits     Git/arXiv/HF
 gov awards      production       patents/OpenAlex
        │              │               │
        └──────────────┼───────────────┘
                       ↓
              IMMUTABLE EVENTS
                       ↓
               ENTITY RESOLVER
                       ↓
             STATE TRANSITIONS
                       ↓
               CAUSAL GRAPH
                       ↓
       INDEPENDENT CONVERGENCE SCORE
                       ↓
       BOTTLENECK / CONSTRAINT DETECTOR
                       ↓
             PUBLIC COMPANY MAP
                       ↓
              FINANCIAL MODEL
                       ↓
               reality.feedify.dev
```

## Canonical Source Stack (30 sources)

| Rank | Source | Alpha | Build |
|------|--------|-------|-------|
| 1 | SEC EDGAR | 10 | NOW |
| 2 | TWSE OpenAPI / MOPS | 10 | NOW |
| 3 | Korea OpenDART | 9.9 | NOW |
| 4 | PUDL | 9.9 | NOW |
| 5 | ERCOT | 9.8 | NOW |
| 6 | USAspending | 9.8 | NOW |
| 7 | SAM.gov | 9.7 | NOW |
| 8 | NRC ADAMS API | 9.7 | NOW |
| 9 | USPTO + EPO OPS | 9.6 | NOW |
| 10 | GitHub | 9.6 | NOW |
| 11 | Corporate job boards | 9.5 | NOW |
| 12 | FERC API/EQR | 9.5 | NOW |
| 13 | EPA ECHO | 9.3 | Next |
| 14 | US Census Trade | 9.3 | Next |
| 15 | Hugging Face Hub | 9.3 | NOW |
| 16 | EU TED procurement | 9.2 | Next |
| 17 | CORDIS | 9.2 | Next |
| 18 | OpenAlex | 9.1 | NOW |
| 19 | OpenReview + arXiv | 9.1 | NOW |
| 20 | Federal Register | 9.0 | Next |
| 21 | Companies House | 8.9 | Next |
| 22 | BaFin | 8.9 | Next |
| 23 | TDnet | 8.9 | Archive |
| 24 | CourtListener | 8.7 | Next |
| 25 | PyPI BigQuery | 8.7 | NOW |
| 26 | GLEIF LEI | 8.5 | NOW |
| 27 | EIA API | 8.5 | Next |
| 28 | UK Contracts Finder | 8.4 | Next |
| 29 | SBIR/STTR bulk | 8.4 | Next |
| 30 | NERC reports | 8.2 | Document |

## MVP: 15 Adapters (This Week)

1. sec
2. twse
3. opendart
4. pudl
5. ercot
6. ferc
7. usaspending
8. sam
9. nrc_adams
10. patent_uspto_epo
11. jobs_greenhouse_ashby_lever
12. github
13. huggingface
14. openalex_arxiv_openreview
15. entity_gleif

## Phase 2: 15 More

16. epa_echo
17. census_trade
18. ted
19. cordis
20. federal_register
21. courtlistener
22. companies_house
23. bafin
24. tdnet
25. sbir
26. pypi

## The Generic Event Schema

```yaml
event_id:
source:
source_record_id:

observed_at:
effective_at:

entity_ids:
counterparty_ids:
technology_ids:
geo_ids:

event_type:
state_before:
state_after:

quantity:
unit:
value:
currency:

evidence:
  url:
  document_hash:
  excerpt:
  primary_source: true

confidence:
novelty:
economic_materiality:
lead_time_score:

access:
  redistribution_class:
  source_license:
```

## The State Machine

```
RESEARCH
idea → paper → independent reproduction

IP
patent application → grant → assignment

GOVERNMENT
RFI → solicitation → LOI → award → option exercised

CORPORATE
pipeline → qualification → order → backlog → shipment → revenue → cash

PHYSICAL
planning application → permit → interconnection request → approved → construction → commissioning → production

NUCLEAR
pre-application → application → regulatory questions → approval → fuel allocation → fuel fabrication → operation
```

## Key Discoveries

### PUDL saves months
Catalyst Cooperative cleaned EIA/FERC/EPA data. Use PUDL as warehouse.

### TWSE is absurdly good
Monthly revenue for Taiwanese companies. Detect acceleration before quarterly earnings.

### OpenDART purpose-built
Korean XBRL, capital increases, treasury shares, lawsuits.

### NRC ADAMS just became easier
Public Search API released Dec 2025. 3M+ records.

### Hiring is better than LinkedIn
Greenhouse/Ashby/Lever public endpoints. Semantic change in hiring composition.

### OpenAlex replaces paper scraping
CC0 research graph. $1/day free API.

## Access Traps

| Source | Trap |
|--------|------|
| JPX TDnet | Public viewer free, historical API not free |
| ERCOT | Geographically restricted outside US |
| PatentsView | New API keys suspended; use bulk |
| SBIR | API under maintenance; use bulk |
| OpenAlex | Dataset open, API not infinitely free |
| EPO OPS | Free only to 4GB/week |

## The Discovery Example: LPKF

```
OpenAlex: glass-substrate papers +190%
CORDIS: new European glass-packaging consortium
USPTO/EPO: TGV patent families accelerating
TWSE: glass-equipment suppliers revenue +40%
GitHub: CPO tooling activity accelerates
Intel job boards: glass-substrate process engineers +12
LPKF jobs: field service hiring in Asia
LPKF: production follow-on order
```

No sentiment analysis. Feedify discovers LPKF from the world.
