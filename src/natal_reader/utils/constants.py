from datetime import datetime, timezone
from pathlib import Path

# utils -> natal_reader -> src -> project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]

NOW_DT: datetime = datetime.now(timezone.utc)
NOW: str = NOW_DT.strftime("%Y-%m-%d %H-%M")
TIMESTAMP: str = NOW_DT.strftime("%Y%m%d_%H%M%S")
DATE_TODAY: str = NOW_DT.strftime("%Y-%m-%d")

OUTPUT_DIR = PROJECT_ROOT / "outputs" / DATE_TODAY
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CREW_OUTPUTS_DIR = PROJECT_ROOT / "crew_outputs" / TIMESTAMP
CREW_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

CHARTS_DIR = OUTPUT_DIR / 'charts'
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

DOCS_DIR = PROJECT_ROOT / "astro_docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

SUBJECT_DIR = Path(__file__).parent.parent / "subjects"
SUBJECT_DIR.mkdir(parents=True, exist_ok=True)

CSS_FILE = PROJECT_ROOT / "src" / "natal_reader" / "utils" / "astro_styling.css"


