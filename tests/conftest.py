from datetime import datetime

import pytest

FIXTURE_SUBJECT = {
    "name": "John Doe",
    "date_of_birth": "1969-07-13 18:45:00",
    "birthplace": {
        "longitude": -0.1093,
        "latitude": 51.3887,
        "place": "Croydon",
        "country": "UK",
        "timezone": "Europe/London",
    },
}


@pytest.fixture(scope="session")
def chart_text():
    from natal_reader.utils.immanuel_natal_chart import get_natal_chart

    dob = datetime.strptime(FIXTURE_SUBJECT["date_of_birth"], "%Y-%m-%d %H:%M:%S")
    bp = FIXTURE_SUBJECT["birthplace"]
    return get_natal_chart(dob, bp["latitude"], bp["longitude"])
