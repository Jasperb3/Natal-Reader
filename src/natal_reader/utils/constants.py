from datetime import datetime
import json
from pathlib import Path

NOW_DT: datetime = datetime.now()
NOW: str = NOW_DT.strftime("%Y-%m-%d %H-%M")
TIMESTAMP: str = NOW_DT.strftime("%Y-%m-%d_%H-%M-%S")
DATE_TODAY: str = NOW_DT.strftime("%Y-%m-%d")

OUTPUT_DIR = Path(f'/home/j/ai/crewAI/astro/natal_reader/natal_reader/outputs/{DATE_TODAY}')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CREW_OUTPUTS_DIR = Path(f'/home/j/ai/crewAI/astro/natal_reader/natal_reader/crew_outputs/{TIMESTAMP}')
CREW_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

CHARTS_DIR = OUTPUT_DIR / 'charts'
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

DOCS_DIR = Path("/home/j/ai/crewAI/astro/natal_reader/natal_reader/astro_docs")
DOCS_DIR.mkdir(parents=True, exist_ok=True)

SUBJECT_DIR = Path(__file__).parent.parent / "subjects"
SUBJECT_DIR.mkdir(parents=True, exist_ok=True)

CSS_FILE = Path('/home/j/ai/crewAI/astro/natal_reader/natal_reader/src/natal_reader/utils/styling.css')


