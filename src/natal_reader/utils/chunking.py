import re

CHUNK_SIZE = 1500
CHUNK_OVERLAP = 250

_HEADING_RE = re.compile(r"^(#{1,3})\s+(.+?)\s*$")


def _split_by_headings(content: str) -> list[tuple[str, str]]:
    """Split content into (heading_path, section_text) pairs on H1-H3
    headings, tracking a heading stack so nested sections get a full
    'H1 > H2 > H3' path."""
    sections = []
    heading_stack: list[tuple[int, str]] = []
    current_lines: list[str] = []

    def flush():
        text = "".join(current_lines)
        if text.strip():
            heading_path = " > ".join(title for _, title in heading_stack)
            sections.append((heading_path, text))

    for line in content.splitlines(keepends=True):
        match = _HEADING_RE.match(line)
        if match:
            flush()
            current_lines = [line]
            level = len(match.group(1))
            title = match.group(2).strip()
            heading_stack = [(lvl, t) for lvl, t in heading_stack if lvl < level]
            heading_stack.append((level, title))
        else:
            current_lines.append(line)
    flush()

    return sections


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Character-window chunking with natural-break look-back (unchanged from
    the original implementation), applied within a single heading section."""
    chunks = []
    current_position = 0
    content_length = len(text)

    while current_position < content_length:
        end_position = min(current_position + chunk_size, content_length)

        if end_position < content_length:
            look_back_range = min(100, chunk_size // 10)
            natural_break_pos = text.rfind("\n\n", end_position - look_back_range, end_position)

            if natural_break_pos != -1:
                end_position = natural_break_pos
            else:
                for punct in [". ", "! ", "? ", "\n"]:
                    natural_break_pos = text.rfind(punct, end_position - look_back_range, end_position)
                    if natural_break_pos != -1:
                        end_position = natural_break_pos + 1
                        break

        chunk = text[current_position:end_position].strip()
        if chunk:
            chunks.append(chunk)

        current_position = end_position - chunk_overlap if end_position < content_length else content_length

    return chunks


def chunk_markdown(content: str, source: str) -> list[dict]:
    """Heading-aware chunking (P1-2): splits on H1-H3 headings first, then
    applies the character window within each section, and prepends
    '{source} > {heading path}' to every chunk so a retrieved chunk is never
    severed from the heading that names the placement it describes."""
    if not content.strip():
        return []

    chunks = []
    for heading_path, section_text in _split_by_headings(content):
        prefix = f"{source} > {heading_path}\n\n" if heading_path else f"{source}\n\n"
        for text_chunk in _chunk_text(section_text):
            chunks.append({
                "text": prefix + text_chunk,
                "source": source,
                "heading": heading_path,
            })
    return chunks
