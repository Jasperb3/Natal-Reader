# Natal Reader — Implementation Plan

**Date:** 2026-02-19
**Goal:** Consolidate the dual-crew analysis pipeline into a single optimized analyst crew, improve data integrity across the pipeline, tune model parameters, and clean up structural concerns.

---

## Architecture Change Summary

**Current pipeline (10 steps):**
```
setup_qdrant → get_natal_chart_data → GPT analysis → Gemini analysis → merge → review (critic + enhancer + markdown) → chart PNG → save → email → stats
```

**New pipeline (8 steps):**
```
setup_qdrant → get_natal_chart_data → analysis crew → review (critic + enhancer) → markdown formatting → chart PNG → save → email → stats
```

**What's removed:**
- `gemini_analysis_crew/` — entire crew directory
- `merge_crew/` — entire crew directory
- `generate_gemini_natal_analysis` flow step
- `merge_natal_analyses` flow step

**What's added/changed:**
- Single optimized `analysis_crew/` replacing both GPT and Gemini crews
- Chart data passed to review crew for factual verification
- Pre-computed chart patterns in the data pipeline
- `markdown_enhancer` extracted from ReviewCrew into its own crew
- Temperature tuning per agent role
- Negative constraints and length targets in task prompts

---

## Step 1: Enrich the Chart Data Output

**File:** `src/natal_reader/utils/immanuel_natal_chart.py`

Add a `--- Pre-computed Patterns ---` section at the end of `get_natal_chart()` (before the final `--- End of Natal Chart ---` line) that includes:

1. **Chart ruler identification** — determine the traditional ruler of the Ascendant sign, then report that planet's sign, house, dignity, and sect status from the already-parsed chart data.
2. **Stellium detection** — iterate through the parsed objects, group by sign and by house, report any grouping of 3+ planets (excluding angles and points).
3. **Hemisphere balance** — using house numbers already parsed:
   - Eastern (Houses 10–3 counterclockwise): count planets
   - Western (Houses 4–9): count planets
   - Northern (Houses 1–6): count planets
   - Southern (Houses 7–12): count planets
4. **Mutual receptions** — for each pair of traditional planets (Sun–Saturn), check if planet A is in planet B's domicile AND planet B is in planet A's domicile. Report any found.
5. **Tight aspect summary** — filter aspects with orb < 2° and list them separately as "Tight Aspects" for easy agent reference.

This requires only the data already computed by Immanuel — no new API calls. Build a helper dict mapping signs to their traditional rulers to support items 1 and 4.

**Acceptance criteria:**
- Running `get_natal_chart()` on an existing subject JSON produces the new sections
- All pre-computed patterns are verifiable against the raw chart data above them
- No new dependencies introduced

---

## Step 2: Create the Single Optimized Analysis Crew

### 2a. Create directory structure

```
src/natal_reader/crews/analysis_crew/
├── __init__.py
├── analysis_crew.py
└── config/
    ├── agents.yaml
    └── tasks.yaml
```

### 2b. Define agents (`config/agents.yaml`)

**Agent 1: `natal_chart_interpreter`**

```yaml
natal_chart_interpreter:
  role: >
    Master Astrological Analyst & Interpreter
  goal: >
    Deliver a structured, technically precise, and multi-layered interpretation
    of natal chart data that integrates both classical technique and psychological depth.
  backstory: >
    You are a master-level astrologer with deep fluency in Hellenistic, Psychological,
    and Humanistic traditions. You synthesize all three lenses into a single, unified
    analytical framework.

    From the Hellenistic tradition, you apply sect doctrine, essential dignities
    (domicile, exaltation, detriment, fall, peregrine), dispositorship chains,
    mutual receptions, and planetary condition analysis with precision. You identify
    the chart ruler's condition, the sect light, and classical aspect doctrine
    (applying vs separating, associative vs dissociate).

    From the Psychological tradition, you interpret planetary placements as
    intrapsychic dynamics — archetypal functions operating through signs and houses.
    You frame aspects as internal dialogues between parts of the psyche, and you
    illustrate key dynamics with concrete behavioral and psychological examples.

    From the Humanistic tradition, you emphasize developmental potential over
    deterministic outcomes. You identify growth arcs, individuation pathways,
    and the evolutionary direction indicated by nodal and eclipse patterns.

    You are rigorous in recognizing patterns across chart factors, tracking themes,
    identifying energetic imbalances, and highlighting high-leverage planetary actors
    (chart rulers, out-of-bounds planets, stellium focal points, angular planets).

    You produce a highly structured analytical document that serves as the essential
    blueprint for the final narrative report.
```

