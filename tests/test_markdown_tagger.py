from natal_reader.utils.markdown_tagger import tag_report

SAMPLE_REPORT = """Some internal commentary that should never appear in the output.

# Natal Chart for John Doe
Date of Report: Monday, 01 January 2026

[natal_chart]

**Date of Birth:** 18:45, 13 July 1969
**Place of Birth:** Croydon, UK

## Introduction

Your Sun is in Cancer, forming a Trine to Neptune. This is a very strong connection.
The Moon in Cancer creates a Conjunction with Mercury, a strong pattern.

| Planet | Sign | House |
|---|---|---|
| Sun | Cancer | 7th |
| Moon | Cancer | 7th |

## Glossary

- **Sect**: whether a chart is diurnal or nocturnal.
- **Stellium**: three or more planets in the same sign or house.
"""


def test_strips_pre_title_commentary():
    out = tag_report(SAMPLE_REPORT)
    assert "internal commentary" not in out
    assert out.startswith("# Natal Chart for John Doe")


def test_preserves_natal_chart_placeholder():
    out = tag_report(SAMPLE_REPORT)
    assert "[natal_chart]" in out


def test_headings_get_ids():
    out = tag_report(SAMPLE_REPORT)
    assert '<h2 id="introduction">Introduction</h2>' in out
    assert '<h2 id="glossary">Glossary</h2>' in out


def test_glyph_appears_once_per_planet():
    out = tag_report(SAMPLE_REPORT)
    assert out.count("☉") == 1  # Sun
    assert out.count("☽") == 1  # Moon


def test_table_converted_to_html():
    out = tag_report(SAMPLE_REPORT)
    assert '<table class="planet-table">' in out
    assert "| Planet | Sign | House |" not in out


def test_glossary_terms_get_definition_divs():
    out = tag_report(SAMPLE_REPORT)
    assert '<div class="definition-term">Sect</div>' in out
    assert '<div class="definition-desc">whether a chart is diurnal or nocturnal.</div>' in out


def test_glossary_terms_not_double_tagged_with_planet_spans():
    out = tag_report(SAMPLE_REPORT)
    glossary_section = out.split('<h2 id="glossary">')[1]
    assert 'class="planet-name' not in glossary_section


def test_idempotent_on_second_pass():
    once = tag_report(SAMPLE_REPORT)
    twice = tag_report(once)
    assert once == twice


def test_bold_colon_outside_glossary_not_converted():
    report = """# Natal Chart for Jane Doe
[natal_chart]

## Introduction

**Note**: this is a regular bolded note, not a glossary entry.
"""
    out = tag_report(report)
    assert 'class="definition-term"' not in out
