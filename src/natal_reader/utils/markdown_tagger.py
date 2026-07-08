import re

PLANET_GLYPHS = {
    "Sun": "☉", "Moon": "☽", "Mercury": "☿", "Venus": "♀", "Mars": "♂",
    "Jupiter": "♃", "Saturn": "♄", "Uranus": "♅", "Neptune": "♆", "Pluto": "♇",
    "Chiron": "⚷", "North Node": "☊", "South Node": "☋", "Part of Fortune": "⊗",
}
PLANET_CLASSES = {
    "Sun": "sun", "Moon": "moon", "Mercury": "mercury", "Venus": "venus", "Mars": "mars",
    "Jupiter": "jupiter", "Saturn": "saturn", "Uranus": "uranus", "Neptune": "neptune", "Pluto": "pluto",
}
SIGN_GLYPHS = {
    "Aries": "♈", "Taurus": "♉", "Gemini": "♊", "Cancer": "♋", "Leo": "♌", "Virgo": "♍",
    "Libra": "♎", "Scorpio": "♏", "Sagittarius": "♐", "Capricorn": "♑", "Aquarius": "♒", "Pisces": "♓",
}
ASPECT_GLYPHS = {
    "Conjunction": "☌", "Opposition": "☍", "Square": "☐", "Trine": "Δ", "Quincunx": "⊼",
}
# Order matters: longer/more-specific labels must match before their substrings ("very strong" before "strong").
STRENGTH_LEVELS = ["very strong", "very weak", "strong", "moderate", "weak"]

_PLACEHOLDER_TEMPLATE = "\x00BLOCK{}\x00"


def _slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[\s]+", "-", text)


def _strip_pre_title_commentary(md: str) -> str:
    match = re.search(r"^# Natal Chart for", md, re.MULTILINE)
    return md[match.start():] if match else md


def _convert_headings(md: str) -> str:
    def replace_heading(match: re.Match) -> str:
        hashes, text = match.group(1), match.group(2).strip()
        level = len(hashes)
        if level == 2:
            return f'<h2 id="{_slugify(text)}">{text}</h2>'
        return f"<h{level}>{text}</h{level}>"

    return re.sub(r"^(#{2,6}) (.+)$", replace_heading, md, flags=re.MULTILINE)


def _convert_tables(md: str) -> str:
    lines = md.splitlines()
    output = []
    i = 0
    while i < len(lines):
        line = lines[i]
        is_table_row = line.strip().startswith("|") and line.strip().endswith("|")
        is_separator = bool(re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1])) if is_table_row and i + 1 < len(lines) else False

        if is_table_row and is_separator:
            header_cells = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 2  # skip header + separator
            body_rows = []
            while i < len(lines) and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                body_rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1

            html = ['<table class="planet-table">', f"<caption>{header_cells[0]}</caption>", "<thead><tr>"]
            html += [f"<th>{cell}</th>" for cell in header_cells]
            html.append("</tr></thead>")
            html.append("<tbody>")
            for row in body_rows:
                html.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>")
            html.append("</tbody></table>")
            output.append("\n".join(html))
        else:
            output.append(line)
            i += 1

    return "\n".join(output)


def _convert_glossary(md: str) -> str:
    """Only converts **Term**: def lines inside the Glossary section — the same
    bold-then-colon shape appears incidentally elsewhere in the report and
    must not be turned into definition divs there."""
    section_match = re.search(r"^##\s+Glossary.*$", md, re.MULTILINE)
    if not section_match:
        return md

    next_heading = re.search(r"^##\s", md[section_match.end():], re.MULTILINE)
    section_end = section_match.end() + next_heading.start() if next_heading else len(md)

    section = md[section_match.end():section_end]
    tagged_section = re.sub(
        r"^(?:[*-]\s*)?\*\*(.+?)\*\*:?\s*(.+)$",
        lambda m: f'<div class="definition-term">{m.group(1)}</div><div class="definition-desc">{m.group(2)}</div>',
        section,
        flags=re.MULTILINE,
    )
    return md[:section_match.end()] + tagged_section + md[section_end:]


def _mask_glossary_and_placeholder(md: str) -> tuple[str, list[str]]:
    """Extract glossary divs and the [natal_chart] placeholder into placeholder
    tokens before inline span injection, so glyphs/spans never touch them."""
    blocks: list[str] = []

    def _mask(match: re.Match) -> str:
        blocks.append(match.group(0))
        return _PLACEHOLDER_TEMPLATE.format(len(blocks) - 1)

    md = re.sub(r'<div class="definition-term">.*?</div><div class="definition-desc">.*?</div>', _mask, md)
    md = re.sub(r"\[natal_chart\]", _mask, md)
    return md, blocks