**Agent 2: `natal_report_writer`**

```yaml
natal_report_writer:
  role: >
    Astrological Storyteller & Natal Report Writer
  goal: >
    Translate the analytical chart interpretation into a cohesive, resonant,
    and psychologically insightful natal report that feels both illuminating
    and grounding.
  backstory: >
    You are an experienced astrological storyteller who bridges analytical
    structure with emotional depth. Your fluency spans classical symbolism,
    psychological archetypes, and developmental astrology.

    You take the Interpreter's precise technical analysis and craft a warm,
    empowering narrative that supports client self-awareness and reflection.
    You use metaphor, real-world examples, and plain-language insight to
    connect the chart to lived experience.

    You ensure each planetary section includes the symbolic meaning of its
    house domain — grounding abstract ideas in relationships, career, identity,
    and growth. You build a clear narrative arc from chart overview through
    planetary dynamics to practical guidance.

    You support accessibility by providing a glossary of all key astrological
    terms. Your reports balance wisdom with relatability, encouraging the
    reader to step into their highest potential.
```

### 2c. Define tasks (`config/tasks.yaml`)

**Task 1: `natal_chart_interpretation_task`**

Combine the strongest elements from both existing GPT and Gemini interpretation tasks. Key additions vs current versions:

```yaml
natal_chart_interpretation_task:
  description: >
    Generate a comprehensive, degree-accurate interpretation of the subject's
    natal chart using the full astronomical dataset provided. Use the tools
    available to you to research information and find additional details
    relevant to the subject's chart.

    Output should be modular and clearly structured to serve as the analytical
    backbone for the final report.

    Required analytical coverage:

    - Chart Context:
        - Classify chart shape and interpret implications for personality flow.
        - Determine diurnal/nocturnal status and analyze sect alignment of each planet.
        - Note Moon phase and house system used.
        - Reference the pre-computed patterns section for chart ruler, stelliums,
          hemisphere balance, and mutual receptions — verify and expand upon them.

    - Element, Modality, Hemisphere, and Quadrant Balance:
        - Provide count summaries and interpretations.
        - Compare dominant and deficient elements/modalities and explain behavioral
          or psychological expression.
        - Relate to psychological temperament and inner vs outer orientation.

    - Ascendant and Chart Ruler:
        - Analyze the rising sign and chart ruler's sign, house, aspects, dignities,
          motion, and sect.
        - Highlight mutual reception, angularity, and dispositorship chains.
        - Interpret the chart ruler's overall influence on life trajectory.

    - Planetary Positions and Conditions:
        - For each classical planet: sign, house, decan, dignity/debility, sect status,
          motion (direct/retrograde).
        - Include symbolic meaning of the house each planet occupies.
        - Include minor points (Chiron, Part of Fortune, Vertex, Lilith variations,
          Juno, Ceres) and lunar nodes with psychological framing.
        - Flag and interpret out-of-bounds planets with unconventional expressions.
        - Provide 1-2 grounded psychological or behavioral examples per planet.

    - Aspects:
        - Identify all major aspects with orb and degree details.
        - Distinguish applying vs separating and associative vs dissociate.
        - Flag tight aspects (<2° orb) from the pre-computed summary and interpret
          their intensification.
        - Group aspects thematically (communication, transformation, relationships, drive).
        - Highlight configurations (T-squares, yods, grand trines) if present.

    - Points and Angles:
        - Analyze Asc, Desc, MC, IC individually.
        - Interpret all symbolic points (Chiron, Nodes, Lilith variants, Vertex,
          Ceres, Juno, Part of Fortune) with karmic/spiritual implications.

    - Eclipse and Syzygy Influence:
        - Analyze pre- and post-natal eclipses as karmic pattern indicators.
        - Interpret the natal syzygy as an evolutionary anchor.

    - Planetary Strengths & Focal Points:
        - Highlight planets with high angularity, multiple aspects, or rulership.
        - Identify stelliums and thematic clusters.

    Constraints:
    - Do NOT fabricate aspects, degrees, or placements not present in the chart data.
    - Do NOT infer house rulership systems beyond what the data provides.
    - If a data point is absent, state that explicitly rather than inventing one.
    - Cite specific degrees and orbs from the data when making claims.
    - Every claim must be traceable to a specific data point in the chart.

    Output guidelines:
    - Clean markdown (no code blocks)
    - Degree-accurate and evidence-based
    - Maintain interpretive richness anchored in concrete chart features
    - Ensure modularity for seamless integration into report generation
    - Target 3,000–5,000 words

    Subject's Name: {name}
    Today's date: {today}
    Natal Chart: {natal_chart}

  expected_output: >
    A detailed, degree-precise, multi-tradition analysis of the subject's natal chart,
    organized for seamless report integration and grounded in psychological insight.
    Every interpretation must be traceable to specific chart data points.
  agent: natal_chart_interpreter
```

