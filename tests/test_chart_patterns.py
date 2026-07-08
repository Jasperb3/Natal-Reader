import re

TRADITIONAL_RULERS = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Mars",
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}


def test_tight_aspects_are_unique(chart_text):
    section = chart_text.split("Tight Aspects (Orb < 2°):")[1].split("-" * 25)[0]
    lines = [line.strip("- ").strip() for line in section.splitlines() if line.strip().startswith("-")]

    pattern = re.compile(r"^(.+?) (Conjunction|Opposition|Square|Trine|Sextile|Quincunx) (.+?) \(Orb: [\d.]+°\)$")
    pairs = []
    for line in lines:
        match = pattern.match(line)
        assert match, f"unparsable tight-aspect line: {line!r}"
        active, aspect_type, passive = match.groups()
        pairs.append(frozenset((active, passive, aspect_type)))

    assert len(pairs) == len(set(pairs)), f"duplicate tight-aspect pairs found: {lines}"


def test_chart_ruler_traditional(chart_text):
    asc_block = chart_text.split("* Asc (Angle)")[1].split("\n\n")[0]
    sign_match = re.search(r"Position: [\d°'\"]+ (\w+) ", asc_block)
    assert sign_match, "could not find Ascendant sign"
    asc_sign = sign_match.group(1)

    ruler_match = re.search(r"Chart Ruler: (\w+) \(ruler of (\w+) Ascendant\)", chart_text)
    assert ruler_match, "Chart Ruler line missing"
    ruler_name, ruler_asc_sign = ruler_match.groups()

    assert ruler_asc_sign == asc_sign
    assert ruler_name == TRADITIONAL_RULERS[asc_sign]


def test_house_system_reported(chart_text):
    match = re.search(r"House System: (.+)", chart_text)
    assert match
    assert match.group(1).strip()


def test_timezone_localization(chart_text):
    match = re.search(r"Birth Date/Time: (.+)", chart_text)
    assert match
    assert "+01:00" in match.group(1)


def test_stellium_section_exists(chart_text):
    assert "Stelliums Detected:" in chart_text
