from md2pdf.core import md2pdf
from pathlib import Path
from natal_reader.utils.constants import CSS_FILE, CHARTS_DIR

def convert_md_to_pdf(md_file_path: Path) -> Path:
    """Convert a markdown file to a PDF file."""
    pdf_file_path = Path(md_file_path).with_suffix('.pdf')

    md2pdf(pdf_file_path,
           md_file_path=md_file_path,
           base_url=CHARTS_DIR,
           css_file_path=CSS_FILE
    )

    return pdf_file_path


if __name__ == "__main__":
    md = '/home/j/ai/crewAI/astro/transit_reader_II/transit_reader/outputs/2025-04-18/Benjamin_Jasper_2025-04-18_20-58-23.md'
    pdf = convert_md_to_pdf(md)
    print(f"PDF file saved to {pdf}")