**Task 2: `natal_report_writing_task`**

Merge the best of both existing report writing tasks. Key changes:
- Add word count targets per section
- Keep the full report structure from the GPT crew's version (sections 0–11)
- Retain all the quality requirements from both versions
- Add: "Do not introduce any chart features not present in the interpreter's analysis"

```yaml
natal_report_writing_task:
  description: >
    Translate the structured natal chart interpretation into a polished,
    psychologically astute, and narratively cohesive report. Faithfully preserve
    all technical accuracy from the interpretation while enhancing emotional
    resonance, symbolic depth, and practical relevance.

    Goal:
    - Present the chart as a symbolic, evolving life map — developmental potentials
      rather than deterministic outcomes.
    - Craft each section as a self-contained thematic unit while weaving them
      into a unified personal narrative.
    - Write with emotional intelligence, psychological nuance, and archetypal clarity.
    - Never extrapolate, speculate, or introduce data beyond the provided interpretation.

    Report Structure (Markdown, no code blocks):

    0. **Title Block and Chart Header** (~50 words)
        ```
        # Natal Chart for {name}
        Date of Report: {today}

        [natal_chart]

        **Date of Birth:** {date_of_birth}
        **Place of Birth:** {place_of_birth}
        ```

    1. **Introduction** (~200-300 words)
        - Chart type, house system, chart shape, Moon phase.
        - Establish tone: symbolic blueprint of potentials, not fixed destiny.

    2. **Energetic Balance & Pattern Emphasis** (~300-500 words)
        - Elemental, modal, hemispheric, and quadrant distributions.
        - Dominant vs underrepresented energies.
        - How the energetic landscape shapes core life orientation.

    3. **Core Identity: The Big 3** (~500-800 words)
        - Ascendant, Sun, Moon — each with sign, house, key aspects.
        - Synthesis of how the Big 3 interact dynamically.

    4. **Planetary Psychology and Celestial Dynamics** (~2,000-3,000 words)
        - Chart Ruler: sign, house, aspects, dignity — primary narrative agent.
        - Classical Planets (Mercury–Saturn): psychological function through
          sign, house, motion, dignity, aspects. 200-400 words each.
        - Modern Planets (Uranus, Neptune, Pluto): generational/unconscious forces.
        - Minor Bodies and Symbolic Points: Chiron, Nodes, Liliths, Vertex,
          Juno, Ceres, Part of Fortune.

    5. **Aspects & Archetypal Dynamics** (~500-800 words)
        - Significant aspects and configurations, especially tight ones.
        - Major intrapsychic conflicts or synergies.
        - Grouped thematically, not as raw listings.

    6. **Eclipse and Syzygy Significance** (~300-500 words)
        - Pre-/post-natal eclipses as karmic markers.
        - Syzygy as developmental backdrop.

    7. **House Emphasis** (~300-500 words)
        - Concentration or angular emphasis.
        - Life domains of focused evolution or recurring challenge.

    8. **Psychological and Developmental Themes** (~400-600 words)
        - Recurrent motifs, inner polarities, key developmental arcs.
        - Vivid, grounded metaphors over clinical abstraction.

    9. **Guidance and Reflections** (~300-500 words)
        - 3-5 actionable insights rooted in specific chart patterns.
        - Empowering, emotionally validating, pragmatically applicable.

    10. **Conclusion** (~200-300 words)
        - Recap strengths, tensions, potential trajectory.
        - Reaffirm lifelong symbolic integration.

    11. **Glossary** (~300-500 words)
        - All technical and symbolic terms used, in accessible language.

    Target total report length: 8,000–12,000 words.

    Requirements:
    - Markdown (no code blocks)
    - Emotionally intelligent, symbolically coherent, supportive tone
    - Modular, consistently formatted structure
    - Thematic integrity over isolated trait listing
    - Emotional validation and empowerment
    - Symbolic and psychological precision — no deterministic labels
    - All analysis tied strictly to provided interpretation data
    - Cohesive narrative weaving across all sections
    - Vivid yet grounded metaphors
    - Client-centered, growth-oriented focus

  expected_output: >
    A modular, engaging, and psychologically insightful natal chart report of
    8,000–12,000 words in clean markdown, structured around the Big 3 identity
    core and planetary dynamics, integrating symbolic and practical meaning throughout.
  agent: natal_report_writer
```

