# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered astrological natal chart reader using CrewAI's multi-agent Flow framework. Generates comprehensive natal chart reports by running dual LLM analyses (GPT-4.1 + Gemini 2.5 Flash), merging results, reviewing/enhancing, then delivering a styled PDF report via Gmail draft.

## Commands

```bash
# Install dependencies (uses UV package manager)
pip install uv
crewai install

# Run the full natal reading flow
crewai run
# or: kickoff
# or: python src/natal_reader/main.py

# Generate flow visualization diagram
plot
```

No test runner, linter, or CI is currently configured.

## Architecture

### Flow Pipeline (`src/natal_reader/main.py`)

`NatalFlow(Flow[NatalState])` orchestrates a sequential 9-step pipeline:

1. **setup_qdrant** — Indexes astrology reference books into Qdrant vector DB
2. **get_natal_chart_data** — Calculates chart using Immanuel library (with pre-computed patterns)
3. **generate_natal_analysis** — Single optimized AnalysisCrew produces interpretation + report
4. **review_natal_analysis** — ReviewCrew critiques and enhances (with chart data verification)
5. **format_natal_analysis** — FormattingCrew applies HTML markup for PDF styling
6. **get_kerykeion_natal_chart** — Generates chart wheel PNG via Kerykeion
7. **save_natal_analysis** — Saves markdown + converts to PDF (WeasyPrint)
8. **send_natal_analysis** — Creates Gmail draft with PDF attachment
9. **print_final_stats** — Logs timing and token usage

Steps are chained via `@start()` and `@listen()` decorators. Token usage is tracked via `@track_token_usage` decorator.

### Four Crews (`src/natal_reader/crews/`)

Each crew has its own directory with `*_crew.py`, `config/agents.yaml`, and `config/tasks.yaml`:

| Crew | Model | Agents | Purpose |
|------|-------|--------|---------|
| `analysis_crew` | GPT-4.1 (temp: 0.4/0.7) | interpreter, writer | Single-pass unified analysis combining Hellenistic, Psychological, and Humanistic traditions |
| `review_crew` | DeepSeek + Gemini 2.5 Flash | critic, enhancer | Factual verification + quality review |
| `formatting_crew` | GPT-4.1-mini (temp: 0.3) | markdown_enhancer | HTML markup for PDF styling |
| `gmail_crew` | GPT-4.1 | email_writer, gmail_drafter | Compose + draft email |

### Tools (`src/natal_reader/tools/`)

Custom CrewAI tools wrapping external APIs:
- `google_search_tool.py` — Google Custom Search
- `gemini_search_tool.py` — Gemini grounded search
- `linkup_search_tool.py` — LinkUp search API
- `qdrant_search_tool.py` — RAG over astrology reference books
- `gmail_tool_with_attachment.py` — Gmail API with OAuth + attachments

### State Management

`NatalState` (Pydantic BaseModel in `utils/models.py`) carries all data between flow steps: birth info, chart data (with pre-computed patterns), analysis output, and file paths. Birth data is loaded interactively from JSON files in `src/natal_reader/subjects/`.

### Key Utilities (`src/natal_reader/utils/`)

- `immanuel_natal_chart.py` — Chart calculation (planets, houses, aspects, dignities)
- `kerykeion_chart_utils.py` — Chart wheel visualization
- `qdrant_setup.py` — Vector DB indexing with Gemini embeddings
- `convert_to_pdf.py` — Markdown → HTML → PDF with custom CSS
- `subject_selection.py` — Interactive CLI for selecting/creating birth data
- `decorators.py` — `@timeit` and `@track_token_usage` decorators
- `constants.py` — Paths, timestamps (hardcoded to `/home/j/ai/crewAI/astro/natal_reader/natal_reader/`)

## Environment Variables (`.env`)

Required API keys:
- `OPENAI_API_KEY`, `GEMINI_API_KEY`
- `GOOGLE_SEARCH_API_KEY`, `SEARCH_ENGINE_ID`
- `GMAPS_API_KEY` (geocoding birth locations)
- `QDRANT_CLUSTER_URL`, `QDRANT_API_KEY`, `QDRANT_COLLECTION_NAME`
- `LINKUP_API_KEY`

Gmail OAuth token stored at `src/natal_reader/utils/token.json`.

## Output Artifacts

- `outputs/{date}/` — Final markdown reports + PDFs
- `outputs/{date}/charts/` — Kerykeion chart PNGs
- `crew_outputs/{timestamp}/` — Intermediate crew task outputs
- `timings/{timestamp}.txt` — Performance logs
- `astro_docs/` — Reference astrology books (markdown) for RAG

## Key Patterns

- **Single-pass multi-tradition analysis**: Unified crew synthesizes Hellenistic, Psychological, and Humanistic astrology in one interpretation
- **Temperature tuning**: 0.4 for precise technical interpretation, 0.7 for creative narrative writing
- **Pre-computed chart patterns**: Chart ruler, stelliums, hemisphere balance, mutual receptions, and tight aspects calculated upfront
- **Factual verification**: Review crew receives raw chart data to verify all degrees, aspects, and placements
- **RAG pipeline**: Astrology books are chunked, embedded (Gemini `text-embedding-004`), and stored in Qdrant for agent retrieval (limit: 8 results, threshold: 0.3)
- **CrewAI Flow**: Sequential steps with `@listen()` decorator chaining; state passed via Pydantic model
- **Crew configuration**: Agents and tasks defined in YAML configs, wired in Python crew classes
- Python `>=3.12.9, <3.13` strictly required
