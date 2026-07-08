from natal_reader.utils.report_verifier import verify_report

FACTS = {
    "planet_signs": {"Sun": "Cancer", "Moon": "Cancer", "Mars": "Sagittarius", "Venus": "Gemini"},
    "planet_houses_placidus": {"Sun": 7, "Moon": 7, "Mars": 12},
    "planet_houses_whole_sign": {"Sun": 8, "Moon": 8, "Mars": 1},
    "aspects": [
        {"a": "Sun", "b": "Moon", "type": "Conjunction", "orb": 10.0},
        {"a": "Venus", "b": "Mars", "type": "Opposition", "orb": 10.0},
    ],
}


def test_verify_report_catches_planted_errors():
    report = """
    Your Sun is in Aries, a bold placement for your core identity.
    The Moon sits in Cancer in the 3rd house, bringing emotional depth to partnerships.
    Mars in Sagittarius energizes your outlook in the 12th house.
    The Sun Conjunction Moon links your identity and instincts.
    Venus Square Mars creates friction between your values and drive.
    """
    mismatches = verify_report(report, FACTS)

    assert len(mismatches) == 3
    assert any("Sun in Aries" in m for m in mismatches)
    assert any("Venus Square Mars" in m for m in mismatches)
    assert any("Moon in house 3" in m for m in mismatches)


def test_verify_report_no_false_positives_on_correct_claims():
    report = """
    Your Sun is in Cancer, bringing warmth and sensitivity.
    The Moon is in Cancer in the 7th house.
    Sun Conjunction Moon links identity and instinct closely.
    """
    assert verify_report(report, FACTS) == []


def test_verify_report_skips_unknown_planet_house_number():
    report = "Mars in the 1st house channels assertive energy (whole-sign)."
    assert verify_report(report, FACTS) == []