### 2d. Create crew Python file (`analysis_crew.py`)

- Use GPT-4.1 for both agents (strongest single-pass quality)
- **Interpreter**: `temperature=0.4` (precision-focused)
- **Report writer**: `temperature=0.7` (creative prose)
- Tools: GoogleSearchTool, GeminiSearchTool, QdrantSearchTool, LinkUpSearchTool (same as current)
- Sequential process: interpretation → report writing

```python
gpt41_precise = LLM(model="gpt-4.1", api_key=..., temperature=0.4)
gpt41_creative = LLM(model="gpt-4.1", api_key=..., temperature=0.7)

@agent
def natal_chart_interpreter(self) -> Agent:
    return Agent(
        config=self.agents_config['natal_chart_interpreter'],
        tools=[google_search_tool, GeminiSearchTool(), QdrantSearchTool(), LinkUpSearchTool()],
        llm=gpt41_precise,
        verbose=True
    )

@agent
def natal_report_writer(self) -> Agent:
    return Agent(
        config=self.agents_config['natal_report_writer'],
        tools=[google_search_tool, GeminiSearchTool(), QdrantSearchTool(), LinkUpSearchTool()],
        llm=gpt41_creative,
        verbose=True
    )
```

**Acceptance criteria:**
- Crew runs standalone with a test subject
- Interpretation output references specific degrees and orbs from chart data
- Report output follows the 12-section structure with approximate word targets
- No fabricated chart features in either output

---

## Step 3: Restructure the Review Crew

### 3a. Pass chart data to the review crew

**File:** `src/natal_reader/main.py`

Update `review_merged_natal_analysis` (rename to `review_natal_analysis`) to pass chart data:

```python
inputs = {
    "name": self.state.name,
    "report": self.state.natal_analysis,  # renamed from merged_natal_analysis
    "natal_chart": self.state.natal_chart,  # NEW — ground truth for verification
    "today": self.state.today,
    "date_of_birth": self.state.dob,
    "place_of_birth": self.state.birthplace
}
```

### 3b. Update critic agent and task

**File:** `review_crew/config/agents.yaml`

Revise the critic backstory. Replace "You assume all astronomical data is accurate" with:

```yaml
You verify that all astrological claims in the report are grounded in the
original chart data. Flag any degrees, aspects, or placements that appear
fabricated or misattributed. Your first pass is always factual accuracy
against the provided chart data; your second pass is interpretive quality
and narrative resonance.
```

**File:** `review_crew/config/tasks.yaml`

Update `review_task` description to include chart data reference:

```yaml
# Add to description:
Use the following astronomical chart data as ground truth to verify all
factual claims in the report (degrees, aspects, house placements, dignities):

{natal_chart}

Your first evaluation pass must check factual accuracy against this data.
Flag any discrepancies before evaluating interpretive quality.
```

### 3c. Constrain the report enhancer's tool usage

**File:** `review_crew/config/tasks.yaml`

Add to `report_enhancement_task` description:

