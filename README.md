# gov-monitor

City-scale intelligence pipeline that ingests open government data from [data.gov.in](https://data.gov.in), normalizes and scores it, stores metrics in CockroachDB, and generates bilingual executive summaries with Gemini for Metabase dashboards.

Built for district-level monitoring (default target: **Pune**), with summaries in **English and Marathi**.

## What it does

The pipeline runs as a long-lived daemon on a configurable interval (`API_FETCH_INTERVAL_SECONDS`, default 24h). Each cycle walks five signal extractors in sequence, normalizes every row, scores it, persists to CockroachDB, and generates a bilingual LLM summary. Verbose stdout logging traces ingestion, penalties, and synthesis; a lightweight HTTP health endpoint (`GET /` → `Pipeline Daemon is Active`) keeps container orchestrators happy.

### 1. Ingest

Each metric has a dedicated extractor in `src/ingestion/signals.py` that extends `BaseGovExtractor`. On every cycle the extractor:

1. **Calls the data.gov.in OGD API** — `GET https://api.data.gov.in/resource/{resource_id}` with your API key, `format=json`, and a row cap (`MAX_ROWS_PER_API_CALL`, default 30).
2. **Applies a server-side geographic filter** when the dataset supports it — city-scoped signals (e.g. AQI) filter on `TARGET_CITY`; district-scoped signals (e.g. Mandi price, rainfall) filter on `TARGET_DISTRICT`. Reservoir level has no geographic filter because the upstream dataset is state-wide.
3. **Re-filters client-side** — Records whose filter column does not exactly match the target (case-insensitive) are dropped, guarding against partial API filter matches.
4. **Handles failures gracefully** — Timeouts, HTTP errors, and JSON parse failures log a critical message and return zero rows for that signal; the rest of the cycle continues.

The five signals fetched per cycle: AQI, Mandi price, reservoir level, Anganwadi students served, and district rainfall (see [Data sources](#data-sources) for resource IDs and filter columns).

### 2. Normalize & score

For every raw API record, the extractor runs `parse_with_audit()` before persistence:

**Normalization**

- The primary value column (e.g. `avg_value` for AQI, `modal_price` for Mandi) is coerced to `float` via `normalize_metric_field()`.
- Values that are `null`, empty, or known sentinels (`n/a`, `na`, `null`, `none`, `-`, `nan`, `nil`, `#n/a`) are treated as missing and **imputed to `0.0`**, with an issue tag `missing_or_noisy:{field}` recorded for scoring.
- `audit_record_fields()` scans the full raw record for additional gaps: the value column again, plus any geographic keys present in the row (`state`, `district`, `city`, and common casing variants). Reservoir metrics skip geographic audits because the API layout lacks standard district strings.

**Confidence score (0.0–1.0)**

Scoring starts at **1.0** and applies deterministic deductions. The final score is clamped to `[0.0, 1.0]` and rounded to two decimal places.

| Penalty | Amount | When it applies |
|---------|--------|-----------------|
| Missing or noisy field | **−0.12** per issue | Each tagged field from normalization or audit (deduplicated per record) |
| Unusable value | **→ 0.0** (hard fail) | Normalized value is `null` or negative |
| Missing geo structure | **−0.20** | Record lacks a state key *or* a district/city key (skipped for reservoir) |

**Metric-specific anomaly penalties** (applied after field penalties):

| Metric | Condition | Penalty |
|--------|-----------|---------|
| AQI | Value > 500 or exactly 0 | −0.70 |
| Mandi price | Value < 100 or > 50,000 INR/quintal | −0.60 |
| Reservoir level | Value > 10,000 | −0.50 |
| Anganwadi students | Value = 0 | −0.40 |
| Anganwadi students | Value > 1,000 | −0.30 |
| Rainfall | Value > 300 mm | −0.40 |

A row with three missing fields (−0.36) plus an out-of-range AQI (−0.70) could land at **0.0** after clamping. Low-confidence rows are **not dropped** — they are stored with their score and full `raw_payload` so dashboards and the LLM layer can surface degraded data explicitly.

### 3. Persist

Each normalized row becomes a `normalized_metrics` record:

- `district` — always `TARGET_DISTRICT` (the monitoring target, default Pune)
- `metric_category`, `metric_name`, `metric_value`, `unit` — from the extractor
- `confidence_score` — algorithmic trust score from step 2
- `raw_payload` — the original API JSON for audit and drill-down
- `timestamp` — server default at insert time

All rows from all five signals are added in a single database transaction and committed at the end of the ingestion pass. If anything fails mid-cycle, the transaction rolls back.

### 4. Synthesize

After persistence, the synthesizer loads the **15 most recent** `normalized_metrics` rows (any signal, ordered by timestamp) and builds a compact payload that includes each metric's value, unit, and **confidence score**. That payload is sent to **Gemini 2.5 Flash** with a prompt targeting the district magistrate: a strict 3-sentence executive alert in English and Marathi, stored as one `executive_summaries` row tagged `English+Marathi`. The LLM sees confidence alongside values so it can weight uncertain readings in the narrative.

### 5. Visualize

Metabase connects to the same CockroachDB instance and can chart `normalized_metrics` (filtering or coloring by `confidence_score`) and display the latest `executive_summaries`.

## Architecture

```
data.gov.in  ──►  Extractors  ──►  Scoring  ──►  CockroachDB
                                              │
                                              ▼
                                         Gemini (LLM)
                                              │
                                              ▼
                                    executive_summaries
                                              │
                                              ▼
                                         Metabase
```

## Data sources

| Signal | Category | Unit | Source filter |
|--------|----------|------|---------------|
| AQI | Environment | Index | city |
| Mandi Price | Economy | INR/Quintal | district |
| Reservoir Level | Utilities | Percent | — |
| Anganwadi Students Served | Infrastructure | Students | district |
| Rainfall | Environment | mm | district |

Each extractor lives in `src/ingestion/signals.py` and extends `BaseGovExtractor` in `src/ingestion/base_extractor.py`.

## Database schema

**`normalized_metrics`** — One row per ingested metric with timestamp, district, category, value, unit, confidence score, and raw JSON payload.

**`executive_summaries`** — Bilingual LLM-generated alerts tagged with `English+Marathi`.

Tables are created automatically on first run via SQLAlchemy (`init_db()`).

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- CockroachDB cluster (Cloud or self-hosted) with TLS
- [data.gov.in API key](https://data.gov.in/)
- [Google Gemini API key](https://ai.google.dev/)
- Docker & Docker Compose (for containerized runs)

## Configuration

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | CockroachDB/PostgreSQL URI. Append `sslmode=verify-full&sslrootcert=ca.pem` for TLS. |
| `DB_CA_CERT` | Cluster CA certificate. Use `\n` for line breaks inside the quoted string. |
| `DATA_GOV_IN_API_KEY` | data.gov.in API key |
| `GEMINI_API_KEY` | Google Gemini API key |
| `TARGET_CITY` | City filter for city-scoped datasets (default: `Pune`) |
| `TARGET_DISTRICT` | District filter and summary target (default: `Pune`) |
| `LANGUAGE_TARGET` | Target language label for synthesis context (default: `Marathi`) |
| `API_FETCH_INTERVAL_SECONDS` | Seconds between pipeline cycles (default: `86400` = 24h) |
| `MAX_ROWS_PER_API_CALL` | Row cap per data.gov.in endpoint per cycle (default: `100`) |

On startup, `DB_CA_CERT` is written to `ca.pem` so SQLAlchemy can verify the cluster certificate.

## Local development

Install dependencies with uv:

```bash
uv sync
```

Run a single pipeline cycle:

```bash
uv run python -m src.main
```

The daemon loops indefinitely. Stop with `Ctrl+C`.

## Docker

Build the dependency tree and image (uses Python 3.11 inside the container):

```bash
./scripts/prepare-docker.sh
```

Start the pipeline and Metabase:

```bash
docker compose up
```

- **Pipeline** — Runs `python -m src.main`; `./src` is mounted for live code edits.
- **Metabase** — Available at [http://localhost:3000](http://localhost:3000). Connect it to your CockroachDB instance using the same `DATABASE_URL`.

To rebuild after dependency changes, remove `.venv` and re-run `prepare-docker.sh`.

## Deploy on Render

[`render.yaml`](render.yaml) defines two services:

1. **gov-monitor-pipeline** — Docker web service (health endpoint keeps the daemon alive on Render).
2. **gov-monitor-dashboard** — Metabase image.

Set `DATABASE_URL`, `DB_CA_CERT`, `DATA_GOV_IN_API_KEY`, `GEMINI_API_KEY`, and `MB_DB_CONNECTION_URI` in the Render dashboard before deploying.

## Project structure

```
gov-monitor/
├── src/
│   ├── main.py                 # Pipeline daemon + health server
│   ├── config.py               # Environment configuration
│   ├── database.py             # SQLAlchemy engine, sessions, init
│   ├── ingestion/
│   │   ├── base_extractor.py   # data.gov.in fetch logic
│   │   └── signals.py          # Metric-specific extractors
│   ├── pipeline/
│   │   ├── scoring.py          # Normalization + confidence scoring
│   │   └── synthesizer.py      # Gemini bilingual summaries
│   └── schemas/
│       └── models.py           # SQLAlchemy ORM models
├── scripts/
│   └── prepare-docker.sh       # Build .venv + Docker image
├── docker-compose.yml
├── Dockerfile
├── render.yaml
└── pyproject.toml
```

## License

See repository license file if present.