def _unmask(md: str, blocks: list[str]) -> str:
    def _restore(match: re.Match) -> str:
        return blocks[int(match.group(1))]

    return re.sub(r"\x00BLOCK(\d+)\x00", _restore, md)


def _in_span(text: str, pos: int) -> bool:
    """True if pos falls inside an already-emitted <span ...>...</span>, so
    span injection stays idempotent on repeated runs."""
    preceding_open = text.rfind("<span", 0, pos)
    if preceding_open == -1:
        return False
    preceding_close = text.rfind("</span>", 0, pos)
    return preceding_close < preceding_open


def _inject_planet_spans(md: str) -> str:
    seen_glyph = set()
    for name in sorted(PLANET_CLASSES, key=len, reverse=True):
        css_class = PLANET_CLASSES[name]
        pattern = re.compile(rf"\b{name}\b")

        def replace(match: re.Match, name=name, css_class=css_class) -> str:
            if _in_span(md, match.start()):
                return match.group(0)
            if name not in seen_glyph and name in PLANET_GLYPHS:
                seen_glyph.add(name)
                return (
                    f'<span class="planet-name {css_class}">{name}</span>'
                    f'<span class="astro-symbol"> ({PLANET_GLYPHS[name]})</span>'
                )
            return f'<span class="planet-name {css_class}">{name}</span>'

        md = pattern.sub(replace, md)
    return md


def _inject_sign_spans(md: str) -> str:
    seen_glyph = set()
    for name, glyph in SIGN_GLYPHS.items():
        css_class = f"sign-{name.lower()}"
        pattern = re.compile(rf"\b{name}\b")

        def replace(match: re.Match, name=name, css_class=css_class, glyph=glyph) -> str:
            if _in_span(md, match.start()):
                return match.group(0)
            if name not in seen_glyph:
                seen_glyph.add(name)
                return f'<span class="{css_class}">{name} ({glyph})</span>'
            return f'<span class="{css_class}">{name}</span>'

        md = pattern.sub(replace, md)
    return md


def _inject_aspect_spans(md: str) -> str:
    seen_glyph = set()
    for name, glyph in ASPECT_GLYPHS.items():
        css_class = f"aspect-{name.lower()}"
        pattern = re.compile(rf"\b{name}\b", re.IGNORECASE)

        def replace(match: re.Match, name=name, css_class=css_class, glyph=glyph) -> str:
            if _in_span(md, match.start()):
                return match.group(0)
            matched_text = match.group(0)
            if name not in seen_glyph:
                seen_glyph.add(name)
                return f'<span class="{css_class}">{matched_text} ({glyph})</span>'
            return f'<span class="{css_class}">{matched_text}</span>'

        md = pattern.sub(replace, md)
    return md


def _inject_strength_spans(md: str) -> str:
    for level in STRENGTH_LEVELS:
        css_class = level.replace(" ", "-")
        pattern = re.compile(rf"\b{level}\b", re.IGNORECASE)

        def replace(match: re.Match, css_class=css_class) -> str:
            if _in_span(md, match.start()):
                return match.group(0)
            return f'<span class="{css_class}">{match.group(0)}</span>'

        md = pattern.sub(replace, md)
    return md


def extract_sections_by_heading(tagged_report: str, heading_keywords: list[str]) -> str:
    """Return only the <h2> sections whose id or title contains any of
    heading_keywords (case-insensitive). Used to give the email-writing task
    just the Introduction + Guidance sections instead of the full 8-12k-word
    report (P2-8) — email_writing_task only needs enough to write a subject
    line and short body."""
    sections = re.split(r"(?=<h2 )", tagged_report)
    matched = []
    for section in sections:
        heading_match = re.match(r'<h2 id="([^"]*)">([^<]*)</h2>', section)
        if not heading_match:
            continue
        heading_id, heading_title = heading_match.groups()
        haystack = f"{heading_id} {heading_title}".lower()
        if any(keyword.lower() in haystack for keyword in heading_keywords):
            matched.append(section.strip())
    return "\n\n".join(matched)


def tag_report(md: str) -> str:
    """Deterministic replacement for formatting_crew's LLM markdown-tagging pass
    (P1-4): every rule in formatting_crew/config/tasks.yaml is mechanical, so
    none of it needs an LLM, and this can't truncate, paraphrase, or drop
    sections the way a full-report LLM regeneration can."""
    md = _strip_pre_title_commentary(md)
    md = _convert_tables(md)
    md = _convert_glossary(md)
    md = _convert_headings(md)

    md, blocks = _mask_glossary_and_placeholder(md)
    md = _inject_planet_spans(md)
    md = _inject_sign_spans(md)
    md = _inject_aspect_spans(md)
    md = _inject_strength_spans(md)
    md = _unmask(md, blocks)

    return md