```yaml
You may use search tools ONLY to verify or enrich existing interpretations
already present in the report. Do NOT introduce new planetary placements,
aspects, or chart features that were not identified in the original analysis.
Any new content must be directly supportable by the chart data provided.
```

### 3d. Consider upgrading the critic model

**File:** `review_crew/review_crew.py`

Change critic from `deepseek-reasoner` to `gpt-4.1` for stronger analytical critique:

```python
@agent
def critic(self) -> Agent:
    return Agent(
        config=self.agents_config['critic'],
        llm=gpt41,  # upgraded from deepseek
        verbose=True
    )
```

This is optional — evaluate deepseek-reasoner's critique quality first. If its critiques are already strong and well-structured, keep it for cost savings.

### 3e. Extract markdown_enhancer into its own crew

Create a new minimal crew:

```
src/natal_reader/crews/formatting_crew/
├── __init__.py
├── formatting_crew.py
└── config/
    ├── agents.yaml
    └── tasks.yaml
```

- Move the `markdown_enhancer` agent and `markdown_enhancement_task` from `review_crew/` to `formatting_crew/`
- Use `gpt-4.1-mini` (or even `gpt-4.1-nano`) — this is a pure formatting/tagging task
- Remove `markdown_enhancer` from `review_crew/` entirely

**File:** `formatting_crew/formatting_crew.py`

```python
gpt41mini = LLM(model="gpt-4.1-mini", api_key=..., temperature=0.3)

@agent
def markdown_enhancer(self) -> Agent:
    return Agent(
        config=self.agents_config['markdown_enhancer'],
        llm=gpt41mini,
        verbose=True
    )
```

**Acceptance criteria:**
- ReviewCrew runs with only critic + enhancer agents
- FormattingCrew runs independently and produces valid HTML-tagged markdown
- Critic output explicitly references chart data when flagging issues
- Enhancer does not introduce new chart features

---

## Step 4: Update the Flow Pipeline

**File:** `src/natal_reader/main.py`

### 4a. Update state model

**File:** `src/natal_reader/utils/models.py`

Remove fields that are no longer needed:
- `gpt_natal_analysis: str`
- `gemini_natal_analysis: str`
- `merged_natal_analysis: str`

Add/rename:
- `natal_analysis: str = ""` (output of the single analysis crew)

### 4b. Rewrite the flow class

New step sequence:

```python
class NatalFlow(Flow[NatalState]):

    @timeit
    @start()
    def setup_qdrant(self):
        # unchanged

    @timeit
    @listen(setup_qdrant)
    def get_natal_chart_data(self):
        # unchanged

    @timeit
    @track_token_usage
    @listen(get_natal_chart_data)
    def generate_natal_analysis(self):
        """Single optimized analysis crew replaces GPT + Gemini + merge."""
        inputs = {
            "name": self.state.name,
            "date_of_birth": self.state.dob,
            "place_of_birth": self.state.birthplace,
            "today": self.state.today,
            "natal_chart": self.state.natal_chart
        }
        result = AnalysisCrew().crew().kickoff(inputs=inputs)
        self.state.natal_analysis = result.raw
        return result

    @timeit
    @track_token_usage
    @listen(generate_natal_analysis)
    def review_natal_analysis(self):
        """Critic + enhancer review with chart data for factual verification."""
        inputs = {
            "name": self.state.name,
            "report": self.state.natal_analysis,
            "natal_chart": self.state.natal_chart,
            "today": self.state.today,
            "date_of_birth": self.state.dob,
            "place_of_birth": self.state.birthplace
        }
        result = ReviewCrew().crew().kickoff(inputs=inputs)
        self.state.final_natal_analysis = result.raw
        return result

    @timeit
    @track_token_usage
    @listen(review_natal_analysis)
    def format_natal_analysis(self):
        """HTML tagging for PDF rendering — separate from content review."""
        inputs = {
            "name": self.state.name,
            "report": self.state.final_natal_analysis,
            "today": self.state.today,
            "date_of_birth": self.state.dob,
            "place_of_birth": self.state.birthplace
        }
        result = FormattingCrew().crew().kickoff(inputs=inputs)
        self.state.final_natal_analysis = result.raw
        return result

    @timeit
    @listen(format_natal_analysis)
    def get_kerykeion_natal_chart(self):
        # unchanged

    @timeit
    @listen(get_kerykeion_natal_chart)
    def save_natal_analysis(self):
        # unchanged

    @timeit
    @track_token_usage
    @listen(save_natal_analysis)
    def send_natal_analysis(self):
        # unchanged — update input key from merged_natal_analysis to final_natal_analysis

    @listen(send_natal_analysis)
    def print_final_stats(self):
        # unchanged
```

