# Natal Reader

Natal Reader is an AI-powered astrological natal chart analysis system built with [crewAI](https://crewai.com). It generates personalized, in-depth natal chart interpretations by orchestrating multiple specialized AI agents through a sequential pipeline.

## Overview

Natal Reader takes birth data (date, time, and location) and produces a comprehensive astrological analysis including:

- **Detailed natal chart calculation** using the Immanuel library
- **Multi-tradition interpretation** combining Hellenistic, Psychological, and Humanistic astrology
- **Factual verification** of all planetary positions, aspects, and degrees
- **Professional PDF report** with chart wheel visualization
- **Email delivery** via Gmail draft

The system leverages RAG (Retrieval-Augmented Generation) with indexed astrology reference books stored in Qdrant vector database, enabling agents to retrieve authoritative astrological knowledge during analysis.

## Installation

Natal Reader requires Python >=3.12.9 <3.13. The project uses [UV](https://docs.astral.sh/uv/) for dependency management.

### 1. Install UV

```bash
pip install uv
```

### 2. Install Dependencies

Navigate to the project directory and install:

```bash
uv sync
```

### 3. Configure Environment Variables

Create a `.env` file in the project root with the following:

```bash
# Required API Keys
OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key

# Qdrant Cloud Configuration
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key

# Gmail OAuth (for email delivery)
# Follow Google OAuth setup to generate token.json
```

### 4. Set Up Qdrant Cloud

Natal Reader uses Qdrant Cloud for vector storage of astrology reference materials. To set up:

1. **Create a Qdrant Cloud account** at [https://cloud.qdrant.io](https://cloud.qdrant.io)

2. **Create a new cluster** in the Qdrant Cloud dashboard

3. **Get your credentials** from the cluster dashboard:
   - **Endpoint URL** (e.g., `https://xxx-xxx.aws.cloud.qdrant.io`)
   - **API Key** from the "API Keys" section

4. **Add credentials to `.env`**:
   ```bash
   QDRANT_URL=https://your-cluster.qdrant.io
   QDRANT_API_KEY=your_api_key
   ```

For detailed setup instructions, see the [Qdrant Cloud Quickstart Guide](https://qdrant.tech/documentation/cloud-quickstart/).

On first run, the `setup_qdrant` step will automatically index reference books from the `docs/` directory into your cloud cluster.

### 5. Configure Gmail OAuth (Optional)

For email delivery functionality:

1. Enable Gmail API in Google Cloud Console
2. Create OAuth 2.0 credentials
3. Run the OAuth flow to generate `token.json` in `src/natal_reader/utils/`

## Project Structure

```
natal_reader/
├── src/natal_reader/
│   ├── crews/
│   │   ├── analysis_crew/     # Chart interpretation & report writing
│   │   ├── review_crew/       # Factual verification & enhancement
│   │   ├── formatting_crew/   # HTML markup for PDF styling
│   │   └── gmail_crew/        # Email composition & delivery
│   ├── utils/
│   │   ├── immanuel_natal_chart.py   # Chart calculation with pre-computed patterns
│   │   ├── kerykeion_chart_utils.py  # Chart wheel visualization
│   │   ├── qdrant_setup.py           # Vector DB indexing
│   │   ├── decorators.py             # Timing & token tracking
│   │   └── models.py                 # Pydantic state management
│   ├── tools/
│   │   ├── qdrant_search_tool.py     # RAG retrieval
│   │   ├── gemini_search_tool.py     # Web search
│   │   └── gmail_tool_with_attachment.py
│   ├── main.py               # Flow pipeline definition
│   └── utils/
├── docs/                     # Astrology reference books (RAG source)
├── outputs/                  # Generated reports & PDFs
├── crew_outputs/             # Intermediate crew task outputs
└── .env                      # Environment configuration
```

## Pipeline Architecture

Natal Reader executes a 9-step sequential pipeline via `NatalFlow`:

```
┌─────────────────┐
│ 1. setup_qdrant │ ─── Index astrology reference books into Qdrant
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│ 2. get_natal_chart  │ ─── Calculate chart using Immanuel library
│      + patterns     │     (chart ruler, stelliums, mutual receptions, etc.)
└────────┬────────────┘
         │
         ▼
┌─────────────────────────┐
│ 3. generate_analysis    │ ─── AnalysisCrew: unified interpretation
│   (GPT-4.1, temp 0.4/0.7)│    combining Hellenistic, Psychological,
└────────┬────────────────┘    and Humanistic traditions (8,000-12,000 words)
         │
         ▼
┌─────────────────────────┐
│ 4. review_analysis      │ ─── ReviewCrew: factual verification
│   (Gemini)   │     using raw chart data for accuracy
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ 5. format_analysis      │ ─── FormattingCrew: apply HTML markup
│   (GPT-4.1-mini, temp 0.3)│    for PDF styling
└────────┬────────────────┘
         │
         ▼
┌───────────────────────────┐
│ 6. get_chart_image        │ ─── Generate chart wheel PNG
│   (Kerykeion)             │     via Kerykeion library
└────────┬──────────────────┘
         │
         ▼
┌─────────────────────────┐
│ 7. save_report          │ ─── Save markdown + convert to PDF
│   (WeasyPrint)          │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ 8. send_email           │ ─── Create Gmail draft with PDF
│   (GmailCrew)           │     attachment
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ 9. print_stats          │ ─── Log timing & token usage
└─────────────────────────┘
```

## Running the Project

Execute the pipeline from the project root:

```bash
uv run python src/natal_reader/main.py
```

The system will:
1. Prompt for subject selection (birth data from `src/natal_reader/subjects/`)
2. Execute the 9-step pipeline
3. Output a PDF report to `outputs/`
4. Create a Gmail draft for delivery

## Crews

Natal Reader uses four specialized AI crews:

| Crew | Model | Agents | Purpose |
|------|-------|--------|---------|
| **AnalysisCrew** | GPT-4.1 | interpreter, writer | Single-pass unified analysis combining Hellenistic, Psychological, and Humanistic traditions |
| **ReviewCrew** | Gemini 3.1 | critic, enhancer | Factual verification of degrees/aspects + quality enhancement |
| **FormattingCrew** | GPT-4.1-mini | markdown_enhancer | HTML markup for PDF styling (temperature: 0.3) |
| **GmailCrew** | GPT-4.1 | email_writer, gmail_drafter | Compose and draft email with PDF attachment |

### Analysis Crew

The core analysis crew produces an 8,000-12,000 word natal report with:

- **Chart overview**: shape, sect, Moon phase, element/modality balance
- **Core identity**: Ascendant, Sun, Moon synthesis
- **Planetary dynamics**: detailed interpretation of all planets, houses, aspects
- **Eclipse & syzygy influences**: karmic pattern indicators
- **Developmental themes**: psychological insights and growth arcs
- **Practical guidance**: actionable reflections
- **Glossary**: accessible definitions of technical terms

Temperature tuning: 0.4 for precise technical interpretation, 0.7 for creative narrative writing.

### Review Crew

Receives raw chart data alongside the analysis for factual verification:

- Validates all planetary degrees, aspects, and orbs
- Checks for fabricated or inaccurate placements
- Enhances clarity and emotional resonance
- Ensures consistency across all sections

## Key Features

### Pre-computed Chart Patterns

The chart calculation step identifies key patterns upfront:

- **Chart ruler**: traditional ruler of Ascendant with sign, house, dignity, sect
- **Stelliums**: 3+ planet groupings by sign and house
- **Hemisphere balance**: eastern/western, northern/southern distribution
- **Mutual receptions**: planets in each other's domiciles
- **Tight aspects**: aspects with orb < 2° for prioritized interpretation

### RAG Pipeline

Astrology reference books are:
1. Chunked into semantic segments
2. Embedded using Gemini `gemini-embedding-001`
3. Stored in Qdrant (similarity threshold: 0.3, limit: 8 results)
4. Queried by agents during analysis for authoritative interpretations

### Token & Timing Tracking

All steps are decorated with `@track_token_usage` and `@timeit` decorators, logging:
- Per-step execution time
- Token consumption by model
- Cumulative pipeline statistics

## Configuration

### Subject Data

Birth data is stored as JSON files in `src/natal_reader/subjects/`:

```json
{
  "name": "Subject Name",
  "date_of_birth": "1990-01-01",
  "time_of_birth": "12:00",
  "place_of_birth": "City, Country",
  "latitude": 40.7128,
  "longitude": -74.0060
}
```

### Agent & Task Configuration

Each crew defines agents and tasks in YAML configs:

- `src/natal_reader/crews/*/config/agents.yaml` — agent roles, goals, backstories
- `src/natal_reader/crews/*/config/tasks.yaml` — task descriptions, expected outputs

## Dependencies

Key libraries:

| Package | Purpose |
|---------|---------|
| `crewai` | Multi-agent orchestration framework |
| `immanuel` | Natal chart calculation (Swiss Ephemeris) |
| `kerykeion` | Chart wheel visualization |
| `qdrant-client` | Vector database for RAG |
| `weasyprint` | PDF conversion from HTML/CSS |
| `google-genai` | Gemini embeddings & search |
| `pydantic` | State management & validation |

## Output

The pipeline generates:

- **Natal report PDF** — `outputs/{timestamp}/natal_report.pdf`
- **Chart wheel PNG** — `outputs/{timestamp}/natal_chart.png`
- **Intermediate markdown** — `crew_outputs/{timestamp}/`
- **Timing logs** — `timings/{timestamp}.txt`
- **Token usage** — logged to console and timing files

## Troubleshooting

### API Key Errors

Ensure all required keys are set in `.env`. Verify with:

```bash
echo $OPENAI_API_KEY
```

### Qdrant Connection Failed

Check Qdrant is running and accessible:

```bash
curl http://localhost:6333
```

### Gmail OAuth Issues

Delete `token.json` and re-run the OAuth flow to refresh credentials.

### Chart Calculation Errors

Verify birth data coordinates are valid. Check Immanuel library ephemeris files are installed.

## License

This project is for personal and research use.
