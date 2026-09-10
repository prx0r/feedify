# August 2026 Extraction Plan

**Goal**: Complete categorized extraction of all 102 X accounts with alpha analysis

## Output Structure

```
august/
├── prima_materia/          # Raw tweets per account (JSON)
│   ├── @handle.json        # Each account's tweets
│   └── ...
├── categories/             # Categorized account reports
│   ├── 01-self-improving-ai.md
│   ├── 02-robot-learning.md
│   ├── 03-bioelectricity.md
│   ├── 04-hardware.md
│   ├── 05-energy-materials.md
│   ├── 06-world-models.md
│   ├── 07-autonomous-science.md
│   ├── 08-ai4science.md
│   ├── 09-cognition.md
│   ├── 10-boundary-falsification.md
│   └── 11-stocks.md
├── analysis/
│   ├── coverage-report.md  # What we have vs what we wanted
│   ├── alpha-summary.md    # What alpha each account provided
│   └── gaps.md             # What's missing and why
└── EXTRACTION_PLAN.md      # This file
```

## Extraction Steps

### Step 1: Dump all tweets as prima materiaper account
- Export all 2,384 tweets as JSON files in `prima_materia/`
- Each file: `@handle.json` with full tweet data

### Step 2: Categorize accounts by domain
- Group 102 accounts into 11 categories
- For each: why picked, what alpha expected, what alpha received

### Step 3: Coverage report
- August coverage per account
- Gaps explained (didn't tweet vs index missing)

### Step 4: Alpha summary
- What each category delivered
- Top findings per domain
- What's actionable

## Data Source
- All tweets from `feedify2.db` (Artifact table, source_type='x')
- 2,384 tweets across 101 accounts
- 163 from August 2026, rest from other dates