### 4c. Update imports

Remove:
```python
from natal_reader.crews.gpt_analysis_crew.gpt_analysis_crew import GPTAnalysisCrew
from natal_reader.crews.gemini_analysis_crew.gemini_analysis_crew import GeminiAnalysisCrew
from natal_reader.crews.merge_crew.merge_crew import MergeCrew
```

Add:
```python
from natal_reader.crews.analysis_crew.analysis_crew import AnalysisCrew
from natal_reader.crews.formatting_crew.formatting_crew import FormattingCrew
```

**Acceptance criteria:**
- Full pipeline runs end-to-end with a test subject
- Output PDF is generated and saved
- Gmail draft is created
- Timings file records all steps
- Total pipeline is faster than current (fewer LLM calls)

---

## Step 5: Clean Up

### 5a. Delete obsolete crew directories

- `src/natal_reader/crews/gpt_analysis_crew/` — entire directory
- `src/natal_reader/crews/gemini_analysis_crew/` — entire directory
- `src/natal_reader/crews/merge_crew/` — entire directory

### 5b. Clean up review_crew

- Remove `markdown_enhancer` agent from `review_crew/config/agents.yaml`
- Remove `markdown_enhancement_task` from `review_crew/config/tasks.yaml`
- Remove `markdown_enhancer` agent and task methods from `review_crew.py`
- Remove unused LLM definitions (`gpt41mini`, `gpt41nano`) if no longer referenced

### 5c. Update Qdrant search tool defaults

**File:** `src/natal_reader/tools/qdrant_search_tool.py`

```python
limit: int = Field(default=8, ...)        # was 5
score_threshold: float = Field(default=0.3, ...)  # was 0.2
```

### 5d. Update CLAUDE.md

Reflect the new architecture: single analysis crew, separate formatting crew, 8-step pipeline.

**Acceptance criteria:**
- No references to deleted crews in any remaining file
- `grep -r "gpt_analysis_crew\|gemini_analysis_crew\|merge_crew" src/` returns no results
- CLAUDE.md accurately describes the new pipeline

---

## Step 6: Validation & Testing

### 6a. End-to-end test run

Run the full pipeline on an existing subject JSON and verify:
- [ ] Chart data includes new pre-computed patterns section
- [ ] Analysis crew produces a single interpretation + report
- [ ] Critic references chart data in its critique
- [ ] Enhancer does not introduce new chart features
- [ ] Formatting crew produces valid HTML-tagged markdown
- [ ] PDF renders correctly with styling
- [ ] Gmail draft is created with attachment
- [ ] Total execution time is shorter than the old pipeline
- [ ] Token usage is lower than the old pipeline

### 6b. Quality comparison

Run the same subject through both old and new pipelines. Compare:
- Factual accuracy (degrees, aspects, house placements)
- Interpretive depth and nuance
- Narrative coherence and readability
- Report length and section completeness
- Glossary completeness

---

## Implementation Order

| Order | Step | Effort | Risk |
|-------|------|--------|------|
| 1 | Step 1: Enrich chart data | Low | Low — additive, no existing behavior changed |
| 2 | Step 2: Create analysis crew | Medium | Medium — new crew must match or exceed dual-crew quality |
| 3 | Step 3: Restructure review crew | Medium | Low — mostly config changes |
| 4 | Step 4: Update flow pipeline | Medium | Medium — wiring changes, must test end-to-end |
| 5 | Step 5: Clean up | Low | Low — deletion of unused code |
| 6 | Step 6: Validation | Low | N/A — verification only |

**Estimated total:** Steps are sequential — each depends on the prior. Step 2 is the critical path; the quality of the single analysis crew determines whether the architectural simplification is a net improvement.
