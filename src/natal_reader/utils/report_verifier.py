import re

PLANETS = [
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter",
    "Saturn", "Uranus", "Neptune", "Pluto",
]
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
ASPECT_TYPES = ["Conjunction", "Sextile", "Square", "Trine", "Opposition", "Quincunx"]

_TAG_RE = re.compile(r"<[^>]+>")

_PLANET_IN_SIGN_RE = re.compile(
    rf"\b({'|'.join(PLANETS)})\b[^.\n]{{0,20}}?\bin\b[^.\n]{{0,20}}?\b({'|'.join(SIGNS)})\b",
    re.IGNORECASE,
)
_PLANET_IN_HOUSE_RE = re.compile(
    rf"\b({'|'.join(PLANETS)})\b[^.\n]{{0,20}}?\bin\b(?:\s+the)?\s+(\d+)(?:st|nd|rd|th)?\s+house\b",
    re.IGNORECASE,
)
_ASPECT_RE = re.compile(
    rf"\b({'|'.join(PLANETS)})\b[^.\n]{{0,15}}?\b({'|'.join(ASPECT_TYPES)})\b[^.\n]{{0,15}}?\b({'|'.join(PLANETS)})\b",
    re.IGNORECASE,
)


def _strip_markup(text: str) -> str:
    return _TAG_RE.sub("", text)


def verify_report(report_text: str, facts: dict) -> list[str]:
    """Precision-over-recall check of report claims against structured chart
    facts. Returns human-readable mismatch strings; an empty list means no
    mismatches were found (not necessarily that none exist — ambiguous
    sentences are skipped rather than flagged)."""
    text = _strip_markup(report_text)
    mismatches = []

    planet_signs = facts.get("planet_signs", {})
    for match in _PLANET_IN_SIGN_RE.finditer(text):
        planet, sign = match.group(1), match.group(2)
        planet, sign = planet.title(), sign.title()
        expected_sign = planet_signs.get(planet)
        if expected_sign and expected_sign != sign:
            mismatches.append(
                f"Report says {planet} in {sign}, but chart data has {planet} in {expected_sign}."
            )

    houses_placidus = facts.get("planet_houses_placidus", {})
    houses_whole_sign = facts.get("planet_houses_whole_sign", {})
    for match in _PLANET_IN_HOUSE_RE.finditer(text):
        planet, house_str = match.group(1).title(), match.group(2)
        try:
            house_number = int(house_str)
        except ValueError:
            continue
        expected_placidus = houses_placidus.get(planet)
        expected_whole_sign = houses_whole_sign.get(planet)
        if expected_placidus is None and expected_whole_sign is None:
            continue
        if house_number not in (expected_placidus, expected_whole_sign):
            mismatches.append(
                f"Report says {planet} in house {house_number}, but chart data has "
                f"house {expected_placidus} (Placidus) / {expected_whole_sign} (whole sign)."
            )

    aspect_lookup = {}
    for aspect in facts.get("aspects", []):
        pair = frozenset((aspect.get("a"), aspect.get("b")))
        aspect_lookup[pair] = aspect.get("type")

    for match in _ASPECT_RE.finditer(text):
        planet_a, aspect_type, planet_b = match.group(1).title(), match.group(2).title(), match.group(3).title()
        if planet_a == planet_b:
            continue
        pair = frozenset((planet_a, planet_b))
        actual_type = aspect_lookup.get(pair)
        if actual_type is None:
            mismatches.append(
                f"Report claims {planet_a} {aspect_type} {planet_b}, but no such aspect exists in the chart data."
            )
        elif actual_type != aspect_type:
            mismatches.append(
                f"Report claims {planet_a} {aspect_type} {planet_b}, but chart data has "
                f"{planet_a} {actual_type} {planet_b}."
            )

    return mismatches
