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
    section = chart_text.split("Tight Aspects (Orb < 2°):")[1].split("\n\nAnaretic Placements")[0]
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


def test_whole_sign_house_shown(chart_text):
    assert re.search(r"House: \d+(st|nd|rd|th) House \(Placidus\) \| \d+(st|nd|rd|th) \(whole sign\)", chart_text)


def test_house_system_is_placidus(chart_text):
    match = re.search(r"House System: (.+)", chart_text)
    assert match
    assert match.group(1).startswith("Placidus")


def test_part_of_fortune_and_syzygy_present(chart_text):
    assert "* Part of Fortune (Point)" in chart_text
    assert "* Syzygy (Point)" in chart_text


def test_anaretic_section_present(chart_text):
    assert "Anaretic Placements (29th degree):" in chart_text


def test_configurations_section_present(chart_text):
    assert "Aspect Configurations:" in chart_text
    assert "T-Squares:" in chart_text
    assert "Grand Trines:" in chart_text
    assert "Grand Crosses:" in chart_text


def test_explicit_timezone_matches_inferred(chart_text):
    from datetime import datetime

    from natal_reader.utils.immanuel_natal_chart import get_natal_chart
    from conftest import FIXTURE_SUBJECT

    dob = datetime.strptime(FIXTURE_SUBJECT["date_of_birth"], "%Y-%m-%d %H:%M:%S")
    bp = FIXTURE_SUBJECT["birthplace"]
    explicit_tz_text = get_natal_chart(dob, bp["latitude"], bp["longitude"], timezone=bp["timezone"])

    assert explicit_tz_text == chart_text


def test_find_mutual_receptions():
    from natal_reader.utils.immanuel_natal_chart import find_mutual_receptions

    # Mars in Cancer (ruled by Moon) and Moon in Aries (ruled by Mars): mutual reception.
    positions = {"Sun": "Leo", "Moon": "Aries", "Mars": "Cancer", "Venus": "Taurus"}
    receptions = find_mutual_receptions(positions)

    assert len(receptions) == 1
    assert "Moon" in receptions[0] and "Mars" in receptions[0]


def test_find_mutual_receptions_none():
    from natal_reader.utils.immanuel_natal_chart import find_mutual_receptions

    positions = {"Sun": "Leo", "Moon": "Taurus", "Mars": "Cancer"}
    assert find_mutual_receptions(positions) == []


def test_unknown_time_chart_omits_houses():
    from datetime import datetime

    from natal_reader.utils.immanuel_natal_chart import get_natal_chart
    from conftest import FIXTURE_SUBJECT

    dob = datetime.strptime(FIXTURE_SUBJECT["date_of_birth"], "%Y-%m-%d %H:%M:%S")
    bp = FIXTURE_SUBJECT["birthplace"]
    out = get_natal_chart(dob, bp["latitude"], bp["longitude"], bp["timezone"], time_known=False)

    assert "BIRTH TIME UNKNOWN" in out
    assert "Chart Ruler:" not in out
    assert "* Asc (Angle)" not in out
    assert "* MC (Angle)" not in out
    assert "Hemisphere Balance:\n" not in out


def test_known_time_unchanged(chart_text):
    assert "BIRTH TIME UNKNOWN" not in chart_text
    assert "Chart Ruler:" in chart_text
    assert "* Asc (Angle)" in chart_text
